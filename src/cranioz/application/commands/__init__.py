"""Application Commands — state mutation contract (ADR-0007).

Public API:

- ``Command`` — immutable data expressing an intent to mutate state.
- ``CommandHandler`` — Protocol; validates, executes, commits, publishes.
- ``CommandBus`` — routes Commands to their Handler by type.
- ``CommandHandlerRegistry`` — Protocol; maps a Command type to its Handler.
- ``CommandStack`` — tracks reversible Commands for undo/redo.
- ``InMemoryCommandBus`` — reference implementation (synchronous, in-memory).
- ``InMemoryCommandStack`` — reference implementation.
- ``CommandError`` and subclasses — application-level errors.

The package has no Qt dependency. Dispatch is synchronous; the caller's
thread is the execution thread. Transaction boundaries, event publication,
and undo/redo integration are the Handler's (or a future CommandExecutor's)
responsibility, not the Bus's.
"""

from cranioz.application.commands.base import (
    Command,
    CommandDispatchError,
    CommandError,
    CommandHandler,
    CommandNotRegistered,
)
from cranioz.application.commands.bus import (
    CommandBus,
    CommandHandlerRegistry,
)
from cranioz.application.commands.in_memory_bus import InMemoryCommandBus
from cranioz.application.commands.stack import (
    CommandStack,
    InMemoryCommandStack,
)

__all__ = [
    "Command",
    "CommandBus",
    "CommandDispatchError",
    "CommandError",
    "CommandHandler",
    "CommandHandlerRegistry",
    "CommandNotRegistered",
    "CommandStack",
    "InMemoryCommandBus",
    "InMemoryCommandStack",
]
