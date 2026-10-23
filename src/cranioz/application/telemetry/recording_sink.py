"""RecordingTelemetrySink — captures events and measurements in lists.

Used by tests that need to assert on emitted telemetry without parsing
logs. The sink never raises.

Each captured event is a frozen tuple:
``(name, severity, attributes, correlation_id)``.
Each captured measurement is a frozen tuple:
``(name, value, unit, attributes, correlation_id)``.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from cranioz.application.telemetry.base import (
    MeasurementUnit,
    Severity,
)


@dataclass(frozen=True)
class RecordedEvent:
    """An event captured by RecordingTelemetrySink."""

    name: str
    severity: Severity
    attributes: dict[str, Any]
    correlation_id: str | None


@dataclass(frozen=True)
class RecordedMeasurement:
    """A measurement captured by RecordingTelemetrySink."""

    name: str
    value: float
    unit: MeasurementUnit
    attributes: dict[str, Any]
    correlation_id: str | None


class RecordingTelemetrySink:
    """Reference implementation of ``TelemetrySink`` that captures all."""

    def __init__(self) -> None:
        self.events: list[RecordedEvent] = []
        self.measurements: list[RecordedMeasurement] = []

    def record_event(
        self,
        name: str,
        *,
        severity: Severity = Severity.INFO,
        attributes: Mapping[str, Any] | None = None,
        correlation_id: str | None = None,
    ) -> None:
        self.events.append(
            RecordedEvent(
                name=name,
                severity=severity,
                attributes=dict(attributes) if attributes else {},
                correlation_id=correlation_id,
            )
        )

    def record_measurement(
        self,
        name: str,
        value: float,
        *,
        unit: MeasurementUnit = MeasurementUnit.NONE,
        attributes: Mapping[str, Any] | None = None,
        correlation_id: str | None = None,
    ) -> None:
        self.measurements.append(
            RecordedMeasurement(
                name=name,
                value=value,
                unit=unit,
                attributes=dict(attributes) if attributes else {},
                correlation_id=correlation_id,
            )
        )

    def clear(self) -> None:
        """Drop all captured data. Useful between test assertions."""
        self.events.clear()
        self.measurements.clear()
