"""Tests for Area."""

# mypy: ignore-errors
# This file exercises Qt widgets indirectly via DummyEditor.

from __future__ import annotations

import pytest

from cranioz.ui.editors.builtin.test_editor import DummyEditor
from cranioz.ui.workspace.areas.area import Area, AreaError

# ----- Construction ------------------------------------------------


def test_area_holds_id_and_title() -> None:
    area = Area(area_id="area.central", title="Central")
    assert area.area_id == "area.central"
    assert area.title == "Central"


def test_area_is_visible_by_default() -> None:
    area = Area(area_id="area.central", title="Central")
    assert area.visible is True


def test_empty_area_id_raises() -> None:
    with pytest.raises(AreaError, match="area_id"):
        Area(area_id="", title="Central")


def test_empty_title_raises() -> None:
    with pytest.raises(AreaError, match="title"):
        Area(area_id="area.central", title="")


# ----- Visibility ---------------------------------------------------


def test_hide_and_show() -> None:
    area = Area(area_id="area.central", title="Central")
    area.hide()
    assert area.visible is False
    area.show()
    assert area.visible is True


# ----- Editor management -------------------------------------------


def test_new_area_has_no_editors() -> None:
    area = Area(area_id="area.central", title="Central")
    assert area.editors() == ()
    assert area.editor_count() == 0
    assert area.active_editor_id is None


def test_add_editor_appends() -> None:
    area = Area(area_id="area.central", title="Central")
    editor = DummyEditor(editor_id="editor.a")
    area.add_editor(editor)
    assert area.editor_count() == 1
    assert area.get_editor("editor.a") is editor


def test_first_editor_becomes_active() -> None:
    area = Area(area_id="area.central", title="Central")
    editor = DummyEditor(editor_id="editor.a")
    area.add_editor(editor)
    assert area.active_editor_id == "editor.a"
    assert area.active_editor is editor


def test_add_editor_with_duplicate_id_raises() -> None:
    area = Area(area_id="area.central", title="Central")
    area.add_editor(DummyEditor(editor_id="editor.a"))
    with pytest.raises(AreaError, match="already hosted"):
        area.add_editor(DummyEditor(editor_id="editor.a"))


def test_remove_editor_returns_it() -> None:
    area = Area(area_id="area.central", title="Central")
    editor = DummyEditor(editor_id="editor.a")
    area.add_editor(editor)
    removed = area.remove_editor("editor.a")
    assert removed is editor
    assert area.editor_count() == 0


def test_remove_unknown_editor_returns_none() -> None:
    area = Area(area_id="area.central", title="Central")
    assert area.remove_editor("editor.unknown") is None


def test_removing_active_editor_promotes_next() -> None:
    area = Area(area_id="area.central", title="Central")
    a = DummyEditor(editor_id="editor.a")
    b = DummyEditor(editor_id="editor.b")
    area.add_editor(a)
    area.add_editor(b)
    assert area.active_editor_id == "editor.a"

    area.remove_editor("editor.a")
    assert area.active_editor_id == "editor.b"


def test_removing_last_editor_clears_active() -> None:
    area = Area(area_id="area.central", title="Central")
    area.add_editor(DummyEditor(editor_id="editor.a"))
    area.remove_editor("editor.a")
    assert area.active_editor_id is None


def test_removing_inactive_editor_keeps_active() -> None:
    area = Area(area_id="area.central", title="Central")
    a = DummyEditor(editor_id="editor.a")
    b = DummyEditor(editor_id="editor.b")
    area.add_editor(a)
    area.add_editor(b)
    area.remove_editor("editor.b")
    assert area.active_editor_id == "editor.a"


# ----- Active Editor -------------------------------------------------


def test_set_active_editor() -> None:
    area = Area(area_id="area.central", title="Central")
    a = DummyEditor(editor_id="editor.a")
    b = DummyEditor(editor_id="editor.b")
    area.add_editor(a)
    area.add_editor(b)
    area.set_active_editor("editor.b")
    assert area.active_editor_id == "editor.b"
    assert area.active_editor is b


def test_set_active_editor_unknown_raises() -> None:
    area = Area(area_id="area.central", title="Central")
    with pytest.raises(AreaError, match="not hosted"):
        area.set_active_editor("editor.unknown")


# ----- Contains and count ------------------------------------------


def test_contains() -> None:
    area = Area(area_id="area.central", title="Central")
    assert not area.contains("editor.a")
    area.add_editor(DummyEditor(editor_id="editor.a"))
    assert area.contains("editor.a")


# ----- Representation ----------------------------------------------


def test_repr_contains_key_fields() -> None:
    area = Area(area_id="area.central", title="Central")
    area.add_editor(DummyEditor(editor_id="editor.a"))
    text = repr(area)
    assert "area.central" in text
    assert "editor.a" in text
