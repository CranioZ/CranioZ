"""Tests for the SQLite Professional repository."""

from __future__ import annotations

import sqlite3
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

import pytest

from cranioz.application.professional import (
    ProfessionalCorrupted,
    ProfessionalService,
    ProfessionalStorageError,
    UpdateProfessionalProfileCommand,
    UpdateProfessionalProfileHandler,
)
from cranioz.domain.professional import (
    Address,
    ProfessionalProfile,
    ProfessionalRegistration,
)
from cranioz.infrastructure.professional import (
    ProfessionalDatabase,
    SqliteProfessionalRepository,
)


def _profile(name: str = "Dra. Ana Silva") -> ProfessionalProfile:
    return ProfessionalProfile(
        full_name=name,
        preferred_name="Dra. Ana",
        salutation="Dra.",
        registrations=(
            ProfessionalRegistration(
                registration_id="registration-1",
                authority="CRM",
                country_code="BR",
                region_code="BR-SP",
                registration_number="123456",
                is_primary=True,
            ),
            ProfessionalRegistration(
                registration_id="registration-2",
                authority="CRO",
                country_code="BR",
                region_code="BR-RJ",
                registration_number="654321",
                is_primary=False,
            ),
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


def _database(tmp_path: Path) -> ProfessionalDatabase:
    return ProfessionalDatabase(tmp_path / "professional" / "professional.db")


def _repository(
    tmp_path: Path,
    *,
    clock: Callable[[], datetime] | None = None,
) -> tuple[SqliteProfessionalRepository, ProfessionalDatabase]:
    database = _database(tmp_path)
    repository = SqliteProfessionalRepository(database, clock=clock)
    return repository, database


def test_initialize_prepares_profile_storage(tmp_path: Path) -> None:
    repository, database = _repository(tmp_path)

    repository.initialize()

    assert database.path.is_file()
    assert repository.load_profile() is None


def test_save_and_load_full_profile(tmp_path: Path) -> None:
    repository, _ = _repository(tmp_path)
    profile = _profile()

    repository.save_profile(profile)

    assert repository.load_profile() == profile


def test_save_replaces_registration_set(tmp_path: Path) -> None:
    repository, database = _repository(tmp_path)
    repository.save_profile(_profile())
    replacement = ProfessionalProfile(full_name="Dr. Bruno Souza")

    repository.save_profile(replacement)

    assert repository.load_profile() == replacement
    with database.connect() as connection:
        count = connection.execute("SELECT COUNT(*) FROM professional_registration").fetchone()
    assert count is not None
    assert count[0] == 0


def test_profile_survives_service_restart(tmp_path: Path) -> None:
    profile = _profile()
    first_repository, database = _repository(tmp_path)
    first_service = ProfessionalService(first_repository)
    first_service.update_profile(profile)

    second_repository = SqliteProfessionalRepository(database)
    second_service = ProfessionalService(second_repository)

    assert second_service.get_profile() == profile


def test_profile_data_survives_reopened_database_file(tmp_path: Path) -> None:
    profile = _profile()
    repository, database = _repository(tmp_path)

    repository.save_profile(profile)

    reopened = SqliteProfessionalRepository(ProfessionalDatabase(database.path))
    reopened.initialize()
    assert reopened.load_profile() == profile


def test_update_command_round_trip_through_sqlite(tmp_path: Path) -> None:
    repository, _ = _repository(tmp_path)
    service = ProfessionalService(repository)
    handler = UpdateProfessionalProfileHandler(service)
    profile = _profile()

    result = handler.handle(UpdateProfessionalProfileCommand(profile=profile))

    assert result is profile
    assert service.get_profile() == profile


def test_updated_at_is_stored_as_utc(tmp_path: Path) -> None:
    fixed = datetime(2026, 11, 24, 15, 30, tzinfo=UTC)
    repository, database = _repository(tmp_path, clock=lambda: fixed)

    repository.save_profile(_profile())

    with database.connect() as connection:
        row = connection.execute(
            "SELECT updated_at FROM professional_profile WHERE profile_id = 1"
        ).fetchone()
    assert row is not None
    assert row[0] == "2026-11-24T15:30:00.000000Z"


def test_save_rolls_back_profile_and_registrations_on_failure(
    tmp_path: Path,
) -> None:
    repository, database = _repository(tmp_path)
    original = _profile()
    repository.save_profile(original)
    with database.connect() as connection:
        connection.execute(
            """
            CREATE TRIGGER reject_registration
            BEFORE INSERT ON professional_registration
            BEGIN
                SELECT RAISE(ABORT, 'registration rejected');
            END
            """
        )
        connection.commit()

    with pytest.raises(ProfessionalStorageError, match="cannot save"):
        repository.save_profile(
            ProfessionalProfile(
                full_name="Dr. Bruno Souza",
                registrations=(
                    ProfessionalRegistration(
                        registration_id="registration-new",
                        authority="CRO",
                        country_code="BR",
                        region_code="BR-SP",
                        registration_number="999",
                        is_primary=True,
                    ),
                ),
            )
        )

    assert repository.load_profile() == original


def test_invalid_persisted_profile_is_reported_as_corrupted(
    tmp_path: Path,
) -> None:
    repository, database = _repository(tmp_path)
    repository.initialize()
    with database.connect() as connection:
        connection.execute(
            """
            INSERT INTO professional_profile (
                profile_id,
                full_name,
                regional_profile,
                updated_at
            ) VALUES (1, 'Dra. Ana Silva', '   ', '2026-11-24T12:00:00Z')
            """
        )
        connection.commit()

    with pytest.raises(ProfessionalCorrupted):
        repository.load_profile()


def test_unopenable_storage_is_reported_at_application_boundary(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "professional" / "professional.db"
    database_path.mkdir(parents=True)
    repository = SqliteProfessionalRepository(ProfessionalDatabase(database_path))

    with pytest.raises(ProfessionalStorageError, match="initialize"):
        repository.initialize()


def test_database_failure_is_reported_as_storage_error(
    tmp_path: Path,
) -> None:
    repository, database = _repository(tmp_path)
    repository.initialize()
    with sqlite3.connect(database.path) as connection:
        connection.execute(
            """
            INSERT INTO professional_profile (profile_id, full_name, updated_at)
            VALUES (1, 'Dra. Ana Silva', '2026-11-24T12:00:00Z')
            """
        )
        connection.execute("DROP TABLE professional_registration")
        connection.commit()

    with pytest.raises(ProfessionalStorageError, match="cannot load"):
        repository.load_profile()
