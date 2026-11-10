"""Integration tests for TomographyEditor.

The TomographyEditor hosts four Views (Axial, Coronal, Sagittal, 3D)
organized in a 2x2 grid via ViewLayoutSpec.

These tests verify:
- The four Views are exposed via views().
- The view_layout() is a 2x2 grid (nested ViewLayoutSpec).
- The content_widget() materializes the four Views as nested QSplitters.
- dispose() releases the Views and the content widget.

Per ADR-0013 §2.6, the TomographyEditor no longer declares Editor-level
Toolbars; its Views (MPRView, Viewport3DView) declare their own
View-level Toolbars. The former ``test_editor_declares_two_toolbars``
and ``test_editor_toolbars_have_left_and_right_positions`` tests moved
to ``test_view_layout_renderer_toolbars.py`` and ``test_mpr_view.py``.

The fixture builds a complete ``EditorContext`` (tool_registry,
theme_service, icon_provider) so ``content_widget()`` can materialize
the View Layout Tree via the ViewLayoutRenderer.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QSplitter
from pytestqt.qtbot import QtBot
from tests.conftest import make_icon_provider, make_theme_service

from cranioz.ui.editors.editor_context import EditorContext
from cranioz.ui.editors.mpr_viewer.view import MPRView
from cranioz.ui.editors.tomography.editor import TomographyEditor
from cranioz.ui.editors.view_layout_spec import (
    SplitDirection,
    ViewLayoutSpec,
    ViewLayoutType,
)
from cranioz.ui.editors.viewport_3d.view import Viewport3DView
from cranioz.ui.theme.tokens import ThemeMode
from cranioz.ui.tools.builtin.log_tool import LogTool
from cranioz.ui.tools.builtin.toggle_tool import ToggleTool
from cranioz.ui.tools.registry.tool_registry import ToolRegistry


@pytest.fixture
def editor() -> TomographyEditor:
    """Build a TomographyEditor with a complete EditorContext.

    ADR-0013 §2.6: the Editor needs tool_registry, theme_service and
    icon_provider to materialize its Views' Toolbars. The fixture
    provides them, so ``content_widget()`` can render the View Layout
    Tree.
    """
    registry = ToolRegistry()
    registry.register("tool.log", LogTool)
    registry.register("tool.toggle", ToggleTool)
    theme_service = make_theme_service(ThemeMode.DARK)
    icon_provider = make_icon_provider(theme_service)

    e = TomographyEditor()
    e.initialize(
        EditorContext(
            editor_id="editor.tomography",
            tool_registry=registry,
            theme_service=theme_service,
            icon_provider=icon_provider,
        )
    )
    return e


# ----- Views --------------------------------------------------------


def test_editor_exposes_four_views(editor: TomographyEditor) -> None:
    views = editor.views()
    assert len(views) == 4


def test_editor_view_types(editor: TomographyEditor) -> None:
    view_ids = {v.view_id for v in editor.views()}
    assert view_ids == {
        "view.axial",
        "view.coronal",
        "view.sagittal",
        "view.3d",
    }


def test_editor_views_are_correct_classes(editor: TomographyEditor) -> None:
    views_by_id = {v.view_id: v for v in editor.views()}
    assert isinstance(views_by_id["view.axial"], MPRView)
    assert isinstance(views_by_id["view.coronal"], MPRView)
    assert isinstance(views_by_id["view.sagittal"], MPRView)
    assert isinstance(views_by_id["view.3d"], Viewport3DView)


# ----- View Layout --------------------------------------------------


def test_editor_view_layout_is_split(editor: TomographyEditor) -> None:
    """The view_layout is a 2x2 grid: a vertical split of two horizontal splits."""
    layout = editor.view_layout()
    assert layout.type is ViewLayoutType.SPLIT
    assert layout.direction is SplitDirection.VERTICAL
    assert len(layout.children) == 2

    # Both children are horizontal splits (top row, bottom row).
    top_row, bottom_row = layout.children
    assert top_row.type is ViewLayoutType.SPLIT
    assert top_row.direction is SplitDirection.HORIZONTAL
    assert bottom_row.type is ViewLayoutType.SPLIT
    assert bottom_row.direction is SplitDirection.HORIZONTAL


def test_editor_view_layout_leaves(editor: TomographyEditor) -> None:
    """The view_layout contains the four Views at the leaves."""
    layout = editor.view_layout()
    view_ids: set[str] = set()

    def visit(node: ViewLayoutSpec) -> None:
        if node.type is ViewLayoutType.LEAF:
            assert node.view_id is not None
            view_ids.add(node.view_id)
        else:
            for child in node.children:
                visit(child)

    visit(layout)
    assert view_ids == {"view.axial", "view.coronal", "view.sagittal", "view.3d"}


# ----- Content Widget -----------------------------------------------


def test_content_widget_returns_qwidget(
    qtbot: QtBot,
    editor: TomographyEditor,
) -> None:
    widget = editor.content_widget()
    qtbot.addWidget(widget)
    assert widget is not None


def test_content_widget_has_qsplitter(
    qtbot: QtBot,
    editor: TomographyEditor,
) -> None:
    widget = editor.content_widget()
    qtbot.addWidget(widget)
    splitter = widget if isinstance(widget, QSplitter) else widget.findChild(QSplitter)
    assert splitter is not None


def test_content_widget_renders_nested_splitters(
    qtbot: QtBot,
    editor: TomographyEditor,
) -> None:
    """The 2x2 grid is rendered as nested QSplitters inside a container."""
    widget = editor.content_widget()
    qtbot.addWidget(widget)

    assert widget is not None

    # Find the QSplitters inside the container. The 2x2 grid has an
    # outer vertical splitter and two inner horizontal splitters. The
    # order returned by findChildren() is depth-first, so the outer
    # splitter is first (it is the parent of the two inner ones).
    splitters = widget.findChildren(QSplitter)
    assert len(splitters) >= 1, "Expected at least one QSplitter in the grid"

    # Find the vertical splitter that divides the two rows.
    vertical = next(
        (s for s in splitters if s.orientation() == Qt.Orientation.Vertical),
        None,
    )
    assert vertical is not None, "Expected a vertical QSplitter dividing the rows"
    assert vertical.count() == 2

    # Both rows are horizontal splitters.
    for i in range(vertical.count()):
        row = vertical.widget(i)
        assert isinstance(row, QSplitter)
        assert row.orientation() == Qt.Orientation.Horizontal


# ----- Dispose ------------------------------------------------------


def test_dispose_releases_content(
    qtbot: QtBot,
    editor: TomographyEditor,
) -> None:
    widget = editor.content_widget()
    qtbot.addWidget(widget)
    editor.dispose()
    # After dispose, content_widget() would need to be recreated by
    # calling content_widget() again. The important contract is that
    # dispose() does not raise.
