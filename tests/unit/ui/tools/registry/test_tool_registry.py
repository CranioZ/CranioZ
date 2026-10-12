"""Tests for ToolRegistry."""

from __future__ import annotations

import pytest

from cranioz.ui.tools.builtin.log_tool import LogTool
from cranioz.ui.tools.registry.tool_registry import (
    ToolRegistry,
    ToolRegistryError,
)


def _make_log() -> LogTool:
    return LogTool()


def test_register_and_resolve() -> None:
    registry = ToolRegistry()
    registry.register("tool.log", _make_log)
    factory = registry.resolve("tool.log")
    assert factory is _make_log


def test_register_idempotent_for_same_factory() -> None:
    registry = ToolRegistry()
    registry.register("tool.log", _make_log)
    registry.register("tool.log", _make_log)  # no raise
    assert registry.contains("tool.log")


def test_register_different_factory_for_same_id_raises() -> None:
    def other_factory() -> LogTool:
        return LogTool()

    registry = ToolRegistry()
    registry.register("tool.log", _make_log)
    with pytest.raises(ToolRegistryError, match="different factory"):
        registry.register("tool.log", other_factory)


def test_register_empty_id_raises() -> None:
    registry = ToolRegistry()
    with pytest.raises(ToolRegistryError, match="must not be empty"):
        registry.register("", _make_log)


def test_resolve_unknown_raises_keyerror() -> None:
    registry = ToolRegistry()
    with pytest.raises(KeyError, match="not registered"):
        registry.resolve("tool.unknown")


def test_create_returns_new_instance_each_time() -> None:
    registry = ToolRegistry()
    registry.register("tool.log", _make_log)
    a = registry.create("tool.log")
    b = registry.create("tool.log")
    assert a is not b
    assert isinstance(a, LogTool)
    assert isinstance(b, LogTool)


def test_unregister_removes() -> None:
    registry = ToolRegistry()
    registry.register("tool.log", _make_log)
    registry.unregister("tool.log")
    assert not registry.contains("tool.log")


def test_unregister_unknown_is_noop() -> None:
    registry = ToolRegistry()
    registry.unregister("tool.unknown")  # no raise


def test_identifiers_in_registration_order() -> None:
    registry = ToolRegistry()
    registry.register("tool.b", _make_log)
    registry.register("tool.a", _make_log)
    assert registry.identifiers() == ("tool.b", "tool.a")


def test_contains() -> None:
    registry = ToolRegistry()
    assert not registry.contains("tool.log")
    registry.register("tool.log", _make_log)
    assert registry.contains("tool.log")
