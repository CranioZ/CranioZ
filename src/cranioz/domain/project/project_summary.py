"""ProjectSummary.

Read-only projection of a Project used for discovery.

The ProjectSummary is a *lightweight* representation designed for
listing and searching. It contains only the fields the Home Page
needs to render a project card or a row in a table. It deliberately
excludes clinical data, workflow state, and any large payload.

The summary is a value object. It is not the Project and it does not
carry the Project's full state. It is derived from ProjectMetadata
and can be produced without loading the project's data.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from cranioz.domain.project.project_id import ProjectId
from cranioz.domain.project.project_metadata import ProjectMetadata
from cranioz.domain.project.project_status import ProjectStatus


@dataclass(frozen=True)
class ProjectSummary:
    """Lightweight read-only projection of a Project."""

    project_id: ProjectId
    project_name: str
    patient_display_name: str
    status: ProjectStatus
    procedure: str
    created_at: datetime
    updated_at: datetime
    last_opened_at: datetime | None

    def __post_init__(self) -> None:
        if not self.project_name:
            raise ValueError("project_name must not be empty")
        if not self.patient_display_name:
            raise ValueError("patient_display_name must not be empty")
        if not self.procedure:
            raise ValueError("procedure must not be empty")

    @classmethod
    def from_metadata(cls, metadata: ProjectMetadata) -> ProjectSummary:
        """Build a summary from the project's metadata.

        This is the canonical way to produce a summary: the metadata
        already contains every field the summary needs.
        """
        return cls(
            project_id=metadata.project_id,
            project_name=metadata.project_name,
            patient_display_name=metadata.patient_display_name,
            status=metadata.status,
            procedure=metadata.clinical_procedure,
            created_at=metadata.created_at,
            updated_at=metadata.updated_at,
            last_opened_at=metadata.last_opened_at,
        )
