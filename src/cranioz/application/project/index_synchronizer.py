"""ProjectIndexSynchronizer — keeps a ProjectIndex consistent.

This module implements the synchronization mechanism defined by
ADR-0016: an in-memory `ProjectIndex` populated by a repository-backed
bootstrap and invalidated by the lifecycle events published by the
`ProjectManager` (`ProjectCreated`, `ProjectUpdated`, `ProjectDeleted`).

Two classes cooperate:

- `ProjectIndexSynchronizer` owns the event subscriptions, the
  bootstrap, the `rebuild`, and the staleness flag.
- `SynchronizedProjectIndex` wraps a `ProjectIndex` and a
  `ProjectIndexSynchronizer`, calling `ensure_fresh()` before every
  read. The catalog consumes the wrapper, never the synchronizer.

Design rules (ADR-0016 §3, §4):

- Bootstrap ordering: `subscribe` → `repository.list_metadata()` →
  `index.replace_all(...)`, on the same synchronous call stack. No
  event queue while the bootstrap is synchronous.
- Handler error containment: handlers never propagate to the
  `EventBus`. On failure they log at WARNING with `project_id` and
  operation name only (no PHI) and set `_possibly_stale = True`.
- Staleness rule: a query never silently returns data from a stale
  index. `ensure_fresh()` rebuilds when stale; if the rebuild fails,
  it raises `ProjectIndexStaleError`.
- External mutations are not detected automatically. A rebuild or
  restart is required (ADR-0016 §3.2). Background reconciliation is
  deferred to Phase 8.

The synchronizer is not thread-safe. It runs on the main thread,
consistent with `EventBus` and `ProjectManager` (ADR-0016 §7.4).
"""

from __future__ import annotations

import logging
from collections.abc import Iterable

from cranioz.application.event_bus import EventBus
from cranioz.application.project.events import (
    ProjectCreated,
    ProjectDeleted,
    ProjectUpdated,
)
from cranioz.application.project.index import (
    ProjectIndex,
    ProjectIndexStaleError,
)
from cranioz.application.project.repository import ProjectRepository
from cranioz.domain.project.project_id import ProjectId
from cranioz.domain.project.project_summary import ProjectSummary

_logger = logging.getLogger(__name__)


