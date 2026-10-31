"""Contract tests for CommandExecutor."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from cranioz.application.commands.base import (
    Command,
    CommandNotRegistered,
)
from cranioz.application.commands.dispatcher import CommandDispatcher
from cranioz.application.commands.executor import CommandExecutor
from cranioz.application.commands.in_memory_bus import InMemoryCommandBus
from cranioz.application.commands.stack import InMemoryCommandStack
from cranioz.application.commands.transaction import (
    InMemoryTransactionManager,
)
from cranioz.application.event_bus import EventBus


@dataclass(frozen=True)
class SampleCommand(Command):
    value: int = 0


@dataclass(frozen=True)
class CompensatingCommand(Command):
    value: int = 0


class SampleHandler:
    def __init__(self) -> None:
        self.calls: list[SampleCommand] = []

    def handle(self, command: SampleCommand) -> int:
        self.calls.append(command)
        return command.value * 2


class FailingHandler:
    def __init__(self) -> None:
        self.calls: list[SampleCommand] = []

    def handle(self, command: SampleCommand) -> int:
        self.calls.append(command)
        raise RuntimeError("handler failed")


@pytest.fixture
def executor() -> CommandExecutor:
    return CommandExecutor(
        command_bus=InMemoryCommandBus(),
        command_stack=InMemoryCommandStack(),
        event_bus=EventBus(),
        transaction_manager=InMemoryTransactionManager(),
    )


def test_satisfies_dispatcher_protocol(executor: CommandExecutor) -> None:
    assert isinstance(executor, CommandDispatcher)


def test_dispatch_calls_handler(executor: CommandExecutor) -> None:
    handler = SampleHandler()
    executor._command_bus.register(SampleCommand, handler)
    result = executor.dispatch(SampleCommand(command_id="c-1", value=21))
    assert result == 42
    assert len(handler.calls) == 1


def test_dispatch_pushes_reversible_command_to_stack(
    executor: CommandExecutor,
) -> None:
    handler = SampleHandler()
    executor._command_bus.register(SampleCommand, handler)
    executor.dispatch(SampleCommand(command_id="c-1"))
    assert executor.can_undo()


def test_dispatch_does_not_push_irreversible_command(
    executor: CommandExecutor,
) -> None:
    handler = SampleHandler()
    executor._command_bus.register(SampleCommand, handler)
    executor.dispatch(SampleCommand(command_id="c-1", is_reversible=False))
    assert not executor.can_undo()


def test_dispatch_unknown_raises(executor: CommandExecutor) -> None:
    with pytest.raises(CommandNotRegistered):
        executor.dispatch(SampleCommand(command_id="c-1"))


def test_dispatch_failing_handler_raises(executor: CommandExecutor) -> None:
    handler = FailingHandler()
    executor._command_bus.register(SampleCommand, handler)
    with pytest.raises(Exception):  # noqa: B017 - handler error wrapped
        executor.dispatch(SampleCommand(command_id="c-1"))
    assert not executor.can_undo()


def test_undo_does_nothing_when_empty(executor: CommandExecutor) -> None:
    executor.undo()  # must not raise
    assert not executor.can_undo()


def test_undo_after_dispatch(executor: CommandExecutor) -> None:
    handler = SampleHandler()
    executor._command_bus.register(SampleCommand, handler)
    executor.dispatch(SampleCommand(command_id="c-1"))
    assert executor.can_undo()
    executor.undo()
    assert not executor.can_undo()
