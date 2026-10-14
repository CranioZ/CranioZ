"""Tests for PatientFiliation (§3 Filiação).

PatientFiliation carries the names of the patient's parents. Both
fields are optional and free-form.
"""

from __future__ import annotations

import dataclasses

import pytest

from cranioz.domain.patient.sections.filiation import PatientFiliation


def test_filiation_defaults() -> None:
    f = PatientFiliation()
    assert f.father_name is None
    assert f.mother_name is None


def test_filiation_holds_names() -> None:
    f = PatientFiliation(father_name="José Silva", mother_name="Maria Silva")
    assert f.father_name == "José Silva"
    assert f.mother_name == "Maria Silva"


def test_filiation_is_frozen() -> None:
    f = PatientFiliation()
    attr = "father_name"
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(f, attr, "X")


def test_whitespace_father_name_raises() -> None:
    with pytest.raises(ValueError, match="father_name"):
        PatientFiliation(father_name="   ")


def test_whitespace_mother_name_raises() -> None:
    with pytest.raises(ValueError, match="mother_name"):
        PatientFiliation(mother_name="   ")


def test_filiation_equality() -> None:
    a = PatientFiliation(father_name="X", mother_name="Y")
    b = PatientFiliation(father_name="X", mother_name="Y")
    assert a == b


def test_filiation_with_different_names_not_equal() -> None:
    a = PatientFiliation(father_name="X")
    b = PatientFiliation(father_name="Y")
    assert a != b
