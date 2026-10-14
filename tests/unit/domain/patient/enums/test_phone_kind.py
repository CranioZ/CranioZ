"""Tests for PhoneKind."""

from __future__ import annotations

import pytest

from cranioz.domain.patient.enums.phone_kind import PhoneKind


def test_members() -> None:
    expected = {"MOBILE", "HOME", "WORK", "OTHER"}
    assert {m.name for m in PhoneKind} == expected


def test_values() -> None:
    assert PhoneKind.MOBILE.value == "mobile"
    assert PhoneKind.HOME.value == "home"
    assert PhoneKind.WORK.value == "work"
    assert PhoneKind.OTHER.value == "other"


def test_lookup_by_value() -> None:
    assert PhoneKind("mobile") is PhoneKind.MOBILE
    assert PhoneKind("other") is PhoneKind.OTHER


def test_unknown_value_raises() -> None:
    with pytest.raises(ValueError):
        PhoneKind("fax")