class ProjectIndexSynchronizer:
    """Maintains a `ProjectIndex` consistent with the repository.

    The synchronizer is the only component that subscribes to the
    project lifecycle events. It runs on the main thread, consistent
    with `EventBus` and `ProjectManager` (ADR-0016 §7.4).
    """

    def __init__(
        self,
        index: ProjectIndex,
        repository: ProjectRepository,
        event_bus: EventBus,
    ) -> None:
        self._index = index
        self._repository = repository
        self._event_bus = event_bus
        self._possibly_stale = False
        self._started = False

    # ----- Lifecycle ------------------------------------------------

    def start(self) -> None:
        """Subscribe to lifecycle events and bootstrap the index.

        The ordering is deliberate and synchronous (ADR-0016 §4):

            1. subscribe to ProjectCreated/Updated/Deleted
            2. summaries = repository.list_metadata()
            3. index.replace_all(summaries)

        No event can be published between (1) and (3) because
        `EventBus.publish` is synchronous and single-threaded, and
        `start()` does not yield control between the steps.

        Calling `start` twice is a programming error: it would
        subscribe the handlers twice. Raise.
        """
        if self._started:
            raise RuntimeError("ProjectIndexSynchronizer.start() called twice")
        self._started = True

        self._event_bus.subscribe(ProjectCreated, self._on_created)
        self._event_bus.subscribe(ProjectUpdated, self._on_updated)
        self._event_bus.subscribe(ProjectDeleted, self._on_deleted)

        self._bootstrap()

    # ----- Staleness ------------------------------------------------

    def ensure_fresh(self) -> None:
        """Rebuild the index if it is possibly stale.

        Called by `SynchronizedProjectIndex` before every read. A
        no-op when the index is considered fresh. If a rebuild is
        needed and fails, `ProjectIndexStaleError` is raised so the
        caller does not silently observe stale data (ADR-0016 §3.3).
        """
        if not self._possibly_stale:
            return
        try:
            self._bootstrap()
        except Exception as exc:
            _logger.warning(
                "project index rebuild failed; raising ProjectIndexStaleError",
                exc_info=True,
            )
            raise ProjectIndexStaleError("project index is stale and the rebuild failed") from exc

    def rebuild(self) -> None:
        """Force a rebuild from the repository.

        Equivalent to the bootstrap: read `list_metadata()` and
        `replace_all`. Used by external callers (e.g. a future
        "Refresh" action) and by tests.
        """
        self._bootstrap()

    # ----- Handlers -------------------------------------------------

    def _on_created(self, event: ProjectCreated) -> None:
        try:
            summary = ProjectSummary.from_metadata(event.metadata)
            self._index.add(summary)
        except Exception:
            self._mark_stale("create", event.project_id)

    def _on_updated(self, event: ProjectUpdated) -> None:
        try:
            summary = ProjectSummary.from_metadata(event.metadata)
            self._index.add(summary)  # idempotent upsert
        except Exception:
            self._mark_stale("update", event.project_id)

    def _on_deleted(self, event: ProjectDeleted) -> None:
        try:
            self._index.remove(event.project_id)
        except Exception:
            self._mark_stale("delete", event.project_id)

    # ----- Internals ------------------------------------------------

    def _bootstrap(self) -> None:
        try:
            summaries: Iterable[ProjectSummary] = self._repository.list_metadata()
            self._index.replace_all(summaries)
        except Exception:
            # Bootstrap failure is itself a staleness condition: the
            # index may be empty, partial, or hold a previous state.
            # Callers that rely on `ensure_fresh()` will be informed
            # on the next read. Log without PHI.
            self._possibly_stale = True
            _logger.warning("project index bootstrap failed", exc_info=True)
            raise
        self._possibly_stale = False

    def _mark_stale(self, operation: str, project_id: ProjectId) -> None:
        """Record a handler failure without leaking PHI.

        Logs only the `project_id` and the operation name, never the
        project or patient display name (ADR-0016 §3.4, §7.5;
        project.md §28).
        """
        self._possibly_stale = True
        _logger.warning(
            "project index handler failed (operation=%s, project_id=%s)",
            operation,
            project_id.value,
            exc_info=True,
        )


class SynchronizedProjectIndex:
    """`ProjectIndex` decorator that ensures freshness before reads.

    The catalog consumes this wrapper. Writes (`add`, `remove`,
    `replace_all`) are delegated directly to the underlying index;
    freshness is checked only before reads, because writes are the
    mechanism that keeps the index current.
    """

    def __init__(
        self,
        index: ProjectIndex,
        synchronizer: ProjectIndexSynchronizer,
    ) -> None:
        self._index = index
        self._synchronizer = synchronizer

    # ----- Reads (freshness-checked) --------------------------------

    def lookup(self, project_id: ProjectId) -> ProjectSummary | None:
        self._synchronizer.ensure_fresh()
        return self._index.lookup(project_id)

    def list_summaries(self) -> tuple[ProjectSummary, ...]:
        self._synchronizer.ensure_fresh()
        return self._index.list_summaries()

    def list_ids(self) -> tuple[ProjectId, ...]:
        self._synchronizer.ensure_fresh()
        return self._index.list_ids()

    def count(self) -> int:
        self._synchronizer.ensure_fresh()
        return self._index.count()

    def contains(self, project_id: ProjectId) -> bool:
        self._synchronizer.ensure_fresh()
        return self._index.contains(project_id)

    # ----- Writes (delegated) ---------------------------------------

    def add(self, summary: ProjectSummary) -> None:
        self._index.add(summary)

    def remove(self, project_id: ProjectId) -> None:
        self._index.remove(project_id)

    def replace_all(self, summaries: Iterable[ProjectSummary]) -> None:
        self._index.replace_all(summaries)
