"""Application Events — scoped subscription and publication (ADR-0007, ADR-0012).

Public API:

- ``EventSubscription`` — Protocol; scoped subscription facade over the
  EventBus. Subscriptions are owned by the facade and cancelled by
  ``dispose()``.
- ``EventPublisher`` — Protocol; publish-only facade over the EventBus.
- ``SubscriptionHandle`` — Protocol; returned by ``subscribe`` and
  cancelled by ``cancel()``.
- ``EventBusAdapter`` — reference implementation over the existing
  ``EventBus``.
- ``SubscriptionClosed`` and ``EventPublicationError`` — application-level
  errors.

The package wraps the existing ``EventBus`` (which has no scope concept).
It does not replace it. The ``EventBus`` remains the single dispatch
mechanism; the facade only adds scoping and a subscribe/publish split.
"""

from cranioz.application.events.base import (
    EventPublisher,
    EventSubscription,
    SubscriptionHandle,
)
from cranioz.application.events.bus_adapter import EventBusAdapter
from cranioz.application.events.errors import (
    EventPublicationError,
    SubscriptionClosed,
)

__all__ = [
    "EventBusAdapter",
    "EventPublicationError",
    "EventPublisher",
    "EventSubscription",
    "SubscriptionClosed",
    "SubscriptionHandle",
]
