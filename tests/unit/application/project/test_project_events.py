"""Tests for Project lifecycle events.

Events are frozen data. These tests cover:

- Construction and required fields.
- Immutability (frozen).
- Equality by value.
- The presence of `project_id` on every event (the minimum contract
  every observer relies on).

The tests do not publish or subscribe; publication is the Project
Manager's concern (Peça 7.5).
"""

from __future__ import annotations

import dataclasses
from datetime import UTC, datetime

import pytest

from cranioz.application.project.project_context import ProjectContext
from cranioz.application.project.project_events import (
    ProjectClosed,
    ProjectClosing,
    ProjectCreated,
    ProjectDeleted,
    ProjectOpened,
    ProjectUpdated,
)
from cranioz.domain.patient.enums.patient_sex import PatientSex
from cranioz.domain.patient.patient_summary import PatientSummary
from cranioz.domain.patient.value_objects.patient_id import PatientId
from cranioz.domain.project.project_id import ProjectId
from cranioz.domain.project.project_metadata import ProjectMetadata
from cranioz.domain.project.project_status import ProjectStatus

# ----- Helpers ------------------------------------------------------


def _now() -> datetime:
    return datetime(2026, 1, 1, 12, 0, tzinfo=UTC)


def _metadata(project_id: str = "p-001") -> ProjectMetadata:
    return ProjectMetadata(
        project_id=ProjectId(project_id),
        project_name=f"Case {project_id}",
        patient_id="pat-001",
        patient_display_name="Gabriel Silva",
        clinical_procedure="orthognathic",
        status=ProjectStatus.ACTIVE,
        created_at=_now(),
        updated_at=_now(),
        last_opened_at=None,
        schema_version=1,
    )


def _patient_summary() -> PatientSummary:
    return PatientSummary(
        patient_id=PatientId("pat-001"),
        display_name="Gabriel Silva",
        birth_date=None,
        sex=PatientSex.MALE,
    )


def _context(project_id: str = "p-001") -> ProjectContext:
    return ProjectContext(
        project_id=ProjectId(project_id),
        metadata=_metadata(project_id),
        patient_summary=_patient_summary(),
    )


# ----- ProjectCreated -----------------------------------------------


def test_project_created_holds_fields() -> None:
    md = _metadata()
    event = ProjectCreated(project_id=ProjectId("p-001"), metadata=md)
    assert event.project_id == ProjectId("p-001")
    assert event.metadata is md


def test_project_created_is_frozen() -> None:
    event = ProjectCreated(project_id=ProjectId("p-001"), metadata=_metadata())
    attr = "project_id"
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(event, attr, ProjectId("p-999"))


def test_project_created_equality_by_value() -> None:
    a = ProjectCreated(project_id=ProjectId("p-001"), metadata=_metadata())
    b = ProjectCreated(project_id=ProjectId("p-001"), metadata=_metadata())
    assert a == b


# ----- ProjectOpened ------------------------------------------------


def test_project_opened_holds_context() -> None:
    ctx = _context()
    event = ProjectOpened(project_id=ProjectId("p-001"), context=ctx)
    assert event.project_id == ProjectId("p-001")
    assert event.context is ctx


def test_project_opened_is_frozen() -> None:
    event = ProjectOpened(project_id=ProjectId("p-001"), context=_context())
    attr = "context"
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(event, attr, _context())


# ----- ProjectUpdated -----------------------------------------------


def test_project_updated_holds_metadata() -> None:
    md = _metadata()
    event = ProjectUpdated(project_id=ProjectId("p-001"), metadata=md)
    assert event.metadata is md


def test_project_updated_is_frozen() -> None:
    event = ProjectUpdated(project_id=ProjectId("p-001"), metadata=_metadata())
    attr = "metadata"
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(event, attr, _metadata())


# ----- ProjectClosing / ProjectClosed -------------------------------


def test_project_closing_holds_only_id() -> None:
    event = ProjectClosing(project_id=ProjectId("p-001"))
    assert event.project_id == ProjectId("p-001")
    assert len(dataclasses.fields(event)) == 1


def test_project_closed_holds_only_id() -> None:
    event = ProjectClosed(project_id=ProjectId("p-001"))
    assert event.project_id == ProjectId("p-001")
    assert len(dataclasses.fields(event)) == 1


def test_project_closing_is_frozen() -> None:
    event = ProjectClosing(project_id=ProjectId("p-001"))
    attr = "project_id"
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(event, attr, ProjectId("p-999"))


def test_project_closed_is_frozen() -> None:
    event = ProjectClosed(project_id=ProjectId("p-001"))
    attr = "project_id"
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(event, attr, ProjectId("p-999"))


# ----- ProjectDeleted -----------------------------------------------


def test_project_deleted_holds_only_id() -> None:
    event = ProjectDeleted(project_id=ProjectId("p-001"))
    assert event.project_id == ProjectId("p-001")
    assert len(dataclasses.fields(event)) == 1


def test_project_deleted_is_frozen() -> None:
    event = ProjectDeleted(project_id=ProjectId("p-001"))
    attr = "project_id"
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(event, attr, ProjectId("p-999"))


# ----- Cross-cutting -----------------------------------------------


def test_every_event_has_project_id() -> None:
    """Every lifecycle event carries the project it refers to.

    This is the minimum contract every observer relies on: from the
    event alone, an observer can route to the right project.
    """
    events = [
        ProjectCreated(project_id=ProjectId("p-001"), metadata=_metadata()),
        ProjectOpened(project_id=ProjectId("p-001"), context=_context()),
        ProjectUpdated(project_id=ProjectId("p-001"), metadata=_metadata()),
        ProjectClosing(project_id=ProjectId("p-001")),
        ProjectClosed(project_id=ProjectId("p-001")),
        ProjectDeleted(project_id=ProjectId("p-001")),
    ]
    for event in events:
        assert hasattr(event, "project_id")
        assert event.project_id == ProjectId("p-001")
