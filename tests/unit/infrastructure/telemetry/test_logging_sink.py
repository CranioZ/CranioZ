"""Contract tests for LoggingTelemetrySink.

The same suite that validates NoOpTelemetrySink also validates
LoggingTelemetrySink, plus logging-specific tests.
"""

from __future__ import annotations

import logging

import pytest

from cranioz.application.telemetry.base import (
    MeasurementUnit,
    Severity,
    TelemetrySink,
)
from cranioz.infrastructure.telemetry.logging_sink import (
    LoggingTelemetrySink,
)


def test_satisfies_protocol() -> None:
    assert isinstance(LoggingTelemetrySink(), TelemetrySink)


def test_record_event_does_not_raise() -> None:
    sink = LoggingTelemetrySink()
    sink.record_event("app.start")


def test_record_event_with_all_arguments() -> None:
    sink = LoggingTelemetrySink()
    sink.record_event(
        "module.load.success",
        severity=Severity.INFO,
        attributes={"module_id": "patient"},
        correlation_id="corr-1",
    )


def test_record_measurement_does_not_raise() -> None:
    sink = LoggingTelemetrySink()
    sink.record_measurement("module.load.duration", 142.0)


def test_record_measurement_with_all_arguments() -> None:
    sink = LoggingTelemetrySink()
    sink.record_measurement(
        "task.duration",
        1.5,
        unit=MeasurementUnit.SECONDS,
        attributes={"task_name": "segmentation"},
        correlation_id="corr-1",
    )


def test_event_is_logged(caplog: pytest.LogCaptureFixture) -> None:
    sink = LoggingTelemetrySink()
    with caplog.at_level(logging.INFO, logger="cranioz.telemetry"):
        sink.record_event(
            "module.load.success",
            severity=Severity.INFO,
            attributes={"module_id": "patient"},
            correlation_id="corr-1",
        )
    assert "module.load.success" in caplog.text
    assert "corr-1" in caplog.text
    assert "patient" in caplog.text


def test_severity_maps_to_log_level(
    caplog: pytest.LogCaptureFixture,
) -> None:
    sink = LoggingTelemetrySink()
    with caplog.at_level(logging.ERROR, logger="cranioz.telemetry"):
        sink.record_event("command.failure", severity=Severity.ERROR)
    assert any(r.levelno == logging.ERROR for r in caplog.records)


def test_measurement_is_logged_at_debug(
    caplog: pytest.LogCaptureFixture,
) -> None:
    sink = LoggingTelemetrySink()
    with caplog.at_level(logging.DEBUG, logger="cranioz.telemetry"):
        sink.record_measurement(
            "module.load.duration",
            142.0,
            unit=MeasurementUnit.MILLISECONDS,
        )
    assert "module.load.duration" in caplog.text
    assert "142.0" in caplog.text
    assert "ms" in caplog.text
