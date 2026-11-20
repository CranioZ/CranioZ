"""ProjectIndex — read-model port for project discovery.

The `ProjectIndex` is a *pure read model*: it knows nothing about the
repository, the event bus, or the filesystem. It stores `ProjectSummary`
values keyed by `ProjectId` and answers discovery queries in memory.

Synchronization with the authoritative `ProjectRepository` is the
responsibility of `ProjectIndexSynchronizer` (see
`index_synchronizer.py`), not of the index itself. This separation
lets the index be tested in isolation and lets alternative backends
(e.g. SQLite) be swapped in without changing the catalog.

Design rules (ADR-0016 §2.1, §3):

- The index does not know about the repository, the event bus, or
  the filesystem.
- `add` is idempotent: adding a summary whose `project_id` already
  exists replaces the previous value. This makes the handler for
  `ProjectUpdated` a single `add` call.
- `remove` is idempotent: removing a missing id is a no-op.
- `replace_all` is atomic: the previous contents are discarded.
- Reads return immutable tuples.
- The index is not thread-safe. `ProjectIndexSynchronizer` and
  `ProjectManager` both run on the main thread (ADR-0016 §7.4).

`ProjectIndexStaleError` lives here, alongside the Protocol, because
it is a read-model failure specific to the index's freshness contract
(ADR-0016 §3.3, §7). It inherits from `ProjectError` so callers can
catch the whole project subsystem with one `except`.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol, runtime_checkable

from cranioz.application.project.errors import ProjectError
from cranioz.domain.project.project_id import ProjectId
from cranioz.domain.project.project_summary import ProjectSummary


class ProjectIndexStaleError(ProjectError):
    """Raised when the project index cannot be guaranteed fresh.

    The catalog delegates reads to a `ProjectIndex` wrapped by a
    `SynchronizedProjectIndex`, which calls `ensure_fresh()` before
    each read. If the index is detected as stale and the rebuild
    fails (e.g. the repository is temporarily unreadable), the
    synchronized decorator raises this error instead of silently
    returning data from a stale index (ADR-0016 §3.3).

    This is a read-projection failure, not a persistence failure:
    the authoritative repository may still be intact. Callers that
    receive it should treat the catalog as temporarily unavailable
    and retry, not assume project data was lost.

    The error carries no `project_id`: staleness affects the whole
    index, not a single project.
    """


@runtime_checkable
class ProjectIndex(Protocol):
    """In-memory read model of `ProjectSummary` values.

    Implementations must be idempotent for `add` and `remove`, and
    atomic for `replace_all`. See ADR-0016 §2.1.
    """

    def add(self, summary: ProjectSummary) -> None:
        """Insert or replace a summary.

        If a summary with the same `project_id` already exists, it
        is replaced. This is the mechanism through which
        `ProjectUpdated` events are reflected in the index.
        """
        ...

    def remove(self, project_id: ProjectId) -> None:
        """Remove a summary. No-op if the id is not present."""
        ...

    def lookup(self, project_id: ProjectId) -> ProjectSummary | None:
        """Return the summary for `project_id`, or `None`."""
        ...

    def list_summaries(self) -> tuple[ProjectSummary, ...]:
        """Return all summaries. Order is unspecified."""
        ...

    def list_ids(self) -> tuple[ProjectId, ...]:
        """Return all ids. Order is unspecified."""
        ...

    def count(self) -> int:
        """Return the number of summaries in the index."""
        ...

    def contains(self, project_id: ProjectId) -> bool:
        """Return `True` if the id is present."""
        ...

    def replace_all(self, summaries: Iterable[ProjectSummary]) -> None:
        """Replace the entire contents with `summaries`.

        The previous contents are discarded atomically: a summary not
        present in `summaries` is not present after the call.
        """
        ...
