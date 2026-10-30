"""Unit tests for ViewLayoutRenderer.

The renderer materializes a ViewLayoutSpec into nested QSplitters
with each View's content_widget() at the Leaves.

These tests use a FakeView (a View subclass) whose content_widget()
returns a QLabel. The tests verify the structure of the rendered
widget tree.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QSplitter
from pytestqt.qtbot import QtBot

from cranioz.ui.editors.view import View
from cranioz.ui.editors.view_layout_renderer import (
    ViewLayoutRenderer,
    ViewLayoutRendererError,
)
from cranioz.ui.editors.view_layout_spec import (
    SplitDirection,
    ViewLayoutSpec,
)


class FakeView(View):
    """A minimal View whose content_widget is a QLabel."""

    def __init__(self, view_id: str, view_type: str = "fake") -> None:
        super().__init__(view_id=view_id, view_type=view_type)
        self._label: QLabel | None = None

    def content_widget(self) -> QLabel:
        if self._label is None:
            self._label = QLabel(self.view_id)
            self._label.setObjectName(f"fake_view.{self.view_id}")
        return self._label


# ----- Fixtures -----------------------------------------------------


@pytest.fixture
def renderer() -> ViewLayoutRenderer:
    return ViewLayoutRenderer()


@pytest.fixture
def views() -> dict[str, View]:
    return {
        "view.a": FakeView("view.a"),
        "view.b": FakeView("view.b"),
        "view.c": FakeView("view.c"),
        "view.d": FakeView("view.d"),
    }


# ----- Single Leaf --------------------------------------------------


def test_render_single_leaf_returns_content_widget(
    qtbot: QtBot,
    renderer: ViewLayoutRenderer,
    views: dict[str, View],
) -> None:
    spec = ViewLayoutSpec.leaf("view.a")
    root = renderer.render(spec, views)
    qtbot.addWidget(root)

    assert isinstance(root, QLabel)
    assert root.text() == "view.a"


def test_render_single_leaf_missing_view_raises(
    renderer: ViewLayoutRenderer,
    views: dict[str, View],
) -> None:
    spec = ViewLayoutSpec.leaf("view.unknown")
    with pytest.raises(ViewLayoutRendererError, match="unknown"):
        renderer.render(spec, views)


# ----- Horizontal Split --------------------------------------------


def test_render_horizontal_split_returns_qsplitter(
    qtbot: QtBot,
    renderer: ViewLayoutRenderer,
    views: dict[str, View],
) -> None:
    spec = ViewLayoutSpec.split(
        SplitDirection.HORIZONTAL,
        (ViewLayoutSpec.leaf("view.a"), ViewLayoutSpec.leaf("view.b")),
    )
    root = renderer.render(spec, views)
    qtbot.addWidget(root)

    assert isinstance(root, QSplitter)
    assert root.orientation() == Qt.Horizontal
    assert root.count() == 2


def test_render_horizontal_split_children_order(
    qtbot: QtBot,
    renderer: ViewLayoutRenderer,
    views: dict[str, View],
) -> None:
    spec = ViewLayoutSpec.split(
        SplitDirection.HORIZONTAL,
        (ViewLayoutSpec.leaf("view.a"), ViewLayoutSpec.leaf("view.b")),
    )
    root = renderer.render(spec, views)
    qtbot.addWidget(root)

    assert isinstance(root, QSplitter)
    child_0 = root.widget(0)
    child_1 = root.widget(1)
    assert isinstance(child_0, QLabel)
    assert isinstance(child_1, QLabel)
    assert child_0.text() == "view.a"
    assert child_1.text() == "view.b"


# ----- Vertical Split ----------------------------------------------


def test_render_vertical_split_returns_qsplitter(
    qtbot: QtBot,
    renderer: ViewLayoutRenderer,
    views: dict[str, View],
) -> None:
    spec = ViewLayoutSpec.split(
        SplitDirection.VERTICAL,
        (ViewLayoutSpec.leaf("view.a"), ViewLayoutSpec.leaf("view.b")),
    )
    root = renderer.render(spec, views)
    qtbot.addWidget(root)

    assert isinstance(root, QSplitter)
    assert root.orientation() == Qt.Vertical


# ----- Nested Split (2x2) ------------------------------------------


def test_render_2x2_nested_split(
    qtbot: QtBot,
    renderer: ViewLayoutRenderer,
    views: dict[str, View],
) -> None:
    spec = ViewLayoutSpec.split(
        SplitDirection.HORIZONTAL,
        (
            ViewLayoutSpec.leaf("view.a"),
            ViewLayoutSpec.split(
                SplitDirection.VERTICAL,
                (
                    ViewLayoutSpec.leaf("view.b"),
                    ViewLayoutSpec.split(
                        SplitDirection.HORIZONTAL,
                        (
                            ViewLayoutSpec.leaf("view.c"),
                            ViewLayoutSpec.leaf("view.d"),
                        ),
                    ),
                ),
            ),
        ),
    )
    root = renderer.render(spec, views)
    qtbot.addWidget(root)

    assert isinstance(root, QSplitter)
    assert root.orientation() == Qt.Horizontal
    assert root.count() == 2

    # Left child is a leaf.
    left = root.widget(0)
    assert isinstance(left, QLabel)
    assert left.text() == "view.a"

    # Right child is a vertical split.
    right = root.widget(1)
    assert isinstance(right, QSplitter)
    assert right.orientation() == Qt.Vertical
    assert right.count() == 2

    # Top of the vertical split is view.b.
    top = right.widget(0)
    assert isinstance(top, QLabel)
    assert top.text() == "view.b"

    # Bottom of the vertical split is a horizontal split.
    bottom = right.widget(1)
    assert isinstance(bottom, QSplitter)
    assert bottom.orientation() == Qt.Horizontal
    assert bottom.count() == 2


# ----- Cache reuse --------------------------------------------------


def test_render_same_spec_twice_reuses_splitter(
    qtbot: QtBot,
    renderer: ViewLayoutRenderer,
    views: dict[str, View],
) -> None:
    spec = ViewLayoutSpec.split(
        SplitDirection.HORIZONTAL,
        (ViewLayoutSpec.leaf("view.a"), ViewLayoutSpec.leaf("view.b")),
    )
    first = renderer.render(spec, views)
    second = renderer.render(spec, views)
    qtbot.addWidget(first)

    assert first is second


def test_clear_cache_discards_splitters(
    qtbot: QtBot,
    renderer: ViewLayoutRenderer,
    views: dict[str, View],
) -> None:
    spec = ViewLayoutSpec.split(
        SplitDirection.HORIZONTAL,
        (ViewLayoutSpec.leaf("view.a"), ViewLayoutSpec.leaf("view.b")),
    )
    renderer.render(spec, views)
    renderer.clear_cache()

    # After clear_cache, a new render creates a new splitter.
    second = renderer.render(spec, views)
    qtbot.addWidget(second)
    assert isinstance(second, QSplitter)
