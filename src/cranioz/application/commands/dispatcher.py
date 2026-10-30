"""CommandDispatcher — the interface used by Editors and Tools.

An Editor or Tool does not know the CommandBus, the Handler, or the
transaction boundary. It receives a CommandDispatcher through its
EditorContext or ToolContext (ADR-0002, ADR-0007).

The dispatcher is a thin facade over the CommandExecutor:

    Editor/Tool → CommandDispatcher.dispatch(command) → CommandExecutor

The executor handles the bus, the transaction boundary, the event
publication, and the undo/redo stack.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from cranioz.application.commands.base import Command


@runtime_checkable
class CommandDispatcher(Protocol):
    """Interface used by Editors and Tools to dispatch Commands."""

    def dispatch(self, command: Command) -> Any:
        """Dispatch a Command and return its result.

        Raises:
            CommandNotRegistered: no Handler is registered for the
                Command type.
            CommandDispatchError: the Handler raised while executing.
        """
        ...
