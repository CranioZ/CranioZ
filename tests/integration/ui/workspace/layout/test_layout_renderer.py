"""Integration tests for LayoutRenderer.

The LayoutRenderer materializes a LayoutTree into Qt widgets. It
delegates the interior of each Area to an AreaWidget, and creates a
QSplitter per Split node.

These tests use qtbot: the renderer creates real widgets, and the
Editors it indirectly materializes (DummyEditor) return a QLabel as
content. A QApplication is therefore required.

What these tests cover:

- Single Leaf: render() returns an AreaWidget.
- Horizontal Split: render() returns a QSplitter with
  Qt.Horizontal orientation.
- Vertical Split: render() returns a QSplitter with Qt.Vertical.
- Nested splits: render() produces nested QSplitters.
- The four-area layout (LEFT + CENTRAL + RIGHT + BOTTOM): the root
  is a vertical split; the top row is a horizontal split.
- AreaWidget caching: rendering the same tree twice returns the
  same AreaWidget instances.
- cached_area_widget() exposes the AreaWidget by area_id.
- clear_cache() discards widgets.
- Empty tree (root is not a Leaf or Split): raises a clear error.
- Child order is preserved and matches the tree.
- Re-rendering after cache clear creates fresh widgets.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QSplitter

from cranioz.ui.editors.builtin.test_editor import DummyEditor
from cranioz.ui.editors.editor_registry import EditorRegistry
from cranioz.ui.theme.service import ThemeName, ThemeService
from cranioz.ui.tools.builtin.log_tool import LogTool
from cranioz.ui.tools.builtin.toggle_tool import ToggleTool
from cranioz.ui.tools.registry.tool_registry import ToolRegistry
from cranioz.ui.workspace.areas.area_widget import AreaWidget
from cranioz.ui.workspace.areas.placement import Placement
from cranioz.ui.workspace.layout.layout_builder import LayoutBuilder
from cranioz.ui.workspace.layout.layout_renderer import (
    LayoutRenderer,
    LayoutRendererError,
)
from cranioz.ui.workspace.layout.layout_tree import Leaf
from cranioz.ui.workspace.specs.area_spec import AreaSpec
from cranioz.ui.workspace.specs.editor_layout_spec import (
    EditorLayoutSpec,
)
from cranioz.ui.workspace.specs.module_ui_spec import ModuleUISpec

# ----- Local helpers ------------------------------------------------


def _leaf(editor_id: str) -> EditorLayoutSpec:
    return EditorLayoutSpec.leaf(editor_id)


def _area(
    area_id: str,
    placement: Placement,
    editor_layout: EditorLayoutSpec,
) -> AreaSpec:
    return AreaSpec(
        area_id=area_id,
        title=area_id,
        placement=placement,
        editor_layout=editor_layout,
    )


def _spec(*areas: AreaSpec) -> ModuleUISpec:
    return ModuleUISpec(areas=tuple(areas))


def _build_result(*areas: AreaSpec):
    """Build a BuildResult from a set of AreaSpecs."""
    registry = EditorRegistry()
    for editor_id in (
        "editor.patient",
        "editor.viewport_3d",
        "editor.mpr_axial",
        "editor.mpr_sagittal",
        "editor.mpr_coronal",
        "editor.object_list",
        "editor.properties",
        "editor.console",
    ):
        registry.register(editor_id, DummyEditor)

    builder = LayoutBuilder(registry)
    return builder.build(_spec(*areas))


# ----- Fixtures local to this module --------------------------------


@pytest.fixture
def tool_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register("tool.log", LogTool)
    registry.register("tool.toggle", ToggleTool)
    return registry


@pytest.fixture
def theme_service() -> ThemeService:
    return ThemeService(theme=ThemeName.DARK)


@pytest.fixture
def renderer(
    tool_registry: ToolRegistry,
    theme_service: ThemeService,
) -> LayoutRenderer:
    return LayoutRenderer(tool_registry, theme_service)


# ----- Single Leaf --------------------------------------------------


def test_render_single_leaf_returns_area_widget(qtbot, renderer: LayoutRenderer) -> None:
    result = _build_result(
        _area("area.central", Placement.CENTRAL, _leaf("editor.patient")),
    )
    root = renderer.render(result.tree)
    qtbot.addWidget(root)

    assert isinstance(root, AreaWidget)
    assert root.area_id == "area.central"


def test_render_leaf_tree_root_is_leaf(
    renderer: LayoutRenderer,
) -> None:
    result = _build_result(
        _area("area.central", Placement.CENTRAL, _leaf("editor.patient")),
    )
    assert isinstance(result.tree.root, Leaf)


# ----- Horizontal Split ---------------------------------------------


def test_render_horizontal_split_returns_qsplitter(qtbot, renderer: LayoutRenderer) -> None:
    result = _build_result(
        _area("area.left", Placement.LEFT, _leaf("editor.object_list")),
        _area("area.central", Placement.CENTRAL, _leaf("editor.viewport_3d")),
        _area("area.right", Placement.RIGHT, _leaf("editor.properties")),
    )
    root = renderer.render(result.tree)
    qtbot.addWidget(root)

    assert isinstance(root, QSplitter)
    assert root.orientation() == Qt.Orientation.Horizontal
    assert root.count() == 3


def test_render_horizontal_split_children_order(qtbot, renderer: LayoutRenderer) -> None:
    result = _build_result(
        _area("area.left", Placement.LEFT, _leaf("editor.object_list")),
        _area("area.central", Placement.CENTRAL, _leaf("editor.viewport_3d")),
        _area("area.right", Placement.RIGHT, _leaf("editor.properties")),
    )
    root = renderer.render(result.tree)
    qtbot.addWidget(root)

    assert isinstance(root, QSplitter)
    child_ids = []
    for i in range(root.count()):
        widget = root.widget(i)
        assert isinstance(widget, AreaWidget)
        child_ids.append(widget.area_id)
    assert child_ids == ["area.left", "area.central", "area.right"]


# ----- Vertical Split -----------------------------------------------


def test_render_vertical_split_returns_qsplitter(qtbot, renderer: LayoutRenderer) -> None:
    result = _build_result(
        _area("area.central", Placement.CENTRAL, _leaf("editor.viewport_3d")),
        _area("area.bottom", Placement.BOTTOM, _leaf("editor.console")),
    )
    root = renderer.render(result.tree)
    qtbot.addWidget(root)

    assert isinstance(root, QSplitter)
    assert root.orientation() == Qt.Orientation.Vertical
    assert root.count() == 2


# ----- Nested Splits ------------------------------------------------


def test_render_four_areas_has_nested_splitters(qtbot, renderer: LayoutRenderer) -> None:
    result = _build_result(
        _area("area.left", Placement.LEFT, _leaf("editor.object_list")),
        _area("area.central", Placement.CENTRAL, _leaf("editor.viewport_3d")),
        _area("area.right", Placement.RIGHT, _leaf("editor.properties")),
        _area("area.bottom", Placement.BOTTOM, _leaf("editor.console")),
    )
    root = renderer.render(result.tree)
    qtbot.addWidget(root)

    # Root: VERTICAL
    assert isinstance(root, QSplitter)
    assert root.orientation() == Qt.Orientation.Vertical
    assert root.count() == 2

    # Top child: HORIZONTAL with 3 areas
    top = root.widget(0)
    assert isinstance(top, QSplitter)
    assert top.orientation() == Qt.Orientation.Horizontal
    assert top.count() == 3

    # Bottom child: single AreaWidget
    bottom = root.widget(1)
    assert isinstance(bottom, AreaWidget)
    assert bottom.area_id == "area.bottom"


# ----- Caching ------------------------------------------------------


def test_render_reuses_area_widgets_from_cache(qtbot, renderer: LayoutRenderer) -> None:
    result = _build_result(
        _area("area.central", Placement.CENTRAL, _leaf("editor.patient")),
    )
    root_first = renderer.render(result.tree)
    root_second = renderer.render(result.tree)
    qtbot.addWidget(root_first)

    assert root_first is root_second


def test_cached_area_widget_returns_widget(qtbot, renderer: LayoutRenderer) -> None:
    result = _build_result(
        _area("area.left", Placement.LEFT, _leaf("editor.object_list")),
        _area("area.central", Placement.CENTRAL, _leaf("editor.viewport_3d")),
    )
    root = renderer.render(result.tree)
    qtbot.addWidget(root)

    left = renderer.cached_area_widget("area.left")
    central = renderer.cached_area_widget("area.central")
    unknown = renderer.cached_area_widget("area.unknown")

    assert isinstance(left, AreaWidget)
    assert isinstance(central, AreaWidget)
    assert left.area_id == "area.left"
    assert central.area_id == "area.central"
    assert unknown is None


def test_clear_cache_discards_widgets(qtbot, renderer: LayoutRenderer) -> None:
    result = _build_result(
        _area("area.central", Placement.CENTRAL, _leaf("editor.patient")),
    )
    renderer.render(result.tree)

    renderer.clear_cache()

    assert renderer.cached_area_widget("area.central") is None


def test_render_after_clear_cache_creates_fresh_widgets(qtbot, renderer: LayoutRenderer) -> None:
    result = _build_result(
        _area("area.central", Placement.CENTRAL, _leaf("editor.patient")),
    )
    first = renderer.render(result.tree)
    qtbot.addWidget(first)

    renderer.clear_cache()
    second = renderer.render(result.tree)
    qtbot.addWidget(second)

    assert first is not second
    assert isinstance(first, AreaWidget)
    assert isinstance(second, AreaWidget)
    assert first.area_id == second.area_id


# ----- Errors -------------------------------------------------------


def test_render_invalid_node_raises(renderer: LayoutRenderer) -> None:
    class FakeTree:
        root = "not a node"

    with pytest.raises(LayoutRendererError, match="unknown layout node"):
        renderer.render(FakeTree())  # type: ignore[arg-type]
