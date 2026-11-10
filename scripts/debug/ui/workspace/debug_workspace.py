"""Debug script: launch the Workspace with the real TomographyEditor.

This script is a development tool. It is NOT part of production.

It builds a Workspace with:
- A real EditorRegistry populated with TomographyEditor.
- A ToolRegistry with LogTool and ToggleTool.
- A real ThemeService (dark, in-memory settings) with the QSS applied.
- A UnicodeIconProvider bound to the same ThemeService.
- A fake, coherent ProjectContext (ADR-0006 requires one).
- A synthetic Volume (sphere shell, ~2000 HU) injected in the
  DomainObjectStore and in the SceneQuery, so the four Views have
  something to render (2D MPR slices + 3D volume).
- A ModuleUISpec with a single Central Area hosting the
  TomographyEditor (editor.tomography).

What you should see (G2 / ADR-0013 §2.6):

- The Top Bar floating over the Central Area.
- A 2x2 grid of Views inside the TomographyEditor:
    Axial (top-left) | Coronal (top-right)
    Sagittal (bottom-left) | 3D (bottom-right)
- Each View wrapped in its own container with:
    - A vertical Toolbar on the LEFT (Tools).
    - A vertical Toolbar on the RIGHT (Display).
- 2D Views show the synthetic volume's slices (a circular shell).
- The 3D View shows the shell rendered with the "bone" preset,
  on the dark blue VTK background.
- No QTabWidget at the bottom of the Area.
- No Editor-level Toolbar wrapping the grid.

The Toolbars are declared with ACTIVE_ONLY, but the visibility
behavior is not implemented yet (Sprint H). All four pairs are
visible simultaneously here — that is expected for G2.

Run with:

    .venv\\Scripts\\python.exe scripts\\debug\\ui\\workspace\\debug_workspace.py

Close the window to exit.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime

# ---------------------------------------------------------------------
# VTK / OpenGL configuration (must run before the first QApplication)
# ---------------------------------------------------------------------
# Mirrors src/cranioz/__main__.py. If AA_ShareOpenGLContexts and the
# Core-profile QSurfaceFormat are not set before QApplication is
# created, QVTKRenderWindowInteractor fails to render (white or black
# 3D viewport). Qt freezes these settings at construction time.
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QSurfaceFormat
from PySide6.QtWidgets import QApplication, QMainWindow, QSplitter, QWidget

QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
_fmt = QSurfaceFormat()
_fmt.setDepthBufferSize(24)
_fmt.setStencilBufferSize(8)
_fmt.setVersion(3, 2)
_fmt.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)
QSurfaceFormat.setDefaultFormat(_fmt)

# ---------------------------------------------------------------------
# CranioZ imports
# ---------------------------------------------------------------------
import numpy as np

from cranioz.application.project.project_context import ProjectContext
from cranioz.application.scene.scene_query import InMemorySceneQuery
from cranioz.domain.imaging.image_metadata import ImageMetadata
from cranioz.domain.imaging.volume import IntensityScale, Volume
from cranioz.domain.imaging.volume_geometry import VolumeGeometry
from cranioz.domain.imaging.volume_provenance import VolumeProvenance
from cranioz.domain.patient.enums.patient_sex import PatientSex
from cranioz.domain.patient.patient_summary import PatientSummary
from cranioz.domain.patient.value_objects.patient_id import PatientId
from cranioz.domain.project.project_id import ProjectId
from cranioz.domain.project.project_metadata import ProjectMetadata
from cranioz.domain.project.project_status import ProjectStatus
from cranioz.domain.scene.domain_object_store import DomainObjectStore
from cranioz.infrastructure.settings.in_memory_settings_service import (
    InMemorySettingsService,
)
from cranioz.ui.editors.editor_registry import EditorRegistry
from cranioz.ui.editors.tomography.editor import TomographyEditor
from cranioz.ui.editors.viewport_3d.view import Viewport3DView
from cranioz.ui.icons.provider import IconProvider
from cranioz.ui.icons.unicode import UnicodeIconProvider
from cranioz.ui.theme.service import ThemeService
from cranioz.ui.theme.tokens import ThemeMode
from cranioz.ui.tools.builtin.log_tool import LogTool
from cranioz.ui.tools.builtin.toggle_tool import ToggleTool
from cranioz.ui.tools.registry.tool_registry import ToolRegistry
from cranioz.ui.workspace.areas.placement import Placement
from cranioz.ui.workspace.specs.area_spec import AreaSpec
from cranioz.ui.workspace.specs.editor_layout_spec import EditorLayoutSpec
from cranioz.ui.workspace.specs.module_ui_spec import ModuleUISpec
from cranioz.ui.workspace.workspace import Workspace

# ----- Project context ----------------------------------------------


def build_project_context() -> ProjectContext:
    """Build a fake, coherent ProjectContext for the debug Workspace."""
    pid = ProjectId("p-debug")
    now = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
    return ProjectContext(
        project_id=pid,
        metadata=ProjectMetadata(
            project_id=pid,
            project_name="Debug Case",
            patient_id="pat-debug",
            patient_display_name="Debug Patient",
            clinical_procedure="orthognathic",
            status=ProjectStatus.ACTIVE,
            created_at=now,
            updated_at=now,
            last_opened_at=None,
            schema_version=1,
        ),
        patient_summary=PatientSummary(
            patient_id=PatientId("pat-debug"),
            display_name="Debug Patient",
            birth_date=None,
            sex=PatientSex.MALE,
        ),
    )


# ----- Synthetic volume ---------------------------------------------


def build_synthetic_volume() -> Volume:
    """Build a small volume with a shell so the 3D View has something to show.

    The shell is a sphere of radius 20-30 voxels at ~2000 HU (bone-like
    intensity), embedded in air (-1000 HU). The 2D MPR Views render
    the slice through the middle; the 3D View renders the shell with
    the "bone" preset (HU-calibrated volume).
    """
    nz, ny, nx = 64, 64, 64
    grid = np.indices((nz, ny, nx))
    cz, cy, cx = nz / 2, ny / 2, nx / 2
    distance_sq = (
        (grid[0] - cz) ** 2
        + (grid[1] - cy) ** 2
        + (grid[2] - cx) ** 2
    )
    data = np.full((nz, ny, nx), -1000, dtype=np.int16)
    data[distance_sq < 30**2] = 500        # soft tissue shell
    data[distance_sq < 25**2] = 1500       # bone shell
    data[distance_sq < 10**2] = -1000      # air core

    geometry = VolumeGeometry.identity(
        dimensions=(nx, ny, nz),
        spacing=(1.0, 1.0, 1.0),
        origin=(0.0, 0.0, 0.0),
    )
    return Volume(
        data=data,
        geometry=geometry,
        metadata=ImageMetadata(),
        intensity_scale=IntensityScale.HU,
        provenance=VolumeProvenance(
            import_timestamp=datetime(2026, 1, 1, 12, 0, tzinfo=UTC),
        ),
        volume_id="volume-debug",
    )


# ----- Editor registry ----------------------------------------------


def build_editor_registry() -> EditorRegistry:
    """Register the real TomographyEditor."""
    registry = EditorRegistry()
    registry.register("editor.tomography", TomographyEditor)
    return registry


# ----- Tool registry ------------------------------------------------


def build_tool_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register("tool.log", LogTool)
    registry.register("tool.toggle", ToggleTool)
    return registry


# ----- ModuleUISpec -------------------------------------------------


def build_spec() -> ModuleUISpec:
    """Build a ModuleUISpec with a single Central Area hosting TomographyEditor."""
    return ModuleUISpec(
        areas=(
            AreaSpec(
                area_id="area.central",
                title="Tomography",
                placement=Placement.CENTRAL,
                editor_layout=EditorLayoutSpec.leaf("editor.tomography"),
            ),
        ),
    )


# ----- Visual diagnostics -------------------------------------------


def _dump_visual_state(workspace: Workspace) -> None:
    """Print the geometry of the AreaWidget, its QSplitters, and its Views.

    Helps diagnose visual regressions that structural tests cannot
    catch: a splitter whose children collapsed to zero, an overlay
    positioned before the window had geometry, a View whose 3D
    content is not initialized, etc.
    """
    print("\n=== Visual state dump ===")
    areas = workspace.areas()
    if not areas:
        print("  no areas")
        return

    for area in areas:
        widget = workspace._layout_renderer.cached_area_widget(area.area_id)  # noqa: SLF001
        if widget is None:
            print(f"  [{area.area_id}] no AreaWidget")
            continue
        print(f"  [{area.area_id}] geometry={widget.geometry()}")

        splitters = widget.findChildren(QSplitter)
        print(f"  [{area.area_id}] splitters={len(splitters)}")
        for i, sp in enumerate(splitters):
            print(
                f"    splitter[{i}] "
                f"orientation={sp.orientation().name} "
                f"sizes={sp.sizes()}"
            )
            for j in range(sp.count()):
                child = sp.widget(j)
                if child is not None:
                    print(
                        f"      child[{j}] "
                        f"objectName={child.objectName()!r} "
                        f"geometry={child.geometry()}"
                    )

        # View containers and their content
        view_containers = [
            w for w in widget.findChildren(QWidget)
            if w.objectName().startswith("view_container.")
        ]
        print(f"  [{area.area_id}] view_containers={len(view_containers)}")
        for vc in view_containers:
            print(
                f"    {vc.objectName()} "
                f"geometry={vc.geometry()}"
            )

        # The 3D View, if present
        viewports = widget.findChildren(Viewport3DView.__mro__[1])  # QWidget
        # (findChildren by base class would be noisy; instead look
        #  up the specific interactor name in the object tree.)
        interactors = widget.findChildren(QWidget, "viewport_3d.view.view.3d")
        for interactor in interactors:
            print(f"    viewport_3d.view.view.3d geometry={interactor.geometry()}")

        # Editor's internal state (only for debugging)
        for editor in area.editors():
            volume_flag = getattr(editor, "_volume_applied", None)
            if volume_flag is not None:
                print(f"    editor[{editor.editor_id}] _volume_applied={volume_flag}")

    # Overlays
    manager = workspace.overlay_manager()
    print(f"  overlays registered: {len(manager.overlays())}")
    for ov in manager.overlays():
        w = ov.widget()
        print(
            f"    overlay[{ov.overlay_id}] "
            f"visible={ov.is_visible()} "
            f"geometry={w.geometry() if w is not None else None}"
        )
    print("=== End visual state dump ===\n")


def _force_splitter_sizes(workspace: Workspace) -> None:
    """Give every QSplitter equal sizes now that the window is shown.

    The QSplitter.setSizes() calls inside ``_render_2x2_grid`` run
    while the parent container has zero total size, so they are
    silently ignored. Once the window is shown and Qt has assigned
    real geometry, re-applying equal sizes makes the four quadrants
    actually visible. The View containers now have
    ``sizePolicy(Expanding, Expanding)``, so the splitter distributes
    the available space instead of limiting to the minimum.
    """
    for area in workspace.areas():
        widget = workspace._layout_renderer.cached_area_widget(area.area_id)  # noqa: SLF001
        if widget is None:
            continue
        for sp in widget.findChildren(QSplitter):
            n = sp.count()
            if n >= 2:
                base = 1000 // n
                sp.setSizes([base] * n)


def _force_reposition_overlays(workspace: Workspace) -> None:
    """Reposition overlays once the AreaWidgets have real geometry.

    ``compute_region_bounds`` returns a placeholder (zero) rectangle
    if the AreaWidgets are not yet laid out. Calling this after
    ``show()`` (with a small delay) positions the Top Bar over the
    Central Area correctly.
    """
    workspace._reposition_overlays()  # noqa: SLF001


# ----- Main ---------------------------------------------------------


def main() -> int:
    app = QApplication.instance() or QApplication([])
    app.setStyle("Fusion")

    # ThemeService needs in-memory settings (Sprint E). Applying the
    # compiled QSS makes the Toolbars and labels look like the real
    # application instead of Fusion's defaults.
    theme_service = ThemeService(
        settings=InMemorySettingsService(),
        default_mode=ThemeMode.DARK,
    )
    theme_service.compiler().apply(theme_service.compiled())

    # The UnicodeIconProvider resolves the ``log``/``toggle`` icon
    # names declared by the built-in tools. It is bound to the same
    # ThemeService so icon colors follow the active theme.
    icon_provider: IconProvider = UnicodeIconProvider(theme_service)

    # Synthetic Volume: the 2D Views render its slices, the 3D View
    # renders its shell. Without this, the Viewport3DView never calls
    # set_volume() and stays blank (white/cinza).
    domain_object_store = DomainObjectStore()
    scene_query = InMemorySceneQuery()
    volume = build_synthetic_volume()
    domain_object_store.add(volume.volume_id, volume)
    scene_query._add(volume.volume_id, object())

    workspace = Workspace(
        editor_registry=build_editor_registry(),
        tool_registry=build_tool_registry(),
        theme_service=theme_service,
        icon_provider=icon_provider,
        project_context=build_project_context(),
        domain_object_store=domain_object_store,
        scene_query=scene_query,
        # debug_colors=True would paint the Area background with a
        # distinct color per Placement. Useful to inspect Area
        # boundaries, but it obscures the View-level Toolbars, so it
        # is off here. Turn it on only when you need to check Area
        # placement.
        debug_colors=False,
    )
    workspace.load_spec(build_spec())

    window = QMainWindow()
    window.setWindowTitle("CranioZ — TomographyEditor debug (G2)")
    window.setCentralWidget(workspace)
    window.resize(1280, 800)
    window.show()

    # Defer layout fixes to the next event loop iterations. When the
    # widgets were created, the QSplitters had zero total size, and
    # the overlays had no Region bounds to anchor to. Qt needs at
    # least one iteration after show() to assign real geometry. The
    # VTK pipeline inside the 3D View may take longer to initialize,
    # so we schedule a third pass.
    for delay_ms in (0, 100, 300):
        QTimer.singleShot(delay_ms, lambda: _force_splitter_sizes(workspace))
        QTimer.singleShot(delay_ms, lambda: _force_reposition_overlays(workspace))

    # Print a snapshot after the layout has settled and VTK had time
    # to initialize. A second dump at 800 ms catches any late layout
    # adjustment (e.g. when the VTK interactor's first render changes
    # its sizeHint).
    QTimer.singleShot(300, lambda: _dump_visual_state(workspace))
    QTimer.singleShot(800, lambda: _dump_visual_state(workspace))

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())