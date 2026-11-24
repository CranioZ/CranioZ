"""Versioned SQLite migrations for the Professional database."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass


class ProfessionalMigrationError(RuntimeError):
    """Raised when a Professional database migration cannot complete."""


class ProfessionalIncompatibleSchemaError(ProfessionalMigrationError):
    """Raised when the database schema is newer than this application supports."""


@dataclass(frozen=True)
class ProfessionalMigration:
    """One ordered, atomic Professional schema migration."""

    version: int
    statements: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.version < 1:
            raise ValueError("migration version must be positive")
        if not self.statements:
            raise ValueError("migration must contain at least one statement")


_VERSION_1 = ProfessionalMigration(
    version=1,
    statements=(
        """
        CREATE TABLE professional_profile (
            profile_id INTEGER PRIMARY KEY CHECK (profile_id = 1),
            full_name TEXT NOT NULL CHECK (length(trim(full_name)) > 0),
            preferred_name TEXT,
            salutation TEXT,
            email TEXT,
            phone TEXT,
            practice_name TEXT,
            address_street TEXT,
            address_number TEXT,
            address_complement TEXT,
            address_district TEXT,
            address_city TEXT,
            address_state TEXT,
            address_postal_code TEXT,
            address_country TEXT,
            regional_profile TEXT NOT NULL DEFAULT 'BR',
            document_language TEXT,
            logo_reference TEXT,
            signature_reference TEXT,
            updated_at TEXT NOT NULL
        )
        """,
        """
        CREATE TABLE professional_registration (
            registration_id TEXT PRIMARY KEY
                CHECK (length(trim(registration_id)) > 0),
            profile_id INTEGER NOT NULL DEFAULT 1,
            authority TEXT NOT NULL
                CHECK (length(trim(authority)) > 0),
            country_code TEXT NOT NULL
                CHECK (length(country_code) = 2),
            region_code TEXT,
            registration_number TEXT NOT NULL
                CHECK (length(trim(registration_number)) > 0),
            is_primary INTEGER NOT NULL DEFAULT 0
                CHECK (is_primary IN (0, 1)),
            FOREIGN KEY (profile_id)
                REFERENCES professional_profile(profile_id)
                ON DELETE CASCADE
        )
        """,
        """
        CREATE UNIQUE INDEX professional_registration_one_primary
        ON professional_registration(profile_id)
        WHERE is_primary = 1
        """,
    ),
)

MIGRATIONS: tuple[ProfessionalMigration, ...] = (_VERSION_1,)
LATEST_PROFESSIONAL_SCHEMA_VERSION = MIGRATIONS[-1].version


def current_schema_version(connection: sqlite3.Connection) -> int:
    """Return the schema version stored in SQLite ``user_version``."""
    row = connection.execute("PRAGMA user_version").fetchone()
    if row is None:
        raise ProfessionalMigrationError("SQLite did not return user_version")
    return int(row[0])


class ProfessionalMigrationService:
    """Applies Professional migrations in order and atomically."""

    def __init__(
        self,
        migrations: tuple[ProfessionalMigration, ...] = MIGRATIONS,
    ) -> None:
        if not migrations:
            raise ValueError("at least one migration is required")

        expected = tuple(range(1, len(migrations) + 1))
        versions = tuple(migration.version for migration in migrations)
        if versions != expected:
            raise ValueError(f"migration versions must be contiguous from 1, got {versions!r}")
        self._migrations = migrations

    @property
    def latest_version(self) -> int:
        return self._migrations[-1].version

    def migrate(self, connection: sqlite3.Connection) -> None:
        """Migrate the connection to the latest supported schema version."""
        installed = current_schema_version(connection)
        if installed > self.latest_version:
            raise ProfessionalIncompatibleSchemaError(
                f"Professional schema {installed} is newer than supported "
                f"version {self.latest_version}"
            )

        for migration in self._migrations:
            if migration.version <= installed:
                continue

            try:
                connection.execute("BEGIN IMMEDIATE")
                for statement in migration.statements:
                    connection.execute(statement)
                connection.execute(f"PRAGMA user_version = {migration.version}")
                connection.commit()
            except Exception as exc:
                connection.rollback()
                raise ProfessionalMigrationError(
                    f"failed to migrate Professional database to schema {migration.version}: {exc}"
                ) from exc
