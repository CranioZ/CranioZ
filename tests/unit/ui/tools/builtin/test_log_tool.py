"""Tests for LogTool."""

from __future__ import annotations

import logging

from pytest import LogCaptureFixture

from cranioz.ui.tools.builtin.log_tool import LogTool
from cranioz.ui.tools.registry.tool_definition import ToolContext


def test_log_tool_metadata() -> None:
    tool = LogTool()
    assert tool.identifier == "tool.log"
    assert tool.label == "Log"
    assert tool.description == "Logs a message"
    assert tool.icon == "log"
    assert tool.category is None


def test_log_tool_is_available_default_true() -> None:
    tool = LogTool()
    assert tool.is_available(ToolContext()) is True


def test_log_tool_is_available_respects_context() -> None:
    tool = LogTool()
    ctx = ToolContext(extras={"available": False})
    assert tool.is_available(ctx) is False


def test_log_tool_is_enabled_default_true() -> None:
    tool = LogTool()
    assert tool.is_enabled(ToolContext()) is True


def test_log_tool_execute_logs_message(caplog: LogCaptureFixture) -> None:
    tool = LogTool(message="hello")
    with caplog.at_level(logging.INFO):
        tool.execute(ToolContext())
    assert "hello" in caplog.text
