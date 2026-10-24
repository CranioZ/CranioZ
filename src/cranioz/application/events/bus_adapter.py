"""EventBusAdapter — scoped and publish-only facades over the EventBus.

The adapter wraps a ``cranioz.application.event_bus.EventBus`` (or any
object satisfying its structural shape) and exposes two Protocol
implementations. Each ``create_subscription()`` call returns a fresh
``EventSubscription`` with its own set of handles; disposing one does
not affect the others.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from cranioz.application.events.base import SubscriptionHandle
from cranioz.application.events.errors import SubscriptionClosed

_logger = logging.getLogger(__name__)

EventHandler = Callable[[Any], None]


class _SubscriptionHandle:
    """Handle for a single subscription."""

    __slots__ = ("_cancelled", "_event_bus", "_event_type", "_handler")

    def __init__(
        self,
        event_bus: Any,
        event_type: type,
        handler: EventHandler,
    ) -> None:
        self._event_bus = event_bus
        self._event_type = event_type
        self._handler = handler
        self._cancelled = False

    def cancel(self) -> None:
        if self._cancelled:
            return
        self._cancelled = True
        try:
            self._event_bus.unsubscribe(self._event_type, self._handler)
        except Exception:
            _logger.exception(
                "failed to unsubscribe handler %r from %r",
                self._handler,
                self._event_type,
            )


class EventBusAdapter:
    """Scoped and publish-only facades over a structural EventBus.

    The adapter does not own the bus. It borrows ``subscribe``,
    ``unsubscribe``, and ``publish``. It does not attempt to wrap
    handlers: the handler passed to ``subscribe`` is the handler
    invoked by the bus.
    """

    def __init__(self, event_bus: Any) -> None:
        self._event_bus = event_bus

    def create_subscription(self) -> _ScopedEventSubscription:
        """Return a fresh ``EventSubscription`` bound to this bus.

        Each call returns a new scope with its own handles. Disposing
        one scope does not affect the others.
        """
        return _ScopedEventSubscription(self._event_bus)

    def create_publisher(self) -> _EventBusPublisher:
        """Return an ``EventPublisher`` bound to this bus."""
        return _EventBusPublisher(self._event_bus)


class _ScopedEventSubscription:
    """``EventSubscription`` implementation backed by a single scope."""

    def __init__(self, event_bus: Any) -> None:
        self._event_bus = event_bus
        self._handles: list[_SubscriptionHandle] = []
        self._disposed = False

    def subscribe(
        self,
        event_type: type,
        handler: EventHandler,
    ) -> SubscriptionHandle:
        if self._disposed:
            raise SubscriptionClosed("cannot subscribe on a disposed EventSubscription")
        self._event_bus.subscribe(event_type, handler)
        handle = _SubscriptionHandle(self._event_bus, event_type, handler)
        self._handles.append(handle)
        return handle

    def dispose(self) -> None:
        if self._disposed:
            return
        self._disposed = True
        for handle in self._handles:
            handle.cancel()
        self._handles.clear()

    def __len__(self) -> int:
        return len(self._handles)


class _EventBusPublisher:
    """``EventPublisher`` implementation backed by a single bus."""

    def __init__(self, event_bus: Any) -> None:
        self._event_bus = event_bus

    def publish(self, event: Any) -> None:
        try:
            self._event_bus.publish(event)
        except Exception:
            _logger.exception("event publication failed for %r", type(event).__name__)
