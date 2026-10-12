"""Tests for the Tool Protocol and ToolContext."""

from __future__ import annotations

from cranioz.ui.tools.registry.tool_definition import ToolContext


class ConcreteTool:
    """Minimal Tool implementation used only in tests."""

    identifier = "tool.log"
    label = "Log"
    description = "Logs a message"
    icon: str | None = None
    category: str | None = None

    def is_available(self, context: ToolContext) -> bool:
        return bool(context.extras.get("available", True))

    def is_enabled(self, context: ToolContext) -> bool:
        return bool(context.extras.get("enabled", True))


def test_tool_context_defaults() -> None:
    ctx = ToolContext()
    assert ctx.extras == {}


def test_tool_context_with_extras() -> None:
    ctx = ToolContext(extras={"enabled": False})
    assert ctx.extras["enabled"] is False


def test_concrete_tool_satisfies_protocol() -> None:
    tool = ConcreteTool()
    ctx = ToolContext()

    assert tool.identifier == "tool.log"
    assert tool.label == "Log"
    assert tool.description == "Logs a message"
    assert tool.icon is None
    assert tool.category is None
    assert tool.is_available(ctx) is True
    assert tool.is_enabled(ctx) is True


def test_tool_is_available() -> None:
    tool = ConcreteTool()
    assert tool.is_available(ToolContext()) is True


def test_tool_is_available_respects_context() -> None:
    tool = ConcreteTool()
    assert tool.is_available(ToolContext(extras={"available": False})) is False


def test_tool_is_enabled_defaults_to_true() -> None:
    tool = ConcreteTool()
    assert tool.is_enabled(ToolContext()) is True


def test_tool_is_enabled_respects_context() -> None:
    tool = ConcreteTool()
    assert tool.is_enabled(ToolContext(extras={"enabled": False})) is False


def test_object_without_methods_fails_protocol() -> None:
    class NotATool:
        identifier = "not.a.tool"

    not_a_tool = NotATool()
    assert not hasattr(not_a_tool, "is_available")
    assert not hasattr(not_a_tool, "is_enabled")
