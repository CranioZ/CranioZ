"""Tests for ProjectContext and ObjectReference.

The ProjectContext is the immutable snapshot handed to the Workspace
when a project opens. These tests cover:

- Construction and required/optional fields.
- The metadata/project_id coherence invariant.
- The workflow_id/workflow_config coupling invariant.
- Immutability (frozen).
- Functional mutators (`with_workflow`, `with_object_references`).
- `has_workflow` helper.
- `ObjectReference` validation.

No Qt, no I/O, no repository.
"""

from __future__ import annotations

import dataclasses
from datetime import UTC, datetime

import pytest

from cranioz.application.project.project_context import (
    ObjectReference,
    ProjectContext,
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


def _context(
    project_id: str = "p-001",
    *,
    workflow_id: str | None = None,
    workflow_config: dict | None = None,
    object_references: tuple[ObjectReference, ...] = (),
) -> ProjectContext:
    return ProjectContext(
        project_id=ProjectId(project_id),
        metadata=_metadata(project_id),
        patient_summary=_patient_summary(),
        workflow_id=workflow_id,
        workflow_config=workflow_config,
        object_references=object_references,
    )


# ----- ObjectReference ---------------------------------------------


def test_object_reference_holds_fields() -> None:
    ref = ObjectReference(
        object_id="ct-001",
        kind="volume",
        display_name="CT Pre-op",
    )
    assert ref.object_id == "ct-001"
    assert ref.kind == "volume"
    assert ref.display_name == "CT Pre-op"


def test_object_reference_is_frozen() -> None:
    ref = ObjectReference(object_id="x", kind="k", display_name="d")
    attr = "kind"
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(ref, attr, "other")


def test_object_reference_rejects_empty_object_id() -> None:
    with pytest.raises(ValueError, match="object_id"):
        ObjectReference(object_id="", kind="k", display_name="d")


def test_object_reference_rejects_empty_kind() -> None:
    with pytest.raises(ValueError, match="kind"):
        ObjectReference(object_id="x", kind="", display_name="d")


def test_object_reference_rejects_empty_display_name() -> None:
    with pytest.raises(ValueError, match="display_name"):
        ObjectReference(object_id="x", kind="k", display_name="")


# ----- ProjectContext construction ---------------------------------


def test_context_holds_all_fields() -> None:
    ref = ObjectReference(object_id="ct-001", kind="volume", display_name="CT")
    ctx = _context(object_references=(ref,))

    assert ctx.project_id == ProjectId("p-001")
    assert ctx.metadata.project_id == ProjectId("p-001")
    assert ctx.patient_summary.display_name == "Gabriel Silva"
    assert ctx.workflow_id is None
    assert ctx.workflow_config is None
    assert ctx.object_references == (ref,)


def test_context_defaults_workflow_to_none() -> None:
    ctx = _context()
    assert ctx.workflow_id is None
    assert ctx.workflow_config is None
    assert ctx.has_workflow() is False


def test_context_accepts_workflow_when_both_are_set() -> None:
    ctx = _context(
        workflow_id="orthognathic_planning",
        workflow_config={"steps": ["patient_data"]},
    )
    assert ctx.workflow_id == "orthognathic_planning"
    assert ctx.workflow_config == {"steps": ["patient_data"]}
    assert ctx.has_workflow() is True


def test_context_is_frozen() -> None:
    ctx = _context()
    attr = "project_id"
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(ctx, attr, ProjectId("p-999"))


def test_context_object_references_default_is_empty_tuple() -> None:
    ctx = _context()
    assert ctx.object_references == ()


def test_context_object_references_default_is_immutable_tuple() -> None:
    ctx = _context()
    assert isinstance(ctx.object_references, tuple)


# ----- Invariants ----------------------------------------------------


def test_metadata_project_id_mismatch_raises() -> None:
    with pytest.raises(ValueError, match=r"metadata\.project_id must match"):
        ProjectContext(
            project_id=ProjectId("p-001"),
            metadata=_metadata("p-999"),
            patient_summary=_patient_summary(),
        )


def test_workflow_id_without_config_raises() -> None:
    with pytest.raises(ValueError, match="workflow_id and workflow_config"):
        _context(workflow_id="orthognathic", workflow_config=None)


def test_workflow_config_without_id_raises() -> None:
    with pytest.raises(ValueError, match="workflow_id and workflow_config"):
        _context(workflow_id=None, workflow_config={"steps": []})


# ----- with_workflow ------------------------------------------------


def test_with_workflow_returns_new_context() -> None:
    original = _context()
    updated = original.with_workflow(
        workflow_id="orthognathic",
        workflow_config={"steps": ["a"]},
    )

    assert updated is not original
    assert updated.workflow_id == "orthognathic"
    assert updated.workflow_config == {"steps": ["a"]}
    assert original.workflow_id is None


def test_with_workflow_rejects_empty_id() -> None:
    with pytest.raises(ValueError, match="workflow_id"):
        _context().with_workflow(workflow_id="", workflow_config={})


def test_with_workflow_copies_config_dict() -> None:
    original = _context()
    source = {"steps": ["a"]}
    updated = original.with_workflow("wf", source)

    assert updated.workflow_config == {"steps": ["a"]}
    assert updated.workflow_config is not source


# ----- with_object_references ---------------------------------------


def test_with_object_references_returns_new_context() -> None:
    original = _context()
    ref = ObjectReference(object_id="ct-001", kind="volume", display_name="CT")
    updated = original.with_object_references((ref,))

    assert updated is not original
    assert updated.object_references == (ref,)
    assert original.object_references == ()


def test_with_object_references_preserves_workflow() -> None:
    original = _context(
        workflow_id="orthognathic",
        workflow_config={"steps": ["a"]},
    )
    updated = original.with_object_references(())

    assert updated.workflow_id == "orthognathic"
    assert updated.workflow_config == {"steps": ["a"]}


# ----- has_workflow -------------------------------------------------


def test_has_workflow_false_when_none() -> None:
    assert _context().has_workflow() is False


def test_has_workflow_true_when_set() -> None:
    ctx = _context(workflow_id="wf", workflow_config={})
    assert ctx.has_workflow() is True
