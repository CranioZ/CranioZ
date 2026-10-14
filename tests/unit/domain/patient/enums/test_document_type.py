"""Tests for DocumentType."""

from __future__ import annotations

import pytest

from cranioz.domain.patient.enums.document_type import DocumentType


def test_members() -> None:
    expected = {
        "NATIONAL_ID",
        "TAX_ID",
        "DRIVERS_LICENSE",
        "PASSPORT",
        "BIRTH_CERTIFICATE",
        "OTHER",
    }
    assert {m.name for m in DocumentType} == expected


def test_values() -> None:
    assert DocumentType.NATIONAL_ID.value == "national_id"
    assert DocumentType.TAX_ID.value == "tax_id"
    assert DocumentType.DRIVERS_LICENSE.value == "drivers_license"
    assert DocumentType.PASSPORT.value == "passport"
    assert DocumentType.BIRTH_CERTIFICATE.value == "birth_certificate"
    assert DocumentType.OTHER.value == "other"


def test_lookup_by_value() -> None:
    assert DocumentType("national_id") is DocumentType.NATIONAL_ID
    assert DocumentType("passport") is DocumentType.PASSPORT


def test_unknown_value_raises() -> None:
    with pytest.raises(ValueError):
        DocumentType("unknown")


def test_no_country_specific_values() -> None:
    """Document types are country-agnostic.

    Country-specific names (RG, CPF, SSN, NIF, ...) are resolved by
    the i18n layer from the ``(type, country)`` pair. They must not
    appear as enum values in the domain, to keep the persisted
    representation stable across countries.
    """
    forbidden = {"rg", "cpf", "cnh", "ssn", "nif", "dni"}
    actual = {m.value for m in DocumentType}
    assert forbidden.isdisjoint(actual)
