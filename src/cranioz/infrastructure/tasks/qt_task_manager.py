"""QtTaskManager — production TaskManager backed by QThreadPool.

Implements the ``TaskManager`` Protocol from
``cranioz.application.tasks.base`` (ADR-0011). Responsibilities:

- Dispatch Tasks onto a ``QThreadPool``.
- Marshal every callback (progress, result, error, cancel) back to
  the GUI thread using ``QMetaObject.invokeMethod`` with
  ``Qt.QueuedConnection``.
- Provide cooperative cancellation via ``CancelToken``.
- Track task state through a ``TaskHandle``.
- Cancel and await pending tasks on ``shutdown()``.

Design notes (see ADR-0011 §2):

- **QThreadPool, not ProcessPoolExecutor.** VTK/ITK release the GIL
  during native calls, so ``QThreadPool`` is sufficient for the
  clinical workloads this application dispatches. Process pools are
  reserved for future tasks that explicitly declare
  ``process_safe = True``.
- **All callbacks run on the GUI thread.** The ``QtTaskManager``
  itself is a ``QObject`` and is therefore a valid receiver for
  ``QMetaObject.invokeMethod``. A single private slot,
  ``_run_callback``, is the only entry point; it unpacks a
  ``(callable, args)`` tuple. This centralizes the marshalling.
- **Cancellation is cooperative.** ``TaskHandle.cancel()`` sets the
  ``CancelToken``; the Task decides when to observe it. The
  TaskManager does not interrupt a running Task (ADR-0011 §6.5).
- **``shutdown()`` is idempotent and bounded.** It cancels every
  outstanding task and waits up to ``grace_seconds`` (default 5.0,
  ADR-0011 §3.5) for the pool to drain. A second call is a no-op.

The class is intentionally not thread-safe for its public API:
``dispatch``, ``cancel``, and ``shutdown`` are called from the GUI
thread (ADR-0011 §2.3).
"""

from __future__ import annotations

import logging
import threading
import uuid
from collections.abc import Callable
from typing import Any

from PySide6.QtCore import (
    QObject,
    QRunnable,
    Qt,
    QThreadPool,
    Signal,
    Slot,
)

from cranioz.application.tasks.base import (
    Task,
    TaskAlreadyDispatched,
    TaskCancelled,
    TaskError,
    TaskHandle,
    TaskState,
)

_logger = logging.getLogger(__name__)

# Default grace period for ``shutdown()``. Matches ADR-0011 §3.5.
_DEFAULT_GRACE_SECONDS = 5.0


class TaskManagerClosed(TaskError):
    """Raised by ``dispatch`` after ``shutdown`` has begun.

    A distinct error (rather than a plain ``TaskError``) so callers can
    tell "the manager is shutting down" from "the task failed".
    """


# ----- Cancel token -------------------------------------------------


class _QtCancelToken:
    """Cooperative cancel token backed by a ``threading.Event``.

    ``threading.Event`` is thread-safe; the Task (worker thread) checks
    ``is_cancelled`` while the GUI thread calls ``_set_cancelled`` via
    ``TaskHandle.cancel``.
    """

    __slots__ = ("_event",)

    def __init__(self) -> None:
        self._event = threading.Event()

    @property
    def is_cancelled(self) -> bool:
        return self._event.is_set()

    def raise_if_cancelled(self) -> None:
        if self._event.is_set():
            raise TaskCancelled()

    def _set_cancelled(self) -> None:
        self._event.set()


# ----- Task handle --------------------------------------------------


class _QtTaskHandle:
    """TaskHandle returned by ``QtTaskManager.dispatch``.

    State transitions are protected by a ``threading.Lock`` because the
    worker thread writes them while the GUI thread may read them. All
    other methods are expected to be called from the GUI thread.
    """

    __slots__ = ("_done_event", "_id", "_lock", "_state", "_token")

    def __init__(self, handle_id: str, token: _QtCancelToken) -> None:
        self._id = handle_id
        self._token = token
        self._state = TaskState.PENDING
        self._lock = threading.Lock()
        self._done_event = threading.Event()

    @property
    def id(self) -> str:
        return self._id

    @property
    def state(self) -> TaskState:
        with self._lock:
            return self._state

    def _set_state(self, state: TaskState) -> None:
        with self._lock:
            self._state = state
        if state in (
            TaskState.CANCELLED,
            TaskState.COMPLETED,
            TaskState.FAILED,
        ):
            self._done_event.set()

    def cancel(self) -> None:
        if self.state in (
            TaskState.CANCELLED,
            TaskState.COMPLETED,
            TaskState.FAILED,
        ):
            return
        self._token._set_cancelled()

    def wait(self, timeout: float | None = None) -> None:
        self._done_event.wait(timeout)


# ----- Runnable -----------------------------------------------------


