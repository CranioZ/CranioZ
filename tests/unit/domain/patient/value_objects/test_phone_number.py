"""Tests for PhoneNumber.

PhoneNumber is a frozen value object combining a phone number with
its kind. These tests exercise construction, validation, equality,
hashing, defaults, and representation.

The tests do not depend on Qt, filesystem, or infrastructure.
"""

from __future__ import annotations

import dataclasses

import pytest

from cranioz.domain.patient.enums.phone_kind import PhoneKind
from cranioz.domain.patient.value_objects.phone_number import PhoneNumber

# ----- Construction -------------------------------------------------


def test_phone_number_holds_fields() -> None:
    phone = PhoneNumber(number="+55 91 99582-8523", kind=PhoneKind.MOBILE)
    assert phone.number == "+55 91 99582-8523"
    assert phone.kind is PhoneKind.MOBILE


def test_default_kind_is_mobile() -> None:
    phone = PhoneNumber(number="+55 91 99582-8523")
    assert phone.kind is PhoneKind.MOBILE


def test_number_is_free_form_string() -> None:
    # The domain does not enforce a format.
    variants = [
        "1234",
        "(91) 3242-1234",
        "+55 91 99582-8523",
        "91 9 9582 8523",
    ]
    for value in variants:
        phone = PhoneNumber(number=value)
        assert phone.number == value


# ----- Validation ---------------------------------------------------


def test_empty_number_raises() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        PhoneNumber(number="")


def test_whitespace_only_number_raises() -> None:
    with pytest.raises(ValueError, match="whitespace"):
        PhoneNumber(number="   ")


def test_tab_and_newline_number_raises() -> None:
    with pytest.raises(ValueError, match="whitespace"):
        PhoneNumber(number="\t\n")


# ----- Immutability -------------------------------------------------


def test_phone_number_is_frozen() -> None:
    phone = PhoneNumber(number="1234")
    attr = "number"
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(phone, attr, "5678")


# ----- Equality and hashing ----------------------------------------


def test_equality_by_value() -> None:
    a = PhoneNumber(number="1234", kind=PhoneKind.HOME)
    b = PhoneNumber(number="1234", kind=PhoneKind.HOME)
    assert a == b


def test_equality_considers_kind() -> None:
    a = PhoneNumber(number="1234", kind=PhoneKind.MOBILE)
    b = PhoneNumber(number="1234", kind=PhoneKind.HOME)
    assert a != b


def test_different_number_is_not_equal() -> None:
    a = PhoneNumber(number="1234")
    b = PhoneNumber(number="5678")
    assert a != b


def test_phone_number_is_hashable() -> None:
    a = PhoneNumber(number="1234", kind=PhoneKind.WORK)
    b = PhoneNumber(number="1234", kind=PhoneKind.WORK)
    assert hash(a) == hash(b)


# ----- Kinds --------------------------------------------------------


def test_all_phone_kinds_are_accepted() -> None:
    for kind in PhoneKind:
        phone = PhoneNumber(number="1234", kind=kind)
        assert phone.kind is kind
