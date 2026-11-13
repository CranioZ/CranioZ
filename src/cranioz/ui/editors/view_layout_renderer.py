"""ViewLayoutRenderer.

Materializes a ViewLayoutSpec (nested split tree of Views) into Qt
widgets.

Per ADR-0013 §2.4, the ViewLayoutRenderer is responsible for
materializing the Views and their declared Toolbars/Control Panels
(§2.6). Each Leaf is rendered as a container:

    [View Toolbars LEFT] [View content] [View Control Panels RIGHT]
    with optional TOP/BOTTOM slots around the content.

The container is built by ``_build_view_container``. The Toolbars
are created by the existing ``Toolbar`` widget (ui/toolbars/base.py),
which needs a ``ToolRegistry``, a ``ThemeService``, and an
``IconProvider``. All three are injected into the renderer.

For the common 2x2 grid pattern (Split(VERTICAL) with two
Split(HORIZONTAL) children, each with two leaves), the renderer
still uses a shared QSplitter grid. The Toolbar-wrapping happens at
the Leaf level, inside ``_build_view_container``.

The renderer is stateless with respect to a single render() call.
It does not mutate the spec.

Active-View flow (Block 4)
--------------------------

When the renderer is constructed with an ``editor``, it installs an
event filter on each View's ``activation_widget()``. Mouse presses
and focus-in events forward to ``editor.set_active_view(view_id)``.
The Editor's ``active_view_changed`` signal is connected to
``_on_active_view_changed``, which toggles the ``ACTIVE_ONLY``
Toolbars of each View: active View's toolbars are emphasized, the
others are dimmed. Toolbars with other visibility modes are
unaffected (``Toolbar.set_active`` is a no-op for them).

If ``editor`` is ``None`` (e.g. in tests that only verify
materialization), the filter is not installed and the ACTIVE_ONLY
policy is not applied.

See ADR-0013 §2.4, §2.6.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import cast

from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QSizePolicy,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from cranioz.ui.editors.base_editor import Editor
from cranioz.ui.editors.view import View
from cranioz.ui.editors.view_layout_spec import (
    SplitDirection,
    ViewLayoutSpec,
    ViewLayoutType,
)
from cranioz.ui.icons.provider import IconProvider
from cranioz.ui.theme.service import ThemeService
from cranioz.ui.toolbars.base import Toolbar
from cranioz.ui.toolbars.specification import (
    ToolbarPosition,
    ToolbarVisibilityMode,
)
from cranioz.ui.tools.registry.tool_registry import ToolRegistry

_logger = logging.getLogger(__name__)


class ViewLayoutRendererError(ValueError):
    """Raised when the ViewLayoutRenderer cannot materialize a spec."""


class _ViewActivationFilter(QObject):
    """Event filter that forwards activation events to a callback.

    Installed on a View's ``activation_widget()``. Detects
    ``MouseButtonPress`` and ``FocusIn`` and calls the callback with
    the view_id. Always returns False so that the event continues to
    propagate (the View's own handlers must keep working; the filter
    only observes).
    """

    _ACTIVATION_EVENTS = frozenset(
        {QEvent.Type.MouseButtonPress, QEvent.Type.FocusIn}
    )

    def __init__(self, view_id: str, callback: Callable[[str], None]) -> None:
        super().__init__()
        self._view_id = view_id
        self._callback = callback

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:  # noqa: N802
        if event.type() in self._ACTIVATION_EVENTS:
            self._callback(self._view_id)
        return False


class ViewLayoutRenderer:
    """Materializes a ViewLayoutSpec into Qt widgets."""

    #: Minimum width for a VERTICAL Toolbar (LEFT/RIGHT). Wide enough
    #: for the widest built-in label ("Toggle") with a 20px icon.
    _VERTICAL_TOOLBAR_WIDTH: int = 96

    #: Minimum height for a HORIZONTAL Toolbar (TOP/BOTTOM).
    _HORIZONTAL_TOOLBAR_HEIGHT: int = 44

    #: Minimum size for a View container. The parent QSplitter uses
    #: this as the floor when distributing space; without it, the
    #: container collapses to the sizeHint of its children (~49 px).
    _VIEW_CONTAINER_MIN_SIZE: int = 200

    #: Minimum size for a View's content widget. Without it, MPRView's
    #: QLabel and the QVTKRenderWindowInteractor (before Initialize)
    #: report 1x1 or 0x0 and the container has no usable content area.
    _CONTENT_MIN_WIDTH: int = 200
    _CONTENT_MIN_HEIGHT: int = 150

    def __init__(
        self,
        tool_registry: ToolRegistry,
        theme_service: ThemeService,
        *,
        icon_provider: IconProvider,
        on_splitter_moved: Callable[[], None] | None = None,
        editor: Editor | None = None,
    ) -> None:
        self._tool_registry = tool_registry
        self._theme_service = theme_service
        self._icon_provider = icon_provider
        self._splitter_moved_callback = on_splitter_moved
        self._editor = editor
        self._split_widgets: dict[int, QSplitter] = {}
        self._grid_widgets: dict[int, QWidget] = {}
        self._view_containers: dict[str, QWidget] = {}
        self._view_filters: dict[str, _ViewActivationFilter] = {}
        self._view_filter_targets: dict[str, QWidget] = {}
        self._toolbars_by_view: dict[str, list[Toolbar]] = {}
        if editor is not None:
            editor.active_view_changed.connect(self._on_active_view_changed)

    # ----- Public API -----------------------------------------------

    def render(
        self,
        spec: ViewLayoutSpec,
        views_by_id: dict[str, View],
    ) -> QWidget:
        """Render the ViewLayoutSpec and return the root widget."""
        return self._render_node(spec, views_by_id)

    def clear_cache(self) -> None:
        """Discard all cached widgets."""
        # Remove event filters first: the widgets may be destroyed
        # below, and removeEventFilter on a dead C++ object raises
        # RuntimeError.
        for view_id, view_filter in self._view_filters.items():
            widget = self._view_filter_targets.get(view_id)
            if widget is not None:
                try:
                    widget.removeEventFilter(view_filter)
                except RuntimeError:
                    pass
        self._view_filters.clear()
        self._view_filter_targets.clear()
        self._toolbars_by_view.clear()

        for splitter in self._split_widgets.values():
            splitter.setParent(None)
            splitter.deleteLater()
        self._split_widgets.clear()

        for grid in self._grid_widgets.values():
            grid.setParent(None)
            grid.deleteLater()
        self._grid_widgets.clear()

        for container in self._view_containers.values():
            container.setParent(None)
            container.deleteLater()
        self._view_containers.clear()

    # ----- Internals ------------------------------------------------

    def _render_node(
        self,
        node: ViewLayoutSpec,
        views_by_id: dict[str, View],
    ) -> QWidget:
        if node.type is ViewLayoutType.LEAF:
            return self._render_leaf(node, views_by_id)
        if node.type is ViewLayoutType.SPLIT:
            if self._is_2x2_grid(node):
                return self._render_2x2_grid(node, views_by_id)
            return self._render_split(node, views_by_id)
        raise ViewLayoutRendererError(f"unknown view layout type: {node.type!r}")

    def _render_leaf(
        self,
        node: ViewLayoutSpec,
        views_by_id: dict[str, View],
    ) -> QWidget:
        view_id = node.view_id
        if view_id is None:
            raise ViewLayoutRendererError("LEAF has no view_id")
        view = views_by_id.get(view_id)
        if view is None:
            raise ViewLayoutRendererError(f"no View registered for view_id: {view_id!r}")
        return self._build_view_container(view)

    def _build_view_container(self, view: View) -> QWidget:
        """Wrap the View's content widget with its declared Toolbars.

        Layout:

            outer (QHBoxLayout)
            ├── Toolbar(s) LEFT
            ├── inner (QVBoxLayout)
            │   ├── Toolbar(s) TOP
            │   ├── view.content_widget() (stretch=1)
            │   └── Toolbar(s) BOTTOM
            └── Toolbar(s) RIGHT

        The Container is what the Editor's View Layout Tree places in
        its QSplitter. The View itself is unchanged; its Toolbars are
        created here, by the ``Toolbar`` widget.

        The container is cached by ``view.view_id``: rendering the same
        View twice returns the same container instance. This is what the
        cache test in ``test_view_layout_renderer_toolbars.py`` asserts,
        and it prevents the container (and its Toolbars) from being
        re-created (and leaked) every time a 2x2 grid or a split is
        re-reconciled.

        Minimum size and Expanding size policy are essential: without
        them, the parent ``QSplitter`` collapses the container to the
        tiny sizeHint of its children (a Toolbar button, an empty
        QLabel, a VTK widget whose minimum is 1x1). ``QSplitter``
        respects ``sizePolicy`` when distributing available space;
        ``setSizes()`` alone is ignored when the children report a
        tiny effective minimum.

        Block 4: after building the container, the renderer indexes
        the Toolbars by View and (if an Editor was injected) installs
        the activation filter on the View's ``activation_widget()``.
        """
        existing = self._view_containers.get(view.view_id)
        if existing is not None:
            return existing

        container = QWidget()
        container.setObjectName(f"view_container.{view.view_id}")
        # Minimum size is the floor; Expanding policy is what allows
        # the QSplitter to actually give the container more than the
        # floor. With only minimumSize, the QSplitter limits the
        # child to that value and leaves the rest of the window blank.
        container.setMinimumSize(
            self._VIEW_CONTAINER_MIN_SIZE,
            self._VIEW_CONTAINER_MIN_SIZE,
        )
        container.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        # The container must be focusable so that FocusIn reaches the
        # event filter installed on the activation widget. (For Views
        # whose activation widget is the container itself, this is
        # sufficient; for Views backed by a VTK interactor, the
        # interactor's own focus policy applies.)
        container.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        toolbars_by_position: dict[ToolbarPosition, list[Toolbar]] = {
            ToolbarPosition.TOP: [],
            ToolbarPosition.BOTTOM: [],
            ToolbarPosition.LEFT: [],
            ToolbarPosition.RIGHT: [],
        }

        specs = [*view.toolbar_specs(), *view.control_panel_specs()]
        for spec in specs:
            toolbar = Toolbar(
                spec=spec,
                registry=self._tool_registry,
                theme=self._theme_service,
                icon_provider=self._icon_provider,
                parent=container,
            )
            toolbars_by_position[spec.position].append(toolbar)

        outer = QHBoxLayout(container)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        for toolbar in toolbars_by_position[ToolbarPosition.LEFT]:
            toolbar.setSizePolicy(
                QSizePolicy.Policy.Fixed,
                QSizePolicy.Policy.Expanding,
            )
            # A VERTICAL Toolbar has a QVBoxLayout of buttons. Without
            # a fixed width, the QHBoxLayout of the container would
            # give it stretch and the buttons would stretch
            # horizontally, eating the View's space.
            toolbar.setFixedWidth(self._VERTICAL_TOOLBAR_WIDTH)
            outer.addWidget(toolbar, stretch=0)

        inner = QWidget(container)
        inner_layout = QVBoxLayout(inner)
        inner_layout.setContentsMargins(0, 0, 0, 0)
        inner_layout.setSpacing(0)

        for toolbar in toolbars_by_position[ToolbarPosition.TOP]:
            toolbar.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Fixed,
            )
            toolbar.setFixedHeight(self._HORIZONTAL_TOOLBAR_HEIGHT)
            inner_layout.addWidget(toolbar, stretch=0)

        content = view.content_widget()
        content.setParent(inner)
        # Force the View's content to occupy meaningful space. MPRView's
        # QLabel and the QVTKRenderWindowInteractor (before Initialize)
        # report minimum sizes of 1x1 (or 0x0), which would collapse
        # the container otherwise.
        content.setMinimumSize(
            self._CONTENT_MIN_WIDTH,
            self._CONTENT_MIN_HEIGHT,
        )
        inner_layout.addWidget(content, stretch=1)

        for toolbar in toolbars_by_position[ToolbarPosition.BOTTOM]:
            toolbar.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Fixed,
            )
            toolbar.setFixedHeight(self._HORIZONTAL_TOOLBAR_HEIGHT)
            inner_layout.addWidget(toolbar, stretch=0)

        outer.addWidget(inner, stretch=1)

        for toolbar in toolbars_by_position[ToolbarPosition.RIGHT]:
            toolbar.setSizePolicy(
                QSizePolicy.Policy.Fixed,
                QSizePolicy.Policy.Expanding,
            )
            toolbar.setFixedWidth(self._VERTICAL_TOOLBAR_WIDTH)
            outer.addWidget(toolbar, stretch=0)

        # ----- Block 4: index Toolbars, set initial state, install filter

        all_toolbars: list[Toolbar] = []
        for tb_list in toolbars_by_position.values():
            all_toolbars.extend(tb_list)
        self._toolbars_by_view[view.view_id] = all_toolbars

        # ACTIVE_ONLY toolbars start inactive: the Editor starts with
        # no active View (Editor.active_view_id is None), so no View's
        # toolbars should be emphasized until the user activates one.
        for tb in all_toolbars:
            if tb.spec.visibility_mode is ToolbarVisibilityMode.ACTIVE_ONLY:
                tb.set_active(False)

        # Install the activation filter on the View's activation
        # widget. For most Views this is the content widget; for
        # Viewport3DView it is the QVTKRenderWindowInteractor, which
        # is the leaf that receives MouseButtonPress.
        if self._editor is not None:
            activation_widget = view.activation_widget()
            activation_filter = _ViewActivationFilter(
                view.view_id, self._on_view_activated
            )
            activation_widget.installEventFilter(activation_filter)
            self._view_filters[view.view_id] = activation_filter
            self._view_filter_targets[view.view_id] = activation_widget

        self._view_containers[view.view_id] = container
        return container

    @staticmethod
    def _is_2x2_grid(node: ViewLayoutSpec) -> bool:
        if node.type is not ViewLayoutType.SPLIT:
            return False
        if node.direction is not SplitDirection.VERTICAL:
            return False
        if len(node.children) != 2:
            return False
        return all(
            row.type is ViewLayoutType.SPLIT
            and row.direction is SplitDirection.HORIZONTAL
            and len(row.children) == 2
            and all(
                leaf.type is ViewLayoutType.LEAF and leaf.view_id is not None
                for leaf in row.children
            )
            for row in node.children
        )

    def _render_2x2_grid(
        self,
        node: ViewLayoutSpec,
        views_by_id: dict[str, View],
    ) -> QWidget:
        key = id(node)
        container = self._grid_widgets.get(key)
        if container is None:
            container = QWidget()
            container.setObjectName(f"view_layout_grid_{key}")
            # Expanding policy lets the grid fill the entire
            # AreaWidget. Without it, the QVBoxLayout of the
            # AreaWidget limits the grid to its sizeHint, leaving
            # ~200 px of unused space at the bottom.
            container.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Expanding,
            )

            outer_layout = QVBoxLayout(container)
            outer_layout.setContentsMargins(0, 0, 0, 0)
            outer_layout.setSpacing(0)

            outer_splitter = QSplitter(Qt.Orientation.Vertical)
            outer_splitter.setObjectName(f"view_layout_grid_{key}_rows")
            outer_splitter.setChildrenCollapsible(False)
            # Same reasoning as the container: the splitter must
            # expand, otherwise it limits the grid to the sizeHint of
            # its rows.
            outer_splitter.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Expanding,
            )

            top_splitter = QSplitter(Qt.Orientation.Horizontal)
            top_splitter.setObjectName(f"view_layout_grid_{key}_top")
            top_splitter.setChildrenCollapsible(False)

            bottom_splitter = QSplitter(Qt.Orientation.Horizontal)
            bottom_splitter.setObjectName(f"view_layout_grid_{key}_bottom")
            bottom_splitter.setChildrenCollapsible(False)

            outer_splitter.addWidget(top_splitter)
            outer_splitter.addWidget(bottom_splitter)
            outer_layout.addWidget(outer_splitter)

            self._sync_splitters(top_splitter, bottom_splitter)
            self._grid_widgets[key] = container

        outer_layout = cast(QVBoxLayout, container.layout())
        item = outer_layout.itemAt(0)
        if item is None:
            raise ViewLayoutRendererError("2x2 grid layout has no items")
        outer_splitter = cast(QSplitter, item.widget())
        top_splitter = cast(QSplitter, outer_splitter.widget(0))
        bottom_splitter = cast(QSplitter, outer_splitter.widget(1))

        for splitter in (top_splitter, bottom_splitter):
            while splitter.count():
                widget = splitter.widget(0)
                if widget is not None:
                    widget.setParent(None)

        top_row, bottom_row = node.children
        top_left, top_right = top_row.children
        bottom_left, bottom_right = bottom_row.children

        top_splitter.addWidget(self._render_leaf(top_left, views_by_id))
        top_splitter.addWidget(self._render_leaf(top_right, views_by_id))
        bottom_splitter.addWidget(self._render_leaf(bottom_left, views_by_id))
        bottom_splitter.addWidget(self._render_leaf(bottom_right, views_by_id))

        for splitter in (outer_splitter, top_splitter, bottom_splitter):
            n = splitter.count()
            if n >= 2:
                base = 1000 // n
                splitter.setSizes([base] * n)

        return container

    def _sync_splitters(self, a: QSplitter, b: QSplitter) -> None:
        def _sync(source: QSplitter, target: QSplitter) -> None:
            target.blockSignals(True)
            target.setSizes(source.sizes())
            target.blockSignals(False)

        a.splitterMoved.connect(lambda pos, idx: _sync(a, b))
        b.splitterMoved.connect(lambda pos, idx: _sync(b, a))

    # ----- QSplitter fallback (arbitrary layouts) -------------------

    def _render_split(
        self,
        node: ViewLayoutSpec,
        views_by_id: dict[str, View],
    ) -> QSplitter:
        key = id(node)
        splitter = self._split_widgets.get(key)
        if splitter is None:
            splitter = QSplitter(self._orientation_for(node.direction))
            splitter.setObjectName(f"view_layout_split_{key}")
            splitter.setChildrenCollapsible(False)
            splitter.splitterMoved.connect(self._on_splitter_moved)
            self._split_widgets[key] = splitter

        self._reconcile_children(splitter, node, views_by_id)
        return splitter

    def _on_splitter_moved(self, pos: int, index: int) -> None:
        if self._splitter_moved_callback is not None:
            self._splitter_moved_callback()

    # ----- Active-View forwarding (Block 4) -------------------------

    def _on_view_activated(self, view_id: str) -> None:
        """Forward a View activation to the Editor.

        Called by the event filter when the user clicks or focuses a
        View. The Editor decides whether to emit
        ``active_view_changed`` (it is idempotent for the same id).
        """
        if self._editor is None:
            return
        self._editor.set_active_view(view_id)

    def _on_active_view_changed(self, view_id: str | None) -> None:
        """Apply the ACTIVE_ONLY policy to every Toolbar.

        ``set_active`` is a no-op on non-ACTIVE_ONLY Toolbars, so it is
        safe to call on every Toolbar regardless of its visibility mode.
        """
        for vid, toolbars in self._toolbars_by_view.items():
            active = vid == view_id
            for toolbar in toolbars:
                toolbar.set_active(active)

    # ----- Internals ------------------------------------------------

    def _reconcile_children(
        self,
        splitter: QSplitter,
        node: ViewLayoutSpec,
        views_by_id: dict[str, View],
    ) -> None:
        expected: list[QWidget] = [self._render_node(child, views_by_id) for child in node.children]

        current: list[QWidget] = []
        for i in range(splitter.count()):
            widget = splitter.widget(i)
            if widget is not None:
                current.append(widget)
        for widget in current:
            if widget not in expected:
                widget.setParent(None)

        for index, widget in enumerate(expected):
            if splitter.indexOf(widget) == index:
                continue
            splitter.insertWidget(index, widget)

        for index in range(splitter.count()):
            splitter.setStretchFactor(index, 1)

        if splitter.count() >= 2:
            n = splitter.count()
            base = 1000 // n
            splitter.setSizes([base] * n)

    @staticmethod
    def _orientation_for(direction: SplitDirection | None) -> Qt.Orientation:
        if direction is SplitDirection.HORIZONTAL:
            return Qt.Orientation.Horizontal
        if direction is SplitDirection.VERTICAL:
            return Qt.Orientation.Vertical
        raise ViewLayoutRendererError(f"unknown split direction: {direction!r}")