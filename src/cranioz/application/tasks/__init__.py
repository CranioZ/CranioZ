"""Application Tasks — off-thread work contract (ADR-0011).

Public API:

- ``Task`` — Protocol; a unit of work executed on a worker thread.
- ``TaskHandle`` — Protocol; the handle returned by ``dispatch``.
- ``TaskManager`` — Protocol; dispatches Tasks and delivers callbacks
  on the GUI thread.
- ``CancelToken`` — Protocol; cooperative cancellation handle passed
  to ``Task.run``.
- ``TaskState`` — Enum; lifecycle of a dispatched Task.
- ``TaskError`` and subclasses — application-level errors.
- ``NoOpTaskManager`` — reference implementation that runs Tasks
  synchronously. Used by tests and by the early bootstrap.

The package has no Qt dependency. The concrete ``QtTaskManager``
(``QThreadPool``/``ProcessPoolExecutor``) lives in
``cranioz.infrastructure.tasks``.
"""

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
from cranioz.application.tasks.noop_task_manager import NoOpTaskManager

__all__ = [
    "CancelToken",
    "NoOpTaskManager",
    "Task",
    "TaskAlreadyDispatched",
    "TaskCancelled",
    "TaskError",
    "TaskHandle",
    "TaskManager",
    "TaskState",
]
