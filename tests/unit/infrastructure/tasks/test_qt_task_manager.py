"""Tests for QtTaskManager.

Two groups:

- **Contract tests**, mirroring ``test_noop_task_manager.py``. These
  must pass against any ``TaskManager`` implementation.
- **Qt-specific tests**, covering behaviour unique to the
  ``QThreadPool``-backed implementation: GUI-thread callbacks,
  worker-thread isolation, cooperative cancellation, shutdown.

``qtbot`` is used only to wait for conditions. The ``QtTaskManager``
uses ``QMetaObject.invokeMethod`` with ``QueuedConnection`` to marshal
callbacks; the tests wait via ``qtbot.waitUntil`` on a
``threading.Event`` they control, rather than relying on Qt signals
emitted by the manager. This keeps the tests agnostic of the
manager's internal signal plumbing.
"""

from __future__ import annotations

import threading
import time
from typing import Any

import pytest
from PySide6.QtCore import QThread
from pytestqt.qtbot import QtBot

from cranioz.application.tasks.base import (
    CancelToken,
    TaskAlreadyDispatched,
    TaskCancelled,
    TaskHandle,
    TaskManager,
    TaskState,
)
from cranioz.infrastructure.tasks.qt_task_manager import (
    QtTaskManager,
    TaskManagerClosed,
)

# ----- Fakes --------------------------------------------------------


class ValueTask:
    """Task that reports progress twice and returns a value."""

    def __init__(self, value: int = 21) -> None:
        self.value = value
        self.thread_names: list[str] = []

    def run(self, progress: Any, cancel_token: CancelToken) -> int:
        self.thread_names.append(threading.current_thread().name)
        progress(0.5)
        progress(1.0)
        return self.value * 2


class RaisingTask:
    def __init__(self) -> None:
        self.exception = RuntimeError("boom")

    def run(self, progress: Any, cancel_token: CancelToken) -> None:
        raise self.exception


class CancelTask:
    """Task that raises ``TaskCancelled`` immediately."""

    def run(self, progress: Any, cancel_token: CancelToken) -> None:
        raise TaskCancelled()


class SlowCancelableTask:
    """Task that observes cancellation via ``CancelToken``."""

    def __init__(self) -> None:
        self.started = threading.Event()

    def run(self, progress: Any, cancel_token: CancelToken) -> None:
        self.started.set()
        while not cancel_token.is_cancelled:
            time.sleep(0.01)
        cancel_token.raise_if_cancelled()


# ----- Fixtures -----------------------------------------------------


@pytest.fixture
def task_manager(qapp: Any) -> QtTaskManager:
    """Isolated ``QtTaskManager`` with a dedicated two-thread pool."""
    tm = QtTaskManager(max_threads=2)
    yield tm
    tm.shutdown(grace_seconds=2.0)


def _wait_until(qtbot: QtBot, predicate: Any, timeout_ms: int = 3000) -> None:
    qtbot.waitUntil(predicate, timeout=timeout_ms)


# ====================================================================
# Contract tests — must pass for any TaskManager implementation
# ====================================================================


def test_manager_satisfies_protocol(task_manager: QtTaskManager) -> None:
    assert isinstance(task_manager, TaskManager)


def test_dispatch_returns_handle(task_manager: QtTaskManager, qtbot: QtBot) -> None:
    done = threading.Event()
    handle = task_manager.dispatch(ValueTask(), on_result=lambda _v: done.set())
    _wait_until(qtbot, done.is_set)
    assert isinstance(handle, TaskHandle)
    assert handle.id
    assert handle.state is TaskState.COMPLETED


def test_dispatch_calls_progress(task_manager: QtTaskManager, qtbot: QtBot) -> None:
    progress_values: list[float] = []
    done = threading.Event()
    task_manager.dispatch(
        ValueTask(),
        on_progress=progress_values.append,
        on_result=lambda _v: done.set(),
    )
    _wait_until(qtbot, done.is_set)
    assert progress_values == [0.5, 1.0]


def test_dispatch_calls_on_result(task_manager: QtTaskManager, qtbot: QtBot) -> None:
    results: list[int] = []
    done = threading.Event()

    def _on_result(v: int) -> None:
        results.append(v)
        done.set()

    task_manager.dispatch(ValueTask(value=21), on_result=_on_result)
    _wait_until(qtbot, done.is_set)
    assert results == [42]


def test_dispatch_calls_on_error(task_manager: QtTaskManager, qtbot: QtBot) -> None:
    errors: list[BaseException] = []
    done = threading.Event()

    def _on_error(e: BaseException) -> None:
        errors.append(e)
        done.set()

    task = RaisingTask()
    handle = task_manager.dispatch(task, on_error=_on_error)
    _wait_until(qtbot, done.is_set)
    assert errors == [task.exception]
    assert handle.state is TaskState.FAILED


