"""SQLite implementation of the Professional repository port."""

from __future__ import annotations

import sqlite3
from collections.abc import Callable
from datetime import UTC, datetime

from cranioz.application.professional.errors import (
    ProfessionalCorrupted,
    ProfessionalRepositoryError,
    ProfessionalStorageError,
)
from cranioz.domain.professional.address import Address
from cranioz.domain.professional.professional_profile import ProfessionalProfile
from cranioz.domain.professional.professional_registration import (
    ProfessionalRegistration,
)
from cranioz.infrastructure.professional.database import (
    ProfessionalDatabase,
    ProfessionalDatabaseError,
)

_PROFILE_ID = 1


class SqliteProfessionalRepository:
    """Persist the single installation profile in the Professional database."""

    def __init__(
        self,
        database: ProfessionalDatabase,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._database = database
        self._clock = clock or (lambda: datetime.now(UTC))

    def initialize(self) -> None:
        connection: sqlite3.Connection | None = None
        try:
            connection = self._database.connect()
        except ProfessionalDatabaseError as exc:
            raise ProfessionalStorageError("cannot initialize Professional storage") from exc
        finally:
            if connection is not None:
                connection.close()

    def load_profile(self) -> ProfessionalProfile | None:
        connection: sqlite3.Connection | None = None
        try:
            connection = self._database.connect()
            row = connection.execute(
                """
                SELECT
                    full_name,
                    preferred_name,
                    salutation,
                    email,
                    phone,
                    practice_name,
                    address_street,
                    address_number,
                    address_complement,
                    address_district,
                    address_city,
                    address_state,
                    address_postal_code,
                    address_country,
                    regional_profile,
                    document_language,
                    logo_reference,
                    signature_reference
                FROM professional_profile
                WHERE profile_id = ?
                """,
                (_PROFILE_ID,),
            ).fetchone()
            if row is None:
                return None

            registrations = self._load_registrations(connection)
            return ProfessionalProfile(
                full_name=str(row[0]),
                preferred_name=self._optional_text(row[1]),
                salutation=self._optional_text(row[2]),
                email=self._optional_text(row[3]),
                phone=self._optional_text(row[4]),
                practice_name=self._optional_text(row[5]),
                address=Address(
                    street=self._optional_text(row[6]),
                    number=self._optional_text(row[7]),
                    complement=self._optional_text(row[8]),
                    district=self._optional_text(row[9]),
                    city=self._optional_text(row[10]),
                    state=self._optional_text(row[11]),
                    postal_code=self._optional_text(row[12]),
                    country=self._optional_text(row[13]),
                ),
                regional_profile=str(row[14]),
                document_language=self._optional_text(row[15]),
                logo_reference=self._optional_text(row[16]),
                signature_reference=self._optional_text(row[17]),
                registrations=registrations,
            )
        except ProfessionalRepositoryError:
            raise
        except (ValueError, TypeError) as exc:
            raise ProfessionalCorrupted("persisted Professional profile is invalid") from exc
        except (ProfessionalDatabaseError, sqlite3.Error) as exc:
            raise ProfessionalStorageError("cannot load Professional profile") from exc
        finally:
            if connection is not None:
                connection.close()

    def save_profile(self, profile: ProfessionalProfile) -> None:
        connection: sqlite3.Connection | None = None
        try:
            connection = self._database.connect()
            connection.execute("BEGIN IMMEDIATE")
            self._upsert_profile(connection, profile)
            connection.execute(
                "DELETE FROM professional_registration WHERE profile_id = ?",
                (_PROFILE_ID,),
            )
            connection.executemany(
                """
                INSERT INTO professional_registration (
                    registration_id,
                    profile_id,
                    authority,
                    country_code,
                    region_code,
                    registration_number,
                    is_primary
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    (
                        registration.registration_id,
                        _PROFILE_ID,
                        registration.authority,
                        registration.country_code,
                        registration.region_code,
                        registration.registration_number,
                        int(registration.is_primary),
                    )
                    for registration in profile.registrations
                ),
            )
            connection.commit()
        except ProfessionalRepositoryError:
            if connection is not None:
                connection.rollback()
            raise
        except (ProfessionalDatabaseError, sqlite3.Error) as exc:
            if connection is not None:
                connection.rollback()
            raise ProfessionalStorageError("cannot save Professional profile") from exc
        finally:
            if connection is not None:
                connection.close()

    def _upsert_profile(
        self,
        connection: sqlite3.Connection,
        profile: ProfessionalProfile,
    ) -> None:
        connection.execute(
            """
            INSERT INTO professional_profile (
                profile_id,
                full_name,
                preferred_name,
                salutation,
                email,
                phone,
                practice_name,
                address_street,
                address_number,
                address_complement,
                address_district,
                address_city,
                address_state,
                address_postal_code,
                address_country,
                regional_profile,
                document_language,
                logo_reference,
                signature_reference,
                updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(profile_id) DO UPDATE SET
                full_name = excluded.full_name,
                preferred_name = excluded.preferred_name,
                salutation = excluded.salutation,
                email = excluded.email,
                phone = excluded.phone,
                practice_name = excluded.practice_name,
                address_street = excluded.address_street,
                address_number = excluded.address_number,
                address_complement = excluded.address_complement,
                address_district = excluded.address_district,
                address_city = excluded.address_city,
                address_state = excluded.address_state,
                address_postal_code = excluded.address_postal_code,
                address_country = excluded.address_country,
                regional_profile = excluded.regional_profile,
                document_language = excluded.document_language,
                logo_reference = excluded.logo_reference,
                signature_reference = excluded.signature_reference,
                updated_at = excluded.updated_at
            """,
            (
                _PROFILE_ID,
                profile.full_name,
                profile.preferred_name,
                profile.salutation,
                profile.email,
                profile.phone,
                profile.practice_name,
                profile.address.street,
                profile.address.number,
                profile.address.complement,
                profile.address.district,
                profile.address.city,
                profile.address.state,
                profile.address.postal_code,
                profile.address.country,
                profile.regional_profile,
                profile.document_language,
                profile.logo_reference,
                profile.signature_reference,
                self._timestamp(),
            ),
        )

    @staticmethod
    def _load_registrations(
        connection: sqlite3.Connection,
    ) -> tuple[ProfessionalRegistration, ...]:
        rows = connection.execute(
            """
            SELECT
                registration_id,
                authority,
                country_code,
                region_code,
                registration_number,
                is_primary
            FROM professional_registration
            WHERE profile_id = ?
            ORDER BY rowid
            """,
            (_PROFILE_ID,),
        ).fetchall()
        return tuple(
            ProfessionalRegistration(
                registration_id=str(row[0]),
                authority=str(row[1]),
                country_code=str(row[2]),
                region_code=SqliteProfessionalRepository._optional_text(row[3]),
                registration_number=str(row[4]),
                is_primary=bool(row[5]),
            )
            for row in rows
        )

    @staticmethod
    def _optional_text(value: object) -> str | None:
        return None if value is None else str(value)

    def _timestamp(self) -> str:
        now = self._clock()
        if now.tzinfo is None:
            now = now.replace(tzinfo=UTC)
        return now.astimezone(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")
