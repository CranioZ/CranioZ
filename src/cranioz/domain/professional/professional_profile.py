"""Professional profile aggregate."""

from __future__ import annotations

from dataclasses import dataclass, field

from cranioz.domain.professional.address import Address
from cranioz.domain.professional.professional_registration import (
    ProfessionalRegistration,
)


@dataclass(frozen=True)
class ProfessionalProfile:
    """Professional and practice information used in generated documents."""

    full_name: str
    preferred_name: str | None = None
    salutation: str | None = None
    registrations: tuple[ProfessionalRegistration, ...] = field(default_factory=tuple)
    email: str | None = None
    phone: str | None = None
    address: Address = field(default_factory=Address)
    practice_name: str | None = None
    logo_reference: str | None = None
    signature_reference: str | None = None
    regional_profile: str = "BR"
    document_language: str | None = None

    def __post_init__(self) -> None:
        self._require_text(self.full_name, "full_name")
        for field_name in (
            "preferred_name",
            "salutation",
            "email",
            "phone",
            "practice_name",
            "logo_reference",
            "signature_reference",
            "regional_profile",
            "document_language",
        ):
            self._validate_optional_text(field_name)

        if not isinstance(self.address, Address):
            raise TypeError("address must be an Address")
        if not isinstance(self.registrations, tuple):
            raise TypeError("registrations must be a tuple")
        if any(
            not isinstance(registration, ProfessionalRegistration)
            for registration in self.registrations
        ):
            raise TypeError("registrations must contain ProfessionalRegistration values")

        registration_ids = [item.registration_id for item in self.registrations]
        if len(registration_ids) != len(set(registration_ids)):
            raise ValueError("registration_id values must be unique")

        primary_count = sum(item.is_primary for item in self.registrations)
        if self.registrations and primary_count != 1:
            raise ValueError(
                "exactly one primary registration is required when registrations exist"
            )

    def display_name(self) -> str:
        """Return the preferred display name with fallback to full name."""
        return self.preferred_name or self.full_name

    @staticmethod
    def _require_text(value: str, field_name: str) -> None:
        if not value:
            raise ValueError(f"{field_name} must not be empty")
        if not value.strip():
            raise ValueError(f"{field_name} must not be whitespace only")

    def _validate_optional_text(self, field_name: str) -> None:
        value = getattr(self, field_name)
        if value is not None and not value.strip():
            raise ValueError(f"{field_name} must not be whitespace only when set")
