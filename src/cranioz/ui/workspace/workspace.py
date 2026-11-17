"""Workspace.

The Workspace is the runtime environment where clinical work happens.
It is the composition of Areas — containers that host Editors — and
Overlays — floating layers over regions.

Responsibilities:

- Materialize a ModuleUISpec as Areas, QSplitters, and Editor widgets.
- Manage the AreaManager, the LayoutRenderer, and the OverlayManager.
- Own the shared TopOverlay (ADR-0005).
- Own the runtime visibility state of the toggleable Areas
  (WorkspaceLayoutState). The state is runtime-only and is not
  persisted (ADR-0010 is Phase 5).
- Apply the visibility state to the rendered AreaWidgets and to the
  Region computation used by the OverlayManager. A hidden Area does
  not contribute to the Region bounds (see
  ``LayoutRenderer.compute_region_bounds``).
- Hide Left, Right and Bottom after each ``load_spec``. The prototype
  shows only the Central Area on first load; lateral Areas become
  visible when the user toggles them from the Top Bar. This default
  will be replaced by the WorkflowEngine in Phase 5.
- Receive and forward the TaskManager, TelemetrySink, CommandDispatcher,
  SceneQuery, EventSubscription, TranslationService, and IconProvider
  to the Editors it hosts (ADR-0011, ADR-0012, ADR-0007, ADR-0013,
  Sprint B, Sprint F).
- Apply the default percentage-based sizes to the splitters (Block
  5.5). Left = 20%, Right = 25%, Bottom = 20%, Central = fill. The
  Central Area never drops below the Top Bar's dynamic minimum
  (``TopOverlay.minimum_width()``). Persistence of the user's
  custom sizes is Phase 4.5 (ADR-0010).

Sprint H adds support for the Editor Layout Tree. The LayoutBuilder
must propagate the `EditorLayoutSpec` from the `AreaSpec` to the
`Area` so the `AreaLayoutRenderer` can materialize it.

Non-responsibilities:

- Persistence of layout state (Bloco 11 / ADR-0010).
- Drag-and-drop, floating Areas, multi-monitor (Bloco 14).
- Top Bar content: populated by the MainWindow (ADR-0006).
- Steps Panel: a second shared Overlay, added with the Flow system.
- Module lifecycle: owned by the Application layer (modules.md v10 §11).
- Deciding which Areas exist. The ModuleUISpec decides; the Workspace
  materializes what the spec declares. An Area declared in the spec
  hosts at least one Editor (the placeholder or a real one), so the
  concept of an "empty Area" does not exist at this level.

Block 5.5 fix (layout architecture):

- A single QTimer (``_layout_update_timer``) with a 50 ms debounce
  coalesces multiple layout requests (load_spec, set_area_visible,
  resizeEvent, showEvent, Top Bar content change) into a single
  ``_apply_default_splitter_sizes`` call. This avoids O(N) work on
  every ``resizeEvent`` during a window drag and prevents the
  "flash" of overlays repositioning with stale Bounds.
- ``_is_applying_sizes`` guards against reentrancy: ``setSizes()``
  emits ``splitterMoved``, which the renderer forwards to
  ``_reposition_overlays``; without the guard, a resize could
  cascade into another resize.
- ``_apply_default_splitter_sizes`` reads ``self._root_widget``
  width/height (the widget actually being split), not the top-level
  window, so the 20% / 25% / 20% ratios are relative to the
  available layout space, not to the OS window frame.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QResizeEvent, QShowEvent
from PySide6.QtWidgets import QSplitter, QVBoxLayout, QWidget

from cranioz.application.project.context import ProjectContext
from cranioz.editors.core.editor.editor_registry import EditorRegistry
from cranioz.ui.icons.provider import IconProvider
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
from cranioz.ui.workspace.layout.layout_state import WorkspaceLayoutState
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
    from cranioz.domain.scene.domain_object_store import DomainObjectStore
    from cranioz.editors.views.viewport_3d.view import Viewport3DView
    from cranioz.infrastructure.i18n.translation_service import TranslationService

_logger = logging.getLogger(__name__)


class WorkspaceError(RuntimeError):
    """Raised when the Workspace is used in an invalid state."""


class Workspace(QWidget):
    """The Workspace facade."""

    #: Block 5.5: default percentages applied on the first render.
    #: Persistence of user-dragged sizes is Phase 4.5 (ADR-0010).
    _LEFT_RATIO: float = 0.20
    _RIGHT_RATIO: float = 0.25
    _BOTTOM_RATIO: float = 0.20

    #: Debounce window for layout recalculation. 50 ms is enough
    #: for Qt to settle a continuous resize and short enough that
    #: the user does not perceive the delay.
    _LAYOUT_DEBOUNCE_MS: int = 50

    def __init__(
        self,
        *,
        # --- Application & Domain Services ---
        project_context: ProjectContext,
        command_dispatcher: CommandDispatcher | None = None,
        scene_query: SceneQuery | None = None,
        domain_object_store: DomainObjectStore | None = None,
        event_subscription: EventSubscription | None = None,
        task_manager: TaskManager | None = None,
        telemetry: TelemetrySink | None = None,
        # --- User Interface & Registries ---
        editor_registry: EditorRegistry,
        tool_registry: ToolRegistry,
        theme_service: ThemeService,
        icon_provider: IconProvider,
        translation_service: TranslationService | None = None,
        # --- Configuration, Flags & Parent ---
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

        # --- Application & Domain Services Assignment ---
        self._project_context = project_context
        self._command_dispatcher = command_dispatcher
        self._scene_query = scene_query
        self._domain_object_store = domain_object_store
        self._event_subscription = event_subscription
        self._task_manager = task_manager
        self._telemetry = telemetry

        # --- User Interface & Registries Assignment ---
        self._editor_registry = editor_registry
        self._tool_registry = tool_registry
        self._theme_service = theme_service
        self._icon_provider = icon_provider
        self._translation_service = translation_service

        # --- Configuration & Flags Assignment ---
        self._debug_colors = debug_colors

        # --- Layout & Component Initialization ---
        self._layout_builder = LayoutBuilder(editor_registry)
        self._layout_renderer = LayoutRenderer(
            tool_registry,
            theme_service,
            icon_provider=icon_provider,
            debug_colors=debug_colors,
            on_splitter_moved=self._reposition_overlays,
        )
        self._overlay_manager = OverlayManager()
        self._top_overlay = TopOverlay(parent=self)

        # Runtime visibility of the toggleable Areas. Not persisted;
        # see the module docstring.
        self._layout_state = WorkspaceLayoutState()

        self._build_result: BuildResult | None = None
        self._root_widget: QWidget | None = None

        # Block 5.5: single debounce timer for layout updates.
        self._layout_update_timer = QTimer(self)
        self._layout_update_timer.setSingleShot(True)
        self._layout_update_timer.setInterval(self._LAYOUT_DEBOUNCE_MS)
        self._layout_update_timer.timeout.connect(self._apply_default_splitter_sizes)

        # Block 5.5: reentrancy guard.
        self._is_applying_sizes: bool = False

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
        # O LayoutBuilder agora injeta o EditorLayoutSpec na Area.
        new_result = self._layout_builder.build(
            spec,
            shared_context={
                "task_manager": self._task_manager,
                "telemetry": self._telemetry,
                "command_dispatcher": self._command_dispatcher,
                "scene_query": self._scene_query,
                "domain_object_store": self._domain_object_store,
                "event_subscription": self._event_subscription,
                "translation_service": self._translation_service,
                "theme_service": self._theme_service,
                "icon_provider": self._icon_provider,
                "tool_registry": self._tool_registry,
            },
        )

        # 2. Clear the old composition.
        if self._build_result is not None:
            self.clear()

        # 3. Render the new composition.
        new_root = self._layout_renderer.render(new_result.tree)

        # 4. Install.
        self._build_result = new_result
        self._root_widget = new_root
        self._root_layout.addWidget(new_root)

        # 5. Hide Left, Right and Bottom.
        self._hide_lateral_areas_by_default()

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

        # 3. Clear the renderer cache.
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

    def find_viewport_3d(self) -> Viewport3DView | None:
        """Return the first ``Viewport3DView`` hosted by an Editor."""
        if self._build_result is None:
            return None

        from cranioz.editors.views.viewport_3d.view import Viewport3DView  # noqa: PLC0415

        for area in self._build_result.areas:
            for editor in area.editors():
                for view in editor.views():
                    if isinstance(view, Viewport3DView):
                        return view
        return None

    # ----- Area visibility ------------------------------------------

    def layout_state(self) -> WorkspaceLayoutState:
        return self._layout_state

    def set_area_visible(self, placement: Placement, visible: bool) -> None:
        self._layout_state.set_visible(placement, visible)

        if self._build_result is None:
            return

        for area in self._build_result.areas:
            if area.placement is not placement:
                continue
            if visible:
                area.show()
            else:
                area.hide()
            widget = self._layout_renderer.cached_area_widget(area.area_id)
            if widget is not None:
                widget.setVisible(visible)

        self._apply_default_splitter_sizes()
        self._reposition_overlays()

    def reload_volume(self) -> None:
        """Ask every hosted Editor to re-resolve its volume."""
        if self._build_result is None:
            return
        for area in self._build_result.areas:
            for editor in area.editors():
                reload = getattr(editor, "reload_volume", None)
                if callable(reload):
                    try:
                        reload()
                    except Exception:
                        _logger.exception(
                            "Editor.reload_volume() failed for %r",
                            editor.editor_id,
                        )

    def is_loaded(self) -> bool:
        return self._build_result is not None

    # ----- Qt events ------------------------------------------------

    def resizeEvent(self, event: QResizeEvent) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._schedule_layout_update()

    def showEvent(self, event: QShowEvent) -> None:  # noqa: N802
        super().showEvent(event)
        self._schedule_layout_update()

    # ----- Internals ------------------------------------------------

    def _schedule_layout_update(self) -> None:
        self._layout_update_timer.start()

    def _apply_default_splitter_sizes(self) -> None:
        if self._is_applying_sizes:
            return
        if self._build_result is None or self._root_widget is None:
            return

        self._is_applying_sizes = True
        try:
            total_w = self._root_widget.width()
            total_h = self._root_widget.height()
            min_central = self._top_overlay.minimum_width()

            if total_w < min_central or total_h <= 0:
                self._layout_update_timer.start()
                return

            for splitter in self._layout_renderer._split_widgets.values():
                if splitter.orientation() == Qt.Orientation.Horizontal:
                    sizes = self._compute_horizontal_sizes(splitter, total_w, min_central)
                    if sizes is not None:
                        splitter.setSizes(sizes)
                        splitter.updateGeometry()
                else:
                    sizes = self._compute_vertical_sizes(splitter, total_h)
                    if sizes is not None:
                        splitter.setSizes(sizes)
                        splitter.updateGeometry()
        finally:
            self._is_applying_sizes = False

        QTimer.singleShot(0, self._reposition_overlays)

    def _compute_horizontal_sizes(
        self, splitter: QSplitter, total_w: int, min_central: int
    ) -> list[int] | None:
        count = splitter.count()
        if count == 0:
            return None

        base_w = splitter.width() if splitter.width() > 0 else total_w

        placements: list[str] = []
        visible_flags: list[bool] = []
        for i in range(count):
            child = splitter.widget(i)
            area = getattr(child, "area", lambda: None)() if child is not None else None
            placements.append(area.placement.value if area else "")
            visible_flags.append(area.visible if area else False)

        left_px = 0
        right_px = 0
        central_indices: list[int] = []
        for i, (p, v) in enumerate(zip(placements, visible_flags, strict=False)):
            if p == "left":
                left_px = int(base_w * self._LEFT_RATIO) if v else 0
            elif p == "right":
                right_px = int(base_w * self._RIGHT_RATIO) if v else 0
            elif p == "central":
                central_indices.append(i)

        handle_px = splitter.handleWidth() * max(0, count - 1)
        available_for_central = base_w - left_px - right_px - handle_px

        if available_for_central < min_central and (left_px + right_px) > 0:
            deficit = min_central - available_for_central
            total_lateral = left_px + right_px
            scale = max(0.0, (total_lateral - deficit) / total_lateral)
            left_px = int(left_px * scale)
            right_px = int(right_px * scale)
            available_for_central = base_w - left_px - right_px - handle_px

        sizes = [0] * count
        if "left" in placements:
            sizes[placements.index("left")] = left_px
        if "right" in placements:
            sizes[placements.index("right")] = right_px
        if central_indices:
            per_central = available_for_central // len(central_indices)
            for i in central_indices:
                sizes[i] = per_central
            sizes[central_indices[-1]] += available_for_central - per_central * len(central_indices)

        return sizes

    def _compute_vertical_sizes(self, splitter: QSplitter, total_h: int) -> list[int] | None:
        count = splitter.count()
        if count == 0:
            return None

        base_h = splitter.height() if splitter.height() > 0 else total_h

        placements: list[str] = []
        visible_flags: list[bool] = []
        for i in range(count):
            child = splitter.widget(i)
            if isinstance(child, QSplitter):
                placements.append("central")
                visible_flags.append(True)
            else:
                area = getattr(child, "area", lambda: None)() if child is not None else None
                placements.append(area.placement.value if area else "")
                visible_flags.append(area.visible if area else False)

        bottom_px = 0
        for _i, (p, v) in enumerate(zip(placements, visible_flags, strict=False)):
            if p == "bottom" and v:
                bottom_px = int(base_h * self._BOTTOM_RATIO)

        handle_px = splitter.handleWidth() * max(0, count - 1)
        top_px = base_h - bottom_px - handle_px
        sizes = [0] * count
        if "bottom" in placements:
            sizes[placements.index("bottom")] = bottom_px
        sizes[0] = max(top_px, 0)

        _logger.info(
            "DEBUG: Vertical splitter (count=%d, base_h=%d). "
            "placements=%s, visible=%s -> setSizes(%s)",
            count,
            base_h,
            placements,
            visible_flags,
            sizes,
        )
        return sizes

    def _hide_lateral_areas_by_default(self) -> None:
        if self._build_result is None:
            return

        for area in self._build_result.areas:
            if area.placement is Placement.CENTRAL:
                continue
            self._layout_state.set_visible(area.placement, False)
            area.hide()
            widget = self._layout_renderer.cached_area_widget(area.area_id)
            if widget is not None:
                widget.setVisible(False)

        self._schedule_layout_update()

    def _reposition_overlays(self) -> None:
        if self._build_result is None or self._root_widget is None:
            return

        bounds_by_placement = self._layout_renderer.compute_region_bounds(self)
        if not bounds_by_placement:
            return

        valid_bounds: dict[Placement, Bounds] = {
            placement: bounds
            for placement, bounds in bounds_by_placement.items()
            if not bounds.is_placeholder() and bounds.width > 0 and bounds.height > 0
        }
        if not valid_bounds:
            return

        regions = self._regions_from_bounds(valid_bounds)
        if not regions:
            return

        self._overlay_manager.reposition_all(regions)

        top_overlay = self._top_overlay
        if top_overlay.is_visible() and not top_overlay.widget().geometry().isEmpty():
            top_overlay.widget().raise_()

    def _regions_from_bounds(
        self,
        bounds_by_placement: dict[Placement, Bounds],
    ) -> tuple[Region, ...]:
        manager = self.area_manager()
        if manager is None:
            return ()
        regions: list[Region] = []
        for placement, bounds in bounds_by_placement.items():
            areas = tuple(a for a in manager.areas() if a.placement is placement and a.visible)
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
