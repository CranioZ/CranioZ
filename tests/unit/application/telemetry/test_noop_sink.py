"""Contract tests for TelemetrySink, exercised against NoOpTelemetrySink."""

from __future__ import annotations

from cranioz.application.telemetry.base import (
    MeasurementUnit,
    Severity,
    TelemetrySink,
)
from cranioz.application.telemetry.noop_sink import NoOpTelemetrySink


def test_noop_sink_satisfies_protocol() -> None:
    assert isinstance(NoOpTelemetrySink(), TelemetrySink)


def test_record_event_is_noop() -> None:
    sink = NoOpTelemetrySink()
    # Must not raise.
    sink.record_event("app.start")


def test_record_event_with_all_arguments() -> None:
    sink = NoOpTelemetrySink()
    sink.record_event(
        "module.load.success",
        severity=Severity.INFO,
        attributes={"module_id": "patient"},
        correlation_id="corr-1",
    )


def test_record_measurement_is_noop() -> None:
    sink = NoOpTelemetrySink()
    # Must not raise.
    sink.record_measurement("module.load.duration", 142.0)


def test_record_measurement_with_all_arguments() -> None:
    sink = NoOpTelemetrySink()
    sink.record_measurement(
        "task.duration",
        1.5,
        unit=MeasurementUnit.SECONDS,
        attributes={"task_name": "segmentation"},
        correlation_id="corr-1",
    )
