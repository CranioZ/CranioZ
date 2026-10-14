"""Tests for PatientRace."""

from __future__ import annotations

import pytest

from cranioz.domain.patient.enums.patient_race import PatientRace


def test_members() -> None:
    expected = {
        "WHITE",
        "BROWN",
        "BLACK",
        "YELLOW",
        "INDIGENOUS",
        "NOT_DECLARED",
    }
    assert {m.name for m in PatientRace} == expected


def test_values() -> None:
    assert PatientRace.WHITE.value == "white"
    assert PatientRace.BROWN.value == "brown"
    assert PatientRace.BLACK.value == "black"
    assert PatientRace.YELLOW.value == "yellow"
    assert PatientRace.INDIGENOUS.value == "indigenous"
    assert PatientRace.NOT_DECLARED.value == "not_declared"


def test_lookup_by_value() -> None:
    assert PatientRace("white") is PatientRace.WHITE
    assert PatientRace("brown") is PatientRace.BROWN
    assert PatientRace("not_declared") is PatientRace.NOT_DECLARED


def test_unknown_value_raises() -> None:
    with pytest.raises(ValueError):
        PatientRace("unknown")


def test_values_are_stable_identifiers() -> None:
    """Values are stable identifiers for persistence, not labels.

    The user-facing labels ("Branca", "Parda", ...) are resolved by
    the i18n layer, keyed by these values. If a value ever changes,
    persisted records break. This test guards against accidental
    renames.
    """
    expected = {
        PatientRace.WHITE: "white",
        PatientRace.BROWN: "brown",
        PatientRace.BLACK: "black",
        PatientRace.YELLOW: "yellow",
        PatientRace.INDIGENOUS: "indigenous",
        PatientRace.NOT_DECLARED: "not_declared",
    }
    for member, value in expected.items():
        assert member.value == value
