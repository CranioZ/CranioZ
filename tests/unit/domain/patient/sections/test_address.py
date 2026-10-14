"""Tests for PatientAddress (§4 Endereço).

PatientAddress carries the patient's address. Every field is
optional and free-form; the domain does not validate any format.
"""

from __future__ import annotations

import dataclasses

import pytest

from cranioz.domain.patient.sections.address import PatientAddress


def test_address_defaults() -> None:
    a = PatientAddress()
    assert a.postal_code is None
    assert a.street is None
    assert a.number is None
    assert a.complement is None
    assert a.district is None
    assert a.city is None
    assert a.state is None
    assert a.country is None


def test_address_holds_all_fields() -> None:
    a = PatientAddress(
        postal_code="66000-000",
        street="Rua das Flores",
        number="123",
        complement="Apto 45",
        district="Centro",
        city="Belém",
        state="PA",
        country="Brazil",
    )
    assert a.postal_code == "66000-000"
    assert a.city == "Belém"


def test_address_is_frozen() -> None:
    a = PatientAddress()
    attr = "city"
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(a, attr, "X")


def test_address_accepts_arbitrary_format() -> None:
    # The domain does not validate postal codes or any other format.
    a = PatientAddress(postal_code="1234", country="XX")
    assert a.postal_code == "1234"


def test_address_equality() -> None:
    a = PatientAddress(city="Belém")
    b = PatientAddress(city="Belém")
    assert a == b


def test_address_with_different_cities_not_equal() -> None:
    a = PatientAddress(city="Belém")
    b = PatientAddress(city="São Paulo")
    assert a != b