def test_dispatch_calls_on_cancel_for_task_cancelled(
    task_manager: QtTaskManager, qtbot: QtBot
) -> None:
    cancels: list[None] = []
    done = threading.Event()

    def _on_cancel() -> None:
        cancels.append(None)
        done.set()

    handle = task_manager.dispatch(CancelTask(), on_cancel=_on_cancel)
    _wait_until(qtbot, done.is_set)
    assert handle.state is TaskState.CANCELLED
    assert cancels == [None]


def test_dispatch_twice_raises(task_manager: QtTaskManager, qtbot: QtBot) -> None:
    task = ValueTask()
    done = threading.Event()
    task_manager.dispatch(task, on_result=lambda _v: done.set())
    _wait_until(qtbot, done.is_set)
    with pytest.raises(TaskAlreadyDispatched):
        task_manager.dispatch(task)


def test_handle_cancel_is_noop_after_completion(task_manager: QtTaskManager, qtbot: QtBot) -> None:
    done = threading.Event()
    handle = task_manager.dispatch(ValueTask(), on_result=lambda _v: done.set())
    _wait_until(qtbot, done.is_set)
    handle.cancel()  # must not raise


def test_handle_wait_returns_after_completion(
    task_manager: QtTaskManager,
) -> None:
    done = threading.Event()
    handle = task_manager.dispatch(ValueTask(), on_result=lambda _v: done.set())
    handle.wait(timeout=3.0)
    assert handle.state is TaskState.COMPLETED


# ====================================================================
# Qt-specific tests
# ====================================================================


def test_callbacks_run_on_gui_thread(task_manager: QtTaskManager, qtbot: QtBot) -> None:
    """``on_result`` must execute on the same thread as QApplication."""
    gui_thread = QThread.currentThread()
    observed: list[QThread] = []
    done = threading.Event()

    def _on_result(_v: Any) -> None:
        observed.append(QThread.currentThread())
        done.set()

    task_manager.dispatch(ValueTask(), on_result=_on_result)
    _wait_until(qtbot, done.is_set)
    assert observed == [gui_thread]


def test_progress_callbacks_preserve_order(task_manager: QtTaskManager, qtbot: QtBot) -> None:
    """Even via QueuedConnection, progress order must be preserved."""
    received: list[float] = []
    done = threading.Event()

    def _on_result(_v: Any) -> None:
        done.set()

    task_manager.dispatch(
        ValueTask(),
        on_progress=received.append,
        on_result=_on_result,
    )
    _wait_until(qtbot, done.is_set)
    assert received == [0.5, 1.0]


def test_cancel_token_cooperative_cancel(task_manager: QtTaskManager, qtbot: QtBot) -> None:
    task = SlowCancelableTask()
    cancel_called = threading.Event()
    handle = task_manager.dispatch(task, on_cancel=cancel_called.set)
    _wait_until(qtbot, task.started.is_set)
    handle.cancel()
    _wait_until(qtbot, cancel_called.is_set)
    assert handle.state is TaskState.CANCELLED


def test_shutdown_cancels_pending_tasks(task_manager: QtTaskManager, qtbot: QtBot) -> None:
    task = SlowCancelableTask()
    task_manager.dispatch(task)
    _wait_until(qtbot, task.started.is_set)
    task_manager.shutdown(grace_seconds=0.5)


def test_dispatch_after_shutdown_raises(
    task_manager: QtTaskManager,
) -> None:
    task_manager.shutdown(grace_seconds=0.1)
    with pytest.raises(TaskManagerClosed):
        task_manager.dispatch(ValueTask())


def test_shutdown_is_idempotent(
    task_manager: QtTaskManager,
) -> None:
    task_manager.shutdown(grace_seconds=0.1)
    task_manager.shutdown(grace_seconds=0.1)  # must not raise


def test_task_raising_after_cancellation_is_failed(
    task_manager: QtTaskManager, qtbot: QtBot
) -> None:
    """A task that ignores cancellation and raises is FAILED, not CANCELLED."""

    class DefiantTask:
        def run(self, progress: Any, cancel_token: CancelToken) -> None:
            raise RuntimeError("defiant")

    errors: list[BaseException] = []
    done = threading.Event()

    def _on_error(e: BaseException) -> None:
        errors.append(e)
        done.set()

    handle = task_manager.dispatch(DefiantTask(), on_error=_on_error)
    _wait_until(qtbot, done.is_set)
    assert handle.state is TaskState.FAILED
    assert any(isinstance(e, RuntimeError) for e in errors)
