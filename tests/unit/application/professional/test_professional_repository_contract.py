"""Contract tests for Professional repository implementations."""

from __future__ import annotations

import pytest

from cranioz.application.professional.in_memory_repository import (
    InMemoryProfessionalRepository,
)
from cranioz.application.professional.repository import ProfessionalRepository
from cranioz.domain.professional import (
    Address,
    ProfessionalProfile,
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
        region_code="BR-SP",
        registration_number=f"number-{registration_id}",
        is_primary=is_primary,
    )


def _profile(name: str = "Dra. Ana Silva") -> ProfessionalProfile:
    return ProfessionalProfile(
        full_name=name,
        preferred_name="Dra. Ana",
        salutation="Dra.",
        registrations=(
            _registration("registration-1", is_primary=True),
            _registration("registration-2", is_primary=False),
        ),
        email="ana@example.com",
        phone="+55 11 99999-0000",
        address=Address(
            postal_code="01001-000",
            street="Rua Exemplo",
            number="100",
            complement="Sala 2",
            district="Centro",
            city="Sao Paulo",
            state="SP",
            country="BR",
        ),
        practice_name="Clinica Exemplo",
        logo_reference="attachments/logo.png",
        signature_reference="attachments/signature.png",
        regional_profile="BR",
        document_language="pt-BR",
    )


@pytest.fixture
def repository() -> ProfessionalRepository:
    return InMemoryProfessionalRepository()


def test_repository_satisfies_protocol(
    repository: ProfessionalRepository,
) -> None:
    assert isinstance(repository, ProfessionalRepository)


def test_initialize_is_idempotent(repository: ProfessionalRepository) -> None:
    repository.initialize()
    repository.initialize()


def test_empty_repository_returns_no_profile(
    repository: ProfessionalRepository,
) -> None:
    assert repository.load_profile() is None


def test_save_and_load_round_trip(
    repository: ProfessionalRepository,
) -> None:
    profile = _profile()

    repository.save_profile(profile)

    assert repository.load_profile() == profile


def test_save_replaces_profile_and_registrations(
    repository: ProfessionalRepository,
) -> None:
    repository.save_profile(_profile("Dra. Ana Silva"))
    replacement = ProfessionalProfile(
        full_name="Dr. Bruno Souza",
        registrations=(_registration("registration-new", is_primary=True),),
    )

    repository.save_profile(replacement)

    assert repository.load_profile() == replacement


def test_profile_may_have_no_registrations(
    repository: ProfessionalRepository,
) -> None:
    profile = ProfessionalProfile(full_name="Dra. Ana Silva")

    repository.save_profile(profile)

    assert repository.load_profile() == profile
