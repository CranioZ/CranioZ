"""Project domain.

The Project domain defines the persistent clinical container used by
CranioZ. It is independent of Qt, filesystem, and infrastructure.

Public API:

- ProjectId          — stable identity value object
- ProjectStatus      — lifecycle status enum
- ProjectMetadata    — persistent metadata of a project
- ProjectSummary     — read-only projection for discovery
- Project            — aggregate root
"""

from cranioz.domain.project.project import Project
from cranioz.domain.project.project_id import ProjectId
from cranioz.domain.project.project_metadata import ProjectMetadata
from cranioz.domain.project.project_status import ProjectStatus
from cranioz.domain.project.project_summary import ProjectSummary

__all__ = [
    "Project",
    "ProjectId",
    "ProjectMetadata",
    "ProjectStatus",
    "ProjectSummary",
]
