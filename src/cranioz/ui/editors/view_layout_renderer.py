"""ViewLayoutRenderer.

Materializes a ViewLayoutSpec (nested split tree of Views) into Qt
widgets, using QSplitter for Splits and each View's content_widget()
for Leaves.

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

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QSplitter, QWidget

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
    """Materializes a ViewLayoutSpec into nested QSplitters + View widgets."""

    def __init__(self, on_splitter_moved: Callable[[], None] | None = None) -> None:
        self._splitter_moved_callback = on_splitter_moved
        self._split_widgets: dict[int, QSplitter] = {}

    # ----- Public API -----------------------------------------------

    def render(
        self,
        spec: ViewLayoutSpec,
        views_by_id: dict[str, View],
    ) -> QWidget:
        """Render the ViewLayoutSpec and return the root widget.

        Args:
            spec: the declarative layout of the Views.
            views_by_id: mapping from view_id to the View instance.
                Every view_id referenced in the spec must exist in
                this mapping.

        Returns:
            The root widget (a QSplitter for a Split root, or the
            View's content widget for a Leaf root).

        Raises:
            ViewLayoutRendererError: if a view_id is missing from
                `views_by_id`, or if the spec is malformed.
        """
        return self._render_node(spec, views_by_id)

    def clear_cache(self) -> None:
        """Discard all cached splitters.

        Called when the Editor is disposed or when the layout is
        rebuilt from scratch. After clear_cache(), a subsequent
        render() creates new splitters.
        """
        for splitter in self._split_widgets.values():
            splitter.setParent(None)
            splitter.deleteLater()
        self._split_widgets.clear()

    # ----- Internals ------------------------------------------------

    def _render_node(
        self,
        node: ViewLayoutSpec,
        views_by_id: dict[str, View],
    ) -> QWidget:
        if node.type is ViewLayoutType.LEAF:
            return self._render_leaf(node, views_by_id)
        if node.type is ViewLayoutType.SPLIT:
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

        # Detach children that are no longer part of the split.
        current: list[QWidget] = []
        for i in range(splitter.count()):
            widget = splitter.widget(i)
            if widget is not None:
                current.append(widget)
        for widget in current:
            if widget not in expected:
                widget.setParent(None)

        # Insert expected children in the right order.
        for index, widget in enumerate(expected):
            if splitter.indexOf(widget) == index:
                continue
            splitter.insertWidget(index, widget)

    @staticmethod
    def _orientation_for(direction: SplitDirection | None) -> Qt.Orientation:
        if direction is SplitDirection.HORIZONTAL:
            return Qt.Orientation.Horizontal
        if direction is SplitDirection.VERTICAL:
            return Qt.Orientation.Vertical
        raise ViewLayoutRendererError(f"unknown split direction: {direction!r}")
