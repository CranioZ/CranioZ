"""Tests for the Telemetry base types."""

from __future__ import annotations

from cranioz.application.telemetry.base import (
    TELEMETRY_RESERVED_EVENTS,
    TELEMETRY_RESERVED_MEASUREMENTS,
    MeasurementUnit,
    Severity,
    TelemetryError,
    TelemetrySink,
)


def test_severity_members() -> None:
    expected = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
    assert {s.name for s in Severity} == expected


def test_severity_values() -> None:
    assert Severity.DEBUG.value == "debug"
    assert Severity.INFO.value == "info"
    assert Severity.WARNING.value == "warning"
    assert Severity.ERROR.value == "error"
    assert Severity.CRITICAL.value == "critical"


def test_measurement_unit_members() -> None:
    expected = {"NONE", "MILLISECONDS", "SECONDS", "BYTES", "COUNT", "PERCENT"}
    assert {u.name for u in MeasurementUnit} == expected


def test_measurement_unit_values() -> None:
    assert MeasurementUnit.NONE.value == "none"
    assert MeasurementUnit.MILLISECONDS.value == "ms"
    assert MeasurementUnit.SECONDS.value == "s"
    assert MeasurementUnit.BYTES.value == "bytes"
    assert MeasurementUnit.COUNT.value == "count"
    assert MeasurementUnit.PERCENT.value == "percent"


def test_telemetry_error_hierarchy() -> None:
    assert issubclass(TelemetryError, Exception)


def test_reserved_events_are_frozenset_of_strings() -> None:
    assert isinstance(TELEMETRY_RESERVED_EVENTS, frozenset)
    for name in TELEMETRY_RESERVED_EVENTS:
        assert isinstance(name, str)
        assert name != ""


def test_reserved_events_contains_core_names() -> None:
    assert "app.start" in TELEMETRY_RESERVED_EVENTS
    assert "command.dispatch" in TELEMETRY_RESERVED_EVENTS
    assert "module.load.success" in TELEMETRY_RESERVED_EVENTS
    assert "task.complete" in TELEMETRY_RESERVED_EVENTS


def test_reserved_measurements_contains_core_names() -> None:
    assert "module.load.duration" in TELEMETRY_RESERVED_MEASUREMENTS
    assert "command.duration" in TELEMETRY_RESERVED_MEASUREMENTS
    assert "task.duration" in TELEMETRY_RESERVED_MEASUREMENTS


def test_telemetry_sink_is_runtime_checkable() -> None:
    class DummySink:
        def record_event(self, name, **kwargs):  # noqa: ANN001
            return None

        def record_measurement(self, name, value, **kwargs):  # noqa: ANN001
            return None

    assert isinstance(DummySink(), TelemetrySink)


def test_object_missing_methods_fails_protocol() -> None:
    class NotASink:
        pass

    assert not isinstance(NotASink(), TelemetrySink)
