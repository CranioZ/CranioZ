"""Tests for ToolbarItem types."""

# mypy: ignore-errors
# This file intentionally mutates frozen dataclasses to test immutability.

from __future__ import annotations

import dataclasses

import pytest

from cranioz.ui.toolbars.item import (
    ActionItem,
    Separator,
    ToggleItem,
    ToolbarItemKind,
)

# ----- ActionItem --------------------------------------------------


def test_action_item_holds_fields() -> None:
    item = ActionItem(tool_id="tool.log", label="Log")
    assert item.tool_id == "tool.log"
    assert item.label == "Log"
    assert item.icon is None
    assert item.kind is ToolbarItemKind.ACTION


def test_action_item_with_icon() -> None:
    item = ActionItem(tool_id="tool.log", label="Log", icon="log")
    assert item.icon == "log"


def test_action_item_requires_tool_id() -> None:
    with pytest.raises(ValueError, match="tool_id"):
        ActionItem(tool_id="", label="Log")


def test_action_item_requires_label() -> None:
    with pytest.raises(ValueError, match="label"):
        ActionItem(tool_id="tool.log", label="")


# ----- ToggleItem --------------------------------------------------


def test_toggle_item_defaults() -> None:
    item = ToggleItem(tool_id="tool.grid", label="Grid")
    assert item.tool_id == "tool.grid"
    assert item.label == "Grid"
    assert item.icon is None
    assert item.checked is False
    assert item.kind is ToolbarItemKind.TOGGLE


def test_toggle_item_checked_true() -> None:
    item = ToggleItem(tool_id="tool.grid", label="Grid", checked=True)
    assert item.checked is True


def test_toggle_item_requires_tool_id() -> None:
    with pytest.raises(ValueError, match="tool_id"):
        ToggleItem(tool_id="", label="Grid")


def test_toggle_item_requires_label() -> None:
    with pytest.raises(ValueError, match="label"):
        ToggleItem(tool_id="tool.grid", label="")


# ----- Separator ---------------------------------------------------


def test_separator_has_separator_kind() -> None:
    sep = Separator()
    assert sep.kind is ToolbarItemKind.SEPARATOR


def test_separators_are_equal() -> None:
    assert Separator() == Separator()


# ----- Equality and immutability -----------------------------------


def test_action_items_with_same_data_are_equal() -> None:
    a = ActionItem(tool_id="tool.log", label="Log")
    b = ActionItem(tool_id="tool.log", label="Log")
    assert a == b


def test_action_items_with_different_data_are_not_equal() -> None:
    a = ActionItem(tool_id="tool.log", label="Log")
    b = ActionItem(tool_id="tool.other", label="Other")
    assert a != b


def test_action_item_is_frozen() -> None:
    item = ActionItem(tool_id="tool.log", label="Log")
    with pytest.raises(dataclasses.FrozenInstanceError):
        item.label = "Other"


def test_toggle_item_is_frozen() -> None:
    item = ToggleItem(tool_id="tool.grid", label="Grid")
    with pytest.raises(dataclasses.FrozenInstanceError):
        item.checked = True


# ----- Enum --------------------------------------------------------


def test_toolbar_item_kind_members() -> None:
    expected = {"ACTION", "TOGGLE", "SEPARATOR"}
    actual = {member.name for member in ToolbarItemKind}
    assert actual == expected
