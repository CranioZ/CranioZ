"""Base types for the Task mechanism (ADR-0011).

A Task is a unit of work that runs on a worker thread. The TaskManager
dispatches it, delivers progress, result, and error callbacks on the
GUI thread, and tracks cancellation cooperatively.

This module defines the data and error types. It has no Qt,
filesystem, or EventBus dependency.
"""

from __future__ import annotations

from collections.abc import Callable
from enum import Enum
from typing import Any, Protocol, runtime_checkable


class TaskState(Enum):
    """Lifecycle state of a dispatched Task."""

    PENDING = "pending"
    RUNNING = "running"
    CANCELLING = "cancelling"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    FAILED = "failed"


@runtime_checkable
class CancelToken(Protocol):
    """Cooperative cancellation handle passed to ``Task.run``.

    The Task must check ``is_cancelled`` at least once per second and
    return early when it is True. ``raise_if_cancelled`` is a
    convenience that raises ``TaskCancelled``.
    """

    @property
    def is_cancelled(self) -> bool: ...

    def raise_if_cancelled(self) -> None: ...


@runtime_checkable
class Task(Protocol):
    """A unit of work executed on a worker thread.

    ``run`` receives a ``progress`` callback and a ``CancelToken``. It
    must not touch QWidget, VTK render objects, the Scene, or any
    GUI-thread state (ADR-0011 §2.3). It reads immutable snapshots and
    returns a value or raises an error.
    """

    def run(
        self,
        progress: Callable[[float], None],
        cancel_token: CancelToken,
    ) -> Any: ...


@runtime_checkable
class TaskHandle(Protocol):
    """Handle returned by ``TaskManager.dispatch``."""

    @property
    def id(self) -> str: ...

    @property
    def state(self) -> TaskState: ...

    def cancel(self) -> None: ...

    def wait(self, timeout: float | None = None) -> None: ...


@runtime_checkable
class TaskManager(Protocol):
    """Dispatches Tasks and delivers callbacks on the GUI thread.

    The TaskManager is the only mechanism for off-thread work in
    CranioZ (ADR-0011 §2.3). Components must not create ``QThread``,
    ``ThreadPoolExecutor``, ``ProcessPoolExecutor``, ``asyncio``
    loops, or raw threads.
    """

    def dispatch(
        self,
        task: Task,
        *,
        on_progress: Callable[[float], None] | None = None,
        on_result: Callable[[Any], None] | None = None,
        on_error: Callable[[BaseException], None] | None = None,
        on_cancel: Callable[[], None] | None = None,
    ) -> TaskHandle: ...


# ----- Errors ------------------------------------------------------


class TaskError(Exception):
    """Base of all Task-related errors."""


class TaskAlreadyDispatched(TaskError):
    """A Task was dispatched twice through the same TaskManager."""


class TaskCancelled(TaskError):
    """Raised by ``CancelToken.raise_if_cancelled``.

    The TaskManager treats ``TaskCancelled`` specially: the Task
    transitions to ``TaskState.CANCELLED`` (not ``FAILED``) and
    ``on_cancel`` is invoked. Any other exception transitions to
    ``FAILED``.
    """
