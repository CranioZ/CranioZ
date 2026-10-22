"""Base types for the Command mechanism (ADR-0007).

A Command is immutable data expressing an intent to change persistent
state. A CommandHandler validates, opens a transaction, mutates the
domain, commits, and publishes events. The CommandBus routes a Command
to its Handler by type.

This module defines the data and error types shared by every Command,
Handler, Bus, and Stack. It has no Qt, filesystem, or EventBus
dependency.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Protocol, TypeVar, runtime_checkable

TCommand = TypeVar("TCommand", contravariant=True)
TResult = TypeVar("TResult", covariant=True)


@dataclass(frozen=True)
class Command:
    """An immutable intent to change persistent state."""

    command_id: str = field(default="")
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def new(
        cls,
        *,
        command_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Command:
        """Return a new Command with a generated ``command_id``."""
        if command_id is None:
            command_id = str(uuid.uuid4())
        if metadata is None:
            metadata = {}
        return cls(command_id=command_id, metadata=metadata, **kwargs)

    @staticmethod
    def new_id() -> str:
        """Return a fresh ``command_id``."""
        return str(uuid.uuid4())


@runtime_checkable
class CommandHandler(Protocol[TCommand, TResult]):
    """Executes a specific Command type."""

    def handle(self, command: TCommand) -> TResult: ...


# ----- Errors ------------------------------------------------------


class CommandError(Exception):
    """Base of all Command-related errors."""


class CommandNotRegistered(CommandError):
    """No Handler is registered for the given Command type."""


class CommandDispatchError(CommandError):
    """A Handler raised while dispatching a Command."""

    def __init__(
        self,
        message: str,
        *,
        command_id: str | None = None,
        command_type: str | None = None,
    ) -> None:
        self.command_id = command_id
        self.command_type = command_type
        super().__init__(message)
