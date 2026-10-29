"""LoggingTelemetrySink — writes events and measurements to logging.

The adapter translates the TelemetrySink protocol into the standard
logging framework. It is the default production sink (ADR-0012 §2.7).

Design rules:
- Fire-and-forget: never raises from record_event / record_measurement.
- Events are logged at their mapped severity (DEBUG, INFO, WARNING,
  ERROR, CRITICAL).
- Measurements are logged at DEBUG level by default (they are noise
  in production, useful in development).
- The adapter does not redact PII. Components are responsible for
  not emitting patient-identifying attributes (ADR-0012 §2.10).
"""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

from cranioz.application.telemetry.base import (
    MeasurementUnit,
    Severity,
)

_logger = logging.getLogger("cranioz.telemetry")

_SEVERITY_MAP: dict[Severity, int] = {
    Severity.DEBUG: logging.DEBUG,
    Severity.INFO: logging.INFO,
    Severity.WARNING: logging.WARNING,
    Severity.ERROR: logging.ERROR,
    Severity.CRITICAL: logging.CRITICAL,
}


class LoggingTelemetrySink:
    """TelemetrySink that writes to the standard logging framework."""

    def record_event(
        self,
        name: str,
        *,
        severity: Severity = Severity.INFO,
        attributes: Mapping[str, Any] | None = None,
        correlation_id: str | None = None,
    ) -> None:
        _logger.log(
            _SEVERITY_MAP.get(severity, logging.INFO),
            "event=%s correlation_id=%s attributes=%s",
            name,
            correlation_id,
            dict(attributes or {}),
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
        _logger.debug(
            "measurement=%s value=%s unit=%s correlation_id=%s attributes=%s",
            name,
            value,
            unit.value,
            correlation_id,
            dict(attributes or {}),
        )
