"""ProjectStatus.

Lifecycle status of a Project.

The status is a semantic classification used by the Project Catalog
and by the Project Manager to reason about what operations are
allowed on a project.

- ``DRAFT``: created but not yet used for clinical work. The user
  may still edit its metadata freely. Draft projects are visible in
  the catalog but flagged as incomplete.
- ``ACTIVE``: in use for clinical planning. This is the normal
  working state.
- ``ARCHIVED``: closed and kept for reference. Archived projects
  are read-only in normal workflows but remain discoverable.
"""

from __future__ import annotations

from enum import Enum


class ProjectStatus(Enum):
    """Lifecycle status of a Project."""

    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"
