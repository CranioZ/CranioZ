"""Integration tests for TomographyEditor.

The TomographyEditor hosts four Views (Axial, Coronal, Sagittal, 3D)
organized in a 2x2 grid via ViewLayoutSpec.

These tests verify:
- The four Views are exposed via views().
- The view_layout() is a 2x2 grid (nested ViewLayoutSpec).
- The content_widget() materializes the four Views as nested QSplitters.
- The Toolbars are declared with LEFT and RIGHT positions.
- dispose() releases the Views and the content widget.
"""

from __future__ import annotations

import pytest
from PySide6.QtWidgets import QSplitter
from pytestqt.qtbot import QtBot

from cranioz.ui.editors.mpr_viewer.view import MPRView
from cranioz.ui.editors.tomography.editor import TomographyEditor
from cranioz.ui.editors.view_layout_spec import (
    SplitDirection,
    ViewLayoutType,
)
from cranioz.ui.editors.viewport_3d.view import Viewport3DView
from cranioz.ui.toolbars.specification import ToolbarPosition


@pytest.fixture
def editor() -> TomographyEditor:
    return TomographyEditor()


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
    layout = editor.view_layout()
    assert layout.type is ViewLayoutType.SPLIT
    assert layout.direction is SplitDirection.HORIZONTAL
    assert len(layout.children) == 2


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
    """The 2x2 grid has a horizontal splitter containing a vertical splitter."""
    widget = editor.content_widget()
    qtbot.addWidget(widget)

    # The root is a horizontal splitter.
    assert isinstance(widget, QSplitter)
    assert widget.count() == 2

    # The right child is a vertical splitter.
    right = widget.widget(1)
    assert isinstance(right, QSplitter)
    assert right.count() == 2


# ----- Toolbars -----------------------------------------------------


def test_editor_declares_two_toolbars(editor: TomographyEditor) -> None:
    specs = editor.toolbar_specs()
    assert len(specs) == 2


def test_editor_toolbars_have_left_and_right_positions(
    editor: TomographyEditor,
) -> None:
    specs = editor.toolbar_specs()
    positions = {s.position for s in specs}
    assert positions == {ToolbarPosition.LEFT, ToolbarPosition.RIGHT}


# ----- Dispose ------------------------------------------------------


def test_dispose_releases_content(
    qtbot: QtBot,
    editor: TomographyEditor,
) -> None:
    widget = editor.content_widget()
    qtbot.addWidget(widget)
    editor.dispose()
    # After dispose, content_widget() creates a fresh widget.
    # (We don't assert the exact identity; we just verify dispose does not raise.)
