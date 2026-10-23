"""Tests for ModuleContext."""

from __future__ import annotations

import dataclasses

import pytest

from cranioz.application.commands.in_memory_bus import InMemoryCommandBus
from cranioz.application.event_bus import EventBus
from cranioz.application.events import EventBusAdapter
from cranioz.application.services import EmptyServiceContainer
from cranioz.application.tasks.noop_task_manager import NoOpTaskManager
from cranioz.application.telemetry.noop_sink import NoOpTelemetrySink
from cranioz.modules.base.module_context import ModuleContext


def _make_context(
    *,
    module_id: str = "patient",
    correlation_id: str | None = None,
) -> ModuleContext:
    bus = EventBus()
    adapter = EventBusAdapter(bus)
    return ModuleContext(
        module_id=module_id,
        correlation_id=correlation_id,
        event_subscription=adapter.create_subscription(),
        event_publisher=adapter.create_publisher(),
        command_bus=InMemoryCommandBus(),
        task_manager=NoOpTaskManager(),
        project_provider=lambda: None,
        services=EmptyServiceContainer(),
        telemetry=NoOpTelemetrySink(),
    )


def test_context_holds_all_fields() -> None:
    ctx = _make_context(module_id="patient", correlation_id="corr-1")
    assert ctx.module_id == "patient"
    assert ctx.correlation_id == "corr-1"


def test_context_is_frozen() -> None:
    ctx = _make_context()
    with pytest.raises(dataclasses.FrozenInstanceError):
        ctx.module_id = "other"  # type: ignore[misc]


def test_empty_module_id_raises() -> None:
    with pytest.raises(ValueError, match="module_id"):
        _make_context(module_id="")


def test_empty_correlation_id_raises() -> None:
    with pytest.raises(ValueError, match="correlation_id"):
        _make_context(correlation_id="")
