"""Contract tests for TaskManager, exercised against NoOpTaskManager."""

from __future__ import annotations

import pytest

from cranioz.application.tasks.base import (
    TaskAlreadyDispatched,
    TaskCancelled,
    TaskHandle,
    TaskManager,
    TaskState,
)
from cranioz.application.tasks.noop_task_manager import NoOpTaskManager


class ValueTask:
    def __init__(self, value: int = 21) -> None:
        self.value = value
        self.progress_calls: list[float] = []

    def run(self, progress, cancel_token):  # noqa: ANN001
        progress(0.5)
        progress(1.0)
        return self.value * 2


class RaisingTask:
    def __init__(self) -> None:
        self.exception = RuntimeError("boom")

    def run(self, progress, cancel_token):  # noqa: ANN001
        raise self.exception


class CancelTask:
    def run(self, progress, cancel_token):  # noqa: ANN001
        raise TaskCancelled()


@pytest.fixture
def manager() -> NoOpTaskManager:
    return NoOpTaskManager()


def test_manager_satisfies_protocol(manager: NoOpTaskManager) -> None:
    assert isinstance(manager, TaskManager)


def test_dispatch_returns_handle(manager: NoOpTaskManager) -> None:
    handle = manager.dispatch(ValueTask())
    assert isinstance(handle, TaskHandle)
    assert handle.id
    assert handle.state is TaskState.COMPLETED


def test_dispatch_calls_progress(manager: NoOpTaskManager) -> None:
    progress_values: list[float] = []
    manager.dispatch(ValueTask(), on_progress=progress_values.append)
    assert progress_values == [0.5, 1.0]


def test_dispatch_calls_on_result(manager: NoOpTaskManager) -> None:
    results: list[int] = []
    manager.dispatch(ValueTask(value=21), on_result=results.append)
    assert results == [42]


def test_dispatch_calls_on_error(manager: NoOpTaskManager) -> None:
    task = RaisingTask()
    errors: list[BaseException] = []
    handle = manager.dispatch(task, on_error=errors.append)
    assert errors == [task.exception]
    assert handle.state is TaskState.FAILED


def test_dispatch_reraises_when_no_on_error(manager: NoOpTaskManager) -> None:
    task = RaisingTask()
    with pytest.raises(RuntimeError, match="boom"):
        manager.dispatch(task)


def test_dispatch_calls_on_cancel_for_task_cancelled(
    manager: NoOpTaskManager,
) -> None:
    cancel_calls: list[None] = []

    def _on_cancel() -> None:
        cancel_calls.append(None)

    handle = manager.dispatch(CancelTask(), on_cancel=_on_cancel)
    assert handle.state is TaskState.CANCELLED
    assert len(cancel_calls) == 1


def test_dispatch_twice_raises(manager: NoOpTaskManager) -> None:
    task = ValueTask()
    manager.dispatch(task)
    with pytest.raises(TaskAlreadyDispatched):
        manager.dispatch(task)


def test_handle_cancel_is_noop_after_completion(
    manager: NoOpTaskManager,
) -> None:
    handle = manager.dispatch(ValueTask())
    # No-op: the Task already ran. Must not raise.
    handle.cancel()


def test_handle_wait_is_noop_after_completion(
    manager: NoOpTaskManager,
) -> None:
    handle = manager.dispatch(ValueTask())
    handle.wait(timeout=0.001)  # must not raise, must not block
