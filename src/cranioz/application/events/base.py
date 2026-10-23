"""Base Protocols for the Events facade (ADR-0007, ADR-0012).

The ``EventBus`` in ``cranioz.application.event_bus`` is a synchronous
publish/subscribe mechanism. It has no concept of scope: a subscriber
is subscribed until it explicitly unsubscribes.

This module defines two facades over that bus:

- ``EventSubscription`` — scoped. Every ``subscribe`` returns a
  ``SubscriptionHandle``. ``dispose()`` cancels all handles created
  through this facade. The facade is idempotent after disposal.
- ``EventPublisher`` — publish-only. No ``subscribe``. Used where a
  component should emit events but must not observe others.

Neither facade raises from ``publish``: a handler that raises is
collected by the EventBus and re-raised as ``EventBusError``, which
the adapter logs and discards (fire-and-forget, ADR-0012 §2.2).
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Protocol, runtime_checkable

EventHandler = Callable[[Any], None]


@runtime_checkable
class SubscriptionHandle(Protocol):
    """Handle returned by ``EventSubscription.subscribe``.

    ``cancel()`` removes the subscription. It is idempotent: calling it
    twice is a no-op. After ``cancel()``, the handler is no longer
    invoked.
    """

    def cancel(self) -> None: ...


@runtime_checkable
class EventSubscription(Protocol):
    """Scoped subscription facade over the EventBus.

    ``subscribe`` returns a handle. ``dispose`` cancels all outstanding
    handles created through this facade and prevents new
    subscriptions. After ``dispose``, ``subscribe`` raises
    ``SubscriptionClosed``.
    """

    def subscribe(
        self,
        event_type: type,
        handler: EventHandler,
    ) -> SubscriptionHandle: ...

    def dispose(self) -> None: ...


@runtime_checkable
class EventPublisher(Protocol):
    """Publish-only facade over the EventBus.

    The publisher can emit events but cannot subscribe. Used where a
    component should produce events without observing others.
    """

    def publish(self, event: Any) -> None: ...
