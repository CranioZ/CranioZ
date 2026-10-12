"""Tests for the Editor ABC."""

from __future__ import annotations

from typing import Any

import pytest

from cranioz.ui.editors.base_editor import Editor
from cranioz.ui.editors.editor_context import EditorContext


class ConcreteEditor(Editor):
    """Minimal concrete Editor used only in tests."""

    def __init__(self, editor_id: str = "editor.test", title: str = "Test") -> None:
        super().__init__(editor_id=editor_id, title=title)
        self.initialize_calls = 0
        self.activate_calls = 0
        self.deactivate_calls = 0
        self.dispose_calls = 0
        self._state: dict[str, Any] = {}

    def content_widget(self) -> str:
        return f"<{self.editor_id}>"

    def initialize(self, context: EditorContext) -> None:
        self.initialize_calls += 1

    def activate(self) -> None:
        self.activate_calls += 1

    def deactivate(self) -> None:
        self.deactivate_calls += 1

    def dispose(self) -> None:
        self.dispose_calls += 1

    def persistent_state(self) -> dict[str, Any]:
        return dict(self._state)

    def restore_state(self, state: dict[str, Any]) -> None:
        self._state = dict(state)


def test_editor_is_abstract() -> None:
    with pytest.raises(TypeError):
        Editor(editor_id="x", title="X")  # type: ignore[abstract]


def test_editor_stores_id_and_title() -> None:
    editor = ConcreteEditor(editor_id="editor.a", title="Alpha")
    assert editor.editor_id == "editor.a"
    assert editor.title == "Alpha"


def test_content_widget_returns_expected_value() -> None:
    editor = ConcreteEditor(editor_id="editor.a")
    assert editor.content_widget() == "<editor.a>"


def test_default_toolbar_specs_is_empty() -> None:
    editor = ConcreteEditor()
    assert editor.toolbar_specs() == []


def test_default_persistent_state_is_empty() -> None:
    # The base class returns {} by default.
    # Our ConcreteEditor returns its own state, so test the base directly.
    class Minimal(Editor):
        def content_widget(self) -> str:
            return ""

    minimal = Minimal(editor_id="editor.min", title="Min")
    assert minimal.persistent_state() == {}


def test_restore_state_round_trip() -> None:
    editor = ConcreteEditor()
    editor.restore_state({"zoom": 2.0})
    assert editor.persistent_state() == {"zoom": 2.0}


def test_lifecycle_methods_can_be_called() -> None:
    editor = ConcreteEditor()
    ctx = EditorContext(editor_id="editor.test")
    editor.initialize(ctx)
    editor.activate()
    editor.deactivate()
    editor.dispose()
    assert editor.initialize_calls == 1
    assert editor.activate_calls == 1
    assert editor.deactivate_calls == 1
    assert editor.dispose_calls == 1
