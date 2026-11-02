"""Application Commands — state mutation contract (ADR-0007).

Public API:
- ``Command`` — immutable data expressing an intent to mutate state.
- ``CommandHandler`` — Protocol; validates, executes, commits, publishes.
- ``CommandBus`` — routes Commands to their Handler by type.
- ``CommandDispatcher`` — interface used by Editors and Tools.
- ``CommandExecutor`` — transactional executor (Sprint 1).
- ``CommandStack`` — tracks reversible Commands for undo/redo.
- ``InMemoryCommandBus`` — reference implementation.
- ``InMemoryCommandStack`` — reference implementation.
- ``InMemoryTransactionManager`` — reference implementation.
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
from cranioz.application.commands.dispatcher import CommandDispatcher
from cranioz.application.commands.executor import CommandExecutor
from cranioz.application.commands.in_memory_bus import InMemoryCommandBus
from cranioz.application.commands.stack import (
    CommandStack,
    InMemoryCommandStack,
)
from cranioz.application.commands.transaction import (
    InMemoryTransactionManager,
    TransactionManager,
)

__all__ = [
    "Command",
    "CommandBus",
    "CommandDispatchError",
    "CommandDispatcher",
    "CommandError",
    "CommandExecutor",
    "CommandHandler",
    "CommandHandlerRegistry",
    "CommandNotRegistered",
    "CommandStack",
    "InMemoryCommandBus",
    "InMemoryCommandStack",
    "InMemoryTransactionManager",
    "TransactionManager",
]
