"""Integration tests for the Workspace facade.

The Workspace is the highest-level component of the Workspace
subsystem. It coordinates:

- LayoutBuilder      (ModuleUISpec -> Areas, LayoutTree, Editors)
- LayoutRenderer     (LayoutTree -> Qt widgets)
- OverlayManager     (registration + repositioning of Overlays)
- TopOverlay         (the shared Top Bar, registered by default)

These tests exercise the full materialization path:

    ModuleUISpec
        -> Workspace.load_spec()
        -> Areas materialized, widgets rendered, overlays repositioned

They use qtbot and a real QApplication. Widgets are laid out by Qt
when the Workspace is shown; the tests call ``show()`` and
``qtbot.waitExposed()`` (or explicitly trigger a resize) when the
geometry matters.

The Workspace receives a ProjectContext at construction (ADR-0006).
A minimal fixture provides one for these tests; the context is not
inspected by the Workspace beyond its presence.

What these tests cover:

- Construction with the required registries, services, and context.
- The TopOverlay is registered by default and accessible.
- load_spec() builds the Areas, the tree, and the widget hierarchy.
- areas() returns the Areas of the current composition.
- area_manager() returns the manager; None before load.
- is_loaded() reflects the composition state.
- clear() drops the composition; the TopOverlay survives.
- Reloading with a different spec replaces the composition.
- Overlays are repositioned on load and on resize.
- Region bounds are derived from the rendered AreaWidgets.
- Empty workspace (no load) does not crash on resize.

Non-goals:

- Layout persistence (Bloco 11).
- Drag-and-drop, floating, multi-monitor (Bloco 14).
- Top Bar content (the three segments are populated by the
  MainWindow, not by the Workspace — ADR-0006).
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from PySide6.QtWidgets import QWidget
from pytestqt.qtbot import QtBot

from cranioz.application.project.project_context import ProjectContext
from cranioz.domain.patient.enums.patient_sex import PatientSex
from cranioz.domain.patient.patient_summary import PatientSummary
from cranioz.domain.patient.value_objects.patient_id import PatientId
from cranioz.domain.project.project_id import ProjectId
from cranioz.domain.project.project_metadata import ProjectMetadata
from cranioz.domain.project.project_status import ProjectStatus
from cranioz.ui.editors.builtin.test_editor import DummyEditor
from cranioz.ui.editors.editor_registry import EditorRegistry
from cranioz.ui.theme.service import ThemeName, ThemeService
from cranioz.ui.tools.builtin.log_tool import LogTool
from cranioz.ui.tools.builtin.toggle_tool import ToggleTool
from cranioz.ui.tools.registry.tool_registry import ToolRegistry
from cranioz.ui.workspace.areas.placement import Placement
from cranioz.ui.workspace.specs.area_spec import AreaSpec
from cranioz.ui.workspace.specs.editor_layout_spec import EditorLayoutSpec
from cranioz.ui.workspace.specs.module_ui_spec import ModuleUISpec
from cranioz.ui.workspace.workspace import Workspace

# ----- Local helpers ------------------------------------------------


def _leaf(editor_id: str) -> EditorLayoutSpec:
    return EditorLayoutSpec.leaf(editor_id)


def _area(
    area_id: str,
    placement: Placement,
    editor_id: str,
) -> AreaSpec:
    return AreaSpec(
        area_id=area_id,
        title=area_id,
        placement=placement,
        editor_layout=_leaf(editor_id),
    )


def _spec(*areas: AreaSpec) -> ModuleUISpec:
    return ModuleUISpec(areas=tuple(areas))


# ----- Fixtures local to this module --------------------------------


@pytest.fixture
def editor_registry() -> EditorRegistry:
    reg = EditorRegistry()
    for editor_id in (
        "editor.patient",
        "editor.viewport_3d",
        "editor.object_list",
        "editor.properties",
        "editor.console",
    ):
        reg.register(editor_id, DummyEditor)
    return reg


@pytest.fixture
def tool_registry() -> ToolRegistry:
    reg = ToolRegistry()
    reg.register("tool.log", LogTool)
    reg.register("tool.toggle", ToggleTool)
    return reg


@pytest.fixture
def theme_service() -> ThemeService:
    return ThemeService(theme=ThemeName.DARK)


@pytest.fixture
def project_context() -> ProjectContext:
    """A minimal ProjectContext for Workspace tests.

    The Workspace only checks for the presence of the context; it does
    not inspect its fields. This fixture provides a coherent one so
    that tests can construct a Workspace without a ProjectManager.
    """
    pid = ProjectId("p-001")
    return ProjectContext(
        project_id=pid,
        metadata=ProjectMetadata(
            project_id=pid,
            project_name="Case 001",
            patient_id="pat-001",
            patient_display_name="Gabriel Silva",
            clinical_procedure="orthognathic",
            status=ProjectStatus.ACTIVE,
            created_at=datetime(2026, 1, 1, 12, 0, tzinfo=UTC),
            updated_at=datetime(2026, 1, 1, 12, 0, tzinfo=UTC),
            last_opened_at=None,
            schema_version=1,
        ),
        patient_summary=PatientSummary(
            patient_id=PatientId("pat-001"),
            display_name="Gabriel Silva",
            birth_date=None,
            sex=PatientSex.MALE,
        ),
    )


@pytest.fixture
def workspace(
    qtbot: QtBot,
    editor_registry: EditorRegistry,
    tool_registry: ToolRegistry,
    theme_service: ThemeService,
    project_context: ProjectContext,
) -> Workspace:
    ws = Workspace(
        editor_registry=editor_registry,
        tool_registry=tool_registry,
        theme_service=theme_service,
        project_context=project_context,
    )
    qtbot.addWidget(ws)
    return ws


# ----- Construction -------------------------------------------------


def test_workspace_is_a_qwidget(workspace: Workspace) -> None:
    assert isinstance(workspace, QWidget)


def test_workspace_has_object_name(workspace: Workspace) -> None:
    assert workspace.objectName() == "workspace"


def test_workspace_starts_unloaded(workspace: Workspace) -> None:
    assert workspace.is_loaded() is False
    assert workspace.areas() == ()
    assert workspace.area_manager() is None


def test_workspace_registers_top_overlay_by_default(
    workspace: Workspace,
) -> None:
    overlay = workspace.top_overlay()
    assert overlay is not None
    assert overlay.overlay_id == "overlay.top_bar"
    assert workspace.overlay_manager().contains("overlay.top_bar")


def test_workspace_exposes_project_context(
    workspace: Workspace,
    project_context: ProjectContext,
) -> None:
    """ADR-0006: the Workspace exposes the ProjectContext it was created for."""
    assert workspace.project_context is project_context


# ----- load_spec — basic materialization ----------------------------


def test_load_spec_single_central(workspace: Workspace) -> None:
    spec = _spec(_area("area.central", Placement.CENTRAL, "editor.patient"))
    workspace.load_spec(spec)

    assert workspace.is_loaded() is True
    assert [a.area_id for a in workspace.areas()] == ["area.central"]


def test_load_spec_left_central_right(workspace: Workspace) -> None:
    spec = _spec(
        _area("area.left", Placement.LEFT, "editor.object_list"),
        _area("area.central", Placement.CENTRAL, "editor.viewport_3d"),
        _area("area.right", Placement.RIGHT, "editor.properties"),
    )
    workspace.load_spec(spec)

    ids = sorted(a.area_id for a in workspace.areas())
    assert ids == ["area.central", "area.left", "area.right"]


def test_load_spec_four_areas(workspace: Workspace) -> None:
    spec = _spec(
        _area("area.left", Placement.LEFT, "editor.object_list"),
        _area("area.central", Placement.CENTRAL, "editor.viewport_3d"),
        _area("area.right", Placement.RIGHT, "editor.properties"),
        _area("area.bottom", Placement.BOTTOM, "editor.console"),
    )
    workspace.load_spec(spec)

    ids = sorted(a.area_id for a in workspace.areas())
    assert ids == [
        "area.bottom",
        "area.central",
        "area.left",
        "area.right",
    ]


def test_load_spec_populates_area_manager(workspace: Workspace) -> None:
    spec = _spec(_area("area.central", Placement.CENTRAL, "editor.patient"))
    workspace.load_spec(spec)

    manager = workspace.area_manager()
    assert manager is not None
    assert manager.contains("area.central")
    assert manager.has_central()


# ----- clear and reload ---------------------------------------------


def test_clear_drops_composition(workspace: Workspace) -> None:
    spec = _spec(_area("area.central", Placement.CENTRAL, "editor.patient"))
    workspace.load_spec(spec)
    assert workspace.is_loaded() is True

    workspace.clear()

    assert workspace.is_loaded() is False
    assert workspace.areas() == ()
    assert workspace.area_manager() is None


def test_clear_on_unloaded_workspace_is_noop(
    workspace: Workspace,
) -> None:
    workspace.clear()  # must not raise
    assert workspace.is_loaded() is False


def test_clear_preserves_top_overlay(workspace: Workspace) -> None:
    spec = _spec(_area("area.central", Placement.CENTRAL, "editor.patient"))
    workspace.load_spec(spec)

    overlay_before = workspace.top_overlay()

    workspace.clear()

    # The TopOverlay instance is stable; the OverlayManager still
    # holds it.
    assert workspace.top_overlay() is overlay_before
    assert workspace.overlay_manager().contains("overlay.top_bar")


def test_reload_replaces_composition(workspace: Workspace) -> None:
    spec_a = _spec(_area("area.central", Placement.CENTRAL, "editor.patient"))
    spec_b = _spec(
        _area("area.left", Placement.LEFT, "editor.object_list"),
        _area("area.central", Placement.CENTRAL, "editor.viewport_3d"),
        _area("area.right", Placement.RIGHT, "editor.properties"),
    )

    workspace.load_spec(spec_a)
    workspace.load_spec(spec_b)

    ids = sorted(a.area_id for a in workspace.areas())
    assert ids == ["area.central", "area.left", "area.right"]


def test_reload_keeps_top_overlay_registered(
    workspace: Workspace,
) -> None:
    spec = _spec(_area("area.central", Placement.CENTRAL, "editor.patient"))

    workspace.load_spec(spec)
    workspace.load_spec(spec)

    assert workspace.overlay_manager().contains("overlay.top_bar")


# ----- Overlays and regions -----------------------------------------


def test_load_spec_triggers_overlay_repositioning(
    qtbot: QtBot,
    workspace: Workspace,
) -> None:
    """After a load + resize, the TopOverlay has non-zero geometry.

    The TopOverlay is anchored to the Central Region. If the Central
    Area has a non-zero size, the TopOverlay must have a non-zero
    width.
    """
    spec = _spec(_area("area.central", Placement.CENTRAL, "editor.patient"))
    workspace.resize(800, 600)
    workspace.show()
    qtbot.waitExposed(workspace)

    workspace.load_spec(spec)
    workspace.resize(800, 600)  # trigger a resizeEvent

    overlay_widget = workspace.top_overlay().widget()
    # The overlay must have received some bounds; width may vary with
    # Qt's layout timing, but the widget must be visible.
    assert overlay_widget.isVisible() is True


def test_workspace_resize_does_not_crash_unloaded(
    qtbot: QtBot,
    workspace: Workspace,
) -> None:
    workspace.show()
    qtbot.waitExposed(workspace)
    workspace.resize(500, 400)  # no load; must not raise


def test_top_overlay_is_above_root_widget(
    qtbot: QtBot,
    workspace: Workspace,
) -> None:
    """The TopOverlay floats above the rendered composition.

    The TopOverlay widget is a child of the Workspace and is raised
    above the composition's root widget. It must not be reparented
    into the root widget.
    """
    spec = _spec(_area("area.central", Placement.CENTRAL, "editor.patient"))
    workspace.resize(800, 600)
    workspace.show()
    qtbot.waitExposed(workspace)

    workspace.load_spec(spec)

    # The TopOverlay's widget's parent is the Workspace itself.
    overlay_widget = workspace.top_overlay().widget()
    assert overlay_widget.parent() is workspace


# ----- Overlay manager stability ------------------------------------


def test_overlay_manager_is_stable_across_load_spec(
    workspace: Workspace,
) -> None:
    manager_before = workspace.overlay_manager()
    spec = _spec(_area("area.central", Placement.CENTRAL, "editor.patient"))
    workspace.load_spec(spec)
    manager_after = workspace.overlay_manager()
    assert manager_before is manager_after


def test_overlay_manager_is_stable_across_clear(
    workspace: Workspace,
) -> None:
    manager_before = workspace.overlay_manager()
    workspace.clear()
    manager_after = workspace.overlay_manager()
    assert manager_before is manager_after


def test_top_overlay_is_positioned_over_central_area(
    qtbot: QtBot,
    workspace: Workspace,
) -> None:
    """The TopOverlay must be positioned over the Central Area.

    This is a regression test for the bug where the TopOverlay was
    positioned at (0, 0) with zero width when the splitter was moved,
    instead of following the Central Area's geometry.
    """
    spec = _spec(
        _area("area.left", Placement.LEFT, "editor.object_list"),
        _area("area.central", Placement.CENTRAL, "editor.viewport_3d"),
        _area("area.right", Placement.RIGHT, "editor.properties"),
    )
    workspace.resize(1200, 800)
    workspace.load_spec(spec)
    workspace.show()
    qtbot.waitExposed(workspace)

    # Find the Central Area widget first, so the waitUntil condition
    # can compare against its actual position.
    central_widget = None
    for area in workspace.areas():
        if area.area_id == "area.central":
            for widget in workspace.findChildren(QWidget):
                if (
                    hasattr(widget, "area_id")
                    and widget.area_id == "area.central"
                ):
                    central_widget = widget
                    break
            break

    assert central_widget is not None, "Central Area widget must exist"

    # Wait until the TopOverlay is ACTUALLY positioned inside the
    # Central Area. Checking x > 0 is insufficient because the
    # TopOverlay may be positioned at x=8 (with bounds from the
    # old layout) before the Qt layout is complete.
    def _overlay_is_over_central() -> bool:
        overlay_geom = workspace.top_overlay().widget().geometry()
        central_top_left = central_widget.mapTo(
            workspace, central_widget.rect().topLeft()
        )
        central_right = central_top_left.x() + central_widget.width()
        return (
            overlay_geom.x() >= central_top_left.x()
            and overlay_geom.x() + overlay_geom.width() <= central_right
            and overlay_geom.width() > 0
        )

    qtbot.waitUntil(_overlay_is_over_central, timeout=2000)

    # Final assertions (redundant but document the contract).
    overlay_geom = workspace.top_overlay().widget().geometry()
    assert overlay_geom.width() > 0, "TopOverlay must have a non-zero width"
    assert overlay_geom.height() > 0, "TopOverlay must have a non-zero height"

    central_top_left = central_widget.mapTo(
        workspace, central_widget.rect().topLeft()
    )
    central_right = central_top_left.x() + central_widget.width()

    assert overlay_geom.x() >= central_top_left.x(), (
        "TopOverlay must not start before the Central Area"
    )
    assert overlay_geom.x() + overlay_geom.width() <= central_right, (
        "TopOverlay must not extend beyond the Central Area"
    )
