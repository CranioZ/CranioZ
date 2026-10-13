"""Tests for TestEditor."""

# mypy: ignore-errors
# This file exercises the Editor contract with Qt widgets.

from __future__ import annotations

from PySide6.QtWidgets import QLabel
from pytestqt.qtbot import QtBot

from cranioz.ui.editors.builtin.test_editor import DummyEditor
from cranioz.ui.editors.editor_context import EditorContext
from cranioz.ui.toolbars.specification import ToolbarOrientation

# ----- Metadata ----------------------------------------------------


def test_editor_metadata() -> None:
    editor = DummyEditor(editor_id="editor.a", title="Alpha")
    assert editor.editor_id == "editor.a"
    assert editor.title == "Alpha"


def test_default_editor_id_and_title() -> None:
    editor = DummyEditor()
    assert editor.editor_id == "editor.test"
    assert editor.title == "Test Editor"


# ----- Content widget ----------------------------------------------


def test_content_widget_is_qlabel(qtbot: QtBot) -> None:
    editor = DummyEditor(editor_id="editor.a")
    widget = editor.content_widget()
    qtbot.addWidget(widget)
    assert isinstance(widget, QLabel)


def test_content_widget_shows_editor_id(qtbot: QtBot) -> None:
    editor = DummyEditor(editor_id="editor.a")
    widget = editor.content_widget()
    qtbot.addWidget(widget)
    assert widget.text() == "editor.a"


def test_content_widget_is_cached(qtbot: QtBot) -> None:
    editor = DummyEditor(editor_id="editor.a")
    widget1 = editor.content_widget()
    widget2 = editor.content_widget()
    qtbot.addWidget(widget1)
    assert widget1 is widget2


def test_content_widget_has_object_name(qtbot: QtBot) -> None:
    editor = DummyEditor(editor_id="editor.a")
    widget = editor.content_widget()
    qtbot.addWidget(widget)
    assert widget.objectName() == "dummy_editor.content.editor.a"


# ----- Toolbar specs ------------------------------------------------


def test_toolbar_specs_returns_one_spec() -> None:
    editor = DummyEditor(editor_id="editor.a")
    specs = editor.toolbar_specs()
    assert len(specs) == 1


def test_toolbar_spec_has_expected_id() -> None:
    editor = DummyEditor(editor_id="editor.a")
    spec = editor.toolbar_specs()[0]
    assert spec.toolbar_id == "toolbar.editor.a"


def test_toolbar_spec_has_log_and_toggle_tools() -> None:
    editor = DummyEditor(editor_id="editor.a")
    spec = editor.toolbar_specs()[0]
    assert "tool.log" in spec.tool_ids
    assert "tool.toggle" in spec.tool_ids


def test_toolbar_spec_respects_orientation() -> None:
    editor = DummyEditor(
        editor_id="editor.a",
        toolbar_orientation=ToolbarOrientation.VERTICAL,
    )
    spec = editor.toolbar_specs()[0]
    assert spec.orientation is ToolbarOrientation.VERTICAL


# ----- Persistence -------------------------------------------------


def test_persistent_state_before_initialize_is_empty() -> None:
    editor = DummyEditor(editor_id="editor.a")
    assert editor.persistent_state() == {}


def test_persistent_state_after_initialize() -> None:
    editor = DummyEditor(editor_id="editor.a")
    ctx = EditorContext(editor_id="editor.a", extras={"zoom": 2.0})
    editor.initialize(ctx)
    state = editor.persistent_state()
    assert state["editor_id"] == "editor.a"
    assert state["extras"] == {"zoom": 2.0}


def test_restore_state_is_noop() -> None:
    editor = DummyEditor(editor_id="editor.a")
    editor.restore_state({"any": "thing"})


# ----- Lifecycle ---------------------------------------------------


def test_initialize_stores_context() -> None:
    editor = DummyEditor(editor_id="editor.a")
    ctx = EditorContext(editor_id="editor.a")
    editor.initialize(ctx)
    assert editor.persistent_state()["editor_id"] == "editor.a"
