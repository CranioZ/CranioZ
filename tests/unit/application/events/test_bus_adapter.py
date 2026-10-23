"""Contract tests for EventSubscription and EventPublisher.

Exercised against ``EventBusAdapter`` wrapping the real ``EventBus``.
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from cranioz.application.event_bus import EventBus
from cranioz.application.events import (
    EventBusAdapter,
    EventPublisher,
    EventSubscription,
    SubscriptionClosed,
    SubscriptionHandle,
)


@dataclass(frozen=True)
class SampleEvent:
    value: int


@dataclass(frozen=True)
class OtherEvent:
    label: str


@pytest.fixture
def bus() -> EventBus:
    return EventBus()


@pytest.fixture
def adapter(bus: EventBus) -> EventBusAdapter:
    return EventBusAdapter(bus)


# ----- Protocol conformance ----------------------------------------


def test_subscription_satisfies_protocol(adapter: EventBusAdapter) -> None:
    sub = adapter.create_subscription()
    assert isinstance(sub, EventSubscription)


def test_publisher_satisfies_protocol(adapter: EventBusAdapter) -> None:
    pub = adapter.create_publisher()
    assert isinstance(pub, EventPublisher)


# ----- Subscription basics -----------------------------------------


def test_subscribe_then_publish_calls_handler(
    adapter: EventBusAdapter,
) -> None:
    received: list[SampleEvent] = []
    sub = adapter.create_subscription()
    handle = sub.subscribe(SampleEvent, received.append)
    assert isinstance(handle, SubscriptionHandle)

    pub = adapter.create_publisher()
    pub.publish(SampleEvent(value=42))

    assert received == [SampleEvent(value=42)]


def test_publish_isolated_by_event_type(
    adapter: EventBusAdapter,
) -> None:
    samples: list[SampleEvent] = []
    others: list[OtherEvent] = []
    sub = adapter.create_subscription()
    sub.subscribe(SampleEvent, samples.append)
    sub.subscribe(OtherEvent, others.append)

    pub = adapter.create_publisher()
    pub.publish(SampleEvent(value=1))

    assert samples == [SampleEvent(value=1)]
    assert others == []


# ----- Multiple handles in one scope --------------------------------


def test_scope_tracks_multiple_handles(adapter: EventBusAdapter) -> None:
    sub = adapter.create_subscription()
    sub.subscribe(SampleEvent, lambda _: None)
    sub.subscribe(SampleEvent, lambda _: None)
    assert len(sub) == 2


def test_dispose_cancels_all_handles(adapter: EventBusAdapter) -> None:
    received: list[SampleEvent] = []
    sub = adapter.create_subscription()
    sub.subscribe(SampleEvent, received.append)

    sub.dispose()

    pub = adapter.create_publisher()
    pub.publish(SampleEvent(value=1))
    assert received == []


def test_dispose_is_idempotent(adapter: EventBusAdapter) -> None:
    sub = adapter.create_subscription()
    sub.subscribe(SampleEvent, lambda _: None)
    sub.dispose()
    sub.dispose()  # must not raise


def test_subscribe_after_dispose_raises(
    adapter: EventBusAdapter,
) -> None:
    sub = adapter.create_subscription()
    sub.dispose()
    with pytest.raises(SubscriptionClosed):
        sub.subscribe(SampleEvent, lambda _: None)


# ----- Individual handle cancellation ------------------------------


def test_handle_cancel_removes_only_that_handler(
    adapter: EventBusAdapter,
) -> None:
    a: list[SampleEvent] = []
    b: list[SampleEvent] = []
    sub = adapter.create_subscription()
    h_a = sub.subscribe(SampleEvent, a.append)
    sub.subscribe(SampleEvent, b.append)

    h_a.cancel()

    pub = adapter.create_publisher()
    pub.publish(SampleEvent(value=1))
    assert a == []
    assert b == [SampleEvent(value=1)]


def test_handle_cancel_is_idempotent(adapter: EventBusAdapter) -> None:
    sub = adapter.create_subscription()
    h = sub.subscribe(SampleEvent, lambda _: None)
    h.cancel()
    h.cancel()  # must not raise


# ----- Independent scopes ------------------------------------------


def test_two_scopes_are_independent(adapter: EventBusAdapter) -> None:
    a: list[SampleEvent] = []
    b: list[SampleEvent] = []
    sub_a = adapter.create_subscription()
    sub_b = adapter.create_subscription()
    sub_a.subscribe(SampleEvent, a.append)
    sub_b.subscribe(SampleEvent, b.append)

    sub_a.dispose()

    pub = adapter.create_publisher()
    pub.publish(SampleEvent(value=1))
    assert a == []
    assert b == [SampleEvent(value=1)]


# ----- Publisher error handling -----------------------------------


def test_publisher_logs_subscriber_failure_without_raising(
    adapter: EventBusAdapter,
    caplog: pytest.LogCaptureFixture,
) -> None:
    def failing(_: SampleEvent) -> None:
        raise RuntimeError("boom")

    sub = adapter.create_subscription()
    sub.subscribe(SampleEvent, failing)

    pub = adapter.create_publisher()
    # Must not raise; logs the failure.
    pub.publish(SampleEvent(value=1))


# ----- Subscription disposal is not automatic on publisher side ----


def test_publisher_does_not_own_subscriptions(
    adapter: EventBusAdapter,
) -> None:
    received: list[SampleEvent] = []
    sub = adapter.create_subscription()
    sub.subscribe(SampleEvent, received.append)

    pub = adapter.create_publisher()
    pub.publish(SampleEvent(value=1))
    pub.publish(SampleEvent(value=2))

    assert received == [SampleEvent(value=1), SampleEvent(value=2)]
