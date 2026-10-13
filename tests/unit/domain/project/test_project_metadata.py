"""Tests for ProjectMetadata."""

from __future__ import annotations

import dataclasses
from datetime import UTC, datetime

import pytest

from cranioz.domain.project.project_id import ProjectId
from cranioz.domain.project.project_metadata import ProjectMetadata
from cranioz.domain.project.project_status import ProjectStatus

# ----- Helpers ------------------------------------------------------


def _now() -> datetime:
    return datetime(2026, 1, 1, 12, 0, tzinfo=UTC)


def _metadata(**overrides) -> ProjectMetadata:
    base: dict = {
        "project_id": ProjectId("p-001"),
        "project_name": "Case 001",
        "patient_id": "pat-001",
        "patient_display_name": "Gabriel Silva",
        "clinical_procedure": "orthognathic",
        "status": ProjectStatus.ACTIVE,
        "created_at": _now(),
        "updated_at": _now(),
        "last_opened_at": None,
        "schema_version": 1,
    }
    base.update(overrides)
    return ProjectMetadata(**base)


# ----- Construction -------------------------------------------------


def test_metadata_holds_all_fields() -> None:
    md = _metadata()
    assert md.project_id == ProjectId("p-001")
    assert md.project_name == "Case 001"
    assert md.patient_id == "pat-001"
    assert md.patient_display_name == "Gabriel Silva"
    assert md.clinical_procedure == "orthognathic"
    assert md.status is ProjectStatus.ACTIVE
    assert md.schema_version == 1


def test_metadata_is_frozen() -> None:
    md = _metadata()
    attr = "project_name"
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(md, attr, "Other")


def test_empty_project_name_raises() -> None:
    with pytest.raises(ValueError, match="project_name"):
        _metadata(project_name="")


def test_empty_patient_id_raises() -> None:
    with pytest.raises(ValueError, match="patient_id"):
        _metadata(patient_id="")


def test_empty_patient_display_name_raises() -> None:
    with pytest.raises(ValueError, match="patient_display_name"):
        _metadata(patient_display_name="")


def test_schema_version_zero_raises() -> None:
    with pytest.raises(ValueError, match="schema_version"):
        _metadata(schema_version=0)


def test_schema_version_negative_raises() -> None:
    with pytest.raises(ValueError, match="schema_version"):
        _metadata(schema_version=-1)


def test_updated_before_created_raises() -> None:
    earlier = datetime(2025, 1, 1, tzinfo=UTC)
    later = datetime(2026, 1, 1, tzinfo=UTC)
    with pytest.raises(ValueError, match="updated_at"):
        _metadata(created_at=later, updated_at=earlier)


def test_last_opened_before_created_raises() -> None:
    earlier = datetime(2025, 1, 1, tzinfo=UTC)
    later = datetime(2026, 1, 1, tzinfo=UTC)
    with pytest.raises(ValueError, match="last_opened_at"):
        _metadata(
            created_at=later,
            updated_at=later,
            last_opened_at=earlier,
        )


def test_naive_created_at_raises() -> None:
    naive = datetime(2026, 1, 1)
    with pytest.raises(ValueError, match="created_at"):
        _metadata(created_at=naive, updated_at=naive)


def test_naive_updated_at_raises() -> None:
    naive = datetime(2026, 1, 1)
    with pytest.raises(ValueError, match="updated_at"):
        _metadata(created_at=_now(), updated_at=naive)


def test_naive_last_opened_at_raises() -> None:
    naive = datetime(2026, 1, 1)
    with pytest.raises(ValueError, match="last_opened_at"):
        _metadata(last_opened_at=naive)


# ----- Mutators -----------------------------------------------------


def test_with_status_returns_new_instance() -> None:
    md = _metadata()
    later = datetime(2026, 2, 1, tzinfo=UTC)
    new_md = md.with_status(ProjectStatus.ARCHIVED, now=later)

    assert new_md is not md
    assert new_md.status is ProjectStatus.ARCHIVED
    assert new_md.updated_at == later
    # Original unchanged.
    assert md.status is ProjectStatus.ACTIVE


def test_with_name_returns_new_instance() -> None:
    md = _metadata()
    later = datetime(2026, 2, 1, tzinfo=UTC)
    new_md = md.with_name("Renamed", now=later)

    assert new_md.project_name == "Renamed"
    assert new_md.updated_at == later
    assert md.project_name == "Case 001"


def test_with_name_empty_raises() -> None:
    md = _metadata()
    later = datetime(2026, 2, 1, tzinfo=UTC)
    with pytest.raises(ValueError, match="project_name"):
        md.with_name("", now=later)


def test_with_last_opened_sets_timestamp() -> None:
    md = _metadata()
    later = datetime(2026, 3, 1, tzinfo=UTC)
    new_md = md.with_last_opened(now=later)

    assert new_md.last_opened_at == later
    assert md.last_opened_at is None
