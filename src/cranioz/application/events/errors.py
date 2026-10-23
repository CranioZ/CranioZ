"""Errors for the Events facade."""

from __future__ import annotations


class EventFacadeError(Exception):
    """Base of all Events-facade errors."""


class SubscriptionClosed(EventFacadeError):
    """Raised by ``EventSubscription.subscribe`` after ``dispose``.

    Once a scope is disposed, no new subscriptions may be made through
    it. The caller must open a new scope.
    """


class EventPublicationError(EventFacadeError):
    """Raised by ``EventPublisher.publish`` when a subscriber fails.

    The underlying ``EventBus`` collects subscriber exceptions and
    re-raises an ``EventBusError``. The adapter logs it and discards it
    (fire-and-forget). This error is defined for callers that need to
    observe publication failures explicitly (e.g., a strict development
    adapter).
    """
