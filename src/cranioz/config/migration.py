"""Configuration schema migration.

In this phase, the schema is 1 and there are no migrations.
This class exists as a future extension point.
"""

from __future__ import annotations

from typing import Any


CURRENT_SCHEMA_VERSION = 1


class ConfigMigrationError(Exception):
    """Error during configuration migration."""


class ConfigMigrator:
    def migrate(self, data: dict[str, Any], from_version: int) -> dict[str, Any]:
        if from_version == CURRENT_SCHEMA_VERSION:
            return data

        if from_version > CURRENT_SCHEMA_VERSION:
            raise ConfigMigrationError(
                f"schema {from_version} is newer than supported "
                f"({CURRENT_SCHEMA_VERSION})"
            )

        # Extension point for future migrations.
        raise ConfigMigrationError(
            f"no migration defined from schema {from_version} "
            f"to {CURRENT_SCHEMA_VERSION}"
        )