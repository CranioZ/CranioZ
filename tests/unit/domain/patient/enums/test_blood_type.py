"""Tests for BloodType."""

from __future__ import annotations

import pytest

from cranioz.domain.patient.enums.blood_type import BloodType


def test_members() -> None:
    expected = {
        "A_POSITIVE",
        "A_NEGATIVE",
        "B_POSITIVE",
        "B_NEGATIVE",
        "AB_POSITIVE",
        "AB_NEGATIVE",
        "O_POSITIVE",
        "O_NEGATIVE",
        "UNKNOWN",
    }
    assert {m.name for m in BloodType} == expected


def test_values() -> None:
    assert BloodType.A_POSITIVE.value == "a_positive"
    assert BloodType.AB_NEGATIVE.value == "ab_negative"
    assert BloodType.O_POSITIVE.value == "o_positive"
    assert BloodType.UNKNOWN.value == "unknown"


def test_lookup_by_value() -> None:
    assert BloodType("a_positive") is BloodType.A_POSITIVE
    assert BloodType("o_negative") is BloodType.O_NEGATIVE
    assert BloodType("unknown") is BloodType.UNKNOWN


def test_unknown_value_raises() -> None:
    with pytest.raises(ValueError):
        BloodType("not_a_blood_type")


def test_all_abo_rh_combinations_present() -> None:
    """All eight ABO/Rh combinations plus UNKNOWN must exist."""
    abo = ("A", "B", "AB", "O")
    for group in abo:
        for sign in ("POSITIVE", "NEGATIVE"):
            member_name = f"{group}_{sign}"
            assert hasattr(BloodType, member_name)
    assert hasattr(BloodType, "UNKNOWN")
