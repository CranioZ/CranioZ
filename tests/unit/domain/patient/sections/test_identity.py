"""Tests for PatientIdentity (§1 Identificação).

PatientIdentity is a frozen value object carrying the patient's
name, birth date, sex, race, nationality, blood type, and optional
photo reference. These tests exercise construction, defaults,
validation, immutability, and equality.

The tests do not depend on Qt, filesystem, or infrastructure.
"""

from __future__ import annotations

import dataclasses
from datetime import date

import pytest

from cranioz.domain.patient.enums.blood_type import BloodType
from cranioz.domain.patient.enums.patient_race import PatientRace
from cranioz.domain.patient.enums.patient_sex import PatientSex
from cranioz.domain.patient.sections.identity import PatientIdentity

# ----- Helpers ------------------------------------------------------


def _identity(**overrides) -> PatientIdentity:
    base: dict = {"full_name": "Gabriel Silva"}
    base.update(overrides)
    return PatientIdentity(**base)


# ----- Construction -------------------------------------------------


def test_identity_holds_full_name() -> None:
    identity = _identity()
    assert identity.full_name == "Gabriel Silva"


def test_identity_defaults() -> None:
    identity = _identity()
    assert identity.social_name is None
    assert identity.birth_date is None
    assert identity.sex is None
    assert identity.race is PatientRace.NOT_DECLARED
    assert identity.nationality is None
    assert identity.blood_type is BloodType.UNKNOWN
    assert identity.photo_reference is None


def test_identity_holds_all_fields() -> None:
    identity = PatientIdentity(
        full_name="Gabriel Silva",
        social_name="Gabi",
        birth_date=date(1990, 5, 12),
        sex=PatientSex.MALE,
        race=PatientRace.BROWN,
        nationality="Brazil",
        blood_type=BloodType.O_POSITIVE,
        photo_reference="patient/photo/portrait",
    )
    assert identity.social_name == "Gabi"
    assert identity.birth_date == date(1990, 5, 12)
    assert identity.sex is PatientSex.MALE
    assert identity.race is PatientRace.BROWN
    assert identity.nationality == "Brazil"
    assert identity.blood_type is BloodType.O_POSITIVE
    assert identity.photo_reference == "patient/photo/portrait"


def test_identity_is_frozen() -> None:
    identity = _identity()
    attr = "full_name"
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(identity, attr, "Other")


# ----- Validation: full_name ---------------------------------------


def test_empty_full_name_raises() -> None:
    with pytest.raises(ValueError, match="full_name"):
        _identity(full_name="")


def test_whitespace_full_name_raises() -> None:
    with pytest.raises(ValueError, match="whitespace"):
        _identity(full_name="   ")


# ----- Validation: social_name -------------------------------------


def test_social_name_can_be_none() -> None:
    identity = _identity(social_name=None)
    assert identity.social_name is None


def test_empty_social_name_raises() -> None:
    """An empty string is not a valid social name.

    ``social_name`` is optional. Absence is expressed as ``None``,
    not as an empty string. If a value is present, it must be a
    non-empty, non-whitespace name.
    """
    with pytest.raises(ValueError, match="social_name"):
        _identity(social_name="")


def test_whitespace_social_name_raises() -> None:
    with pytest.raises(ValueError, match="social_name"):
        _identity(social_name="   ")


# ----- Validation: photo_reference ----------------------------------


def test_photo_reference_can_be_none() -> None:
    identity = _identity(photo_reference=None)
    assert identity.photo_reference is None


def test_empty_photo_reference_raises() -> None:
    with pytest.raises(ValueError, match="photo_reference"):
        _identity(photo_reference="")


def test_whitespace_photo_reference_raises() -> None:
    with pytest.raises(ValueError, match="photo_reference"):
        _identity(photo_reference="   ")


# ----- Equality -----------------------------------------------------


def test_identity_equality_by_value() -> None:
    a = _identity()
    b = _identity()
    assert a == b


def test_identity_with_different_names_not_equal() -> None:
    a = _identity(full_name="A")
    b = _identity(full_name="B")
    assert a != b
