"""Project.

Aggregate root of the Project domain.

A Project is the persistent clinical container of CranioZ. It
references a Patient and holds the metadata, clinical data
references, workflow state, and configuration of one planning case.

This class is deliberately minimal in this piece. It carries the
project's identity and metadata, and it defines the invariant that
the metadata's project_id matches the Project's own project_id. As
more domain concepts are implemented (patient record, workflow
state, object references), they will be added to this aggregate.

The Project is mutable because it is the aggregate root through
which the Project Manager coordinates updates. Individual value
objects (ProjectId, ProjectMetadata) are immutable; the aggregate
is the boundary across which consistency is maintained.

Rules:

- The Project always has a ProjectId and a ProjectMetadata.
- The metadata's project_id must equal the Project's project_id.
- The Project does not know about persistence, filesystem, or Qt.
  Those are responsibilities of the infrastructure and application
  layers.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from cranioz.domain.project.project_id import ProjectId
from cranioz.domain.project.project_metadata import ProjectMetadata


@dataclass
class Project:
    """Aggregate root of the Project domain."""

    project_id: ProjectId
    metadata: ProjectMetadata
    # Extension point: further fields (patient_record, workflow_state,
    # object_references, ...) will be added as they are implemented.
    # Kept as a plain dict for forward compatibility of serialization.
    extras: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.metadata.project_id != self.project_id:
            raise ValueError(
                "metadata.project_id must match project_id "
                f"(metadata={self.metadata.project_id.value!r}, "
                f"project={self.project_id.value!r})"
            )

    def update_metadata(self, new_metadata: ProjectMetadata) -> None:
        """Replace the project's metadata.

        Raises ValueError if the new metadata belongs to a different
        project. This protects the aggregate invariant at every
        update boundary.
        """
        if new_metadata.project_id != self.project_id:
            raise ValueError(
                "cannot replace metadata with one belonging to a "
                f"different project (expected {self.project_id.value!r}, "
                f"got {new_metadata.project_id.value!r})"
            )
        self.metadata = new_metadata

    def __repr__(self) -> str:
        return (
            f"Project(project_id={self.project_id.value!r}, "
            f"name={self.metadata.project_name!r}, "
            f"status={self.metadata.status.value!r})"
        )
