"""Tests for PatientSummary.

PatientSummary is a lightweight read-only projection of a Patient.
It carries only the fields needed to identify and display the
patient in contexts where the full record is not required, such as
project listings, tooltips, breadcrumbs, and the ProjectContext
handed to the Workspace.

The summary is a value object. It is derived from a Patient, but it
is not the Patient itself, and it does not carry any clinical data
(no medical history, no imaging references).

See ADR-0004 §13 for the design rationale.
"""

from __future__ import annotations

import dataclasses
from datetime import date

import pytest

from cranioz.domain.patient.enums.patient_sex import PatientSex
from cranioz.domain.patient.patient_summary import PatientSummary
from cranioz.domain.patient.value_objects.patient_id import PatientId

# ----- Helpers ------------------------------------------------------


def _summary(**overrides) -> PatientSummary:
    """Build a PatientSummary with sensible defaults.

    Callers may override any field by keyword.
    """
    base: dict = {
        "patient_id": PatientId("pat-001"),
        "display_name": "Gabriel Silva",
        "birth_date": date(1990, 5, 12),
        "sex": PatientSex.MALE,
    }
    base.update(overrides)
    return PatientSummary(**base)


# ----- Construction -------------------------------------------------


def test_summary_holds_all_fields() -> None:
    s = _summary()
    assert s.patient_id == PatientId("pat-001")
    assert s.display_name == "Gabriel Silva"
    assert s.birth_date == date(1990, 5, 12)
    assert s.sex is PatientSex.MALE


def test_summary_is_frozen() -> None:
    s = _summary()
    attr = "display_name"
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(s, attr, "Other")


def test_summary_is_hashable() -> None:
    a = _summary()
    b = _summary()
    # Equal summaries have equal hashes, so they can be used in sets
    # and as dict keys.
    assert hash(a) == hash(b)


def test_two_summaries_with_same_data_are_equal() -> None:
    a = _summary()
    b = _summary()
    assert a == b


# ----- Validation ---------------------------------------------------


def test_empty_display_name_raises() -> None:
    with pytest.raises(ValueError, match="display_name"):
        _summary(display_name="")


def test_whitespace_only_display_name_raises() -> None:
    with pytest.raises(ValueError, match="whitespace"):
        _summary(display_name="   ")


# ----- Optional fields ----------------------------------------------


def test_birth_date_can_be_none() -> None:
    s = _summary(birth_date=None)
    assert s.birth_date is None


def test_sex_can_be_none() -> None:
    s = _summary(sex=None)
    assert s.sex is None


def test_summary_with_all_optional_fields_none() -> None:
    s = _summary(birth_date=None, sex=None)
    assert s.birth_date is None
    assert s.sex is None
    # Required fields remain present.
    assert s.patient_id == PatientId("pat-001")
    assert s.display_name == "Gabriel Silva"


# ----- Equality and hashing ----------------------------------------


def test_summaries_with_different_display_names_are_not_equal() -> None:
    a = _summary(display_name="A")
    b = _summary(display_name="B")
    assert a != b


def test_summaries_with_different_ids_are_not_equal() -> None:
    a = _summary(patient_id=PatientId("pat-001"))
    b = _summary(patient_id=PatientId("pat-002"))
    assert a != b


# ----- Representation ----------------------------------------------


def test_repr_mentions_key_fields() -> None:
    s = _summary()
    text = repr(s)
    assert "pat-001" in text
    assert "Gabriel Silva" in text


# ----- Boundaries ---------------------------------------------------


def test_summary_does_not_carry_clinical_data() -> None:
    """The summary intentionally excludes clinical fields.

    The projection exists to answer "who is this patient?", not
    "what is this patient's clinical state?". Fields such as
    medical history, medications, allergies, and section value
    objects must never become part of the summary. This test
    documents and guards that boundary.
    """
    forbidden = {
        "medical_history",
        "medications",
        "allergies",
        "comorbidities",
        "antecedents",
        "identity",
        "documents",
        "filiation",
        "address",
        "complaint",
        "habits",
    }
    fields = {f.name for f in dataclasses.fields(PatientSummary)}
    assert fields.isdisjoint(forbidden)


def test_summary_only_carries_the_expected_fields() -> None:
    """The summary has exactly four fields, by design.

    Adding a field to PatientSummary is a deliberate decision: it
    increases the weight of every listing, tooltip, and breadcrumb
    that carries the summary. This test guards against accidental
    additions.
    """
    fields = {f.name for f in dataclasses.fields(PatientSummary)}
    assert fields == {
        "patient_id",
        "display_name",
        "birth_date",
        "sex",
    }
