"""Application event bus.

Minimal synchronous publish/subscribe bus for application-level events.
Threading and async dispatch are out of scope for this phase.

Rules:
- Subscribers receive events synchronously, in registration order.
- Publishing an event with no subscribers is a no-op.
- A failing subscriber does not prevent other subscribers from running;
  errors are collected and re-raised after all subscribers have been
  notified.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from typing import Any


class EventBusError(Exception):
    """Raised when subscriber dispatch fails."""


EventHandler = Callable[[Any], None]


class EventBus:
    """Synchronous in-process event bus."""

    def __init__(self) -> None:
        self._subscribers: dict[type, list[EventHandler]] = defaultdict(list)

    def subscribe(self, event_type: type, handler: EventHandler) -> None:
        """Register a handler for a specific event type."""
        self._subscribers[event_type].append(handler)

    def unsubscribe(self, event_type: type, handler: EventHandler) -> None:
        """Remove a previously registered handler.

        No-op if the handler is not registered.
        """
        handlers = self._subscribers.get(event_type)
        if not handlers:
            return
        try:
            handlers.remove(handler)
        except ValueError:
            return

    def publish(self, event: Any) -> None:
        """Publish an event to all handlers registered for its type.

        Dispatches in registration order. If any handler raises, the
        remaining handlers still run, and the collected exceptions are
        re-raised as an EventBusError at the end.
        """
        handlers = list(self._subscribers.get(type(event), ()))
        errors: list[BaseException] = []
        for handler in handlers:
            try:
                handler(event)
            except Exception as exc:  # noqa: BLE001
                errors.append(exc)
        if errors:
            raise EventBusError(
                f"{len(errors)} subscriber(s) failed while publishing "
                f"{type(event).__name__}"
            ) from errors[0]

    def subscriber_count(self, event_type: type) -> int:
        """Return the number of handlers registered for an event type."""
        return len(self._subscribers.get(event_type, ()))