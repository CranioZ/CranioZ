"""Tests for the Professional SQLite foundation."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from cranioz.infrastructure.professional.database import (
    ProfessionalDatabase,
    ProfessionalDatabaseError,
)
from cranioz.infrastructure.professional.migrations import (
    LATEST_PROFESSIONAL_SCHEMA_VERSION,
    ProfessionalIncompatibleSchemaError,
    ProfessionalMigration,
    ProfessionalMigrationError,
    ProfessionalMigrationService,
    current_schema_version,
)


def _database(tmp_path: Path) -> ProfessionalDatabase:
    return ProfessionalDatabase(tmp_path / "professional" / "professional.db")


def test_connect_creates_and_migrates_database(tmp_path: Path) -> None:
    database = _database(tmp_path)

    with database.connect() as connection:
        assert current_schema_version(connection) == LATEST_PROFESSIONAL_SCHEMA_VERSION
        table_names = {
            row[0]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        }

    assert database.path.is_file()
    assert {"professional_profile", "professional_registration"} <= table_names


def test_connection_enables_foreign_keys(tmp_path: Path) -> None:
    database = _database(tmp_path)

    with database.connect() as connection:
        enabled = connection.execute("PRAGMA foreign_keys").fetchone()
        assert enabled is not None
        assert enabled[0] == 1

        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO professional_registration (
                    registration_id,
                    authority,
                    country_code,
                    registration_number
                ) VALUES (?, ?, ?, ?)
                """,
                ("registration-1", "CRM", "BR", "123"),
            )


def test_database_persists_across_reopen(tmp_path: Path) -> None:
    database = _database(tmp_path)
    with database.connect() as connection:
        connection.execute(
            """
            INSERT INTO professional_profile (profile_id, full_name, updated_at)
            VALUES (1, ?, ?)
            """,
            ("Dra. Ana Silva", "2026-11-24T12:00:00Z"),
        )
        connection.commit()

    with database.connect() as reopened:
        row = reopened.execute(
            "SELECT full_name FROM professional_profile WHERE profile_id = 1"
        ).fetchone()

    assert row is not None
    assert row[0] == "Dra. Ana Silva"


def test_only_one_primary_registration_is_allowed(tmp_path: Path) -> None:
    database = _database(tmp_path)

    with database.connect() as connection:
        connection.execute(
            """
            INSERT INTO professional_profile (profile_id, full_name, updated_at)
            VALUES (1, ?, ?)
            """,
            ("Dra. Ana Silva", "2026-11-24T12:00:00Z"),
        )
        insert = """
            INSERT INTO professional_registration (
                registration_id,
                profile_id,
                authority,
                country_code,
                registration_number,
                is_primary
            ) VALUES (?, 1, 'CRM', 'BR', ?, 1)
        """
        connection.execute(insert, ("registration-1", "123"))

        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(insert, ("registration-2", "456"))


def test_newer_schema_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "professional" / "professional.db"
    path.parent.mkdir()
    with sqlite3.connect(path) as connection:
        connection.execute(f"PRAGMA user_version = {LATEST_PROFESSIONAL_SCHEMA_VERSION + 1}")

    with pytest.raises(ProfessionalDatabaseError, match="newer than supported"):
        ProfessionalDatabase(path).connect()


def test_failed_migration_rolls_back_schema_and_version(tmp_path: Path) -> None:
    migration_service = ProfessionalMigrationService(
        (
            ProfessionalMigration(
                version=1,
                statements=(
                    "CREATE TABLE should_roll_back (id INTEGER PRIMARY KEY)",
                    "THIS IS NOT VALID SQL",
                ),
            ),
        )
    )
    database = ProfessionalDatabase(
        tmp_path / "professional.db",
        migration_service=migration_service,
    )

    with pytest.raises(ProfessionalDatabaseError, match="failed to migrate"):
        database.connect()

    with sqlite3.connect(database.path) as connection:
        assert current_schema_version(connection) == 0
        row = connection.execute(
            """
            SELECT COUNT(*)
            FROM sqlite_master
            WHERE type = 'table' AND name = 'should_roll_back'
            """
        ).fetchone()
        assert row is not None
        assert row[0] == 0


def test_existing_database_is_backed_up_before_migration(tmp_path: Path) -> None:
    path = tmp_path / "professional" / "professional.db"
    path.parent.mkdir()
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE legacy_data (value TEXT NOT NULL)")
        connection.execute("INSERT INTO legacy_data(value) VALUES ('preserve-me')")
        connection.commit()

    ProfessionalDatabase(path).connect().close()
    backups = tuple(path.parent.glob("professional.bak.*.db"))

    assert len(backups) == 1
    with sqlite3.connect(backups[0]) as backup:
        row = backup.execute("SELECT value FROM legacy_data").fetchone()
    assert row == ("preserve-me",)


def test_migration_versions_must_be_contiguous() -> None:
    with pytest.raises(ValueError, match="contiguous"):
        ProfessionalMigrationService(
            (
                ProfessionalMigration(version=1, statements=("SELECT 1",)),
                ProfessionalMigration(version=3, statements=("SELECT 2",)),
            )
        )


def test_future_schema_error_is_specific() -> None:
    error = ProfessionalIncompatibleSchemaError("future")
    assert isinstance(error, ProfessionalMigrationError)
