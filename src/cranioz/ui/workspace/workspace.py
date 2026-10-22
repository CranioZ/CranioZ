"""Workspace.

The Workspace is the runtime environment where clinical work happens.
It is the composition of Areas — containers that host Editors — and
Overlays — floating layers over Regions.

Public responsibilities:

- ``load_spec(spec)``: materialize a ModuleUISpec. Rebuilds the
  whole visual tree and repositions every registered Overlay.
- ``clear()``: drop the current composition (Areas, widgets,
  Overlays registrations remain; they can be re-added on the next
  ``load_spec``).
- ``areas()``: return the Areas of the current composition.
- ``overlay_manager``: read-only access for advanced callers.
- ``top_overlay``: the shared Top Bar Overlay, exposed so the
  Workspace host can populate its content.
- ``project_context``: the immutable ProjectContext this Workspace
  was created for (ADR-0006).

Non-responsibilities:

- Persistence of layout state (Bloco 11).
- Drag-and-drop, floating Areas, multi-monitor (Bloco 14).
- Top Bar content: the three segments are populated by the
  MainWindow, not by the Workspace (ADR-0006).
- Steps Panel: a second shared Overlay, to be added when the Flow
  system is implemented (Bloco 9).

Design rules:

- The Workspace is a QWidget. Its single visual child is the root
  widget returned by the LayoutRenderer.
- ``load_spec()`` is idempotent in the sense that calling it again
  replaces the previous composition. It always calls ``clear()``
  first.
- The Workspace owns the AreaManager produced by the build result.
- The Workspace owns the LayoutRenderer instance.
- The TopOverlay is registered in the OverlayManager on construction.
- The Workspace receives its ProjectContext at construction and
  does not orchestrate its own project lifecycle. It is created and
  destroyed by the MainWindow (ADR-0006).
"""

from __future__ import annotations

from PySide6.QtCore import QTimer
from PySide6.QtGui import QResizeEvent
from PySide6.QtWidgets import QVBoxLayout, QWidget

from cranioz.application.project.project_context import ProjectContext
from cranioz.ui.editors.editor_registry import EditorRegistry
from cranioz.ui.theme.service import ThemeService
from cranioz.ui.tools.registry.tool_registry import ToolRegistry
from cranioz.ui.workspace.areas.area import Area
from cranioz.ui.workspace.areas.area_manager import AreaManager
from cranioz.ui.workspace.areas.placement import Placement
from cranioz.ui.workspace.layout.layout_builder import (
    BuildResult,
    LayoutBuilder,
)
from cranioz.ui.workspace.layout.layout_renderer import LayoutRenderer
from cranioz.ui.workspace.overlays.overlay_manager import OverlayManager
from cranioz.ui.workspace.overlays.region import Bounds, Region
from cranioz.ui.workspace.overlays.top_overlay import TopOverlay
from cranioz.ui.workspace.specs.module_ui_spec import ModuleUISpec


class WorkspaceError(RuntimeError):
    """Raised when the Workspace is used in an invalid state."""


class Workspace(QWidget):
    """The Workspace facade."""

    def __init__(
            self,
            *,
            editor_registry: EditorRegistry,
            tool_registry: ToolRegistry,
            theme_service: ThemeService,
            project_context: ProjectContext,
            debug_colors: bool = False,
            parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("workspace")

        if project_context is None:
            raise WorkspaceError(
                "Workspace requires a ProjectContext; it exists only "
                "within an opened project (ADR-0006)."
            )

        self._editor_registry = editor_registry
        self._tool_registry = tool_registry
        self._theme_service = theme_service
        self._project_context = project_context
        self._debug_colors = debug_colors

        self._layout_builder = LayoutBuilder(editor_registry)
        self._layout_renderer = LayoutRenderer(
            tool_registry,
            theme_service,
            debug_colors=debug_colors,
        )
        self._overlay_manager = OverlayManager()
        self._top_overlay = TopOverlay(parent=self)

        self._build_result: BuildResult | None = None
        self._root_widget: QWidget | None = None

        self._root_layout = QVBoxLayout(self)
        self._root_layout.setContentsMargins(0, 0, 0, 0)
        self._root_layout.setSpacing(0)

        self._overlay_manager.register(self._top_overlay)
        self._top_overlay.widget().setParent(self)

        if debug_colors:
            self.setStyleSheet("QWidget#workspace { background-color: #ffffff; }")
            self._top_overlay.widget().setStyleSheet(
                "QFrame#top_overlay { background-color: #fadbd8; border: 1px solid #e74c3c; }"
            )

    # ----- Public API -----------------------------------------------

    @property
    def project_context(self) -> ProjectContext:
        """The immutable ProjectContext this Workspace was created for."""
        return self._project_context

    def load_spec(self, spec: ModuleUISpec) -> None:
        """Materialize the given ModuleUISpec."""
        self.clear()

        result = self._layout_builder.build(spec)
        self._build_result = result

        root = self._layout_renderer.render(result.tree)
        self._root_widget = root
        self._root_layout.addWidget(root)

        self._top_overlay.widget().setParent(self)
        self._top_overlay.widget().raise_()

        self._reposition_overlays()
        QTimer.singleShot(0, self._reposition_overlays)

    def clear(self) -> None:
        """Remove the current composition."""
        if self._root_widget is not None:
            self._root_layout.removeWidget(self._root_widget)
            self._root_widget.setParent(None)
            self._root_widget.deleteLater()
            self._root_widget = None

        self._layout_renderer.clear_cache()
        self._build_result = None

    def areas(self) -> tuple[Area, ...]:
        """Return the Areas of the current composition."""
        if self._build_result is None:
            return ()
        return self._build_result.areas

    def area_manager(self) -> AreaManager | None:
        """Return the AreaManager of the current composition."""
        if self._build_result is None:
            return None
        return self._build_result.area_manager

    def overlay_manager(self) -> OverlayManager:
        """Return the OverlayManager."""
        return self._overlay_manager

    def top_overlay(self) -> TopOverlay:
        """Return the shared Top Bar Overlay."""
        return self._top_overlay

    def is_loaded(self) -> bool:
        """Return True if a composition has been loaded."""
        return self._build_result is not None

    # ----- Qt events ------------------------------------------------

    def resizeEvent(self, event: QResizeEvent) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._reposition_overlays()

    # ----- Internals ------------------------------------------------

    def _reposition_overlays(self) -> None:
        bounds_by_placement = self._layout_renderer.compute_region_bounds()
        regions = self._regions_from_bounds(bounds_by_placement)
        self._overlay_manager.reposition_all(regions)
        self._top_overlay.widget().raise_()

    def _regions_from_bounds(
        self,
        bounds_by_placement: dict[Placement, Bounds],
    ) -> tuple[Region, ...]:
        manager = self.area_manager()
        if manager is None:
            return ()

        regions: list[Region] = []
        for placement, bounds in bounds_by_placement.items():
            areas = tuple(area for area in manager.areas() if area.placement is placement)
            if not areas:
                continue
            regions.append(
                Region(
                    region_id=placement.value,
                    bounds=bounds,
                    areas=areas,
                    semantic_role=placement,
                )
            )
        return tuple(regions)
