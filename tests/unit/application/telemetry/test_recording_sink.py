"""Tests for RecordingTelemetrySink."""

from __future__ import annotations

from cranioz.application.telemetry.base import (
    MeasurementUnit,
    Severity,
    TelemetrySink,
)
from cranioz.application.telemetry.recording_sink import (
    RecordedEvent,
    RecordedMeasurement,
    RecordingTelemetrySink,
)


def test_recording_sink_satisfies_protocol() -> None:
    assert isinstance(RecordingTelemetrySink(), TelemetrySink)


def test_new_sink_is_empty() -> None:
    sink = RecordingTelemetrySink()
    assert sink.events == []
    assert sink.measurements == []


def test_record_event_captures() -> None:
    sink = RecordingTelemetrySink()
    sink.record_event(
        "module.load.success",
        severity=Severity.INFO,
        attributes={"module_id": "patient"},
        correlation_id="corr-1",
    )
    assert len(sink.events) == 1
    recorded = sink.events[0]
    assert isinstance(recorded, RecordedEvent)
    assert recorded.name == "module.load.success"
    assert recorded.severity is Severity.INFO
    assert recorded.attributes == {"module_id": "patient"}
    assert recorded.correlation_id == "corr-1"


def test_record_event_defaults() -> None:
    sink = RecordingTelemetrySink()
    sink.record_event("app.start")
    recorded = sink.events[0]
    assert recorded.severity is Severity.INFO
    assert recorded.attributes == {}
    assert recorded.correlation_id is None


def test_record_measurement_captures() -> None:
    sink = RecordingTelemetrySink()
    sink.record_measurement(
        "module.load.duration",
        142.0,
        unit=MeasurementUnit.MILLISECONDS,
        attributes={"module_id": "patient"},
        correlation_id="corr-1",
    )
    assert len(sink.measurements) == 1
    recorded = sink.measurements[0]
    assert isinstance(recorded, RecordedMeasurement)
    assert recorded.name == "module.load.duration"
    assert recorded.value == 142.0
    assert recorded.unit is MeasurementUnit.MILLISECONDS
    assert recorded.attributes == {"module_id": "patient"}
    assert recorded.correlation_id == "corr-1"


def test_record_measurement_defaults() -> None:
    sink = RecordingTelemetrySink()
    sink.record_measurement("task.duration", 1.0)
    recorded = sink.measurements[0]
    assert recorded.unit is MeasurementUnit.NONE
    assert recorded.attributes == {}
    assert recorded.correlation_id is None


def test_clear_drops_everything() -> None:
    sink = RecordingTelemetrySink()
    sink.record_event("app.start")
    sink.record_measurement("app.memory.rss", 1024.0)
    sink.clear()
    assert sink.events == []
    assert sink.measurements == []


def test_attributes_are_copied() -> None:
    sink = RecordingTelemetrySink()
    original = {"module_id": "patient"}
    sink.record_event("module.load.success", attributes=original)
    original["module_id"] = "tomography"
    assert sink.events[0].attributes == {"module_id": "patient"}
