"""PatientDocuments (§2 Documentos e Contato).

Identity documents, contact information, and health insurance data.

The section carries:

- One identity document (type, country, number).
- Two phone numbers (primary and optional secondary), each with a
  kind.
- An optional email.
- Optional health insurance data (name and card number).

Conditional rules enforced by this section:

- If ``document_type`` is set, both ``document_country`` and
  ``document_number`` must be set and non-empty.
- If ``document_type`` is ``None``, both ``document_country`` and
  ``document_number`` must be ``None``.
- ``document_country``, when set, must be an ISO 3166-1 alpha-2
  code: two uppercase ASCII letters (e.g., ``"BR"``, ``"US"``,
  ``"PT"``).
- If ``health_insurance`` is set, ``insurance_card_number`` must be
  set and non-empty.
- If ``health_insurance`` is ``None``, ``insurance_card_number``
  must be ``None``.

These rules depend only on fields inside this section, so they are
enforced here, not in the Patient aggregate.

See ADR-0004 §5 for the design rationale.
"""

from __future__ import annotations

from dataclasses import dataclass

from cranioz.domain.patient.enums.document_type import DocumentType
from cranioz.domain.patient.value_objects.phone_number import PhoneNumber


@dataclass(frozen=True)
class PatientDocuments:
    """Documents and contact information of the patient (§2)."""

    document_type: DocumentType | None = None
    document_country: str | None = None
    document_number: str | None = None
    phone_primary: PhoneNumber | None = None
    phone_secondary: PhoneNumber | None = None
    email: str | None = None
    health_insurance: str | None = None
    insurance_card_number: str | None = None
    notes: str = ""

    def __post_init__(self) -> None:
        self._validate_document()
        self._validate_insurance()

    def _validate_document(self) -> None:
        if self.document_type is None:
            if self.document_country is not None:
                raise ValueError("document_country must be None when document_type is None")
            if self.document_number is not None:
                raise ValueError("document_number must be None when document_type is None")
            return

        if not self.document_country:
            raise ValueError("document_country is required when document_type is set")
        if not self.document_number:
            raise ValueError("document_number is required when document_type is set")
        if not self.document_number.strip():
            raise ValueError("document_number must not be whitespace only")

        # ISO 3166-1 alpha-2: exactly two uppercase ASCII letters.
        if (
            len(self.document_country) != 2
            or not self.document_country.isascii()
            or not self.document_country.isupper()
        ):
            raise ValueError(
                "document_country must be an ISO 3166-1 alpha-2 code "
                f"(two uppercase ASCII letters), got {self.document_country!r}"
            )

    def _validate_insurance(self) -> None:
        if self.health_insurance is None:
            if self.insurance_card_number is not None:
                raise ValueError("insurance_card_number must be None when health_insurance is None")
            return

        if not self.health_insurance.strip():
            raise ValueError("health_insurance must not be whitespace only")
        if not self.insurance_card_number:
            raise ValueError("insurance_card_number is required when health_insurance is set")
        if not self.insurance_card_number.strip():
            raise ValueError("insurance_card_number must not be whitespace only")
