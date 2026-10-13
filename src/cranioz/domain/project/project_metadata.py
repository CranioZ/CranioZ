"""ProjectMetadata.

Persistent metadata of a Project. This is the lightweight
information that describes *what* the project is without loading
its clinical data.

The metadata is used by:

- The Project Catalog, to render project lists without loading the
  full project.
- The Project Manager, to reason about the project's status,
  schema version, and lifecycle.
- The Project Repository, as the top-level structure that describes
  the persistent representation.

The metadata is immutable. Updates produce a new instance; the
Project Manager is responsible for coordinating those updates and
for persisting them through the repository.

Timestamps use timezone-aware datetime objects in UTC. The domain
does not concern itself with serialization; the infrastructure
layer is responsible for converting to and from ISO 8601.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime

from cranioz.domain.project.project_id import ProjectId
from cranioz.domain.project.project_status import ProjectStatus


@dataclass(frozen=True)
class ProjectMetadata:
    """Persistent metadata of a Project."""

    project_id: ProjectId
    project_name: str
    patient_id: str
    patient_display_name: str
    clinical_procedure: str
    status: ProjectStatus
    created_at: datetime
    updated_at: datetime
    last_opened_at: datetime | None
    schema_version: int

    def __post_init__(self) -> None:
        if not self.project_name:
            raise ValueError("project_name must not be empty")
        if not self.patient_id:
            raise ValueError("patient_id must not be empty")
        if not self.patient_display_name:
            raise ValueError("patient_display_name must not be empty")
        if self.schema_version < 1:
            raise ValueError(
                f"schema_version must be >= 1, got {self.schema_version}"
            )

        # Validate timezone-awareness BEFORE comparing datetimes.
        # Comparing a naive and an aware datetime raises TypeError
        # in Python; we want a clear ValueError instead.
        self._validate_timezone(self.created_at, "created_at")
        self._validate_timezone(self.updated_at, "updated_at")
        if self.last_opened_at is not None:
            self._validate_timezone(self.last_opened_at, "last_opened_at")

        if self.updated_at < self.created_at:
            raise ValueError(
                "updated_at must not be earlier than created_at"
            )
        if self.last_opened_at is not None and self.last_opened_at < self.created_at:
            raise ValueError(
                "last_opened_at must not be earlier than created_at"
            )

    @staticmethod
    def _validate_timezone(value: datetime, field_name: str) -> None:
        if value.tzinfo is None:
            raise ValueError(
                f"{field_name} must be timezone-aware (UTC)"
            )

    # ----- Convenience mutators -------------------------------------

    def with_status(
            self,
            status: ProjectStatus,
            *,
            now: datetime,
    ) -> ProjectMetadata:
        ...
        """Return a new metadata with the given status.

        ``now`` becomes the new ``updated_at``. The caller is
        responsible for supplying a timezone-aware UTC datetime.
        """
        return replace(self, status=status, updated_at=now)

    def with_name(
        self,
        project_name: str,
        *,
        now: datetime,
    ) -> ProjectMetadata:
        """Return a new metadata with a new project_name."""
        if not project_name:
            raise ValueError("project_name must not be empty")
        return replace(self, project_name=project_name, updated_at=now)

    def with_last_opened(
        self,
        *,
        now: datetime,
    ) -> ProjectMetadata:
        """Return a new metadata with last_opened_at set to now."""
        return replace(self, last_opened_at=now)
