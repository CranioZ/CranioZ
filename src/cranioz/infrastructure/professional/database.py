"""SQLite database lifecycle for the Professional Module."""

from __future__ import annotations

import logging
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from cranioz.infrastructure.professional.migrations import (
    ProfessionalMigrationService,
    current_schema_version,
)

_logger = logging.getLogger(__name__)


class ProfessionalDatabaseError(RuntimeError):
    """Raised when the Professional database cannot be opened or initialized."""


class ProfessionalDatabase:
    """Owns the SQLite file and migrates it before returning a connection."""

    def __init__(
        self,
        path: Path,
        *,
        migration_service: ProfessionalMigrationService | None = None,
    ) -> None:
        self._path = path
        self._migration_service = migration_service or ProfessionalMigrationService()

    @property
    def path(self) -> Path:
        return self._path

    def connect(self) -> sqlite3.Connection:
        """Open, configure, back up when needed, and migrate the database."""
        connection: sqlite3.Connection | None = None
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            connection = sqlite3.connect(self._path)
            connection.row_factory = sqlite3.Row
            self._configure(connection)

            installed = current_schema_version(connection)
            if installed < self._migration_service.latest_version and self._has_user_schema(
                connection
            ):
                self._backup(connection)

            self._migration_service.migrate(connection)
            return connection
        except Exception as exc:
            if connection is not None:
                connection.close()
            message = f"cannot open Professional database at {self._path}: {exc}"
            raise ProfessionalDatabaseError(message) from exc

    @staticmethod
    def _configure(connection: sqlite3.Connection) -> None:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 5000")
        try:
            connection.execute("PRAGMA journal_mode = WAL").fetchone()
        except sqlite3.DatabaseError:
            _logger.warning(
                "SQLite WAL journal mode is unavailable; continuing with default",
                exc_info=True,
            )

    @staticmethod
    def _has_user_schema(connection: sqlite3.Connection) -> bool:
        row = connection.execute(
            """
            SELECT COUNT(*)
            FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
            """
        ).fetchone()
        return row is not None and int(row[0]) > 0

    def _backup(self, source: sqlite3.Connection) -> Path:
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
        backup_path = self._path.with_name(f"{self._path.stem}.bak.{timestamp}{self._path.suffix}")
        try:
            with sqlite3.connect(backup_path) as destination:
                source.backup(destination)
        except Exception as exc:
            raise ProfessionalDatabaseError(
                f"cannot back up Professional database before migration: {exc}"
            ) from exc

        _logger.info("Professional database backup created at %s", backup_path)
        return backup_path
