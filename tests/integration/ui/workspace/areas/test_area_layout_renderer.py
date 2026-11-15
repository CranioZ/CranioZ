"""Integration tests for AreaLayoutRenderer (revised).

The AreaLayoutRenderer no longer materializes Toolbars; Toolbars
are the View's responsibility (ADR-0013 §2.6, §2.7). The tests
verify that the renderer still organizes Editors correctly and
that no Toolbar widget appears at the Area level.
"""

from __future__ import annotations

import pytest
from PySide6.QtWidgets import QSplitter, QWidget
from pytestqt.qtbot import QtBot

from cranioz.ui.editors.builtin.test_editor import DummyEditor
from cranioz.ui.toolbars.base import Toolbar
from cranioz.ui.workspace.areas.area import Area
from cranioz.ui.workspace.areas.area_layout_renderer import AreaLayoutRenderer
from cranioz.ui.workspace.areas.editor_layout_spec import (
    EditorLayoutSpec,
    EditorStackOrientation,
    SplitDirection,
)
from cranioz.ui.workspace.areas.editor_stack import EditorStack
from cranioz.ui.workspace.areas.placement import Placement


@pytest.fixture
def renderer() -> AreaLayoutRenderer:
    return AreaLayoutRenderer()


def _area() -> Area:
    return Area(area_id="area.central", title="Central", placement=Placement.CENTRAL)


def test_single_editor_returns_container_not_splitter(
    qtbot: QtBot,
    renderer: AreaLayoutRenderer,
) -> None:
    area = _area()
    area.add_editor(DummyEditor(editor_id="editor.a"))
    content_widgets: dict[str, QWidget] = {}

    widget = renderer.render(area, content_widgets)
    qtbot.addWidget(widget)

    assert widget.findChild(QSplitter) is None


def test_single_editor_content_is_present(
    qtbot: QtBot,
    renderer: AreaLayoutRenderer,
) -> None:
    area = _area()
    editor = DummyEditor(editor_id="editor.a")
    area.add_editor(editor)
    content_widgets: dict[str, QWidget] = {}

    widget = renderer.render(area, content_widgets)
    qtbot.addWidget(widget)

    assert widget.isAncestorOf(editor.content_widget())
    assert "editor.a" in content_widgets


def test_single_editor_no_toolbars_at_area_level(
    qtbot: QtBot,
    renderer: AreaLayoutRenderer,
) -> None:
    """ADR-0013 §2.7: the Area does not render Toolbars."""
    area = _area()
    area.add_editor(DummyEditor(editor_id="editor.a"))
    content_widgets: dict[str, QWidget] = {}

    widget = renderer.render(area, content_widgets)
    qtbot.addWidget(widget)

    assert widget.findChildren(Toolbar) == []


def test_multiple_editors_returns_splitter(
    qtbot: QtBot,
    renderer: AreaLayoutRenderer,
) -> None:
    area = _area()
    area.add_editor(DummyEditor(editor_id="editor.a"))
    area.add_editor(DummyEditor(editor_id="editor.b"))
    content_widgets: dict[str, QWidget] = {}

    widget = renderer.render(area, content_widgets)
    qtbot.addWidget(widget)

    splitter = widget if isinstance(widget, QSplitter) else widget.findChild(QSplitter)
    assert splitter is not None
    assert splitter.count() == 2


def test_multiple_editors_content_is_present(
    qtbot: QtBot,
    renderer: AreaLayoutRenderer,
) -> None:
    area = _area()
    editor_a = DummyEditor(editor_id="editor.a")
    editor_b = DummyEditor(editor_id="editor.b")
    area.add_editor(editor_a)
    area.add_editor(editor_b)
    content_widgets: dict[str, QWidget] = {}

    widget = renderer.render(area, content_widgets)
    qtbot.addWidget(widget)

    assert widget.isAncestorOf(editor_a.content_widget())
    assert widget.isAncestorOf(editor_b.content_widget())
    assert set(content_widgets.keys()) == {"editor.a", "editor.b"}


def test_empty_area_raises(renderer: AreaLayoutRenderer) -> None:
    area = _area()
    content_widgets: dict[str, QWidget] = {}
    with pytest.raises(ValueError, match="non-empty Area"):
        renderer.render(area, content_widgets)


def test_stack_spec_materializes_editor_stack(
    qtbot: QtBot,
    renderer: AreaLayoutRenderer,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """STACK materializes an EditorStack."""
    area = _area()
    area.add_editor(DummyEditor(editor_id="editor.a"))
    area.add_editor(DummyEditor(editor_id="editor.b"))
    content_widgets: dict[str, QWidget] = {}

    # Set a fake EditorLayoutSpec on the Area to trigger STACK materialization.
    area.set_editor_layout_spec(
        EditorLayoutSpec.stack(
            children=(
                EditorLayoutSpec.leaf("editor.a"),
                EditorLayoutSpec.leaf("editor.b"),
            ),
            direction=SplitDirection.HORIZONTAL,
            orientation=EditorStackOrientation.BOTTOM,
        )
    )

    result = renderer.render(area, content_widgets)
    qtbot.addWidget(result)

    assert isinstance(result, EditorStack)
    assert "__editor_stack__" in content_widgets
    assert content_widgets["__editor_stack__"] is result
