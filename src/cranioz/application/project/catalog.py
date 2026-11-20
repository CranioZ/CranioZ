"""ProjectCatalog — read-only discovery projection.

The ProjectCatalog is the read model consumed by the Home Page
(project.md §5, §7). It answers "which projects exist and what do
they look like?" without loading clinical data.

Under ADR-0016, the catalog consumes a `ProjectIndex` rather than
querying the `ProjectRepository` directly. The index is maintained
by a `ProjectIndexSynchronizer` and wrapped by a
`SynchronizedProjectIndex`, which guarantees freshness before every
read. The catalog does not know about the synchronizer or the
repository.

Design rules (project.md §5, §7; ADR-0016 §2.1):

- The catalog is read-only. It does not create, modify, delete,
  archive, or restore projects.
- The catalog is not the source of truth. The repository is. The
  index is a read-optimized projection.
- The catalog does not implement lifecycle policy.
- The catalog does not know about the synchronizer or the
  repository. It depends only on the `ProjectIndex` read contract.
- There is no `refresh()`. Freshness is automatic via
  `SynchronizedProjectIndex.ensure_fresh()`.
"""

from __future__ import annotations

from cranioz.application.project.index import ProjectIndex
from cranioz.domain.project.project_id import ProjectId
from cranioz.domain.project.project_summary import ProjectSummary


class ProjectCatalog:
    """Read-only projection of the projects known to a `ProjectIndex`."""

    def __init__(self, index: ProjectIndex) -> None:
        self._index = index

    # ----- Listing ---------------------------------------------------

    def list_projects(self) -> tuple[ProjectSummary, ...]:
        """Return summaries of all projects known to the index."""
        return self._index.list_summaries()

    # ----- Lookup ----------------------------------------------------

    def get_project_summary(
        self,
        project_id: ProjectId,
    ) -> ProjectSummary | None:
        """Return the summary of a specific project, or None if unknown.

        The catalog does not raise `ProjectNotFound`; it returns
        `None`. For discovery purposes, "not in the catalog" and
        "not persisted" are equivalent.
        """
        return self._index.lookup(project_id)

    # ----- Search ----------------------------------------------------

    def search_projects(self, query: str) -> tuple[ProjectSummary, ...]:
        """Return summaries whose text fields match `query`.

        Case-insensitive substring over `project_name` and
        `patient_display_name`. No regex, no fuzzy, no ranking.
        An empty or whitespace-only query returns all projects.
        """
        normalized = query.strip().lower()
        all_summaries = self._index.list_summaries()
        if not normalized:
            return all_summaries

        matches: list[ProjectSummary] = []
        for summary in all_summaries:
            if (
                normalized in summary.project_name.lower()
                or normalized in summary.patient_display_name.lower()
            ):
                matches.append(summary)
        return tuple(matches)

    # ----- Convenience -----------------------------------------------

    def count(self) -> int:
        """Return the number of projects known to the index."""
        return self._index.count()

    def is_empty(self) -> bool:
        """Return True if the index reports no projects."""
        return self._index.count() == 0

    def contains(self, project_id: ProjectId) -> bool:
        """Return True if a project with the given id is discoverable."""
        return self._index.contains(project_id)
