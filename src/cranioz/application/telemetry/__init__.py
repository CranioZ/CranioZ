"""Application Telemetry — observability contract (ADR-0012).

Public API:

- ``TelemetrySink`` — Protocol; records events and measurements.
- ``Severity`` — Enum; event severity.
- ``MeasurementUnit`` — Enum; measurement unit.
- ``TELEMETRY_RESERVED_EVENTS`` — frozenset of reserved event names.
- ``TELEMETRY_RESERVED_MEASUREMENTS`` — frozenset of reserved
  measurement names.
- ``TelemetryError`` — base of all telemetry errors.
- ``NoOpTelemetrySink`` — reference implementation that discards
  everything.
- ``RecordingTelemetrySink`` — reference implementation that captures
  events and measurements in lists.

The package has no dependency on ``logging``, ``json``, or any
transport. Adapters (``LoggingTelemetrySink``, ``FileTelemetrySink``,
future ``OTelTelemetrySink``) live in
``cranioz.infrastructure.telemetry``.
"""

from cranioz.application.telemetry.base import (
    TELEMETRY_RESERVED_EVENTS,
    TELEMETRY_RESERVED_MEASUREMENTS,
    MeasurementUnit,
    Severity,
    TelemetryError,
    TelemetrySink,
)
from cranioz.application.telemetry.noop_sink import NoOpTelemetrySink
from cranioz.application.telemetry.recording_sink import (
    RecordingTelemetrySink,
)

__all__ = [
    "TELEMETRY_RESERVED_EVENTS",
    "TELEMETRY_RESERVED_MEASUREMENTS",
    "MeasurementUnit",
    "NoOpTelemetrySink",
    "RecordingTelemetrySink",
    "Severity",
    "TelemetryError",
    "TelemetrySink",
]
