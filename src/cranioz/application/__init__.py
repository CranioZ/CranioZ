"""Project subsystem — application layer.

Public API of the Project management subsystem:

- `ProjectRepository` — persistence port (Protocol).
- `InMemoryProjectRepository` — reference implementation, test-only.
- The `ProjectRepositoryError` family — application-level errors.

Infrastructure adapters (e.g. `FilesystemProjectRepository`) live in
`cranioz.infrastructure.project` and are imported by the bootstrap,
not by this package.
"""

from cranioz.application.project.in_memory_project_repository import (
    InMemoryProjectRepository,
)
from cranioz.application.project.project_errors import (
    ProjectAlreadyExists,
    ProjectCorrupted,
    ProjectError,
    ProjectNotFound,
    ProjectRepositoryError,
    ProjectStorageError,
)
from cranioz.application.project.project_repository import ProjectRepository

__all__ = [
    "InMemoryProjectRepository",
    "ProjectAlreadyExists",
    "ProjectCorrupted",
    "ProjectError",
    "ProjectNotFound",
    "ProjectRepository",
    "ProjectRepositoryError",
    "ProjectStorageError",
]
