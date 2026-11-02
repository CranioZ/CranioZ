"""CommandExecutor — ties CommandBus, CommandStack, EventBus, and
TransactionManager into a single transactional execution path.

The executor is the single entry point for state-changing operations.
It orchestrates (ADR-0007 §2.1):

1. Open a transaction.
2. Dispatch the Command to its Handler (via CommandBus).
3. If the Handler succeeds, commit the transaction and push the
   Command (with its compensating) to the CommandStack.
4. If the Handler raises, roll back (no events are published).

Events are published **only after** a successful commit (ADR-0007 §2.4).
A Handler that publishes events directly violates this contract.

Undo/redo also uses the transaction boundary: the compensating Command
is dispatched through the same executor, so it also gets a transaction,
post-commit event publication, and stack management.
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
    """Single entry point for state-changing operations.

    The executor is the only component that:
    - Opens a transaction.
    - Dispatches the Command.
    - Publishes post-commit events.
    - Manages the undo/redo stack.

    Editors and Tools receive a ``CommandDispatcher`` interface
    (implemented by this class) through their ``EditorContext`` and
    ``ToolContext``. They never interact with the ``CommandBus``,
    the ``TransactionManager``, or the ``CommandStack`` directly.
    """

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

        Raises:
            CommandNotRegistered: no Handler is registered for the
                Command type.
            CommandDispatchError: the Handler raised while executing.
        """
        try:
            with self._transaction_manager.begin():
                result = self._command_bus.dispatch(command)
        except (CommandNotRegistered, CommandDispatchError):
            # The transaction manager already rolled back.
            # No events were published.
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
        """Undo the last reversible Command.

        The compensating Command is dispatched through the same
        transactional path, so it gets its own transaction, post-commit
        event publication, and stack management.

        If the stack has nothing to undo, or the last Command is
        irreversible, this method is a no-op.
        """
        compensating = self._command_stack.undo()
        if compensating is None:
            return

        try:
            with self._transaction_manager.begin():
                self._command_bus.dispatch(compensating)
        except (CommandNotRegistered, CommandDispatchError):
            _logger.exception(
                "undo failed for compensating command %s",
                type(compensating).__name__,
            )
            raise

    def redo(self) -> None:
        """Redo the last undone Command.

        The Command is dispatched through the same transactional path.
        """
        command = self._command_stack.redo()
        if command is None:
            return

        try:
            with self._transaction_manager.begin():
                self._command_bus.dispatch(command)
        except (CommandNotRegistered, CommandDispatchError):
            _logger.exception(
                "redo failed for command %s",
                type(command).__name__,
            )
            raise

    def can_undo(self) -> bool:
        return self._command_stack.can_undo()

    def can_redo(self) -> bool:
        return self._command_stack.can_redo()
