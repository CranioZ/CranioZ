"""Serialization of Project to/from JSON-compatible dictionaries.

Pure functions. No I/O, no filesystem, no repository. The functions
here define the *shape* of the persisted representation; the repository
(Peça 7.3) handles file reading/writing and error translation.

Design rules (see `project.md` §13):

- The serialized form is versioned (`schema_version`). Migrations are
  the responsibility of a dedicated migrator; this module only knows
  the current version.
- Timestamps are ISO 8601 with timezone (`+00:00`), matching the
  domain's `datetime` with `tzinfo=UTC`.
- Enums are serialized by their `.value` string, not by `.name`. The
  values are stable identifiers (`"active"`, not `"ACTIVE"`).
- The metadata's project_id is the canonical key; it must match the
  directory name (`ProjectPathResolver.project_id`).
- `patient_record.json` is NOT serialized here. The Repository does
  not own the Patient record; it only stores the reference
  (`patient_id`) and the denormalized `patient_display_name` used by
  the read model.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from cranioz.domain.project.project import Project
from cranioz.domain.project.project_id import ProjectId
from cranioz.domain.project.project_metadata import ProjectMetadata
from cranioz.domain.project.project_status import ProjectStatus

# The current version of the persisted representation. Bumped whenever
# the shape of project.json changes in a way that requires migration.
CURRENT_SCHEMA_VERSION = 1


class ProjectSerializationError(ValueError):
    """Raised when a dict cannot be interpreted as a valid Project."""


# ----- Encode --------------------------------------------------------


def project_to_dict(project: Project) -> dict[str, Any]:
    """Return a JSON-compatible dict for the given Project."""
    md = project.metadata
    return {
        "schema_version": md.schema_version,
        "project_id": project.project_id.value,
        "project_name": md.project_name,
        "patient_id": md.patient_id,
        "patient_display_name": md.patient_display_name,
        "clinical_procedure": md.clinical_procedure,
        "status": md.status.value,
        "created_at": _datetime_to_iso(md.created_at),
        "updated_at": _datetime_to_iso(md.updated_at),
        "last_opened_at": (
            _datetime_to_iso(md.last_opened_at) if md.last_opened_at is not None else None
        ),
    }


# ----- Decode --------------------------------------------------------


def project_from_dict(data: dict[str, Any]) -> Project:
    """Reconstruct a Project from a dict.

    Raises:
        ProjectSerializationError: the dict is missing required keys,
            has invalid types, or fails a domain invariant.
    """
    if not isinstance(data, dict):
        raise ProjectSerializationError(
            f"project data must be a dict, got {type(data).__name__}"
        )

    schema_version = _require_int(data, "schema_version")
    if schema_version != CURRENT_SCHEMA_VERSION:
        raise ProjectSerializationError(
            f"unsupported schema_version: {schema_version} "
            f"(expected {CURRENT_SCHEMA_VERSION})"
        )

    try:
        project_id = ProjectId(_require_str(data, "project_id"))
        metadata = ProjectMetadata(
            project_id=project_id,
            project_name=_require_str(data, "project_name"),
            patient_id=_require_str(data, "patient_id"),
            patient_display_name=_require_str(data, "patient_display_name"),
            clinical_procedure=_require_str(data, "clinical_procedure"),
            status=_parse_status(_require_str(data, "status")),
            created_at=_parse_datetime(_require_str(data, "created_at"), "created_at"),
            updated_at=_parse_datetime(_require_str(data, "updated_at"), "updated_at"),
            last_opened_at=_parse_optional_datetime(data, "last_opened_at"),
            schema_version=schema_version,
        )
    except ProjectSerializationError:
        raise
    except Exception as exc:
        raise ProjectSerializationError(f"invalid project data: {exc}") from exc

    try:
        return Project(project_id=project_id, metadata=metadata)
    except ValueError as exc:
        raise ProjectSerializationError(f"invalid project: {exc}") from exc


# ----- Internals ----------------------------------------------------


def _require_str(data: dict[str, Any], key: str) -> str:
    if key not in data:
        raise ProjectSerializationError(f"missing required key: {key!r}")
    value = data[key]
    if not isinstance(value, str):
        raise ProjectSerializationError(
            f"invalid type for {key!r}: expected str, got {type(value).__name__}"
        )
    return value


def _require_int(data: dict[str, Any], key: str) -> int:
    if key not in data:
        raise ProjectSerializationError(f"missing required key: {key!r}")
    value = data[key]
    if not isinstance(value, int) or isinstance(value, bool):
        raise ProjectSerializationError(
            f"invalid type for {key!r}: expected int, got {type(value).__name__}"
        )
    return value


def _datetime_to_iso(value: datetime) -> str:
    return value.isoformat()


def _parse_datetime(value: str, field_name: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ProjectSerializationError(
            f"invalid ISO 8601 for {field_name!r}: {value!r}"
        ) from exc
    if parsed.tzinfo is None:
        raise ProjectSerializationError(
            f"{field_name!r} must be timezone-aware, got {value!r}"
        )
    return parsed


def _parse_optional_datetime(data: dict[str, Any], key: str) -> datetime | None:
    value = data.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ProjectSerializationError(
            f"invalid type for {key!r}: expected str or null, "
            f"got {type(value).__name__}"
        )
    return _parse_datetime(value, key)


def _parse_status(value: str) -> ProjectStatus:
    try:
        return ProjectStatus(value)
    except ValueError as exc:
        raise ProjectSerializationError(f"invalid project status: {value!r}") from exc