class _TaskRunnable(QRunnable):
    """Runs a ``Task`` on a worker thread and reports results back.

    This is the only object that touches the Task on the worker thread.
    It calls the manager's ``_schedule_callback`` to marshal results to
    the GUI thread; it never invokes user callbacks directly.
    """

    def __init__(
        self,
        *,
        task: Task,
        handle: _QtTaskHandle,
        manager: QtTaskManager,
        on_progress: Callable[[float], None] | None,
        on_result: Callable[[Any], None] | None,
        on_error: Callable[[BaseException], None] | None,
        on_cancel: Callable[[], None] | None,
    ) -> None:
        super().__init__()
        self._task = task
        self._handle = handle
        self._manager = manager
        self._on_progress = on_progress
        self._on_result = on_result
        self._on_error = on_error
        self._on_cancel = on_cancel

    def run(self) -> None:
        self._handle._set_state(TaskState.RUNNING)

        def _progress(value: float) -> None:
            # Do not marshal progress after cancellation: the contract
            # guarantees no progress callback is delivered after
            # cancellation is observed (ADR-0011 §2.4).
            if self._handle._token.is_cancelled:
                return
            self._manager._schedule_callback(self._on_progress, value)

        try:
            result = self._task.run(_progress, self._handle._token)
        except TaskCancelled:
            self._handle._set_state(TaskState.CANCELLED)
            self._manager._schedule_callback(self._on_cancel)
            return
        except BaseException as exc:
            self._handle._set_state(TaskState.FAILED)
            if self._on_error is not None:
                self._manager._schedule_callback(self._on_error, exc)
            else:
                _logger.exception(
                    "task %r failed with no on_error callback",
                    type(self._task).__name__,
                )
            return

        self._handle._set_state(TaskState.COMPLETED)
        self._manager._schedule_callback(self._on_result, result)


# ----- Task manager -------------------------------------------------


class QtTaskManager(QObject):
    """Production ``TaskManager`` backed by ``QThreadPool``.

    The manager owns a dedicated pool (not ``QThreadPool.globalInstance``)
    so CranioZ's tasks are isolated from Qt-internal short-lived work.
    The pool can be bounded via ``max_threads`` (useful for tests).
    """

    _invoke_callback = Signal(object)

    def __init__(
        self,
        *,
        max_threads: int | None = None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._pool = QThreadPool(self)
        if max_threads is not None:
            if max_threads < 1:
                raise ValueError(f"max_threads must be >= 1, got {max_threads}")
            self._pool.setMaxThreadCount(max_threads)
        self._handles: dict[str, _QtTaskHandle] = {}
        self._dispatched: set[int] = set()
        self._shutting_down = False

        # Marshalling channel: worker thread emits; GUI thread receives.
        # ``QueuedConnection`` is the default for cross-thread signals but
        # is made explicit because ADR-0011 §2.2 requires GUI-thread delivery.
        self._invoke_callback.connect(
            self._run_callback,
            Qt.ConnectionType.QueuedConnection,
        )

    # ----- Public API ----------------------------------------------

    def dispatch(
        self,
        task: Task,
        *,
        on_progress: Callable[[float], None] | None = None,
        on_result: Callable[[Any], None] | None = None,
        on_error: Callable[[BaseException], None] | None = None,
        on_cancel: Callable[[], None] | None = None,
    ) -> TaskHandle:
        if self._shutting_down:
            raise TaskManagerClosed("QtTaskManager is shutting down; dispatch is refused")

        key = id(task)
        if key in self._dispatched:
            raise TaskAlreadyDispatched(f"task {type(task).__name__} has already been dispatched")
        self._dispatched.add(key)

        token = _QtCancelToken()
        handle = _QtTaskHandle(str(uuid.uuid4()), token)
        self._handles[handle.id] = handle

        runnable = _TaskRunnable(
            task=task,
            handle=handle,
            manager=self,
            on_progress=on_progress,
            on_result=on_result,
            on_error=on_error,
            on_cancel=on_cancel,
        )
        self._pool.start(runnable)
        return handle

    def shutdown(self, grace_seconds: float = _DEFAULT_GRACE_SECONDS) -> None:
        """Cancel every outstanding task and wait for the pool.

        Idempotent: a second call is a no-op. Bounded: waits at most
        ``grace_seconds`` for running tasks to observe cancellation.
        A task that ignores the token for longer than the grace period
        is abandoned to the OS at process exit; its diagnostic record
        is the ``_logger`` warning emitted below.
        """
        if self._shutting_down:
            return
        self._shutting_down = True

        for handle in self._handles.values():
            handle.cancel()

        drained = self._pool.waitForDone(int(grace_seconds * 1000))
        if not drained:
            _logger.warning(
                "QtTaskManager.shutdown: %d task(s) did not observe cancellation "
                "within %.1fs; abandoning to process exit",
                self._pool.activeThreadCount(),
                grace_seconds,
            )

    # ----- Callback marshalling ------------------------------------

    def _schedule_callback(
        self,
        callback: Callable[..., None] | None,
        *args: Any,
    ) -> None:
        """Marshal ``callback(*args)`` onto the GUI thread.

        A ``None`` callback is a no-op (the caller decided not to
        subscribe). The ``(callback, args)`` tuple travels as a single
        ``object`` through the ``_invoke_callback`` signal; the slot
        signature stays stable across callbacks.

        ``Signal.emit`` is thread-safe; ``QueuedConnection`` (connected
        in ``__init__``) delivers the payload on the GUI thread.
        """
        if callback is None:
            return
        self._invoke_callback.emit((callback, args))

    @Slot(object)
    def _run_callback(self, payload: object) -> None:
        """Execute a marshalled callback on the GUI thread."""
        callback, args = payload  # type: ignore[misc]
        try:
            callback(*args)
        except Exception:
            _logger.exception("task callback %r raised", callback)
