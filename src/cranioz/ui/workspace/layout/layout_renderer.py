"""LayoutRenderer.

Materializes a LayoutTree into Qt widgets.

The LayoutRenderer is a translator between the pure data model
(LayoutTree, produced by the LayoutBuilder) and Qt. It never mutates
the LayoutTree.

The renderer maintains a rebuildable cache of widgets:

- split_widgets: id(Split)  -> QSplitter
- area_widgets:  area_id    -> AreaWidget

The cache is an optimization. It is always rebuildable from the
tree. If there is any divergence between the cache and the tree,
the tree wins. The cache exists so that incremental re-renders (for
example, when a single Area changes) can reuse existing widgets
instead of rebuilding everything.

Responsibilities:

- Walk the LayoutTree recursively.
- For each Leaf, obtain or create an AreaWidget for the Area.
- For each Split, obtain or create a QSplitter with the correct
  orientation, and insert the rendered children.
- Return the root widget.
- Compute the geometric Bounds of each Region, using ``Area.visible``
  (the runtime source of truth) to decide whether an Area should
  contribute.

Non-responsibilities:

- The LayoutRenderer does not create Editors. Editors come from the
  LayoutBuilder, already initialized.
- The LayoutRenderer does not materialize the interior of an Area.
  That is the AreaWidget's job.
- The LayoutRenderer does not manage overlays or regions. Those are
  handled in later pieces.
- The LayoutRenderer does not persist layout state. That is
  handled in a later piece.

Qt dependency:

- The LayoutRenderer imports PySide6. It is the first piece of the
  Workspace layout subsystem that requires a QApplication to run.
- Its tests use qtbot and instantiate real widgets.
"""

from __future__ import annotations

import logging
from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QSplitter, QWidget

from cranioz.ui.icons.provider import IconProvider
from cranioz.ui.theme.service import ThemeService
from cranioz.ui.tools.registry.tool_registry import ToolRegistry
from cranioz.ui.workspace.areas.area_widget import AreaWidget
from cranioz.ui.workspace.areas.placement import Placement
from cranioz.ui.workspace.layout.layout_tree import (
    LayoutNode,
    LayoutTree,
    Leaf,
    Split,
)
from cranioz.ui.workspace.overlays.region import Bounds
from cranioz.ui.workspace.specs.editor_layout_spec import SplitDirection

_logger = logging.getLogger(__name__)


class LayoutRendererError(ValueError):
    """Raised when the LayoutRenderer cannot materialize a tree."""


