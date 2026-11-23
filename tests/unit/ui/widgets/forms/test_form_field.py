"""Unit tests for FormField."""

from __future__ import annotations

import pytest
from PySide6.QtCore import Qt

from cranioz.ui.widgets.forms import FormField


@pytest.fixture
def field(qtbot):
    widget = FormField(label="Name")
    qtbot.addWidget(widget)
    return widget


def test_default_state(field):
    assert field.label == "Name"
    assert field.text == ""
    assert field.read_only is False


def test_text_roundtrip(field):
    field.text = "Alice"
    assert field.text == "Alice"


def test_text_changed_signal(field, qtbot):
    with qtbot.waitSignal(field.text_changed, timeout=500) as blocker:
        field.text = "Bob"
    assert blocker.args == ["Bob"]


def test_editing_finished_signal_on_enter(field, qtbot):
    field.setFocus()
    field.text = "Carol"
    with qtbot.waitSignal(field.editing_finished, timeout=500) as blocker:
        qtbot.keyClick(field._line_edit, Qt.Key.Key_Return)
    assert blocker.args == ["Carol"]


def test_clear(field):
    field.text = "x"
    field.clear()
    assert field.text == ""


def test_accessible_name_reflects_label(field):
    assert field.accessibleName() == "Name"
    field.label = "Full name"
    assert field.accessibleName() == "Full name"


def test_read_only_toggle(field):
    field.read_only = True
    assert field.read_only is True
    field.read_only = False
    assert field.read_only is False


def test_disabled_state(field):
    field.setEnabled(False)
    assert field.isEnabled() is False
