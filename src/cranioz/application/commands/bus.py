"""CommandBus and CommandHandlerRegistry contracts (ADR-0007).

The Bus is the only entry point for state-changing operations. It
routes a Command to its Handler by type, calls the Handler
synchronously, and returns its result (or raises
``CommandDispatchError`` with the original exception as ``__cause__``).

The Bus does not validate. It does not open transactions. It does not
publish events. Those are the Handler's (or a future CommandExecutor's)
responsibility.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from cranioz.application.commands.base import Command, CommandHandler


@runtime_checkable
class CommandHandlerRegistry(Protocol):
    """Maps Command types to their Handler."""

    def register(
        self,
        command_type: type[Command],
        handler: CommandHandler[Any, Any],
    ) -> None: ...

    def resolve(
        self,
        command_type: type[Command],
    ) -> CommandHandler[Any, Any]: ...

    def contains(self, command_type: type[Command]) -> bool: ...

    def command_types(self) -> tuple[type[Command], ...]: ...


@runtime_checkable
class CommandBus(Protocol):
    """Routes Commands to their Handler."""

    def register(
        self,
        command_type: type[Command],
        handler: CommandHandler[Any, Any],
    ) -> None:
        """Register a Handler for the given Command type."""
        ...

    def unregister(self, command_type: type[Command]) -> None:
        """Remove the Handler for the given Command type.

        No-op if the type is unknown.
        """
        ...

    def dispatch(self, command: Command) -> Any: ...

    def can_dispatch(self, command_type: type[Command]) -> bool: ...
