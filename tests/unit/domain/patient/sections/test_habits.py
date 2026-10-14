"""Tests for PatientHabits (§9 Hábitos e Vícios).

PatientHabits carries lifestyle factors relevant to surgical
planning: smoking, alcohol, and drug use. All fields are free-form
text.
"""

from __future__ import annotations

import dataclasses

import pytest

from cranioz.domain.patient.sections.habits import PatientHabits


def test_habits_defaults_are_empty_strings() -> None:
    h = PatientHabits()
    assert h.smoking == ""
    assert h.alcohol == ""
    assert h.drug_use == ""


def test_habits_holds_text() -> None:
    h = PatientHabits(
        smoking="10 cigarettes/day for 5 years",
        alcohol="Social drinking",
        drug_use="None",
    )
    assert h.smoking == "10 cigarettes/day for 5 years"
    assert h.alcohol == "Social drinking"
    assert h.drug_use == "None"


def test_habits_is_frozen() -> None:
    h = PatientHabits()
    attr = "smoking"
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(h, attr, "X")


def test_habits_accepts_multiline_text() -> None:
    text = "Former smoker\nQuit 3 years ago"
    h = PatientHabits(smoking=text)
    assert h.smoking == text


def test_habits_equality() -> None:
    a = PatientHabits(smoking="X")
    b = PatientHabits(smoking="X")
    assert a == b


def test_habits_with_different_values_not_equal() -> None:
    a = PatientHabits(smoking="X")
    b = PatientHabits(smoking="Y")
    assert a != b
