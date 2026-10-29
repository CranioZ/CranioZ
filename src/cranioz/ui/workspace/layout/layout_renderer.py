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
    ) -> None:
        self._tool_registry = tool_registry
        self._theme_service = theme_service
        self._debug_colors = debug_colors

        # Caches. Keyed by the identity of the model object (id(Split))
        # or by the stable domain identifier (area_id).
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

    def compute_region_bounds(
        self,
        workspace: QWidget,
    ) -> dict[Placement, Bounds]:
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
                    # Guard: if the widget is not yet laid out by Qt,
                    # its geometry is invalid. Skip it.
                    if not w.isVisible() or w.width() <= 0 or w.height() <= 0:
                        continue
                    top_left = w.mapTo(workspace, w.rect().topLeft())
                    # QPoint does NOT have isValid(). Just check the widget's size.
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
        """Return (or create) a QSplitter for the split node.

        The QSplitter is created once per Split node (keyed by
        id(split)) and reused on subsequent renders of the same tree.
        Children are always re-inserted in the correct order, so the
        splitter reflects the current structure of the tree.
        """
        key = id(split)
        splitter = self._split_widgets.get(key)
        if splitter is None:
            splitter = QSplitter(self._orientation_for(split.direction))
            splitter.setObjectName(f"split_{key}")
            splitter.setChildrenCollapsible(False)
            self._split_widgets[key] = splitter

        # Ensure children are present and in the right order. We do
        # not recreate children that are already attached to the
        # splitter, to preserve their internal state (e.g. tab
        # selection inside an AreaWidget).
        self._reconcile_children(splitter, split)
        return splitter

    def _reconcile_children(
        self,
        splitter: QSplitter,
        split: Split,
    ) -> None:
        """Ensure the splitter's children match the split's children.

        Rules:
        - A child widget that is already attached to the splitter is
          left in place (its internal state is preserved).
        - A child widget that is missing is created and inserted in
          the right position.
        - A child widget that is attached but no longer part of the
          split is detached (its parent is cleared, but the widget is
          not destroyed — it may be reused elsewhere, or it lives in
          the area_widgets cache).
        """
        expected_widgets: list[QWidget] = [self._render_node(child) for child in split.children]

        # Collect the widgets currently attached to the splitter.
        # QSplitter.widget(i) is typed as QWidget | None, so we filter
        # out None values explicitly. This is not merely a typing fix:
        # it protects the loop below from a None that would otherwise
        # break .setParent().
        current_widgets: list[QWidget] = []
        for i in range(splitter.count()):
            widget = splitter.widget(i)
            if widget is not None:
                current_widgets.append(widget)

        # Detach widgets that should no longer be children of this
        # splitter. We do not destroy them here: they may still be in
        # the area_widgets cache and reused later.
        for widget in current_widgets:
            if widget not in expected_widgets:
                widget.setParent(None)

        # Insert the expected widgets in the right order. Qt's
        # QSplitter inserts at the requested index when the widget is
        # not yet a child. If the widget is already a child at the
        # correct index, insertWidget() is a no-op for the position.
        for index, widget in enumerate(expected_widgets):
            current_index = splitter.indexOf(widget)
            if current_index == index:
                continue
            splitter.insertWidget(index, widget)

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
