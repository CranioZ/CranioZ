"""Tests for the Command base types."""

from __future__ import annotations

import dataclasses

import pytest

from cranioz.application.commands.base import (
    Command,
    CommandDispatchError,
    CommandError,
    CommandNotRegistered,
)

# ----- Command ------------------------------------------------------


def test_command_new_generates_command_id() -> None:
    command = Command.new()
    assert isinstance(command.command_id, str)
    assert command.command_id != ""


def test_command_new_accepts_explicit_command_id() -> None:
    command = Command.new(command_id="test-1")
    assert command.command_id == "test-1"


def test_command_new_accepts_metadata() -> None:
    command = Command.new(metadata={"actor": "alice"})
    assert command.metadata == {"actor": "alice"}


def test_command_new_id_returns_unique_ids() -> None:
    a = Command.new_id()
    b = Command.new_id()
    assert a != b
    assert isinstance(a, str)
    assert isinstance(b, str)


def test_command_is_frozen() -> None:
    command = Command.new()
    with pytest.raises(dataclasses.FrozenInstanceError):
        command.command_id = "other"  # type: ignore[misc]


def test_command_equality_by_value() -> None:
    a = Command.new(command_id="x")
    b = Command.new(command_id="x")
    assert a == b


def test_command_inequality_by_command_id() -> None:
    a = Command.new(command_id="x")
    b = Command.new(command_id="y")
    assert a != b


# ----- Errors ------------------------------------------------------


def test_command_error_hierarchy() -> None:
    assert issubclass(CommandNotRegistered, CommandError)
    assert issubclass(CommandDispatchError, CommandError)
    assert issubclass(CommandError, Exception)


def test_command_dispatch_error_carries_context() -> None:
    err = CommandDispatchError(
        "boom",
        command_id="c-1",
        command_type="MoveMaxillaCommand",
    )
    assert err.command_id == "c-1"
    assert err.command_type == "MoveMaxillaCommand"
    assert str(err) == "boom"


def test_command_dispatch_error_context_is_optional() -> None:
    err = CommandDispatchError("boom")
    assert err.command_id is None
    assert err.command_type is None


def test_command_dispatch_error_preserves_cause() -> None:
    original = ValueError("inner")
    try:
        try:
            raise original
        except ValueError as exc:
            raise CommandDispatchError("boom") from exc
    except CommandDispatchError as wrapped:
        assert wrapped.__cause__ is original
