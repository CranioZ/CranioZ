"""Tests for PatientComplaint (§5 Queixa e História).

PatientComplaint carries the chief complaint and the history of the
present illness. Both fields are free-form text with empty-string
defaults.
"""

from __future__ import annotations

import dataclasses

import pytest

from cranioz.domain.patient.sections.complaint import PatientComplaint


def test_complaint_defaults_are_empty_strings() -> None:
    c = PatientComplaint()
    assert c.chief_complaint == ""
    assert c.present_illness_history == ""


def test_complaint_holds_text() -> None:
    c = PatientComplaint(
        chief_complaint="Dor mandibular",
        present_illness_history="Paciente relata dor há 3 meses.",
    )
    assert c.chief_complaint == "Dor mandibular"
    assert c.present_illness_history == "Paciente relata dor há 3 meses."


def test_complaint_is_frozen() -> None:
    c = PatientComplaint()
    attr = "chief_complaint"
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(c, attr, "X")


def test_complaint_accepts_multiline_text() -> None:
    text = "Line 1\nLine 2\nLine 3"
    c = PatientComplaint(present_illness_history=text)
    assert c.present_illness_history == text


def test_complaint_equality() -> None:
    a = PatientComplaint(chief_complaint="X")
    b = PatientComplaint(chief_complaint="X")
    assert a == b


def test_complaint_with_different_text_not_equal() -> None:
    a = PatientComplaint(chief_complaint="X")
    b = PatientComplaint(chief_complaint="Y")
    assert a != b
