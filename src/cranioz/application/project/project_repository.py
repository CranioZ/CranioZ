"""ProjectRepository — persistence port for the Project subsystem.

`ProjectRepository` is a Protocol. It defines the persistence operations
the Project Manager relies on, without committing to filesystem, database,
or remote storage. Concrete adapters live in `infrastructure/` (e.g.
`FilesystemProjectRepository`) or in the application layer for test
doubles (e.g. `InMemoryProjectRepository`).

Design rules (see `project.md` §12):

- The repository is *not* the lifecycle authority. It does not decide
  whether a project should be created, opened, or deleted. It performs
  the operation and reports success or failure.
- The repository does not validate domain invariants. `Project` is
  already a valid domain aggregate when it reaches the repository.
- The repository does not publish events. Events belong to the
  Project Manager, which coordinates lifecycle transitions.
- The repository translates infrastructure failures into the
  `ProjectRepositoryError` family. Callers never see `OSError`,
  `FileNotFoundError`, or JSON `DecodeError`.
- `list_metadata` returns `ProjectSummary`, not `Project`. This is
  the read model used by the Home Page (`project.md` §5, §7): it
  must not load clinical data.
- `exists` is a cheap, side-effect-free probe. The Project Manager
  uses it to detect races before `create`.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from cranioz.domain.project.project import Project
from cranioz.domain.project.project_id import ProjectId
from cranioz.domain.project.project_summary import ProjectSummary


@runtime_checkable
class ProjectRepository(Protocol):
    """Persistence port for the Project subsystem.

    Implementations must raise the errors from
    `cranioz.application.project.project_errors` for every documented
    failure mode. They must not raise `KeyError`, `ValueError`, or any
    `OSError` to the caller.
    """

    def create(self, project: Project) -> None:
        """Persist a new project.

        Raises:
            ProjectAlreadyExists: a project with the same `project_id`
                is already persisted. The repository does not overwrite.
            ProjectStorageError: the underlying storage rejected the
                operation (permissions, disk full, I/O error, ...).
        """
        ...

    def get(self, project_id: ProjectId) -> Project:
        """Load and return a project by id.

        Raises:
            ProjectNotFound: no project with the given id is persisted.
            ProjectCorrupted: the persisted representation cannot be
                loaded as a valid `Project`.
            ProjectStorageError: the underlying storage failed while
                reading (permissions, I/O error, ...).
        """
        ...

    def update(self, project: Project) -> None:
        """Replace the persisted representation of an existing project.

        The `project.project_id` is the key. The repository does not
        create a project through `update`; it requires the project to
        already exist.

        Raises:
            ProjectNotFound: no project with the given id is persisted.
            ProjectStorageError: the underlying storage rejected the
                operation.
        """
        ...

    def delete(self, project_id: ProjectId) -> None:
        """Remove a project and its persisted representation.

        The operation is idempotent only at the *documented* level: the
        repository may raise `ProjectNotFound` if the project does not
        exist. Callers that want idempotency check `exists` first. This
        distinction lets the Project Manager distinguish "deleted now"
        from "already gone" when coordinating lifecycle events.

        Raises:
            ProjectNotFound: no project with the given id is persisted.
            ProjectStorageError: the underlying storage rejected the
                operation.
        """
        ...

    def exists(self, project_id: ProjectId) -> bool:
        """Return True if a project with the given id is persisted.

        A cheap, side-effect-free probe. Never raises for a missing
        project; that is the point. May raise `ProjectStorageError`
        if the underlying storage cannot be queried at all (e.g. the
        projects root is inaccessible).
        """
        ...

    def list_metadata(self) -> tuple[ProjectSummary, ...]:
        """Return lightweight summaries of all persisted projects.

        Returns a read-model projection (`ProjectSummary`), not full
        `Project` aggregates. The Home Page (`project.md` §7) relies
        on this contract: listing projects must not load clinical data.

        The order is unspecified; callers that need a particular order
        sort the tuple themselves. An empty tuple is returned when no
        project is persisted, not an error.

        Raises:
            ProjectStorageError: the underlying storage cannot be
                listed (e.g. the projects root is inaccessible).
        """
        ...

    def list_ids(self) -> tuple[ProjectId, ...]:
        """Return the ids of all persisted projects.

        A cheaper alternative to `list_metadata` for callers that only
        need identity (e.g. a completeness check in the Project
        Manager). Order is unspecified.

        Raises:
            ProjectStorageError: the underlying storage cannot be
                listed.
        """
        ...
