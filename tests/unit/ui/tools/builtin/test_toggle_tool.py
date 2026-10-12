"""Tests for ToggleTool."""

from __future__ import annotations

from cranioz.ui.tools.builtin.toggle_tool import ToggleTool
from cranioz.ui.tools.registry.tool_definition import ToolContext


def test_toggle_tool_metadata() -> None:
    tool = ToggleTool()
    assert tool.identifier == "tool.toggle"
    assert tool.label == "Toggle"
    assert tool.icon == "toggle"


def test_toggle_default_state_is_false() -> None:
    tool = ToggleTool()
    assert tool.checked is False


def test_toggle_flips_state() -> None:
    tool = ToggleTool()
    assert tool.toggle() is True
    assert tool.checked is True
    assert tool.toggle() is False
    assert tool.checked is False


def test_toggle_initial_state_can_be_set() -> None:
    tool = ToggleTool(checked=True)
    assert tool.checked is True


def test_toggle_is_available_respects_context() -> None:
    tool = ToggleTool()
    assert tool.is_available(ToolContext(extras={"available": False})) is False


def test_toggle_is_enabled_respects_context() -> None:
    tool = ToggleTool()
    assert tool.is_enabled(ToolContext(extras={"enabled": False})) is False
