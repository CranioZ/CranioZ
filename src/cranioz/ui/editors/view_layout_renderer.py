"""ViewLayoutRenderer.

Materializes a ViewLayoutSpec (nested split tree of Views) into Qt
widgets.

For the common 2x2 grid pattern (Split(VERTICAL) with two
Split(HORIZONTAL) children, each with two leaves), the renderer uses
a QGridLayout, so the row and column dividers are shared (dragging
one divider moves all cells in that row/column). This is the
expected behavior for a 2x2 grid.

For other layouts (arbitrary N-ary split trees), the renderer falls
back to nested QSplitters, each managing its own children
independently. This is the expected behavior for non-grid layouts.

This is the counterpart of LayoutRenderer (which materializes the
Area Layout Tree). The ViewLayoutRenderer does the same job for the
View Layout Tree inside an Editor.

The renderer is stateless with respect to a single render() call: it
can be reused across renders. It does not mutate the spec.

See ADR-0013 §2.4.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import cast

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QSplitter, QVBoxLayout, QWidget

from cranioz.ui.editors.view import View
from cranioz.ui.editors.view_layout_spec import (
    SplitDirection,
    ViewLayoutSpec,
    ViewLayoutType,
)

_logger = logging.getLogger(__name__)


class ViewLayoutRendererError(ValueError):
    """Raised when the ViewLayoutRenderer cannot materialize a spec."""


class ViewLayoutRenderer:
    """Materializes a ViewLayoutSpec into Qt widgets."""

    def __init__(self, on_splitter_moved: Callable[[], None] | None = None) -> None:
        self._splitter_moved_callback = on_splitter_moved
        self._split_widgets: dict[int, QSplitter] = {}
        self._grid_widgets: dict[int, QWidget] = {}

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
        for splitter in self._split_widgets.values():
            splitter.setParent(None)
            splitter.deleteLater()
        self._split_widgets.clear()

        for grid in self._grid_widgets.values():
            grid.setParent(None)
            grid.deleteLater()
        self._grid_widgets.clear()

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
        return view.content_widget()

    # ----- 2x2 grid (QGridLayout) -----------------------------------

    @staticmethod
    def _is_2x2_grid(node: ViewLayoutSpec) -> bool:
        """Return True if node is a 2x2 grid pattern."""
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

            outer_layout = QVBoxLayout(container)
            outer_layout.setContentsMargins(0, 0, 0, 0)
            outer_layout.setSpacing(0)

            outer_splitter = QSplitter(Qt.Orientation.Vertical)
            outer_splitter.setObjectName(f"view_layout_grid_{key}_rows")
            outer_splitter.setChildrenCollapsible(False)

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

        # Find the outer splitter and the two inner splitters.
        outer_layout = cast(QVBoxLayout, container.layout())
        item = outer_layout.itemAt(0)
        if item is None:
            raise ViewLayoutRendererError("2x2 grid layout has no items")
        outer_splitter = cast(QSplitter, item.widget())
        top_splitter = cast(QSplitter, outer_splitter.widget(0))
        bottom_splitter = cast(QSplitter, outer_splitter.widget(1))

        # Clear existing children from the inner splitters.
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

    def _sync_splitters(
        self,
        a: QSplitter,
        b: QSplitter,
    ) -> None:
        """Synchronize two splitters: dragging one moves the other."""

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
        """Notify the Editor that a splitter was moved."""
        if self._splitter_moved_callback is not None:
            self._splitter_moved_callback()

    def _reconcile_children(
        self,
        splitter: QSplitter,
        node: ViewLayoutSpec,
        views_by_id: dict[str, View],
    ) -> None:
        """Ensure the splitter's children match the spec's children."""
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

        # Give every child the same stretch factor.
        for index in range(splitter.count()):
            splitter.setStretchFactor(index, 1)

        # Force a perfectly equal distribution of sizes.
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
