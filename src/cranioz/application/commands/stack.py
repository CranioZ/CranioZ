"""CommandStack — undo/redo tracking (ADR-0007 §2.5).

The CommandStack does not execute Commands. It stores pairs
``(command, compensating)`` and returns the next Command to dispatch
on undo/redo. The caller (typically a future CommandExecutor) is
responsible for dispatching the returned Command on the CommandBus.

A Command with ``compensating=None`` is irreversible: ``undo`` pops it
and returns ``None``, which tells the caller that the Command cannot
be undone. Pushing any Command clears the redo branch.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from cranioz.application.commands.base import Command


@runtime_checkable
class CommandStack(Protocol):
    """Tracks reversible Commands for undo/redo."""

    def push(
        self,
        command: Command,
        compensating: Command | None,
    ) -> None:
        """Record a dispatched Command and its compensating Command.

        ``compensating`` is ``None`` for irreversible Commands. In
        either case, ``push`` clears the redo branch.
        """
        ...

    def undo(self) -> Command | None:
        """Pop the last undoable Command and return its compensating.

        Returns ``None`` if there is nothing to undo, or if the popped
        Command is irreversible. The caller dispatches the returned
        Command when it is not ``None``.
        """
        ...

    def redo(self) -> Command | None:
        """Pop the last redone Command and return its original.

        Returns ``None`` if there is nothing to redo. The caller
        dispatches the returned Command.
        """
        ...

    def can_undo(self) -> bool:
        """Return True if there is at least one undoable Command."""
        ...

    def can_redo(self) -> bool:
        """Return True if there is at least one redone Command."""
        ...

    def clear(self) -> None:
        """Clear both undo and redo stacks."""
        ...


class InMemoryCommandStack:
    """Reference implementation of ``CommandStack``.

    Two lists (undo and redo). Not thread-safe.
    """

    def __init__(self) -> None:
        self._undo: list[tuple[Command, Command | None]] = []
        self._redo: list[tuple[Command, Command | None]] = []

    def push(
        self,
        command: Command,
        compensating: Command | None,
    ) -> None:
        self._undo.append((command, compensating))
        self._redo.clear()

    def undo(self) -> Command | None:
        if not self._undo:
            return None
        command, compensating = self._undo.pop()
        self._redo.append((command, compensating))
        return compensating

    def redo(self) -> Command | None:
        if not self._redo:
            return None
        command, compensating = self._redo.pop()
        self._undo.append((command, compensating))
        return command

    def can_undo(self) -> bool:
        return bool(self._undo)

    def can_redo(self) -> bool:
        return bool(self._redo)

    def clear(self) -> None:
        self._undo.clear()
        self._redo.clear()

    def __len__(self) -> int:
        return len(self._undo)

    def __repr__(self) -> str:
        return (
            f"InMemoryCommandStack(undo={len(self._undo)}, "
            f"redo={len(self._redo)})"
        )
