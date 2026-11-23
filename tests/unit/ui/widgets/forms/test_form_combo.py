"""Unit tests for FormCombo."""

from __future__ import annotations

import pytest

from cranioz.ui.widgets.forms import FormCombo


@pytest.fixture
def combo(qtbot):
    widget = FormCombo(label="Role")
    widget.add_items([("Doctor", "doc"), ("Assistant", "asst")])
    qtbot.addWidget(widget)
    return widget


def test_default_state(combo):
    assert combo.label == "Role"
    assert combo.current_index == 0
    assert combo.current_value == "doc"


def test_current_changed_emits_item_data(combo, qtbot):
    with qtbot.waitSignal(combo.current_changed, timeout=500) as blocker:
        combo.current_index = 1
    assert blocker.args == ["asst"]


def test_set_current_by_value(combo):
    assert combo.set_current_by_value("asst") is True
    assert combo.current_value == "asst"


def test_set_current_by_missing_value_returns_false(combo):
    assert combo.set_current_by_value("missing") is False


def test_clear_items(combo):
    combo.clear_items()
    assert combo.current_index == -1


def test_add_item_preserves_order(combo):
    combo.add_item("Patient", "pat")
    assert combo.current_index == 0  # selection unchanged by add_item
    combo.current_index = 2
    assert combo.current_value == "pat"


def test_accessible_name_reflects_label(combo):
    assert combo.accessibleName() == "Role"
