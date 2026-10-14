"""Tests for PatientAntecedents (§8 Antecedentes).

PatientAntecedents carries the patient's history beyond the current
complaint, organized in four subsections: surgical history,
devices/implants, family history, and women's health (conditional).

All fields are free-form text. The women's health fields are
meaningful only when the patient's sex is FEMALE; that rule is
enforced by the Patient aggregate, not by this section. This
section only validates that each field is a string.
"""

from __future__ import annotations

import dataclasses

import pytest

from cranioz.domain.patient.sections.antecedents import PatientAntecedents


def test_antecedents_defaults_are_empty_strings() -> None:
    a = PatientAntecedents()
    assert a.previous_surgeries == ""
    assert a.anesthesia_history == ""
    assert a.prostheses_implants == ""
    assert a.family_history == ""
    assert a.pregnancy_contraception == ""
    assert a.breastfeeding == ""


def test_antecedents_holds_all_fields() -> None:
    a = PatientAntecedents(
        previous_surgeries="Appendectomy 2010",
        anesthesia_history="No adverse events",
        prostheses_implants="Titanium plate on left femur",
        family_history="Father with hypertension",
        pregnancy_contraception="",
        breastfeeding="",
    )
    assert a.previous_surgeries == "Appendectomy 2010"
    assert a.prostheses_implants == "Titanium plate on left femur"
    assert a.family_history == "Father with hypertension"


def test_antecedents_holds_womens_health_fields() -> None:
    a = PatientAntecedents(
        pregnancy_contraception="Not currently pregnant",
        breastfeeding="No",
    )
    assert a.pregnancy_contraception == "Not currently pregnant"
    assert a.breastfeeding == "No"


def test_antecedents_does_not_enforce_womens_health_rule() -> None:
    """The section does not know the patient's sex.

    The rule "women's health fields must be empty when the patient
    is not female" is enforced by the Patient aggregate. This
    section only validates individual fields. This test documents
    that the section accepts any combination of the fields.
    """
    a = PatientAntecedents(pregnancy_contraception="X")
    assert a.pregnancy_contraception == "X"


def test_antecedents_is_frozen() -> None:
    a = PatientAntecedents()
    attr = "previous_surgeries"
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(a, attr, "X")


def test_antecedents_equality() -> None:
    a = PatientAntecedents(previous_surgeries="X")
    b = PatientAntecedents(previous_surgeries="X")
    assert a == b


def test_antecedents_with_different_values_not_equal() -> None:
    a = PatientAntecedents(previous_surgeries="X")
    b = PatientAntecedents(previous_surgeries="Y")
    assert a != b
