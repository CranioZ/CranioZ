"""Settings schema migration.

Mirrors the shape of ``cranioz.config.migration.ConfigMigrator`` but is
a separate class, because configuration defaults and user settings are
distinct persisted artifacts with independent lifecycles.

Rules:
- A file at the current schema version is returned unchanged.
- A file at a newer version is rejected with ``SettingsMigrationError``.
- A file at an older version is migrated step by step.
"""

from __future__ import annotations

from typing import Any

from cranioz.infrastructure.settings.errors import SettingsMigrationError

CURRENT_SCHEMA_VERSION = 1


class SettingsMigrator:
    """Migrates a settings dictionary to the current schema version."""

    def migrate(self, data: dict[str, Any], from_version: int) -> dict[str, Any]:
        if from_version == CURRENT_SCHEMA_VERSION:
            return data

        if from_version > CURRENT_SCHEMA_VERSION:
            raise SettingsMigrationError(
                f"settings schema {from_version} is newer than supported ({CURRENT_SCHEMA_VERSION})"
            )

        # Extension point for future migrations (e.g. 1 -> 2).
        raise SettingsMigrationError(
            f"no migration defined from schema {from_version} to {CURRENT_SCHEMA_VERSION}"
        )
