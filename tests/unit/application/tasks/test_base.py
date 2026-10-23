"""Tests for the Task base types."""

from __future__ import annotations

import pytest

from cranioz.application.tasks.base import (
    CancelToken,
    Task,
    TaskAlreadyDispatched,
    TaskCancelled,
    TaskError,
    TaskHandle,
    TaskManager,
    TaskState,
)


def test_task_state_members() -> None:
    expected = {
        "PENDING",
        "RUNNING",
        "CANCELLING",
        "CANCELLED",
        "COMPLETED",
        "FAILED",
    }
    assert {s.name for s in TaskState} == expected


def test_task_error_hierarchy() -> None:
    assert issubclass(TaskAlreadyDispatched, TaskError)
    assert issubclass(TaskCancelled, TaskError)


def test_protocols_are_runtime_checkable() -> None:
    # The @runtime_checkable decorator allows isinstance checks against
    # structural Protocol. We only verify that the decorator is present
    # and the checks do not blow up; concrete conformance is exercised
    # in test_noop_task_manager.py.
    class DummyTask:
        def run(self, progress, cancel_token):  # noqa: ANN001
            return None

    class DummyToken:
        @property
        def is_cancelled(self) -> bool:
            return False

        def raise_if_cancelled(self) -> None:
            return None

    class DummyHandle:
        @property
        def id(self) -> str:
            return "h-1"

        @property
        def state(self) -> TaskState:
            return TaskState.COMPLETED

        def cancel(self) -> None:
            return None

        def wait(self, timeout: float | None = None) -> None:
            return None

    class DummyManager:
        def dispatch(self, task, **callbacks):  # noqa: ANN001
            return None

    assert isinstance(DummyTask(), Task)
    assert isinstance(DummyToken(), CancelToken)
    assert isinstance(DummyHandle(), TaskHandle)
    assert isinstance(DummyManager(), TaskManager)


def test_object_missing_methods_fails_protocol() -> None:
    class NotATask:
        pass

    assert not isinstance(NotATask(), Task)


@pytest.mark.parametrize("state", list(TaskState))
def test_task_state_has_value(state: TaskState) -> None:
    assert isinstance(state.value, str)
    assert state.value != ""
