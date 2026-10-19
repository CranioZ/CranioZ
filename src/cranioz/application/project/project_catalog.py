"""ProjectCatalog — read-only discovery projection.

The ProjectCatalog is the read model consumed by the Home Page
(project.md §5, §7; startup_project_opening_workflow.md §4). It answers
"which projects exist and what do they look like?" without loading
clinical data.

Design rules (see `project.md`):

- The catalog is **read-only**. It does not create, modify, delete,
  archive, or restore projects.
- The catalog is **not the source of truth**. It is a projection of
  what `ProjectRepository.list_metadata()` reports. If the repository
  changes, the next call to the catalog reflects the change; there is
  no cache to invalidate.
- The catalog **does not implement lifecycle policy**. It reports
  what exists. Whether a project is "openable", "in use", or
  "archived per policy" is the Project Manager's concern (piece 7.5).
- The catalog **does not maintain an independent authoritative list**.
  It has no `_projects` attribute. Every call delegates to the
  repository.
- The catalog **does not read from the filesystem or any other I/O**.
  It only consumes the repository, which already translates
  infrastructure failures into the `ProjectRepositoryError` family.

Why no cache in this piece:

The catalog will be called every time the Home Page refreshes. On a
local SSD, reading a few `project.json` files takes microseconds per
project. Premature caching would introduce invalidation bugs (stale
data after `ProjectDeleted`, cache misses during module switch) for
no measured benefit. If future profiling shows the catalog is a hot
path, a cache will be added in a separate piece, explicitly
invalidated by subscribing to `ProjectCreated` / `ProjectUpdated` /
`ProjectDeleted`. Until then: no cache.
"""

from __future__ import annotations

from cranioz.application.project.project_repository import ProjectRepository
from cranioz.domain.project.project_id import ProjectId
from cranioz.domain.project.project_summary import ProjectSummary


class ProjectCatalog:
    """Read-only projection of the projects known to a repository.

    The catalog is the entry point for discovery: listing, searching,
    and looking up project summaries. It is not the entry point for
    lifecycle operations (create/open/close/delete); those belong to
    the Project Manager (piece 7.5).
    """

    def __init__(self, repository: ProjectRepository) -> None:
        self._repository = repository

    # ----- Listing ---------------------------------------------------

    def list_projects(self) -> tuple[ProjectSummary, ...]:
        """Return summaries of all projects known to the repository.

        Order is unspecified. Returns an empty tuple when no project
        exists (not an error). Propagates `ProjectStorageError` if the
        repository cannot list at all.
        """
        return self._repository.list_metadata()

    # ----- Lookup ----------------------------------------------------

    def get_project_summary(
        self,
        project_id: ProjectId,
    ) -> ProjectSummary | None:
        """Return the summary of a specific project, or None if unknown.

        The catalog does **not** raise `ProjectNotFound`. It returns
        `None`. Rationale: for discovery purposes, "not in the catalog"
        and "not persisted" are equivalent — the Home Page shows the
        same empty state either way. Callers that need to distinguish
        "not found" from "storage failure" should query the repository
        directly, or use `ProjectManager.get_project` (piece 7.5),
        which does raise.

        Propagates `ProjectStorageError` if the repository cannot list
        at all (as opposed to "the specific id is not present").
        """
        for summary in self._repository.list_metadata():
            if summary.project_id == project_id:
                return summary
        return None

    # ----- Search ----------------------------------------------------

    def search_projects(self, query: str) -> tuple[ProjectSummary, ...]:
        """Return summaries whose text fields match `query`.

        Matching is **case-insensitive substring** over:
        - `project_name`
        - `patient_display_name`

        No regex. No fuzzy matching. No ranking. `query` is treated as
        a literal substring, after `strip()`. An empty or
        whitespace-only query returns all projects (equivalent to
        `list_projects()`), which is the natural behavior for a
        search-as-you-type input.

        Rationale for no regex: the input comes from a user-facing
        search box. Allowing regex opens a ReDoS surface and is not
        what users expect from a "search" field. If advanced matching
        is ever needed, it will be an explicit `advanced_search`
        method with its own contract.

        Order is unspecified. Returns an empty tuple when nothing
        matches.
        """
        normalized = query.strip().lower()
        all_summaries = self._repository.list_metadata()
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
        """Return the number of projects known to the repository."""
        return len(self._repository.list_metadata())

    def is_empty(self) -> bool:
        """Return True if the repository reports no projects."""
        return len(self._repository.list_metadata()) == 0

    def contains(self, project_id: ProjectId) -> bool:
        """Return True if a project with the given id is discoverable.

        Cheap check; implemented via `get_project_summary`.
        """
        return self.get_project_summary(project_id) is not None
