"""Tests for EditorRegistry."""

# mypy: ignore-errors
# This file exercises Qt widgets and the Editor contract with type-ignore needs.

from __future__ import annotations

import pytest
from pytestqt.qtbot import QtBot

from cranioz.ui.editors.base_editor import Editor
from cranioz.ui.editors.builtin.test_editor import DummyEditor
from cranioz.ui.editors.editor_registry import (
    EditorRegistry,
    EditorRegistryError,
)


class OtherEditor(Editor):
    """A second concrete Editor for tests."""

    def content_widget(self) -> str:
        return self.editor_id


# ----- Registration ------------------------------------------------


def test_register_and_resolve() -> None:
    registry = EditorRegistry()
    registry.register("editor.test", DummyEditor)
    assert registry.resolve("editor.test") is DummyEditor


def test_register_idempotent_for_same_class() -> None:
    registry = EditorRegistry()
    registry.register("editor.test", DummyEditor)
    registry.register("editor.test", DummyEditor)  # no raise
    assert registry.contains("editor.test")


def test_register_different_class_for_same_id_raises() -> None:
    registry = EditorRegistry()
    registry.register("editor.test", DummyEditor)
    with pytest.raises(EditorRegistryError, match="different type"):
        registry.register("editor.test", OtherEditor)


def test_register_empty_id_raises() -> None:
    registry = EditorRegistry()
    with pytest.raises(EditorRegistryError, match="must not be empty"):
        registry.register("", DummyEditor)


# ----- Resolution and creation -------------------------------------


def test_resolve_unknown_raises_keyerror() -> None:
    registry = EditorRegistry()
    with pytest.raises(KeyError, match="not registered"):
        registry.resolve("editor.unknown")


def test_create_returns_new_instance(qtbot: QtBot) -> None:
    registry = EditorRegistry()
    registry.register("editor.test", DummyEditor)

    editor = registry.create("editor.test", editor_id="editor.a", title="Alpha")
    widget = editor.content_widget()
    qtbot.addWidget(widget)

    assert isinstance(editor, DummyEditor)
    assert editor.editor_id == "editor.a"
    assert editor.title == "Alpha"


def test_create_twice_returns_distinct_instances(qtbot: QtBot) -> None:
    registry = EditorRegistry()
    registry.register("editor.test", DummyEditor)

    a = registry.create("editor.test", editor_id="editor.a")
    b = registry.create("editor.test", editor_id="editor.b")
    qtbot.addWidget(a.content_widget())
    qtbot.addWidget(b.content_widget())

    assert a is not b


def test_create_unknown_raises_keyerror() -> None:
    registry = EditorRegistry()
    with pytest.raises(KeyError, match="not registered"):
        registry.create("editor.unknown")


# ----- Unregister and inspect --------------------------------------


def test_unregister_removes() -> None:
    registry = EditorRegistry()
    registry.register("editor.test", DummyEditor)
    registry.unregister("editor.test")
    assert not registry.contains("editor.test")


def test_unregister_unknown_is_noop() -> None:
    registry = EditorRegistry()
    registry.unregister("editor.unknown")  # no raise


def test_identifiers_in_registration_order() -> None:
    registry = EditorRegistry()
    registry.register("editor.b", DummyEditor)
    registry.register("editor.a", DummyEditor)
    assert registry.identifiers() == ("editor.b", "editor.a")


def test_contains() -> None:
    registry = EditorRegistry()
    assert not registry.contains("editor.test")
    registry.register("editor.test", DummyEditor)
    assert registry.contains("editor.test")
