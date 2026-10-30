"""CommandExecutor — ties CommandBus, CommandStack, and EventBus.

The executor is the single entry point for state-changing operations.
It orchestrates:

1. Authorization (future: ProjectAccessPolicy).
2. Validation (delegated to the Handler).
3. Transaction boundary (delegated to the Handler, for now).
4. Domain mutation (delegated to the Handler).
5. Commit (delegated to the Handler, for now).
6. Post-commit event publication (via EventBus).
7. Undo/redo stack (via CommandStack).

The executor does NOT:
- Know the Domain (it delegates to the Handler).
- Know the UI (it is in the Application layer).
- Own a transaction manager (future: TransactionManager).
- Know what events to publish (the Handler declares them).

For the first version, the executor assumes:
- The Handler publishes its own events (for now; a future version
  will centralize event publication in the executor).
- The Handler declares reversibility via `command.is_reversible`
  (future; for now, all Commands are considered reversible).
- No transaction manager (future: the executor will open a
  transaction, call the Handler, and commit/rollback).
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
from cranioz.application.event_bus import EventBus

_logger = logging.getLogger(__name__)


class CommandExecutor:
    """Single entry point for state-changing operations.

    The executor is the implementation of the `CommandDispatcher`
    Protocol. It coordinates the CommandBus, the CommandStack, and
    the EventBus.
    """

    def __init__(
        self,
        command_bus: CommandBus,
        command_stack: CommandStack,
        event_bus: EventBus,
    ) -> None:
        self._command_bus = command_bus
        self._command_stack = command_stack
        self._event_bus = event_bus

    # ----- CommandDispatcher interface ------------------------------

    def dispatch(self, command: Command) -> Any:
        """Dispatch a Command and return its result.

        The executor:
        1. Routes the Command to its Handler (via CommandBus).
        2. If the Handler succeeds, pushes the Command to the
           CommandStack (for undo/redo).
        3. (Future) Opens a transaction, calls the Handler, commits
           or rolls back, and publishes post-commit events.

        Raises:
            CommandNotRegistered: no Handler is registered for the
                Command type.
            CommandDispatchError: the Handler raised while executing.
        """
        try:
            result = self._command_bus.dispatch(command)
        except (CommandNotRegistered, CommandDispatchError):
            # The bus already wrapped the error with context.
            raise

        # For now, all Commands are considered reversible.
        # A future version will read `command.is_reversible`.
        self._command_stack.push(command, compensating=None)
        return result

    # ----- Undo/Redo ------------------------------------------------

    def undo(self) -> None:
        """Undo the last reversible Command.

        Dispatches the compensating Command (if any).
        """
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
