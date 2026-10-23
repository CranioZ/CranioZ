"""NoOpTelemetrySink — discards every event and measurement.

Used by tests and by the early bootstrap before a real adapter is
configured. It never raises.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from cranioz.application.telemetry.base import (
    MeasurementUnit,
    Severity,
)


class NoOpTelemetrySink:
    """Reference implementation of ``TelemetrySink`` that discards all."""

    def record_event(
        self,
        name: str,
        *,
        severity: Severity = Severity.INFO,
        attributes: Mapping[str, Any] | None = None,
        correlation_id: str | None = None,
    ) -> None:
        return None

    def record_measurement(
        self,
        name: str,
        value: float,
        *,
        unit: MeasurementUnit = MeasurementUnit.NONE,
        attributes: Mapping[str, Any] | None = None,
        correlation_id: str | None = None,
    ) -> None:
        return None
