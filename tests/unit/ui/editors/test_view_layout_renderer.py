"""Unit tests for ViewLayoutRenderer.

The renderer materializes a ViewLayoutSpec into nested QSplitters
with each View's content_widget() at the Leaves.

These tests use a FakeView (a View subclass) whose content_widget()
returns a QLabel. The tests verify the structure of the rendered
widget tree.

Per ADR-0013 §2.6, each Leaf is wrapped in a container widget that
holds the View's declared Toolbars around the content_widget().
These tests use a FakeView that declares no Toolbars, so the
container has no Toolbar children, but the Leaf is still a container
(not the raw content_widget()).
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QSplitter, QWidget
from pytestqt.qtbot import QtBot
from tests.conftest import make_icon_provider, make_theme_service

from cranioz.ui.editors.view import View
from cranioz.ui.editors.view_layout_renderer import (
    ViewLayoutRenderer,
    ViewLayoutRendererError,
)
from cranioz.ui.editors.view_layout_spec import (
    SplitDirection,
    ViewLayoutSpec,
)
from cranioz.ui.icons.provider import IconProvider
from cranioz.ui.theme.service import ThemeService
from cranioz.ui.toolbars.base import Toolbar
from cranioz.ui.tools.builtin.log_tool import LogTool
from cranioz.ui.tools.builtin.toggle_tool import ToggleTool
from cranioz.ui.tools.registry.tool_registry import ToolRegistry


class FakeView(View):
    """A minimal View whose content_widget is a QLabel.

    Declares no Toolbars, so the container has no Toolbar children.
    """

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
def tool_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register("tool.log", LogTool)
    registry.register("tool.toggle", ToggleTool)
    return registry


@pytest.fixture
def theme_service() -> ThemeService:
    return make_theme_service()


@pytest.fixture
def icon_provider(theme_service: ThemeService) -> IconProvider:
    return make_icon_provider(theme_service)


@pytest.fixture
def renderer(
    tool_registry: ToolRegistry,
    theme_service: ThemeService,
    icon_provider: IconProvider,
) -> ViewLayoutRenderer:
    return ViewLayoutRenderer(
        tool_registry=tool_registry,
        theme_service=theme_service,
        icon_provider=icon_provider,
    )


@pytest.fixture
def views() -> dict[str, View]:
    return {
        "view.a": FakeView("view.a"),
        "view.b": FakeView("view.b"),
        "view.c": FakeView("view.c"),
        "view.d": FakeView("view.d"),
    }


# ----- Single Leaf --------------------------------------------------


def test_render_single_leaf_returns_container(
    qtbot: QtBot,
    renderer: ViewLayoutRenderer,
    views: dict[str, View],
) -> None:
    """A Leaf is wrapped in a container, not returned as the raw content.

    Per ADR-0013 §2.6, the container is where View-level Toolbars
    live. Even when the View declares no Toolbars, the Leaf is still
    a container (so future Toolbars do not require a structural
    change).
    """
    spec = ViewLayoutSpec.leaf("view.a")
    root = renderer.render(spec, views)
    qtbot.addWidget(root)

    assert isinstance(root, QWidget)
    assert not isinstance(root, QSplitter)
    # No Toolbars (the FakeView declares none).
    assert root.findChildren(Toolbar) == []
    # The View's content_widget() is inside the container.
    content = views["view.a"].content_widget()
    assert root.isAncestorOf(content)
    assert content.text() == "view.a"


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
    # Children are containers, not raw QLabels. Verify the order by
    # inspecting the content label inside each container.
    child_0 = root.widget(0)
    child_1 = root.widget(1)
    assert isinstance(child_0, QWidget)
    assert isinstance(child_1, QWidget)

    content_a = views["view.a"].content_widget()
    content_b = views["view.b"].content_widget()
    assert child_0.isAncestorOf(content_a)
    assert child_1.isAncestorOf(content_b)
    assert content_a.text() == "view.a"
    assert content_b.text() == "view.b"


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

    # Left child is a container holding view.a's content.
    left = root.widget(0)
    assert isinstance(left, QWidget)
    assert left.isAncestorOf(views["view.a"].content_widget())

    # Right child is a vertical split.
    right = root.widget(1)
    assert isinstance(right, QSplitter)
    assert right.orientation() == Qt.Vertical
    assert right.count() == 2

    # Top of the vertical split is a container holding view.b's content.
    top = right.widget(0)
    assert isinstance(top, QWidget)
    assert top.isAncestorOf(views["view.b"].content_widget())

    # Bottom of the vertical split is a horizontal split.
    bottom = right.widget(1)
    assert isinstance(bottom, QSplitter)
    assert bottom.orientation() == Qt.Horizontal
    assert bottom.count() == 2

    # Its children are containers holding view.c and view.d.
    bottom_0 = bottom.widget(0)
    bottom_1 = bottom.widget(1)
    assert isinstance(bottom_0, QWidget)
    assert isinstance(bottom_1, QWidget)
    assert bottom_0.isAncestorOf(views["view.c"].content_widget())
    assert bottom_1.isAncestorOf(views["view.d"].content_widget())


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


def test_render_2x2_grid_container_expands(
    qtbot: QtBot,
    renderer: ViewLayoutRenderer,
    views: dict[str, View],
) -> None:
    """The grid container must use Expanding policy (G2 polish).

    Without Expanding, the QVBoxLayout of the AreaWidget limits the
    grid to its sizeHint, leaving ~200 px of unused space.
    """
    from PySide6.QtWidgets import QSizePolicy

    spec = ViewLayoutSpec.split(
        SplitDirection.VERTICAL,
        (
            ViewLayoutSpec.split(
                SplitDirection.HORIZONTAL,
                (ViewLayoutSpec.leaf("view.a"), ViewLayoutSpec.leaf("view.b")),
            ),
            ViewLayoutSpec.split(
                SplitDirection.HORIZONTAL,
                (ViewLayoutSpec.leaf("view.c"), ViewLayoutSpec.leaf("view.d")),
            ),
        ),
    )
    root = renderer.render(spec, views)
    qtbot.addWidget(root)

    assert root.sizePolicy().horizontalPolicy() == QSizePolicy.Policy.Expanding
    assert root.sizePolicy().verticalPolicy() == QSizePolicy.Policy.Expanding


def test_render_2x2_outer_splitter_expands(
    qtbot: QtBot,
    renderer: ViewLayoutRenderer,
    views: dict[str, View],
) -> None:
    """The outer QSplitter of the 2x2 grid must use Expanding policy."""
    from PySide6.QtWidgets import QSizePolicy

    spec = ViewLayoutSpec.split(
        SplitDirection.VERTICAL,
        (
            ViewLayoutSpec.split(
                SplitDirection.HORIZONTAL,
                (ViewLayoutSpec.leaf("view.a"), ViewLayoutSpec.leaf("view.b")),
            ),
            ViewLayoutSpec.split(
                SplitDirection.HORIZONTAL,
                (ViewLayoutSpec.leaf("view.c"), ViewLayoutSpec.leaf("view.d")),
            ),
        ),
    )
    root = renderer.render(spec, views)
    qtbot.addWidget(root)

    outer_splitter = root.findChild(QSplitter)
    assert outer_splitter is not None
    assert outer_splitter.sizePolicy().horizontalPolicy() == QSizePolicy.Policy.Expanding
    assert outer_splitter.sizePolicy().verticalPolicy() == QSizePolicy.Policy.Expanding
