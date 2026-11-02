"""Contract tests for CommandExecutor."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from cranioz.application.commands.base import (
    Command,
    CommandDispatchError,
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


@dataclass(frozen=True)
class SampleEvent:
    value: int


class SampleHandler:
    """Handler that records calls and returns a result."""

    def __init__(self) -> None:
        self.calls: list[SampleCommand] = []

    def handle(self, command: SampleCommand) -> int:
        self.calls.append(command)
        return command.value * 2


class FailingHandler:
    """Handler that raises."""

    def __init__(self) -> None:
        self.calls: list[SampleCommand] = []

    def handle(self, command: SampleCommand) -> int:
        self.calls.append(command)
        raise RuntimeError("handler failed")


class EventPublishingHandler:
    """Handler that publishes an event (simulating a domain event)."""

    def __init__(self, event_bus: EventBus) -> None:
        self._event_bus = event_bus

    def handle(self, command: SampleCommand) -> int:
        self._event_bus.publish(SampleEvent(value=command.value))
        return command.value


@pytest.fixture
def event_bus() -> EventBus:
    return EventBus()


@pytest.fixture
def command_bus() -> InMemoryCommandBus:
    return InMemoryCommandBus()


@pytest.fixture
def command_stack() -> InMemoryCommandStack:
    return InMemoryCommandStack()


@pytest.fixture
def executor(
    command_bus: InMemoryCommandBus,
    command_stack: InMemoryCommandStack,
    event_bus: EventBus,
) -> CommandExecutor:
    return CommandExecutor(
        command_bus=command_bus,
        command_stack=command_stack,
        event_bus=event_bus,
        transaction_manager=InMemoryTransactionManager(),
    )


# ----- Protocol -----------------------------------------------------


def test_executor_satisfies_dispatcher_protocol(executor: CommandExecutor) -> None:
    assert isinstance(executor, CommandDispatcher)


# ----- Dispatch -----------------------------------------------------


def test_dispatch_calls_handler(
    executor: CommandExecutor,
    command_bus: InMemoryCommandBus,
) -> None:
    handler = SampleHandler()
    command_bus.register(SampleCommand, handler)

    result = executor.dispatch(SampleCommand(command_id="c-1", value=21))

    assert result == 42
    assert len(handler.calls) == 1
    assert handler.calls[0].value == 21


def test_dispatch_pushes_reversible_command_to_stack(
    executor: CommandExecutor,
    command_bus: InMemoryCommandBus,
) -> None:
    handler = SampleHandler()
    command_bus.register(SampleCommand, handler)

    executor.dispatch(SampleCommand(command_id="c-1"))

    assert executor.can_undo() is True
    assert executor.can_redo() is False


def test_dispatch_does_not_push_irreversible_command(
    executor: CommandExecutor,
    command_bus: InMemoryCommandBus,
) -> None:
    handler = SampleHandler()
    command_bus.register(SampleCommand, handler)

    executor.dispatch(SampleCommand(command_id="c-1", is_reversible=False))

    assert executor.can_undo() is False


def test_dispatch_unknown_raises(executor: CommandExecutor) -> None:
    with pytest.raises(CommandNotRegistered):
        executor.dispatch(SampleCommand(command_id="c-1"))


def test_dispatch_failing_handler_raises(
    executor: CommandExecutor,
    command_bus: InMemoryCommandBus,
) -> None:
    handler = FailingHandler()
    command_bus.register(SampleCommand, handler)

    with pytest.raises(CommandDispatchError):
        executor.dispatch(SampleCommand(command_id="c-1"))

    # No push on failure.
    assert executor.can_undo() is False


# ----- Event publication -------------------------------------------


def test_events_published_after_commit(
    executor: CommandExecutor,
    command_bus: InMemoryCommandBus,
    event_bus: EventBus,
) -> None:
    """Events must be published only after a successful commit."""
    received: list[SampleEvent] = []
    event_bus.subscribe(SampleEvent, received.append)

    handler = EventPublishingHandler(event_bus)
    command_bus.register(SampleCommand, handler)

    executor.dispatch(SampleCommand(command_id="c-1", value=42))

    assert received == [SampleEvent(value=42)]


def test_no_events_published_on_failure(
    executor: CommandExecutor,
    command_bus: InMemoryCommandBus,
    event_bus: EventBus,
) -> None:
    """A failing Handler must not publish events."""
    received: list[SampleEvent] = []
    event_bus.subscribe(SampleEvent, received.append)

    handler = FailingHandler()
    command_bus.register(SampleCommand, handler)

    with pytest.raises(CommandDispatchError):
        executor.dispatch(SampleCommand(command_id="c-1"))

    assert received == []


# ----- Undo/Redo ----------------------------------------------------


def test_undo_does_nothing_when_empty(executor: CommandExecutor) -> None:
    executor.undo()  # must not raise
    assert executor.can_undo() is False


def test_undo_dispatches_compensating(
    executor: CommandExecutor,
    command_bus: InMemoryCommandBus,
) -> None:
    handler = SampleHandler()
    command_bus.register(SampleCommand, handler)
    command_bus.register(CompensatingCommand, SampleHandler())

    compensating = CompensatingCommand(command_id="c-undo")
    command = SampleCommand(command_id="c-1", compensating=compensating)

    executor.dispatch(command)
    assert executor.can_undo() is True

    executor.undo()
    assert executor.can_undo() is False
    assert executor.can_redo() is True


def test_redo_dispatches_original(
    executor: CommandExecutor,
    command_bus: InMemoryCommandBus,
) -> None:
    handler = SampleHandler()
    command_bus.register(SampleCommand, handler)
    command_bus.register(CompensatingCommand, SampleHandler())

    compensating = CompensatingCommand(command_id="c-undo")
    command = SampleCommand(command_id="c-1", compensating=compensating)

    executor.dispatch(command)
    executor.undo()

    executor.redo()
    assert executor.can_undo() is True
    assert executor.can_redo() is False


def test_undo_unknown_compensating_raises(
    executor: CommandExecutor,
    command_bus: InMemoryCommandBus,
) -> None:
    handler = SampleHandler()
    command_bus.register(SampleCommand, handler)

    # CompensatingCommand is not registered.
    compensating = CompensatingCommand(command_id="c-undo")
    command = SampleCommand(command_id="c-1", compensating=compensating)

    executor.dispatch(command)
    with pytest.raises(CommandNotRegistered):
        executor.undo()
