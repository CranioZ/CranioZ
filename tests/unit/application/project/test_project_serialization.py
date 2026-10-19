"""Tests for Project serialization.

Pure functions, no I/O.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from cranioz.domain.project.project import Project
from cranioz.domain.project.project_id import ProjectId
from cranioz.domain.project.project_metadata import ProjectMetadata
from cranioz.domain.project.project_status import ProjectStatus
from cranioz.infrastructure.project.project_serialization import (
    CURRENT_SCHEMA_VERSION,
    ProjectSerializationError,
    project_from_dict,
    project_to_dict,
)


def _now() -> datetime:
    return datetime(2026, 1, 1, 12, 0, tzinfo=UTC)


def _project(project_id: str = "p-001") -> Project:
    pid = ProjectId(project_id)
    return Project(
        project_id=pid,
        metadata=ProjectMetadata(
            project_id=pid,
            project_name=f"Case {project_id}",
            patient_id="pat-001",
            patient_display_name="Gabriel Silva",
            clinical_procedure="orthognathic",
            status=ProjectStatus.ACTIVE,
            created_at=_now(),
            updated_at=_now(),
            last_opened_at=None,
            schema_version=CURRENT_SCHEMA_VERSION,
        ),
    )


# ----- Round-trip ----------------------------------------------------


def test_round_trip_preserves_all_fields() -> None:
    original = _project("p-001")
    reconstructed = project_from_dict(project_to_dict(original))
    assert reconstructed.project_id == original.project_id
    assert reconstructed.metadata == original.metadata


def test_round_trip_preserves_last_opened() -> None:
    later = datetime(2026, 2, 1, 15, 30, tzinfo=UTC)
    original = _project("p-001")
    original = Project(
        project_id=original.project_id,
        metadata=original.metadata.with_last_opened(now=later),
    )
    reconstructed = project_from_dict(project_to_dict(original))
    assert reconstructed.metadata.last_opened_at == later


# ----- Serialization shape -------------------------------------------


def test_serialized_dict_contains_expected_keys() -> None:
    data = project_to_dict(_project())
    expected = {
        "schema_version",
        "project_id",
        "project_name",
        "patient_id",
        "patient_display_name",
        "clinical_procedure",
        "status",
        "created_at",
        "updated_at",
        "last_opened_at",
    }
    assert set(data.keys()) == expected


def test_status_is_serialized_by_value() -> None:
    data = project_to_dict(_project())
    assert data["status"] == "active"


def test_timestamps_are_iso_with_timezone() -> None:
    data = project_to_dict(_project())
    assert data["created_at"].endswith("+00:00")
    assert data["updated_at"].endswith("+00:00")


def test_last_opened_none_is_serialized_as_null() -> None:
    assert project_to_dict(_project())["last_opened_at"] is None


# ----- Decode errors --------------------------------------------------


def test_missing_required_key_raises() -> None:
    data = project_to_dict(_project())
    del data["project_name"]
    with pytest.raises(ProjectSerializationError, match="project_name"):
        project_from_dict(data)


def test_invalid_schema_version_raises() -> None:
    data = project_to_dict(_project())
    data["schema_version"] = 99
    with pytest.raises(ProjectSerializationError, match="schema_version"):
        project_from_dict(data)


def test_invalid_status_raises() -> None:
    data = project_to_dict(_project())
    data["status"] = "not-a-status"
    with pytest.raises(ProjectSerializationError, match="status"):
        project_from_dict(data)


def test_invalid_timestamp_raises() -> None:
    data = project_to_dict(_project())
    data["created_at"] = "not-a-date"
    with pytest.raises(ProjectSerializationError, match="created_at"):
        project_from_dict(data)


def test_naive_timestamp_raises() -> None:
    data = project_to_dict(_project())
    data["created_at"] = "2026-01-01T12:00:00"
    with pytest.raises(ProjectSerializationError, match="timezone-aware"):
        project_from_dict(data)


def test_bool_schema_version_is_rejected() -> None:
    """bool is a subclass of int; the parser must reject it explicitly."""
    data = project_to_dict(_project())
    data["schema_version"] = True
    with pytest.raises(ProjectSerializationError, match="schema_version"):
        project_from_dict(data)


def test_non_dict_input_raises() -> None:
    with pytest.raises(ProjectSerializationError, match="dict"):
        project_from_dict([])  # type: ignore[arg-type]


def test_domain_invariant_failure_is_wrapped() -> None:
    data = project_to_dict(_project())
    data["updated_at"] = "2025-01-01T00:00:00+00:00"
    with pytest.raises(ProjectSerializationError, match="updated_at"):
        project_from_dict(data)
