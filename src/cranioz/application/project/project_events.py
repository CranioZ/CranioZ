"""Project lifecycle events.

These events communicate state changes that have *already happened*.
They are published by the Project Manager (Peça 7.5) after a successful
repository operation, via the EventBus. The events themselves are pure
data; this module does not publish, subscribe, or route anything.

Design rules (see `project.md` §22, `overview.md` §13):

- Events are **facts**, not intents. "ProjectOpened" means the project
  is open. If a caller sees this event, it does not need to check.
- Events are **frozen**. Observers must not mutate them.
- Events are **not commands**. The fact that a project was deleted does
  not mean an observer may now act; that is a separate concern.
- Every event carries the `project_id` it refers to. This is the
  minimum contract every observer relies on.
- Events carry **payload specific to their lifecycle moment**:
  `ProjectCreated` carries the initial metadata; `ProjectUpdated` carries
  the new metadata; `ProjectOpened` carries the `ProjectContext`
  (the Workspace needs it); `ProjectClosed` carries nothing extra (the
  context is discarded by the Workspace, not carried in the event).

The event bus is not imported here. The publication mechanism is the
Project Manager's concern.
"""

from __future__ import annotations

from dataclasses import dataclass

from cranioz.application.project.project_context import ProjectContext
from cranioz.domain.project.project_id import ProjectId
from cranioz.domain.project.project_metadata import ProjectMetadata


@dataclass(frozen=True)
class ProjectCreated:
    """A new project has been persisted.

    Carries the metadata with which the project was created. Observers
    (e.g. the Project Catalog, Peça 7.4) can update their read model
    without re-fetching from the repository.
    """

    project_id: ProjectId
    metadata: ProjectMetadata


@dataclass(frozen=True)
class ProjectOpened:
    """A project has been opened and a runtime context created.

    Carries the `ProjectContext` that the Workspace will consume. The
    event itself is published *after* the context is built, so
    observers can rely on its completeness.
    """

    project_id: ProjectId
    context: ProjectContext


@dataclass(frozen=True)
class ProjectUpdated:
    """A project's metadata or state has changed.

    Carries the *new* metadata. The previous metadata is not carried;
    observers that need the previous value must have cached it, which
    is not a supported pattern. Observers see the current state.
    """

    project_id: ProjectId
    metadata: ProjectMetadata


@dataclass(frozen=True)
class ProjectClosing:
    """A project is about to close, but has not closed yet.

    Published **before** pending state is persisted and before the
    context is discarded. Observers that need to react while the
    context is still active (e.g. autosave flush) subscribe to this
    event, not `ProjectClosed`.
    """

    project_id: ProjectId


@dataclass(frozen=True)
class ProjectClosed:
    """A project has closed and its runtime context is discarded.

    Published **after** the context has been released. Observers that
    held a reference to the context must not use it after this event.
    The project remains persisted and discoverable; only the runtime
    state is gone.
    """

    project_id: ProjectId


@dataclass(frozen=True)
class ProjectDeleted:
    """A project has been deleted from persistent storage.

    Published **after** the repository confirms the deletion. The
    project is no longer discoverable. Observers (Catalog, Home Page,
    recent-projects list) must remove it from their view.
    """

    project_id: ProjectId
