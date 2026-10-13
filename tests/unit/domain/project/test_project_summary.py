"""Tests for ProjectSummary."""

from __future__ import annotations

import dataclasses
from datetime import UTC, datetime

import pytest

from cranioz.domain.project.project_id import ProjectId
from cranioz.domain.project.project_metadata import ProjectMetadata
from cranioz.domain.project.project_status import ProjectStatus
from cranioz.domain.project.project_summary import ProjectSummary

# ----- Helpers ------------------------------------------------------


def _now() -> datetime:
    return datetime(2026, 1, 1, 12, 0, tzinfo=UTC)


def _metadata() -> ProjectMetadata:
    return ProjectMetadata(
        project_id=ProjectId("p-001"),
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


def _summary(**overrides) -> ProjectSummary:
    base: dict = {
        "project_id": ProjectId("p-001"),
        "project_name": "Case 001",
        "patient_display_name": "Gabriel Silva",
        "status": ProjectStatus.ACTIVE,
        "procedure": "orthognathic",
        "created_at": _now(),
        "updated_at": _now(),
        "last_opened_at": None,
    }
    base.update(overrides)
    return ProjectSummary(**base)


# ----- Construction -------------------------------------------------


def test_summary_holds_all_fields() -> None:
    s = _summary()
    assert s.project_id == ProjectId("p-001")
    assert s.project_name == "Case 001"
    assert s.patient_display_name == "Gabriel Silva"
    assert s.status is ProjectStatus.ACTIVE
    assert s.procedure == "orthognathic"


def test_summary_is_frozen() -> None:
    s = _summary()
    attr = "project_name"
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(s, attr, "Other")


def test_empty_project_name_raises() -> None:
    with pytest.raises(ValueError, match="project_name"):
        _summary(project_name="")


def test_empty_patient_display_name_raises() -> None:
    with pytest.raises(ValueError, match="patient_display_name"):
        _summary(patient_display_name="")


def test_empty_procedure_raises() -> None:
    with pytest.raises(ValueError, match="procedure"):
        _summary(procedure="")


# ----- from_metadata ------------------------------------------------


def test_from_metadata_copies_fields() -> None:
    md = _metadata()
    s = ProjectSummary.from_metadata(md)

    assert s.project_id == md.project_id
    assert s.project_name == md.project_name
    assert s.patient_display_name == md.patient_display_name
    assert s.status == md.status
    assert s.procedure == md.clinical_procedure
    assert s.created_at == md.created_at
    assert s.updated_at == md.updated_at
    assert s.last_opened_at == md.last_opened_at


def test_from_metadata_with_last_opened() -> None:
    later = datetime(2026, 2, 1, tzinfo=UTC)
    md = _metadata().with_last_opened(now=later)
    s = ProjectSummary.from_metadata(md)
    assert s.last_opened_at == later
