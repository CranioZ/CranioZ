"""Tests for Project."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from cranioz.domain.project.project import Project
from cranioz.domain.project.project_id import ProjectId
from cranioz.domain.project.project_metadata import ProjectMetadata
from cranioz.domain.project.project_status import ProjectStatus

# ----- Helpers ------------------------------------------------------


def _now() -> datetime:
    return datetime(2026, 1, 1, 12, 0, tzinfo=UTC)


def _metadata(project_id: str = "p-001") -> ProjectMetadata:
    return ProjectMetadata(
        project_id=ProjectId(project_id),
        project_name="Case 001",
        patient_id="pat-001",
        patient_display_name="Gabriel Silva",
        clinical_procedure="orthognathic",
        status=ProjectStatus.ACTIVE,
        created_at=_now(),
        updated_at=_now(),
        last_opened_at=None,
        schema_version=1,
    )


def _project(project_id: str = "p-001") -> Project:
    pid = ProjectId(project_id)
    return Project(project_id=pid, metadata=_metadata(project_id))


# ----- Construction -------------------------------------------------


def test_project_holds_id_and_metadata() -> None:
    p = _project()
    assert p.project_id == ProjectId("p-001")
    assert p.metadata.project_id == ProjectId("p-001")
    assert p.metadata.project_name == "Case 001"


def test_project_extras_default_to_empty_dict() -> None:
    p = _project()
    assert p.extras == {}


def test_metadata_project_id_mismatch_raises() -> None:
    pid = ProjectId("p-001")
    wrong_md = _metadata("p-999")
    with pytest.raises(ValueError, match="must match"):
        Project(project_id=pid, metadata=wrong_md)


# ----- update_metadata ----------------------------------------------


def test_update_metadata_replaces() -> None:
    p = _project()
    later = datetime(2026, 2, 1, tzinfo=UTC)
    new_md = p.metadata.with_name("Renamed", now=later)

    p.update_metadata(new_md)

    assert p.metadata.project_name == "Renamed"
    assert p.metadata.updated_at == later


def test_update_metadata_wrong_project_raises() -> None:
    p = _project()
    other_md = _metadata("p-999")
    with pytest.raises(ValueError, match="different project"):
        p.update_metadata(other_md)


# ----- Representation -----------------------------------------------


def test_repr_mentions_key_fields() -> None:
    p = _project()
    text = repr(p)
    assert "p-001" in text
    assert "Case 001" in text
    assert "active" in text
