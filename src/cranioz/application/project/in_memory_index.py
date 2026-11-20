"""InMemoryProjectIndex — reference implementation of ProjectIndex.

Backed by a dict. Used by:

- Contract tests (parametrizable for future `SqliteProjectIndex`).
- `ProjectIndexSynchronizer` as the default index during Phase 3.
- Higher-layer tests, where a real index (not a mock) is desired.

Not thread-safe. Runs on the main thread (ADR-0016 §7.4).
"""

from __future__ import annotations

from collections.abc import Iterable

from cranioz.domain.project.project_id import ProjectId
from cranioz.domain.project.project_summary import ProjectSummary


class InMemoryProjectIndex:
    """Reference implementation of `ProjectIndex`, backed by a dict."""

    def __init__(self) -> None:
        self._summaries: dict[ProjectId, ProjectSummary] = {}

    # ----- Writes ---------------------------------------------------

    def add(self, summary: ProjectSummary) -> None:
        self._summaries[summary.project_id] = summary

    def remove(self, project_id: ProjectId) -> None:
        self._summaries.pop(project_id, None)

    def replace_all(self, summaries: Iterable[ProjectSummary]) -> None:
        self._summaries = {s.project_id: s for s in summaries}

    # ----- Reads ----------------------------------------------------

    def lookup(self, project_id: ProjectId) -> ProjectSummary | None:
        return self._summaries.get(project_id)

    def list_summaries(self) -> tuple[ProjectSummary, ...]:
        return tuple(self._summaries.values())

    def list_ids(self) -> tuple[ProjectId, ...]:
        return tuple(self._summaries.keys())

    def count(self) -> int:
        return len(self._summaries)

    def contains(self, project_id: ProjectId) -> bool:
        return project_id in self._summaries
