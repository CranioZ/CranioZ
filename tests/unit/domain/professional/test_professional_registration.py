"""Tests for ProfessionalRegistration."""

from __future__ import annotations

import pytest

from cranioz.domain.professional.professional_registration import (
    ProfessionalRegistration,
)


def test_registration_normalizes_country_region_and_authority() -> None:
    registration = ProfessionalRegistration(
        registration_id="registration-1",
        authority=" crm ",
        country_code="br",
        region_code="br-sp",
        registration_number="123456",
        is_primary=True,
    )

    assert registration.authority == "CRM"
    assert registration.country_code == "BR"
    assert registration.region_code == "BR-SP"
    assert registration.is_primary is True


def test_registration_is_frozen() -> None:
    registration = ProfessionalRegistration(
        registration_id="registration-1",
        authority="CRO",
        country_code="BR",
        registration_number="123456",
    )
    with pytest.raises(AttributeError):
        registration.authority = "CRM"  # type: ignore[misc]


@pytest.mark.parametrize(
    ("field_name", "value"),
    (
        ("registration_id", ""),
        ("registration_id", "   "),
        ("authority", ""),
        ("registration_number", ""),
    ),
)
def test_required_text_fields_are_validated(field_name: str, value: str) -> None:
    values = {
        "registration_id": "registration-1",
        "authority": "CRO",
        "country_code": "BR",
        "registration_number": "123456",
    }
    values[field_name] = value

    with pytest.raises(ValueError, match=field_name):
        ProfessionalRegistration(**values)  # type: ignore[arg-type]


def test_country_code_must_have_two_letters() -> None:
    with pytest.raises(ValueError, match="country_code"):
        ProfessionalRegistration(
            registration_id="registration-1",
            authority="CRO",
            country_code="BRA",
            registration_number="123456",
        )


def test_region_code_uses_iso_3166_2_form() -> None:
    with pytest.raises(ValueError, match="ISO 3166-2"):
        ProfessionalRegistration(
            registration_id="registration-1",
            authority="CRM",
            country_code="BR",
            region_code="SP",
            registration_number="123456",
        )


def test_brazilian_crm_requires_region() -> None:
    with pytest.raises(ValueError, match="Brazilian CRM"):
        ProfessionalRegistration(
            registration_id="registration-1",
            authority="CRM",
            country_code="BR",
            registration_number="123456",
        )


def test_is_primary_must_be_bool() -> None:
    with pytest.raises(TypeError, match="is_primary"):
        ProfessionalRegistration(
            registration_id="registration-1",
            authority="CRO",
            country_code="BR",
            registration_number="123456",
            is_primary=1,  # type: ignore[arg-type]
        )
