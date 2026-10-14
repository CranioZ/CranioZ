"""Tests for PatientMedications (§7 Medicamentos e Alergias).

PatientMedications carries current medications, previous
medications, and allergies. All fields are free-form text.
"""

from __future__ import annotations

import dataclasses

import pytest

from cranioz.domain.patient.sections.medications import PatientMedications


def test_medications_defaults_are_empty_strings() -> None:
    m = PatientMedications()
    assert m.current_medications == ""
    assert m.previous_medications == ""
    assert m.allergies == ""


def test_medications_holds_text() -> None:
    m = PatientMedications(
        current_medications="Losartan 50mg",
        previous_medications="Ibuprofen",
        allergies="Penicillin",
    )
    assert m.current_medications == "Losartan 50mg"
    assert m.previous_medications == "Ibuprofen"
    assert m.allergies == "Penicillin"


def test_medications_is_frozen() -> None:
    m = PatientMedications()
    attr = "allergies"
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(m, attr, "X")


def test_medications_accepts_multiline_text() -> None:
    text = "Losartan 50mg\nMetformin 500mg"
    m = PatientMedications(current_medications=text)
    assert m.current_medications == text


def test_medications_equality() -> None:
    a = PatientMedications(allergies="X")
    b = PatientMedications(allergies="X")
    assert a == b


def test_medications_with_different_allergies_not_equal() -> None:
    a = PatientMedications(allergies="X")
    b = PatientMedications(allergies="Y")
    assert a != b
