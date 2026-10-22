"""InMemoryCommandBus — reference implementation of CommandBus.

Used by tests, by higher-layer contract tests, and by the early
bootstrap before the Application layer is fully wired. It registers
Handlers by Command type and dispatches synchronously on the caller's
thread.

Thread-safety: not thread-safe. Dispatch runs on the caller's thread.
The GUI thread is the expected caller.
"""

from __future__ import annotations

from typing import Any

from cranioz.application.commands.base import (
    Command,
    CommandDispatchError,
    CommandHandler,
    CommandNotRegistered,
)


class InMemoryCommandBus:
    """Reference implementation of ``CommandBus``."""

    def __init__(self) -> None:
        self._handlers: dict[type[Command], CommandHandler[Any, Any]] = {}

    # ----- Registration ---------------------------------------------

    def register(
        self,
        command_type: type[Command],
        handler: CommandHandler[Any, Any],
    ) -> None:
        existing = self._handlers.get(command_type)
        if existing is handler:
            return
        if existing is not None:
            raise ValueError(
                f"a different handler is already registered for "
                f"{command_type.__name__}"
            )
        self._handlers[command_type] = handler

    def unregister(self, command_type: type[Command]) -> None:
        self._handlers.pop(command_type, None)

    # ----- Dispatch -------------------------------------------------

    def dispatch(self, command: Command) -> Any:
        handler = self._handlers.get(type(command))
        if handler is None:
            raise CommandNotRegistered(
                f"no handler registered for {type(command).__name__}"
            )
        try:
            return handler.handle(command)
        except Exception as exc:
            raise CommandDispatchError(
                f"handler for {type(command).__name__} raised "
                f"{type(exc).__name__}: {exc}",
                command_id=command.command_id,
                command_type=type(command).__name__,
            ) from exc

    def can_dispatch(self, command_type: type[Command]) -> bool:
        return command_type in self._handlers

    # ----- Introspection --------------------------------------------

    def command_types(self) -> tuple[type[Command], ...]:
        return tuple(self._handlers.keys())

    # ----- Convenience ----------------------------------------------

    def __len__(self) -> int:
        return len(self._handlers)

    def __repr__(self) -> str:
        types = [t.__name__ for t in self._handlers]
        return f"InMemoryCommandBus(handlers={types!r})"
