"""Tests for PatientDocuments (§2 Documentos e Contato).

PatientDocuments carries the patient's identity document, phone
numbers, email, and health insurance data. It enforces two groups
of conditional invariants:

- Document coherence: type, country, and number must be set
  together, or none of them set.
- Insurance coherence: name and card number must be set together,
  or none of them set.

The tests do not depend on Qt, filesystem, or infrastructure.
"""

from __future__ import annotations

import dataclasses

import pytest

from cranioz.domain.patient.enums.document_type import DocumentType
from cranioz.domain.patient.enums.phone_kind import PhoneKind
from cranioz.domain.patient.sections.documents import PatientDocuments
from cranioz.domain.patient.value_objects.phone_number import PhoneNumber

# ----- Construction -------------------------------------------------


def test_documents_defaults() -> None:
    docs = PatientDocuments()
    assert docs.document_type is None
    assert docs.document_country is None
    assert docs.document_number is None
    assert docs.phone_primary is None
    assert docs.phone_secondary is None
    assert docs.email is None
    assert docs.health_insurance is None
    assert docs.insurance_card_number is None
    assert docs.notes == ""


def test_documents_with_all_fields() -> None:
    docs = PatientDocuments(
        document_type=DocumentType.TAX_ID,
        document_country="BR",
        document_number="123.456.789-00",
        phone_primary=PhoneNumber("+55 91 99582-8523"),
        phone_secondary=PhoneNumber("(91) 3242-1234", PhoneKind.HOME),
        email="maria@example.com",
        health_insurance="Unimed",
        insurance_card_number="1234567890",
        notes="Additional notes.",
    )
    assert docs.document_type is DocumentType.TAX_ID
    assert docs.document_country == "BR"
    assert docs.document_number == "123.456.789-00"
    assert docs.email == "maria@example.com"
    assert docs.health_insurance == "Unimed"


def test_documents_is_frozen() -> None:
    docs = PatientDocuments()
    attr = "notes"
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(docs, attr, "changed")


# ----- Validation: document coherence ------------------------------


def test_document_type_without_country_raises() -> None:
    with pytest.raises(ValueError, match="document_country"):
        PatientDocuments(
            document_type=DocumentType.NATIONAL_ID,
            document_number="12345",
        )


def test_document_type_without_number_raises() -> None:
    with pytest.raises(ValueError, match="document_number"):
        PatientDocuments(
            document_type=DocumentType.NATIONAL_ID,
            document_country="BR",
        )


def test_document_country_without_type_raises() -> None:
    with pytest.raises(ValueError, match="document_country"):
        PatientDocuments(document_country="BR")


def test_document_number_without_type_raises() -> None:
    with pytest.raises(ValueError, match="document_number"):
        PatientDocuments(document_number="12345")


def test_document_country_must_be_two_letters() -> None:
    with pytest.raises(ValueError, match="ISO 3166-1"):
        PatientDocuments(
            document_type=DocumentType.NATIONAL_ID,
            document_country="BRA",
            document_number="12345",
        )


def test_document_country_must_be_uppercase() -> None:
    with pytest.raises(ValueError, match="ISO 3166-1"):
        PatientDocuments(
            document_type=DocumentType.NATIONAL_ID,
            document_country="br",
            document_number="12345",
        )


def test_document_country_must_be_ascii() -> None:
    with pytest.raises(ValueError, match="ISO 3166-1"):
        PatientDocuments(
            document_type=DocumentType.NATIONAL_ID,
            document_country="B\u00c7",  # "BÇ"
            document_number="12345",
        )


def test_document_number_whitespace_only_raises() -> None:
    with pytest.raises(ValueError, match="whitespace"):
        PatientDocuments(
            document_type=DocumentType.NATIONAL_ID,
            document_country="BR",
            document_number="   ",
        )


# ----- Validation: insurance coherence -----------------------------


def test_insurance_without_card_number_raises() -> None:
    with pytest.raises(ValueError, match="insurance_card_number"):
        PatientDocuments(health_insurance="Unimed")


def test_card_number_without_insurance_raises() -> None:
    with pytest.raises(ValueError, match="insurance_card_number"):
        PatientDocuments(insurance_card_number="12345")


def test_insurance_whitespace_only_raises() -> None:
    with pytest.raises(ValueError, match="whitespace"):
        PatientDocuments(
            health_insurance="   ",
            insurance_card_number="12345",
        )


def test_card_number_whitespace_only_raises() -> None:
    with pytest.raises(ValueError, match="whitespace"):
        PatientDocuments(
            health_insurance="Unimed",
            insurance_card_number="   ",
        )


# ----- Equality -----------------------------------------------------


def test_documents_equality_by_value() -> None:
    a = PatientDocuments(notes="x")
    b = PatientDocuments(notes="x")
    assert a == b


def test_documents_with_different_notes_not_equal() -> None:
    a = PatientDocuments(notes="x")
    b = PatientDocuments(notes="y")
    assert a != b
