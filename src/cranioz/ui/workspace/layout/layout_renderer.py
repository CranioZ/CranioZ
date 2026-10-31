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
        debug_colors: bool = False,
        on_splitter_moved: Callable[[], None] | None = None,
    ) -> None:
        self._tool_registry = tool_registry
        self._theme_service = theme_service
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

        `widget.geometry()` is relative to the widget's parent. In nested
        QSplitter layouts, AreaWidgets may have different parents, so the
        union of their geometries does NOT represent a Workspace-coordinate
        Region. This method maps each AreaWidget's rect to Workspace
        coordinates via `mapTo(workspace, ...)` before unioning.
        """
        grouped: dict[Placement, list[AreaWidget]] = {}
        for widget in self._area_widgets.values():
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
        """Return (or create) an AreaWidget for the leaf's Area."""
        area = leaf.area
        widget = self._area_widgets.get(area.area_id)
        if widget is None:
            widget = AreaWidget(
                area=area,
                tool_registry=self._tool_registry,
                theme_service=self._theme_service,
                debug_colors=self._debug_colors,
            )
            self._area_widgets[area.area_id] = widget
        return widget

    def _render_split(self, split: Split) -> QSplitter:
        key = id(split)
        splitter = self._split_widgets.get(key)
        if splitter is None:
            splitter = QSplitter(self._orientation_for(split.direction))
            splitter.setObjectName(f"split_{key}")
            splitter.setChildrenCollapsible(False)
            # NOVO: conectar splitterMoved ao callback
            splitter.splitterMoved.connect(self._on_splitter_moved)
            self._split_widgets[key] = splitter

        self._reconcile_children(splitter, split)
        return splitter

    def _on_splitter_moved(self, pos: int, index: int) -> None:
        """Notify the Workspace that a splitter was moved."""
        if self._splitter_moved_callback is not None:
            self._splitter_moved_callback()

    def _reconcile_children(
        self,
        splitter: QSplitter,
        split: Split,
    ) -> None:
        """Ensure the splitter's children match the split's children."""
        expected_widgets: list[QWidget] = [self._render_node(child) for child in split.children]

        # Detach all current widgets. We re-add them below.
        while splitter.count():
            item = splitter.widget(0)
            if item is not None:
                item.setParent(None)

        # Insert the expected widgets in the right order.
        for widget in expected_widgets:
            splitter.addWidget(widget)

        # Give every child the same stretch factor and equal sizes.
        for index in range(splitter.count()):
            splitter.setStretchFactor(index, 1)
        if splitter.count() >= 2:
            n = splitter.count()
            base = 1000 // n
            splitter.setSizes([base] * n)

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
