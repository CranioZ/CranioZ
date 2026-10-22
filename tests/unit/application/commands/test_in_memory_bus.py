"""Contract tests for CommandBus, exercised against InMemoryCommandBus.

Any future implementation of CommandBus (e.g., a CommandExecutor with
transaction boundaries and event publication) should pass these tests
unchanged, plus its own adapter-specific tests.
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from cranioz.application.commands.base import (
    Command,
    CommandDispatchError,
    CommandNotRegistered,
)
from cranioz.application.commands.bus import CommandBus
from cranioz.application.commands.in_memory_bus import InMemoryCommandBus

# ----- Fixtures -----------------------------------------------------


@dataclass(frozen=True)
class SampleCommand(Command):
    value: int = 0


@dataclass(frozen=True)
class OtherCommand(Command):
    label: str = ""


class SampleHandler:
    def __init__(self) -> None:
        self.calls: list[SampleCommand] = []

    def handle(self, command: SampleCommand) -> int:
        self.calls.append(command)
        return command.value * 2


class RaisingHandler:
    def handle(self, command: SampleCommand) -> int:
        raise RuntimeError("boom")


@pytest.fixture
def bus() -> InMemoryCommandBus:
    return InMemoryCommandBus()


# ----- Protocol -----------------------------------------------------


def test_bus_satisfies_protocol(bus: InMemoryCommandBus) -> None:
    assert isinstance(bus, CommandBus)


# ----- Dispatch -----------------------------------------------------


def test_dispatch_calls_handler_with_command(bus: InMemoryCommandBus) -> None:
    handler = SampleHandler()
    bus.register(SampleCommand, handler)
    result = bus.dispatch(SampleCommand(command_id="c-1", value=21))
    assert result == 42
    assert len(handler.calls) == 1
    assert handler.calls[0].value == 21


def test_dispatch_unknown_raises(bus: InMemoryCommandBus) -> None:
    with pytest.raises(CommandNotRegistered):
        bus.dispatch(SampleCommand(command_id="c-1", value=1))


def test_dispatch_unknown_error_mentions_type(bus: InMemoryCommandBus) -> None:
    with pytest.raises(CommandNotRegistered, match="SampleCommand"):
        bus.dispatch(SampleCommand(command_id="c-1"))


def test_dispatch_wraps_handler_error(bus: InMemoryCommandBus) -> None:
    bus.register(SampleCommand, RaisingHandler())
    with pytest.raises(CommandDispatchError) as exc_info:
        bus.dispatch(SampleCommand(command_id="c-1"))
    assert isinstance(exc_info.value.__cause__, RuntimeError)


def test_dispatch_error_carries_command_context(bus: InMemoryCommandBus) -> None:
    bus.register(SampleCommand, RaisingHandler())
    with pytest.raises(CommandDispatchError) as exc_info:
        bus.dispatch(SampleCommand(command_id="c-42"))
    err = exc_info.value
    assert err.command_id == "c-42"
    assert err.command_type == "SampleCommand"


# ----- Registration -------------------------------------------------


def test_register_different_types_is_allowed() -> None:
    bus = InMemoryCommandBus()
    bus.register(SampleCommand, SampleHandler())
    bus.register(OtherCommand, SampleHandler())
    assert bus.can_dispatch(SampleCommand)
    assert bus.can_dispatch(OtherCommand)


def test_register_same_type_same_handler_is_idempotent() -> None:
    bus = InMemoryCommandBus()
    handler = SampleHandler()
    bus.register(SampleCommand, handler)
    bus.register(SampleCommand, handler)
    assert bus.can_dispatch(SampleCommand)


def test_register_same_type_different_handler_raises() -> None:
    bus = InMemoryCommandBus()
    bus.register(SampleCommand, SampleHandler())
    with pytest.raises(ValueError, match="already registered"):
        bus.register(SampleCommand, SampleHandler())


def test_can_dispatch_reflects_registration() -> None:
    bus = InMemoryCommandBus()
    assert not bus.can_dispatch(SampleCommand)
    bus.register(SampleCommand, SampleHandler())
    assert bus.can_dispatch(SampleCommand)


def test_unregister_removes_handler() -> None:
    bus = InMemoryCommandBus()
    bus.register(SampleCommand, SampleHandler())
    bus.unregister(SampleCommand)
    assert not bus.can_dispatch(SampleCommand)


def test_unregister_unknown_is_noop() -> None:
    bus = InMemoryCommandBus()
    bus.unregister(SampleCommand)  # must not raise


def test_command_types_returns_registered_types() -> None:
    bus = InMemoryCommandBus()
    bus.register(SampleCommand, SampleHandler())
    bus.register(OtherCommand, SampleHandler())
    assert set(bus.command_types()) == {SampleCommand, OtherCommand}


def test_len_reflects_registration() -> None:
    bus = InMemoryCommandBus()
    assert len(bus) == 0
    bus.register(SampleCommand, SampleHandler())
    assert len(bus) == 1
