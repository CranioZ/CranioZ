"""Base types for the Telemetry mechanism (ADR-0012).

A TelemetrySink records events (``module.load.success``) and
measurements (``module.load.duration = 142 ms``). Every event and
measurement carries a ``correlation_id`` identifying the operation.

This module defines the data types and the reserved taxonomy. It has
no dependency on logging, json, or any transport.
"""

from __future__ import annotations

from collections.abc import Mapping
from enum import Enum
from typing import Any, Protocol, runtime_checkable


class Severity(Enum):
    """Severity of a telemetry event."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class MeasurementUnit(Enum):
    """Unit of a telemetry measurement."""

    NONE = "none"
    MILLISECONDS = "ms"
    SECONDS = "s"
    BYTES = "bytes"
    COUNT = "count"
    PERCENT = "percent"


@runtime_checkable
class TelemetrySink(Protocol):
    """Records events and measurements.

    The contract is fire-and-forget: a sink that raises does not
    affect the caller's lifecycle. Adapters log their own failures at
    WARNING level. Adapters must not raise for malformed input; they
    log and discard.

    Every event and measurement carries a ``correlation_id`` that
    identifies the operation. The ``correlation_id`` may be ``None``
    when no operation is in progress.
    """

    def record_event(
        self,
        name: str,
        *,
        severity: Severity = Severity.INFO,
        attributes: Mapping[str, Any] | None = None,
        correlation_id: str | None = None,
    ) -> None: ...

    def record_measurement(
        self,
        name: str,
        value: float,
        *,
        unit: MeasurementUnit = MeasurementUnit.NONE,
        attributes: Mapping[str, Any] | None = None,
        correlation_id: str | None = None,
    ) -> None: ...


# ----- Reserved taxonomy ------------------------------------------


TELEMETRY_RESERVED_EVENTS: frozenset[str] = frozenset(
    {
        "app.start",
        "app.stop",
        "module.load.start",
        "module.load.success",
        "module.load.failure",
        "module.unload.start",
        "module.unload.success",
        "module.unload.failure",
        "module.activate",
        "module.deactivate",
        "workspace.load_spec",
        "workspace.load_spec.failure",
        "workspace.clear",
        "workspace.teardown",
        "command.dispatch",
        "command.success",
        "command.failure",
        "task.dispatch",
        "task.complete",
        "task.cancel",
        "task.failure",
    }
)


TELEMETRY_RESERVED_MEASUREMENTS: frozenset[str] = frozenset(
    {
        "module.load.duration",
        "module.unload.duration",
        "workspace.load_spec.duration",
        "workspace.teardown.duration",
        "command.duration",
        "task.duration",
        "app.memory.rss",
    }
)


# ----- Errors ------------------------------------------------------


class TelemetryError(Exception):
    """Base of all telemetry-related errors.

    The TelemetrySink contract is fire-and-forget: adapters should not
    raise from ``record_event`` / ``record_measurement``. The error
    exists so that future adapters that *do* validate (e.g., a strict
    development sink) have a base class.
    """
