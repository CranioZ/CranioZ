"""NoOpTaskManager — reference implementation of TaskManager.

Used by tests, by higher-layer contract tests, and by the early
bootstrap before the concrete ``QtTaskManager`` exists. It runs every
``Task`` synchronously on the caller's thread, immediately, and
returns a ``TaskHandle`` that is already in a terminal state.

This is not a toy. It respects the TaskManager contract:

- ``dispatch`` returns immediately (with a completed handle).
- Callbacks (``on_progress``, ``on_result``, ``on_error``,
  ``on_cancel``) are called on the caller's thread.
- ``TaskCancelled`` raised by the Task transitions to ``CANCELLED``
  and calls ``on_cancel``.
- Any other exception transitions to ``FAILED`` and calls
  ``on_error``. If ``on_error`` is not provided, the exception is
  re-raised after the handle is marked ``FAILED``.
- ``dispatch`` on the same Task twice raises ``TaskAlreadyDispatched``.

Thread-safety: not thread-safe. Dispatch runs on the caller's thread.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from typing import Any

from cranioz.application.tasks.base import (
    Task,
    TaskAlreadyDispatched,
    TaskCancelled,
    TaskHandle,
    TaskState,
)


class _SimpleCancelToken:
    """CancelToken used by NoOpTaskManager.

    Runs synchronously, so cancellation is always False during
    ``Task.run``. Exposed so tests can pass a real CancelToken to a
    fake Task if they need to.
    """

    __slots__ = ("_cancelled",)

    def __init__(self) -> None:
        self._cancelled = False

    @property
    def is_cancelled(self) -> bool:
        return self._cancelled

    def raise_if_cancelled(self) -> None:
        if self._cancelled:
            raise TaskCancelled()


class _NoOpTaskHandle:
    """TaskHandle returned by NoOpTaskManager.dispatch."""

    __slots__ = ("_id", "_state", "_token")

    def __init__(self, handle_id: str, token: _SimpleCancelToken) -> None:
        self._id = handle_id
        self._state = TaskState.PENDING
        self._token = token

    @property
    def id(self) -> str:
        return self._id

    @property
    def state(self) -> TaskState:
        return self._state

    def _set_state(self, state: TaskState) -> None:
        self._state = state

    def cancel(self) -> None:
        # The Task already ran to completion. Cancelling a terminal
        # handle is a no-op, per ADR-0011 §2.2.
        return None

    def wait(self, timeout: float | None = None) -> None:
        # Already complete; nothing to wait for.
        return None


class NoOpTaskManager:
    """Reference implementation of ``TaskManager``."""

    def __init__(self) -> None:
        self._dispatched: set[int] = set()

    def dispatch(
        self,
        task: Task,
        *,
        on_progress: Callable[[float], None] | None = None,
        on_result: Callable[[Any], None] | None = None,
        on_error: Callable[[BaseException], None] | None = None,
        on_cancel: Callable[[], None] | None = None,
    ) -> TaskHandle:
        key = id(task)
        if key in self._dispatched:
            raise TaskAlreadyDispatched(f"task {type(task).__name__} has already been dispatched")
        self._dispatched.add(key)

        token = _SimpleCancelToken()
        handle = _NoOpTaskHandle(str(uuid.uuid4()), token)

        def _progress(value: float) -> None:
            if on_progress is not None:
                on_progress(value)

        handle._set_state(TaskState.RUNNING)
        try:
            result = task.run(_progress, token)
        except TaskCancelled:
            handle._set_state(TaskState.CANCELLED)
            if on_cancel is not None:
                on_cancel()
            return handle
        except BaseException as exc:
            handle._set_state(TaskState.FAILED)
            if on_error is not None:
                on_error(exc)
            else:
                raise
            return handle

        handle._set_state(TaskState.COMPLETED)
        if on_result is not None:
            on_result(result)
        return handle
