"""Tests for EventBus."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from cranioz.application.event_bus import EventBus, EventBusError


@dataclass(frozen=True)
class SampleEvent:
    value: int


@dataclass(frozen=True)
class OtherEvent:
    value: int


def test_publish_with_no_subscribers_is_noop() -> None:
    bus = EventBus()
    bus.publish(SampleEvent(value=1))  # must not raise


def test_subscribe_and_publish_receives_event() -> None:
    bus = EventBus()
    received: list[SampleEvent] = []
    bus.subscribe(SampleEvent, received.append)

    bus.publish(SampleEvent(value=42))

    assert received == [SampleEvent(value=42)]


def test_subscribers_are_isolated_by_event_type() -> None:
    bus = EventBus()
    received_sample: list[SampleEvent] = []
    received_other: list[OtherEvent] = []
    bus.subscribe(SampleEvent, received_sample.append)
    bus.subscribe(OtherEvent, received_other.append)

    bus.publish(SampleEvent(value=1))

    assert received_sample == [SampleEvent(value=1)]
    assert received_other == []


def test_multiple_subscribers_called_in_registration_order() -> None:
    bus = EventBus()
    order: list[str] = []
    bus.subscribe(SampleEvent, lambda _: order.append("first"))
    bus.subscribe(SampleEvent, lambda _: order.append("second"))
    bus.subscribe(SampleEvent, lambda _: order.append("third"))

    bus.publish(SampleEvent(value=1))

    assert order == ["first", "second", "third"]


def test_unsubscribe_removes_handler() -> None:
    bus = EventBus()
    received: list[SampleEvent] = []
    handler = received.append
    bus.subscribe(SampleEvent, handler)
    bus.unsubscribe(SampleEvent, handler)

    bus.publish(SampleEvent(value=1))

    assert received == []


def test_unsubscribe_unknown_handler_is_noop() -> None:
    bus = EventBus()
    bus.unsubscribe(SampleEvent, lambda _: None)  # must not raise


def test_failing_subscriber_does_not_block_others() -> None:
    bus = EventBus()
    called: list[str] = []

    def failing(_: SampleEvent) -> None:
        raise RuntimeError("boom")

    bus.subscribe(SampleEvent, failing)
    bus.subscribe(SampleEvent, lambda _: called.append("ok"))

    with pytest.raises(EventBusError):
        bus.publish(SampleEvent(value=1))

    assert called == ["ok"]


def test_subscriber_count() -> None:
    bus = EventBus()
    assert bus.subscriber_count(SampleEvent) == 0
    bus.subscribe(SampleEvent, lambda _: None)
    assert bus.subscriber_count(SampleEvent) == 1
    assert bus.subscriber_count(OtherEvent) == 0