"""Tests for the Professional Address value object."""

from __future__ import annotations

import pytest

from cranioz.domain.professional.address import Address


def test_empty_address_is_valid() -> None:
    assert Address() == Address()


def test_address_holds_all_fields() -> None:
    address = Address(
        postal_code="01001-000",
        street="Rua Exemplo",
        number="100",
        complement="Sala 2",
        district="Centro",
        city="São Paulo",
        state="SP",
        country="BR",
    )

    assert address.city == "São Paulo"
    assert address.country == "BR"


def test_address_is_frozen() -> None:
    address = Address()
    with pytest.raises(AttributeError):
        address.city = "São Paulo"  # type: ignore[misc]


def test_present_whitespace_field_is_rejected() -> None:
    with pytest.raises(ValueError, match="city"):
        Address(city="   ")
