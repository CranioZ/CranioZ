"""ProjectContext — immutable initialization snapshot.

The ProjectContext is created when the Project Manager opens a
project (Peça 7.5). It is the runtime representation handed to the
Workspace: everything the Workspace needs to know about the active
project, and nothing more.

Design rules (see `project.md` §17, `startup_project_opening_workflow.md` §9):

- The context is **frozen**. The Workspace must never mutate it.
- The context is **not** the Project. It does not own the project's
  lifecycle; the Project Manager does. Discarding the context does not
  discard the project.
- The context carries **no service locator**. Services (ProjectManager,
  Repository, EventBus, ...) are injected via dependency injection by
  the bootstrap, not resolved through the context. The note in
  `project.md` §17 is explicit: the context is data, not a registry.
- The context carries **no physical paths**. Logical references only
  (`project_id`, `workflow_id`); physical path resolution belongs to
  `ProjectPathResolver` at the infrastructure boundary.
- `workflow_id` and `workflow_config` are optional. A project may be
  opened before a clinical workflow is selected
  (`startup_project_opening_workflow.md` §10: "If no flow is resolved,
  the Workspace opens in flow selection mode"). The two are either
  both set or both `None` — a workflow id without a config is
  meaningless.
- `object_references` is a tuple, not a list. Immutability is
  structural, not just by convention.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from cranioz.domain.patient.patient_summary import PatientSummary
from cranioz.domain.project.project_id import ProjectId
from cranioz.domain.project.project_metadata import ProjectMetadata


@dataclass(frozen=True)
class ObjectReference:
    """A logical reference to a domain object visible to the Workspace.

    The context does not carry the object itself; it carries enough
    to *identify* it. Resolution to the live object happens through
    the Project's `DomainObjectStore` (see `scene.md` §4), which is
    not part of the context.
    """

    object_id: str
    kind: str
    display_name: str

    def __post_init__(self) -> None:
        if not self.object_id:
            raise ValueError("object_id must not be empty")
        if not self.kind:
            raise ValueError("kind must not be empty")
        if not self.display_name:
            raise ValueError("display_name must not be empty")


@dataclass(frozen=True)
class ProjectContext:
    """Immutable snapshot handed to the Workspace when a project opens.

    Every field is a plain domain value. No service, no callable, no
    physical path. The Workspace consumes it; it does not mutate it and
    it does not fetch anything the context does not carry.
    """

    project_id: ProjectId
    metadata: ProjectMetadata
    patient_summary: PatientSummary
    workflow_id: str | None = None
    workflow_config: dict[str, Any] | None = None
    object_references: tuple[ObjectReference, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.metadata.project_id != self.project_id:
            raise ValueError(
                "metadata.project_id must match project_id "
                f"(metadata={self.metadata.project_id.value!r}, "
                f"context={self.project_id.value!r})"
            )

        if (self.workflow_id is None) != (self.workflow_config is None):
            raise ValueError("workflow_id and workflow_config must be set together or both be None")

    def has_workflow(self) -> bool:
        """Return True if a clinical workflow has been selected."""
        return self.workflow_id is not None

    def with_workflow(
        self,
        workflow_id: str,
        workflow_config: dict[str, Any],
    ) -> ProjectContext:
        """Return a new context with the workflow attached."""
        if not workflow_id:
            raise ValueError("workflow_id must not be empty")
        return ProjectContext(
            project_id=self.project_id,
            metadata=self.metadata,
            patient_summary=self.patient_summary,
            workflow_id=workflow_id,
            workflow_config=dict(workflow_config),
            object_references=self.object_references,
        )

    def with_object_references(
        self,
        object_references: tuple[ObjectReference, ...],
    ) -> ProjectContext:
        """Return a new context with different object references."""
        return ProjectContext(
            project_id=self.project_id,
            metadata=self.metadata,
            patient_summary=self.patient_summary,
            workflow_id=self.workflow_id,
            workflow_config=dict(self.workflow_config) if self.workflow_config else None,
            object_references=object_references,
        )
