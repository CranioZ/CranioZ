"""Application-level errors for the Project subsystem.

These errors belong to the Application layer. They are the vocabulary
through which the Project Manager and the UI communicate about project
lifecycle failures. They are intentionally independent of any
infrastructure concept: an `OSError`, a `FileNotFoundError`, or a
JSON `DecodeError` must be translated into one of these errors at the
repository boundary, never propagated as-is.

Design rules (see `project.md` §27):

- Every error derives from `ProjectError`, so callers can catch the
  whole family with one `except`.
- Errors carry enough context to be actionable: the `project_id` that
  failed, and (when known) the underlying cause.
- Errors are not `ValueError` or `KeyError` subclasses. They are a
  separate hierarchy so that callers do not accidentally conflate a
  domain validation error with an application lifecycle error.

Two families live under `ProjectError`:

- `ProjectRepositoryError` and subclasses — persistence failures.
  Raised by repository implementations (filesystem, in-memory).
- `ProjectAccessDenied`, `ProjectInUse` — application decisions.
  Raised by the Project Manager before touching persistence. They are
  not persistence errors and must not be caught as such.
"""

from __future__ import annotations

from cranioz.domain.project.project_id import ProjectId


class ProjectError(Exception):
    """Base of all application-level Project subsystem errors.

    Catching `ProjectError` catches every failure the Project Manager
    can raise. Catching a more specific subclass lets the caller react
    differently to, e.g., "not found" vs "already exists".
    """


# ----- Persistence failures -----------------------------------------


class ProjectRepositoryError(ProjectError):
    """Base of all errors raised by a `ProjectRepository` implementation.

    Repositories raise this family of errors when a persistence operation
    fails for reasons that the repository itself cannot resolve. The
    Project Manager (which coordinates the lifecycle) is responsible for
    translating these into user-facing decisions.
    """

    def __init__(
        self,
        message: str,
        *,
        project_id: ProjectId | None = None,
    ) -> None:
        self.project_id = project_id
        super().__init__(message)


class ProjectNotFound(ProjectRepositoryError):
    """Raised when a requested project does not exist.

    Used by `get` and (with a different policy) by `update` and `delete`.
    The message includes the `project_id` so that logs are diagnosable
    without re-reading the exception attribute.
    """


class ProjectAlreadyExists(ProjectRepositoryError):
    """Raised when `create` is called with an id that already exists.

    Projects are identified by a stable `ProjectId`; creating a second
    project with the same id is a programming error at the application
    level, never a silent overwrite.
    """


class ProjectCorrupted(ProjectRepositoryError):
    """Raised when a project's persisted representation is unreadable.

    Examples: a malformed `project.json`, a missing required file, a
    schema version that cannot be migrated, a conflicting metadata
    file. The repository does not attempt recovery; it reports the
    problem so that the Project Manager can apply the recovery policy.
    """


class ProjectStorageError(ProjectRepositoryError):
    """Raised when the underlying storage rejects an operation.

    Examples: permission denied, disk full, a file locked by another
    process, an I/O error on the network share. The repository wraps
    the underlying `OSError` as `__cause__`; callers that need the
    original exception can inspect `__cause__` explicitly.
    """


# ----- Application decisions ---------------------------------------


class ProjectAccessDenied(ProjectError):
    """Raised when the access policy denies a project operation.

    The operation was not attempted: no state was mutated, no event
    was published. The policy is consulted before any other step, so
    this error means "you were not allowed to ask", not "your request
    was invalid".
    """

    def __init__(
        self,
        message: str,
        *,
        project_id: ProjectId | None = None,
    ) -> None:
        self.project_id = project_id
        super().__init__(message)


class ProjectInUse(ProjectError):
    """Raised when an operation conflicts with an open project.

    The project is currently open (has an active runtime context);
    the caller must close it first. This is a deliberate refusal,
    not an implicit close: closing and deleting are two distinct
    commands with different effects, and mixing them could discard
    a context the user is still using.
    """

    def __init__(
        self,
        message: str,
        *,
        project_id: ProjectId | None = None,
    ) -> None:
        self.project_id = project_id
        super().__init__(message)
