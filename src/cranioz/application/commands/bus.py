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
    """Maps Command types to their Handler.

    The registry is the source of truth for "which handler handles
    which command". It does not dispatch; the CommandBus does.
    """

    def register(
        self,
        command_type: type[Command],
        handler: CommandHandler[Any, Any],
    ) -> None:
        """Register a Handler for the given Command type.

        Raises ``ValueError`` if a different Handler is already
        registered for the same type. Idempotent for the same Handler.
        """
        ...

    def resolve(
        self,
        command_type: type[Command],
    ) -> CommandHandler[Any, Any]:
        """Return the Handler registered for the Command type.

        Raises ``KeyError`` if the type is unknown.
        """
        ...

    def contains(self, command_type: type[Command]) -> bool:
        """Return True if a Handler is registered for the type."""
        ...

    def command_types(self) -> tuple[type[Command], ...]:
        """Return the registered Command types, in registration order."""
        ...


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

    def dispatch(self, command: Command) -> Any:
        """Dispatch the Command to its Handler.

        Raises ``CommandNotRegistered`` if no Handler is registered for
        the Command's type. Raises ``CommandDispatchError`` (with the
        original exception as ``__cause__``) if the Handler raises.
        """
        ...

    def can_dispatch(self, command_type: type[Command]) -> bool:
        """Return True if the type has a registered Handler."""
        ...
