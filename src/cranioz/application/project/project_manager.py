"""ProjectManager — single authority for project lifecycle.

The Project Manager is the only component allowed to create, open,
update, close, or delete a project (project.md §4, §25). It
coordinates:

- `ProjectRepository` (piece 7.3): persistence.
- `ProjectCatalog` (piece 7.4): not consulted directly. The catalog
  is a pure projection; it reflects the repository on every call.
  The Manager does not need to invalidate or refresh it.
- `EventBus`: lifecycle event publication (piece 7.2 vocabulary).
- `ProjectAccessPolicy`: authorization, evaluated before mutating
  state.

Design rules (see `project.md` §4, §16, §17, §21, §22, §25):

- The Manager is **not thread-safe**. It runs on the application's
  main thread. Concurrency is a separate concern (project.md §26,
  pending ADR); this piece does not introduce locks.
- The Manager does **not** access the filesystem directly. Every
  persistence operation goes through the repository, which
  translates infrastructure failures into the
  `ProjectRepositoryError` family.
- The Manager **does not build ProjectContext from a patient
  registry**. The context's `PatientSummary` is a projection of
  the project's own metadata (`patient_id`, `patient_display_name`);
  `birth_date` and `sex` are left as `None` because the project
  does not carry them. This keeps `open_project` self-contained
  (no dependency on a patient repository), and documents that the
  context is not a clinical record.
- The Manager **publishes events only after a successful
  mutation**. If the repository raises, no event is published.
  This is the transaction boundary (project.md §10, §13).
- `delete_project` on an open project raises `ProjectInUse`
  **before** touching state or publishing events. Closing
  implicitly would mix two distinct commands and could discard a
  context the user is still using. The caller must close first,
  then delete.
- `close_project` on a non-open project is a **silent no-op** (no
  events published). Closing is idempotent; a second close is not
  an error.

Active contexts:

The Manager holds a dict `{ProjectId: ProjectContext}` for the
currently open projects. In this piece, at most one project is
open at a time in practice (the Workspace is single-context), but
the Manager does not enforce that — the enforcement is a
Workspace/Application policy decision (project.md §21). If a
second `open_project` is called while another is open, both remain
open in the Manager; the caller decides which to close. This
matches `project.md` §21 ("Whether another project can be opened
before the current project is closed is an application/session
policy and should not be implemented independently by the Home
Page").
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from cranioz.application.event_bus import EventBus
from cranioz.application.project.project_access_policy import (
    Actor,
    ProjectAccessPolicy,
)
from cranioz.application.project.project_context import ProjectContext
from cranioz.application.project.project_errors import (
    ProjectAccessDenied,
    ProjectInUse,
)
from cranioz.application.project.project_events import (
    ProjectClosed,
    ProjectClosing,
    ProjectCreated,
    ProjectDeleted,
    ProjectOpened,
    ProjectUpdated,
)
from cranioz.application.project.project_repository import ProjectRepository
from cranioz.domain.patient.patient_summary import PatientSummary
from cranioz.domain.patient.value_objects.patient_id import PatientId
from cranioz.domain.project.project import Project
from cranioz.domain.project.project_id import ProjectId
from cranioz.domain.project.project_metadata import ProjectMetadata
from cranioz.domain.project.project_status import ProjectStatus


class ProjectManager:
    """Single authority for the project lifecycle."""

    def __init__(
        self,
        repository: ProjectRepository,
        event_bus: EventBus,
        access_policy: ProjectAccessPolicy,
    ) -> None:
        self._repository = repository
        self._event_bus = event_bus
        self._access_policy = access_policy
        self._active_contexts: dict[ProjectId, ProjectContext] = {}

    # ----- Create ----------------------------------------------------

    def create_project(
        self,
        actor: Actor,
        *,
        project_id: ProjectId,
        project_name: str,
        patient_id: PatientId,
        patient_display_name: str,
        clinical_procedure: str,
        status: ProjectStatus = ProjectStatus.DRAFT,
    ) -> Project:
        """Create, persist, and publish a new project.

        Raises:
            ProjectAccessDenied: the policy denies the operation.
            ProjectAlreadyExists: the project id is already persisted.
            ProjectStorageError: the repository cannot persist.
        """
        if not self._access_policy.can_create(actor):
            raise ProjectAccessDenied(f"actor {actor!r} is not allowed to create projects")

        now = _now()
        metadata = ProjectMetadata(
            project_id=project_id,
            project_name=project_name,
            patient_id=patient_id.value,
            patient_display_name=patient_display_name,
            clinical_procedure=clinical_procedure,
            status=status,
            created_at=now,
            updated_at=now,
            last_opened_at=None,
            schema_version=1,
        )
        project = Project(project_id=project_id, metadata=metadata)

        self._repository.create(project)
        self._event_bus.publish(ProjectCreated(project_id=project.project_id, metadata=metadata))
        return project

    # ----- Open ------------------------------------------------------

    def open_project(
        self,
        actor: Actor,
        project_id: ProjectId,
        *,
        workflow_id: str | None = None,
        workflow_config: dict[str, Any] | None = None,
    ) -> ProjectContext:
        """Load a project, build its context, and publish ProjectOpened.

        If the project is already open, returns the existing context
        unchanged and does not publish a second ProjectOpened.

        Raises:
            ProjectAccessDenied: the policy denies the operation.
            ProjectNotFound: the project is not persisted.
            ProjectCorrupted: the persisted form is unreadable.
            ProjectStorageError: the repository cannot read.
        """
        if not self._access_policy.can_open(actor, project_id):
            raise ProjectAccessDenied(
                f"actor {actor!r} is not allowed to open {project_id.value!r}"
            )

        existing = self._active_contexts.get(project_id)
        if existing is not None:
            return existing

        project = self._repository.get(project_id)

        now = _now()
        updated_metadata = project.metadata.with_last_opened(now=now)
        updated_project = Project(
            project_id=project.project_id,
            metadata=updated_metadata,
        )
        self._repository.update(updated_project)

        context = self._build_context(
            updated_project,
            workflow_id=workflow_id,
            workflow_config=workflow_config,
        )
        self._active_contexts[project_id] = context

        self._event_bus.publish(ProjectOpened(project_id=project_id, context=context))
        return context

    # ----- Update ----------------------------------------------------

    def update_project(self, actor: Actor, project: Project) -> None:
        """Persist an updated project and publish ProjectUpdated.

        Raises:
            ProjectAccessDenied: the policy denies the operation.
            ProjectNotFound: the project is not persisted.
            ProjectStorageError: the repository cannot persist.
        """
        if not self._access_policy.can_update(actor, project.project_id):
            raise ProjectAccessDenied(
                f"actor {actor!r} is not allowed to update {project.project_id.value!r}"
            )

        self._repository.update(project)
        self._event_bus.publish(
            ProjectUpdated(
                project_id=project.project_id,
                metadata=project.metadata,
            )
        )

    # ----- Close -----------------------------------------------------

    def close_project(self, actor: Actor, project_id: ProjectId) -> None:
        """Close an open project. No-op if the project is not open.

        Publishes ProjectClosing before releasing the context, then
        ProjectClosed after. Does not touch persistence: the project's
        persisted metadata is not modified by close (last_opened_at
        was already updated at open time).

        Close does not need an access check: closing a project you
        opened is always allowed. The actor parameter is accepted for
        symmetry and future auditing.
        """
        del actor  # explicitly unused; close needs no authorization
        if project_id not in self._active_contexts:
            return  # silent no-op; close is idempotent

        self._event_bus.publish(ProjectClosing(project_id=project_id))
        del self._active_contexts[project_id]
        self._event_bus.publish(ProjectClosed(project_id=project_id))

    # ----- Delete ----------------------------------------------------

    def delete_project(self, actor: Actor, project_id: ProjectId) -> None:
        """Delete a persisted project and publish ProjectDeleted.

        Raises:
            ProjectAccessDenied: the policy denies the operation.
            ProjectInUse: the project is currently open. Close it
                first. This is a deliberate refusal: closing
                implicitly would mix two distinct commands and could
                discard a context the user is still using.
            ProjectNotFound: the project is not persisted.
            ProjectStorageError: the repository cannot delete.
        """
        if not self._access_policy.can_delete(actor, project_id):
            raise ProjectAccessDenied(
                f"actor {actor!r} is not allowed to delete {project_id.value!r}"
            )

        if project_id in self._active_contexts:
            raise ProjectInUse(f"cannot delete open project {project_id.value!r}; close it first")

        self._repository.delete(project_id)
        self._event_bus.publish(ProjectDeleted(project_id=project_id))

    # ----- Active context --------------------------------------------

    def get_active_context(
        self,
        project_id: ProjectId,
    ) -> ProjectContext | None:
        """Return the runtime context if the project is open, else None."""
        return self._active_contexts.get(project_id)

    def is_open(self, project_id: ProjectId) -> bool:
        """Return True if the project currently has an active context."""
        return project_id in self._active_contexts

    # ----- Internals -------------------------------------------------

    def _build_context(
        self,
        project: Project,
        *,
        workflow_id: str | None,
        workflow_config: dict[str, Any] | None,
    ) -> ProjectContext:
        """Build the runtime context from the project's own data.

        The PatientSummary carried by the context is a **projection
        of the project metadata**, not a fresh read from a patient
        registry. Fields derived:

        - patient_id           <- metadata.patient_id
        - display_name         <- metadata.patient_display_name
        - birth_date           <- None (not carried by the project)
        - sex                  <- None (not carried by the project)

        Rationale: opening a project must be self-contained.
        Requiring a patient repository at open time would introduce a
        dependency on the patient registry, with availability and
        consistency concerns that belong to a different flow. The
        Workspace consumes the context for the project; if it later
        needs fresh patient data, that is a separate query against a
        dedicated patient provider, not part of `open_project`.
        """
        patient_summary = PatientSummary(
            patient_id=PatientId(project.metadata.patient_id),
            display_name=project.metadata.patient_display_name,
            birth_date=None,
            sex=None,
        )
        return ProjectContext(
            project_id=project.project_id,
            metadata=project.metadata,
            patient_summary=patient_summary,
            workflow_id=workflow_id,
            workflow_config=workflow_config,
        )


# ----- Internals -----------------------------------------------------


def _now() -> datetime:
    """Current UTC time. Isolated so tests can monkeypatch it."""
    return datetime.now(tz=UTC)
