"""Contract tests for CommandStack, exercised against InMemoryCommandStack."""

from __future__ import annotations

from dataclasses import dataclass

from cranioz.application.commands.base import Command
from cranioz.application.commands.stack import (
    CommandStack,
    InMemoryCommandStack,
)


@dataclass(frozen=True)
class SampleCommand(Command):
    tag: str = ""


def _cmd(tag: str) -> SampleCommand:
    return SampleCommand(command_id=Command.new_id(), tag=tag)


# ----- Protocol -----------------------------------------------------


def test_stack_satisfies_protocol() -> None:
    assert isinstance(InMemoryCommandStack(), CommandStack)


# ----- Empty stack --------------------------------------------------


def test_new_stack_is_empty() -> None:
    stack = InMemoryCommandStack()
    assert not stack.can_undo()
    assert not stack.can_redo()
    assert stack.undo() is None
    assert stack.redo() is None


# ----- Push / undo / redo -------------------------------------------


def test_push_then_undo_returns_compensating() -> None:
    stack = InMemoryCommandStack()
    original = _cmd("original")
    compensating = _cmd("compensating")
    stack.push(original, compensating)
    assert stack.can_undo()
    assert not stack.can_redo()
    assert stack.undo() is compensating
    assert stack.can_redo()
    assert not stack.can_undo()


def test_redo_returns_original() -> None:
    stack = InMemoryCommandStack()
    original = _cmd("original")
    compensating = _cmd("compensating")
    stack.push(original, compensating)
    stack.undo()
    assert stack.redo() is original
    assert stack.can_undo()
    assert not stack.can_redo()


def test_push_clears_redo() -> None:
    stack = InMemoryCommandStack()
    stack.push(_cmd("a"), _cmd("a-undo"))
    stack.undo()
    assert stack.can_redo()
    stack.push(_cmd("b"), _cmd("b-undo"))
    assert not stack.can_redo()


# ----- Irreversible Commands ---------------------------------------


def test_irreversible_command_pushes_with_none_compensating() -> None:
    stack = InMemoryCommandStack()
    stack.push(_cmd("irreversible"), None)
    assert stack.can_undo()
    assert stack.undo() is None
    assert stack.can_redo()


# ----- Multiple undo / redo ----------------------------------------


def test_multiple_undos_in_reverse_order() -> None:
    stack = InMemoryCommandStack()
    c1, k1 = _cmd("c1"), _cmd("k1")
    c2, k2 = _cmd("c2"), _cmd("k2")
    stack.push(c1, k1)
    stack.push(c2, k2)
    assert stack.undo() is k2
    assert stack.undo() is k1
    assert stack.undo() is None


def test_multiple_redos_in_forward_order() -> None:
    stack = InMemoryCommandStack()
    c1, k1 = _cmd("c1"), _cmd("k1")
    c2, k2 = _cmd("c2"), _cmd("k2")
    stack.push(c1, k1)
    stack.push(c2, k2)
    stack.undo()
    stack.undo()
    assert stack.redo() is c1
    assert stack.redo() is c2
    assert stack.redo() is None


# ----- Clear --------------------------------------------------------


def test_clear_empties_both_stacks() -> None:
    stack = InMemoryCommandStack()
    stack.push(_cmd("a"), _cmd("a-undo"))
    stack.undo()
    stack.clear()
    assert not stack.can_undo()
    assert not stack.can_redo()
