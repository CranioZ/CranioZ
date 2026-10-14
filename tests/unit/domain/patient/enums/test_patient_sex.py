"""Tests for PatientSex."""

from __future__ import annotations

import pytest

from cranioz.domain.patient.enums.patient_sex import PatientSex


def test_members() -> None:
    expected = {"MALE", "FEMALE", "OTHER"}
    assert {m.name for m in PatientSex} == expected


def test_values() -> None:
    assert PatientSex.MALE.value == "male"
    assert PatientSex.FEMALE.value == "female"
    assert PatientSex.OTHER.value == "other"


def test_lookup_by_value() -> None:
    assert PatientSex("male") is PatientSex.MALE
    assert PatientSex("female") is PatientSex.FEMALE
    assert PatientSex("other") is PatientSex.OTHER


def test_unknown_value_raises() -> None:
    with pytest.raises(ValueError):
        PatientSex("nonbinary")


def test_no_unknown_member() -> None:
    """Sex has no UNKNOWN member.

    When the sex is not recorded, the field is ``None`` at the
    domain level, not a sentinel enum value. This keeps "not
    recorded" distinct from "recorded as OTHER".
    """
    assert not hasattr(PatientSex, "UNKNOWN")
