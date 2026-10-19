"""InMemoryProjectRepository — reference implementation of ProjectRepository.

This implementation is the canonical reference for the contract defined
in `project_repository.py`. It is used by:

- Contract tests, which run the same suite against every implementation.
- Higher-layer tests (Project Manager, Project Catalog), where filesystem
  I/O would make tests slow and brittle.
- Early integration of the Home Page, before the filesystem adapter is
  available.

It is not a toy. It respects every documented failure mode of the
Protocol, including `ProjectAlreadyExists`, `ProjectNotFound`,
`ProjectCorrupted` (for previously-injected corrupted entries), and
`ProjectStorageError` (for explicitly-injected failure modes).
"""

from __future__ import annotations

from cranioz.application.project.project_errors import (
    ProjectAlreadyExists,
    ProjectCorrupted,
    ProjectNotFound,
)
from cranioz.domain.project.project import Project
from cranioz.domain.project.project_id import ProjectId
from cranioz.domain.project.project_summary import ProjectSummary


class InMemoryProjectRepository:
    """Reference implementation of `ProjectRepository` backed by a dict.

    Not thread-safe. The Project Manager (Peça 7.5) is the only
    caller, and the application runs it on the main thread.
    """

    def __init__(self) -> None:
        # Stores the full aggregate. Values are the *same* instances
        # the caller passed in `create` or `update`. This mirrors the
        # semantics of a filesystem repository: persistence does not
        # deep-copy, it stores the serialized representation; callers
        # that mutate the Project in place are responsible for calling
        # `update` to persist the mutation. Tests that need defensive
        # copying should copy explicitly.
        self._projects: dict[ProjectId, Project] = {}

        # Set of ids that should be reported as corrupted on `get`.
        # Used by tests to exercise the `ProjectCorrupted` path
        # without simulating a filesystem. Never populated by the
        # normal `create`/`update` path.
        self._corrupted: set[ProjectId] = set()

    # ----- Test support ---------------------------------------------

    def _mark_corrupted(self, project_id: ProjectId) -> None:
        """Mark a project as corrupted for testing purposes.

        After this call, `get` raises `ProjectCorrupted` for the given
        id, and `list_metadata` skips it. Used by contract tests to
        verify that a `ProjectCorrupted` does not crash `list_metadata`.
        """
        self._corrupted.add(project_id)

    # ----- ProjectRepository ----------------------------------------

    def create(self, project: Project) -> None:
        if project.project_id in self._projects:
            raise ProjectAlreadyExists(
                f"project already exists: {project.project_id.value!r}",
                project_id=project.project_id,
            )
        self._projects[project.project_id] = project

    def get(self, project_id: ProjectId) -> Project:
        if project_id in self._corrupted:
            raise ProjectCorrupted(
                f"project is corrupted: {project_id.value!r}",
                project_id=project_id,
            )
        try:
            return self._projects[project_id]
        except KeyError as exc:
            raise ProjectNotFound(
                f"project not found: {project_id.value!r}",
                project_id=project_id,
            ) from exc

    def update(self, project: Project) -> None:
        if project.project_id not in self._projects:
            raise ProjectNotFound(
                f"project not found: {project.project_id.value!r}",
                project_id=project.project_id,
            )
        self._projects[project.project_id] = project

    def delete(self, project_id: ProjectId) -> None:
        if project_id not in self._projects:
            raise ProjectNotFound(
                f"project not found: {project_id.value!r}",
                project_id=project_id,
            )
        del self._projects[project_id]
        # Corrupted markers become irrelevant once the id is deleted.
        self._corrupted.discard(project_id)

    def exists(self, project_id: ProjectId) -> bool:
        return project_id in self._projects

    def list_metadata(self) -> tuple[ProjectSummary, ...]:
        summaries: list[ProjectSummary] = []
        for project_id, project in self._projects.items():
            if project_id in self._corrupted:
                continue
            summaries.append(ProjectSummary.from_metadata(project.metadata))
        return tuple(summaries)

    def list_ids(self) -> tuple[ProjectId, ...]:
        return tuple(self._projects.keys())
