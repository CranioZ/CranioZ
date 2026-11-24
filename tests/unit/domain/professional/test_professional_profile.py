"""Tests for ProfessionalProfile."""

from __future__ import annotations

import pytest

from cranioz.domain.professional.address import Address
from cranioz.domain.professional.professional_profile import ProfessionalProfile
from cranioz.domain.professional.professional_registration import (
    ProfessionalRegistration,
)


def _registration(
    registration_id: str,
    *,
    is_primary: bool,
) -> ProfessionalRegistration:
    return ProfessionalRegistration(
        registration_id=registration_id,
        authority="CRO",
        country_code="BR",
        registration_number=registration_id,
        is_primary=is_primary,
    )


def test_profile_has_empty_optional_state_by_default() -> None:
    profile = ProfessionalProfile(full_name="Dra. Ana Silva")

    assert profile.registrations == ()
    assert profile.address == Address()
    assert profile.regional_profile == "BR"
    assert profile.display_name() == "Dra. Ana Silva"


def test_display_name_prefers_preferred_name() -> None:
    profile = ProfessionalProfile(
        full_name="Ana Carolina Silva",
        preferred_name="Dra. Ana",
    )
    assert profile.display_name() == "Dra. Ana"


def test_profile_is_frozen() -> None:
    profile = ProfessionalProfile(full_name="Dra. Ana Silva")
    with pytest.raises(AttributeError):
        profile.full_name = "Dra. Maria"  # type: ignore[misc]


@pytest.mark.parametrize("full_name", ("", "   "))
def test_full_name_is_required(full_name: str) -> None:
    with pytest.raises(ValueError, match="full_name"):
        ProfessionalProfile(full_name=full_name)


def test_optional_text_rejects_whitespace() -> None:
    with pytest.raises(ValueError, match="preferred_name"):
        ProfessionalProfile(full_name="Dra. Ana Silva", preferred_name="   ")


def test_registration_ids_must_be_unique() -> None:
    with pytest.raises(ValueError, match="unique"):
        ProfessionalProfile(
            full_name="Dra. Ana Silva",
            registrations=(
                _registration("registration-1", is_primary=True),
                _registration("registration-1", is_primary=False),
            ),
        )


def test_registrations_require_exactly_one_primary() -> None:
    with pytest.raises(ValueError, match="exactly one primary"):
        ProfessionalProfile(
            full_name="Dra. Ana Silva",
            registrations=(_registration("registration-1", is_primary=False),),
        )

    with pytest.raises(ValueError, match="exactly one primary"):
        ProfessionalProfile(
            full_name="Dra. Ana Silva",
            registrations=(
                _registration("registration-1", is_primary=True),
                _registration("registration-2", is_primary=True),
            ),
        )


def test_profile_accepts_one_primary_registration() -> None:
    profile = ProfessionalProfile(
        full_name="Dra. Ana Silva",
        registrations=(
            _registration("registration-1", is_primary=True),
            _registration("registration-2", is_primary=False),
        ),
    )

    assert sum(item.is_primary for item in profile.registrations) == 1


def test_address_requires_address_type() -> None:
    with pytest.raises(TypeError, match="Address"):
        ProfessionalProfile(
            full_name="Dra. Ana Silva",
            address="not-an-address",  # type: ignore[arg-type]
        )
