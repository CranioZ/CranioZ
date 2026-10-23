"""Flow errors."""

from __future__ import annotations


class FlowError(Exception):
    """Base of all Flow-related errors."""


class FlowNotFound(FlowError):
    """Raised when a requested flow is not persisted."""

    def __init__(
        self,
        message: str,
        *,
        flow_id: str | None = None,
    ) -> None:
        self.flow_id = flow_id
        super().__init__(message)


class FlowCorrupted(FlowError):
    """Raised when a persisted flow cannot be read as a valid flow."""

    def __init__(
        self,
        message: str,
        *,
        flow_id: str | None = None,
    ) -> None:
        self.flow_id = flow_id
        super().__init__(message)


class FlowStorageError(FlowError):
    """Raised when the underlying storage rejects an operation."""

    def __init__(
        self,
        message: str,
        *,
        flow_id: str | None = None,
    ) -> None:
        self.flow_id = flow_id
        super().__init__(message)
