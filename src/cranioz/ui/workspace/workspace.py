"""Workspace.

The Workspace is the runtime environment where clinical work happens.
It is the composition of Areas — containers that host Editors — and
Overlays — floating layers over regions.

Responsibilities:

- Materialize a ModuleUISpec as Areas, QSplitters, and Editor widgets.
- Manage the AreaManager, the LayoutRenderer, and the OverlayManager.
- Own the shared TopOverlay (ADR-0005).
- Receive and forward the TaskManager, TelemetrySink, CommandDispatcher,
  SceneQuery, and EventSubscription to the Editors it hosts
  (ADR-0011, ADR-0012, ADR-0007, ADR-0013).

Non-responsibilities:

- Persistence of layout state (Bloco 11).
- Drag-and-drop, floating Areas, multi-monitor (Bloco 14).
- Top Bar content: populated by the MainWindow (ADR-0006).
- Steps Panel: a second shared Overlay, added with the Flow system.
- Module lifecycle: owned by the Application layer (modules.md v10 §11).
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PySide6.QtCore import QTimer
from PySide6.QtGui import QResizeEvent, QShowEvent
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

if TYPE_CHECKING:
    from cranioz.application.commands.dispatcher import CommandDispatcher
    from cranioz.application.events.base import EventSubscription
    from cranioz.application.scene.scene_query import SceneQuery
    from cranioz.application.tasks.base import TaskManager
    from cranioz.application.telemetry.base import TelemetrySink

_logger = logging.getLogger(__name__)


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
        task_manager: TaskManager | None = None,
        telemetry: TelemetrySink | None = None,
        command_dispatcher: CommandDispatcher | None = None,
        scene_query: SceneQuery | None = None,
        event_subscription: EventSubscription | None = None,
        debug_colors: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("workspace")
        self._command_dispatcher = command_dispatcher
        self._scene_query = scene_query
        self._event_subscription = event_subscription

        if project_context is None:
            raise WorkspaceError(
                "Workspace requires a ProjectContext; it exists only "
                "within an opened project (ADR-0006)."
            )

        self._editor_registry = editor_registry
        self._tool_registry = tool_registry
        self._theme_service = theme_service
        self._project_context = project_context
        self._task_manager = task_manager
        self._telemetry = telemetry
        self._debug_colors = debug_colors

        self._layout_builder = LayoutBuilder(editor_registry)
        self._layout_renderer = LayoutRenderer(
            tool_registry,
            theme_service,
            debug_colors=debug_colors,
            on_splitter_moved=self._reposition_overlays,
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
        return self._project_context

    def task_manager(self) -> TaskManager | None:
        return self._task_manager

    def telemetry(self) -> TelemetrySink | None:
        return self._telemetry

    def load_spec(self, spec: ModuleUISpec) -> None:
        """Materialize a ModuleUISpec atomically.

        The new composition is built first (validates the spec). If
        the build succeeds, the old composition is torn down and the
        new one is rendered and installed. If the build fails, the
        old composition remains intact.
        """
        # 1. Build the new composition (validates the spec).
        new_result = self._layout_builder.build(
            spec,
            shared_context={
                "task_manager": self._task_manager,
                "telemetry": self._telemetry,
                "command_dispatcher": self._command_dispatcher,
                "scene_query": self._scene_query,
                "event_subscription": self._event_subscription,
            },
        )

        # 2. Clear the old composition (disposes Editors, clears cache).
        self.clear()

        # 3. Render the new composition (populates a fresh cache).
        new_root = self._layout_renderer.render(new_result.tree)

        # 4. Install.
        self._build_result = new_result
        self._root_widget = new_root
        self._root_layout.addWidget(new_root)

        # 5. Ensure the TopOverlay floats above.
        self._top_overlay.widget().raise_()

        # 6. Position overlays after the layout is computed.
        QTimer.singleShot(0, self._reposition_overlays)

    def clear(self) -> None:
        """Tear down the current composition.

        Disposes every Editor, detaches the rendered widget tree,
        clears the renderer cache, and drops the build result.
        """
        # 1. Dispose every Editor.
        if self._build_result is not None:
            for area in self._build_result.areas:
                for editor in area.editors():
                    try:
                        editor.dispose()
                    except Exception:
                        _logger.exception("Editor.dispose() failed for %r", editor.editor_id)

        # 2. Detach and delete the rendered widget tree.
        if self._root_widget is not None:
            self._root_layout.removeWidget(self._root_widget)
            self._root_widget.setParent(None)
            self._root_widget.deleteLater()
            self._root_widget = None

        # 3. Clear the renderer cache. Required so that a subsequent
        #    render() creates fresh AreaWidgets instead of reusing
        #    the ones that were just deleted.
        self._layout_renderer.clear_cache()

        # 4. Drop the build result.
        self._build_result = None

    def areas(self) -> tuple[Area, ...]:
        if self._build_result is None:
            return ()
        return self._build_result.areas

    def area_manager(self) -> AreaManager | None:
        if self._build_result is None:
            return None
        return self._build_result.area_manager

    def overlay_manager(self) -> OverlayManager:
        return self._overlay_manager

    def top_overlay(self) -> TopOverlay:
        return self._top_overlay

    def is_loaded(self) -> bool:
        return self._build_result is not None

    # ----- Qt events ------------------------------------------------

    def resizeEvent(self, event: QResizeEvent) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._reposition_overlays()

    def showEvent(self, event: QShowEvent) -> None:  # noqa: N802
        """Reposition overlays after the workspace is shown."""
        super().showEvent(event)
        QTimer.singleShot(0, self._reposition_overlays)

    # ----- Internals ------------------------------------------------

    def _reposition_overlays(self) -> None:
        bounds_by_placement = self._layout_renderer.compute_region_bounds(self)
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
            areas = tuple(a for a in manager.areas() if a.placement is placement)
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
