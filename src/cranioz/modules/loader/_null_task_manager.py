"""A no-op TaskManager used by InMemoryModuleLoader."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from cranioz.application.tasks.base import (
    Task,
    TaskHandle,
    TaskState,
)


class _NullHandle:
    __slots__ = ("_id",)

    def __init__(self, handle_id: str) -> None:
        self._id = handle_id

    @property
    def id(self) -> str:
        return self._id

    @property
    def state(self) -> TaskState:
        return TaskState.FAILED

    def cancel(self) -> None:
        return None

    def wait(self, timeout: float | None = None) -> None:
        return None


class NullTaskManager:
    """TaskManager that fails every dispatch. Used as a placeholder."""

    def dispatch(
        self,
        task: Task,
        *,
        on_progress: Callable[[float], None] | None = None,
        on_result: Callable[[Any], None] | None = None,
        on_error: Callable[[BaseException], None] | None = None,
        on_cancel: Callable[[], None] | None = None,
    ) -> TaskHandle:
        return _NullHandle("null-handle")


_NULL_TASK_MANAGER = NullTaskManager()
