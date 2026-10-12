"""Tests for EditorContext."""

# mypy: ignore-errors
# This file intentionally mutates frozen dataclasses to test immutability.

from __future__ import annotations

import dataclasses

import pytest

from cranioz.ui.editors.editor_context import EditorContext


def test_editor_context_holds_editor_id() -> None:
    ctx = EditorContext(editor_id="editor.a")
    assert ctx.editor_id == "editor.a"
    assert ctx.extras == {}


def test_editor_context_holds_extras() -> None:
    ctx = EditorContext(editor_id="editor.a", extras={"zoom": 1.5})
    assert ctx.extras["zoom"] == 1.5


def test_editor_context_is_frozen() -> None:
    ctx = EditorContext(editor_id="editor.a")
    with pytest.raises(dataclasses.FrozenInstanceError):
        ctx.editor_id = "editor.b"  # type: ignore[misc,assignment,attr-defined]


def test_two_editor_contexts_with_same_data_are_equal() -> None:
    a = EditorContext(editor_id="editor.a")
    b = EditorContext(editor_id="editor.a")
    assert a == b


def test_default_extras_are_not_shared_between_instances() -> None:
    a = EditorContext(editor_id="editor.a")
    b = EditorContext(editor_id="editor.b")
    # dicts created via default_factory are independent
    assert a.extras is not b.extras
