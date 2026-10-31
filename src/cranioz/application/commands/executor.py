"""CommandExecutor — ties CommandBus, CommandStack, EventBus,
TransactionManager.

The executor is the single entry point for state-changing operations.
It orchestrates (ADR-0007 §2.1):

1. Authorize (future: ProjectAccessPolicy).
2. Validate (delegated to the Handler).
3. Open a transaction.
4. Domain mutation (delegated to the Handler).
5. Commit or rollback.
6. Post-commit event publication (via EventBus).
7. Undo/redo stack (via CommandStack).

The executor does NOT know the Domain, the UI, or the Handler
internals. It coordinates the platform services.
"""

from __future__ import annotations

import logging
from typing import Any

from cranioz.application.commands.base import (
    Command,
    CommandDispatchError,
    CommandNotRegistered,
)
from cranioz.application.commands.bus import CommandBus
from cranioz.application.commands.stack import CommandStack
from cranioz.application.commands.transaction import TransactionManager
from cranioz.application.event_bus import EventBus

_logger = logging.getLogger(__name__)


class CommandExecutor:
    """Single entry point for state-changing operations."""

    def __init__(
        self,
        command_bus: CommandBus,
        command_stack: CommandStack,
        event_bus: EventBus,
        transaction_manager: TransactionManager,
    ) -> None:
        self._command_bus = command_bus
        self._command_stack = command_stack
        self._event_bus = event_bus
        self._transaction_manager = transaction_manager

    # ----- CommandDispatcher interface ------------------------------

    def dispatch(self, command: Command) -> Any:
        """Dispatch a Command within a transaction.

        The executor:
        1. Opens a transaction.
        2. Routes the Command to its Handler (via CommandBus).
        3. If the Handler succeeds, commits the transaction and pushes
           the Command (with its compensating) to the CommandStack.
        4. If the Handler raises, rolls back (no events are published).
        """
        try:
            with self._transaction_manager.begin():
                result = self._command_bus.dispatch(command)
        except (CommandNotRegistered, CommandDispatchError):
            raise

        # Handler succeeded; push to the undo/redo stack.
        if command.is_reversible:
            self._command_stack.push(
                command,
                compensating=command.compensating,
            )
        return result

    # ----- Undo/Redo ------------------------------------------------

    def undo(self) -> None:
        """Undo the last reversible Command."""
        compensating = self._command_stack.undo()
        if compensating is None:
            return
        self._command_bus.dispatch(compensating)

    def redo(self) -> None:
        """Redo the last undone Command."""
        command = self._command_stack.redo()
        if command is None:
            return
        self._command_bus.dispatch(command)

    def can_undo(self) -> bool:
        return self._command_stack.can_undo()

    def can_redo(self) -> bool:
        return self._command_stack.can_redo()