class LayoutRenderer:
    """Materializes a LayoutTree into Qt widgets.

    The renderer is stateless with respect to a single render() call:
    it can be reused across renders. State that varies between renders
    (the widget cache) is stored on the instance but is always
    rebuildable from the tree.
    """

    def __init__(
        self,
        tool_registry: ToolRegistry,
        theme_service: ThemeService,
        *,
        icon_provider: IconProvider,
        debug_colors: bool = False,
        on_splitter_moved: Callable[[], None] | None = None,
    ) -> None:
        self._tool_registry = tool_registry
        self._theme_service = theme_service
        self._icon_provider = icon_provider
        self._debug_colors = debug_colors
        self._splitter_moved_callback = on_splitter_moved

        self._split_widgets: dict[int, QSplitter] = {}
        self._area_widgets: dict[str, AreaWidget] = {}

    # ----- Public API -----------------------------------------------

    def render(self, tree: LayoutTree) -> QWidget:
        """Render the LayoutTree and return the root widget.

        The root widget is either:

        - a QSplitter, when the root node is a Split;
        - an AreaWidget, when the root node is a Leaf.

        The method is idempotent for the same tree instance: calling
        it twice returns the same root widget, reusing cached
        sub-widgets.
        """
        return self._render_node(tree.root)

    def clear_cache(self) -> None:
        """Discard all cached widgets.

        Called when the tree is fully rebuilt and old widgets are no
        longer needed. After clear_cache(), a subsequent render()
        creates new widgets from scratch.
        """
        for splitter in self._split_widgets.values():
            splitter.setParent(None)
            splitter.deleteLater()
        for area_widget in self._area_widgets.values():
            area_widget.setParent(None)
            area_widget.deleteLater()
        self._split_widgets.clear()
        self._area_widgets.clear()

    def cached_area_widget(self, area_id: str) -> AreaWidget | None:
        """Return the cached AreaWidget for the given area_id, if any."""
        return self._area_widgets.get(area_id)

    # ----- Region geometry ------------------------------------------

    def compute_region_bounds(self, workspace: QWidget) -> dict[Placement, Bounds]:
        """Compute the geometric Bounds of each Region in Workspace coordinates.

        ``widget.geometry()`` is relative to the widget's parent. In
        nested QSplitter layouts, AreaWidgets may have different
        parents, so the union of their geometries does NOT represent a
        Workspace-coordinate Region. This method maps each AreaWidget's
        rect to Workspace coordinates via ``mapTo(workspace, ...)``
        before unioning.

        Only Areas whose model says ``visible`` participate. The model
        (``Area.visible``) is the runtime source of truth: it is set
        by ``Workspace.set_area_visible`` and is independent of the
        Qt visibility propagation, which can lag behind (for example,
        a widget hidden inside a QSplitter may report ``isHidden()``
        as False until the splitter re-lays out). Using the model
        keeps the Region bounds aligned with what the Workspace
        intends, not with what Qt currently reports.
        """
        grouped: dict[Placement, list[AreaWidget]] = {}
        for widget in self._area_widgets.values():
            if not widget.area().visible:
                continue
            placement = widget.area_placement()
            grouped.setdefault(placement, []).append(widget)

        result: dict[Placement, Bounds] = {}
        for placement, widgets in grouped.items():
            if not widgets:
                continue
            rects: list[tuple[int, int, int, int]] = []
            for w in widgets:
                try:
                    top_left = w.mapTo(workspace, w.rect().topLeft())
                    rects.append(
                        (
                            top_left.x(),
                            top_left.y(),
                            top_left.x() + w.width(),
                            top_left.y() + w.height(),
                        )
                    )
                except RuntimeError:
                    _logger.exception("cannot map area widget %r to workspace", w.area_id)
                    continue
            if not rects:
                continue
            left = min(r[0] for r in rects)
            top = min(r[1] for r in rects)
            right = max(r[2] for r in rects)
            bottom = max(r[3] for r in rects)
            result[placement] = Bounds(
                x=float(left),
                y=float(top),
                width=float(right - left),
                height=float(bottom - top),
            )
        return result

    @staticmethod
    def _union_bounds(widgets: list[AreaWidget]) -> Bounds | None:
        """Return the axis-aligned union of the widgets' geometries.

        Returns None when the list is empty. Coordinates are in the
        local coordinate space of each widget's parent; the union
        assumes the widgets share a common parent, which is the
        case for all AreaWidgets inside the same Workspace.
        """
        if not widgets:
            return None

        rects = [widget.geometry() for widget in widgets]
        left = min(r.left() for r in rects)
        top = min(r.top() for r in rects)
        right = max(r.right() for r in rects)
        bottom = max(r.bottom() for r in rects)

        return Bounds(
            x=float(left),
            y=float(top),
            width=float(right - left),
            height=float(bottom - top),
        )

    # ----- Internals ------------------------------------------------

    def _render_node(self, node: LayoutNode) -> QWidget:
        """Dispatch a node to the leaf or split renderer."""
        if isinstance(node, Leaf):
            return self._render_leaf(node)
        if isinstance(node, Split):
            return self._render_split(node)
        raise LayoutRendererError(f"unknown layout node type: {type(node).__name__}")

    def _render_leaf(self, leaf: Leaf) -> AreaWidget:
        """Return (or create) an AreaWidget for the leaf's Area.

        Block 5.5: the widget uses ``QSizePolicy.Expanding`` so the
        parent QSplitter gives it the full available space. The
        minimum size is forced to 0 so the Workspace can apply
        percentage-based splitter sizes (20% / 25% / 20%) even when
        the editor content has a larger intrinsic sizeHint. This is
        the *only* place where the minimum is reset; the Workspace
        does not need to do it on every layout pass, which keeps the
        layout recalculation O(1) per widget instead of O(N) per
        splitter per event.
        """
        area = leaf.area
        widget = self._area_widgets.get(area.area_id)
        if widget is None:
            widget = AreaWidget(
                area=area,
                tool_registry=self._tool_registry,
                theme_service=self._theme_service,
                icon_provider=self._icon_provider,
                debug_colors=self._debug_colors,
            )
            # Force minimum to 0 so the QSplitter respects the
            # percentage-based setSizes() applied by the Workspace.
            widget.setMinimumSize(0, 0)
            self._area_widgets[area.area_id] = widget
        return widget

    def _render_split(self, split: Split) -> QSplitter:
        key = id(split)
        splitter = self._split_widgets.get(key)
        if splitter is None:
            splitter = QSplitter(self._orientation_for(split.direction))
            splitter.setObjectName(f"split_{key}")
            splitter.setChildrenCollapsible(False)
            splitter.setHandleWidth(8)
            splitter.splitterMoved.connect(self._on_splitter_moved)
            self._split_widgets[key] = splitter

        self._reconcile_children(splitter, split)
        return splitter

    def _on_splitter_moved(self, pos: int, index: int) -> None:
        """Notify the Workspace that a splitter was moved.

        Block 5.5: the Workspace uses this callback to reposition
        the overlays (so the TopOverlay follows the Central Area's
        new bounds) but does NOT reschedule the splitter-size
        calculation, so a user drag is not overwritten by the
        default percentages.
        """
        if self._splitter_moved_callback is not None:
            self._splitter_moved_callback()

    def _reconcile_children(
        self,
        splitter: QSplitter,
        split: Split,
    ) -> None:
        """Ensure the splitter's children match the split's children.

        Block 5.5: the earlier version hardcoded
        ``setSizes([200, 800, 250])`` here, which competed with the
        Workspace's percentage-based sizing and caused the Central
        Area to be squeezed or the lateral Areas to look oversized.
        The hardcoded call is removed: the Workspace is now the
        single source of truth for splitter sizes, applied in
        ``_apply_default_splitter_sizes``.
        """
        expected_widgets: list[QWidget] = [
            self._render_node(child) for child in split.children
        ]

        # Detach all current widgets. We re-add them below.
        while splitter.count():
            item = splitter.widget(0)
            if item is not None:
                item.setParent(None)

        # Insert the expected widgets in the right order.
        for w in expected_widgets:
            splitter.addWidget(w)

        # Configure stretch factors based on placement.
        count = splitter.count()
        for index in range(count):
            child: QWidget | None = splitter.widget(index)
            if child is None:
                continue
            is_central = (
                hasattr(child, "area")
                and child.area().placement.value == "central"
            )
            stretch = 2 if is_central else 1
            splitter.setStretchFactor(index, stretch)

    @staticmethod
    def _orientation_for(direction: SplitDirection) -> Qt.Orientation:
        """Map a SplitDirection to a Qt orientation.

        HORIZONTAL in CranioZ means "children are laid out
        side by side, from left to right". That corresponds to
        Qt.Horizontal (QSplitter splits horizontally into columns).

        VERTICAL means "children are stacked top to bottom". That
        corresponds to Qt.Vertical.
        """
        if direction is SplitDirection.HORIZONTAL:
            return Qt.Orientation.Horizontal
        if direction is SplitDirection.VERTICAL:
            return Qt.Orientation.Vertical
        raise LayoutRendererError(f"unknown split direction: {direction!r}")