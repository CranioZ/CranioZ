"""User settings infrastructure.

The SettingsService owns the persistence of user preferences (as opposed
to the packaged defaults in cranioz.config, which are read-only).

This package must not depend on UI, domain, or application layers.
"""

from cranioz.infrastructure.settings.errors import (
    SettingsError,
    SettingsMigrationError,
)
from cranioz.infrastructure.settings.filesystem_settings_service import (
    FilesystemSettingsService,
)
from cranioz.infrastructure.settings.in_memory_settings_service import (
    InMemorySettingsService,
)
from cranioz.infrastructure.settings.migrator import SettingsMigrator
from cranioz.infrastructure.settings.protocol import SettingsService

__all__ = [
    "FilesystemSettingsService",
    "InMemorySettingsService",
    "SettingsError",
    "SettingsMigrationError",
    "SettingsMigrator",
    "SettingsService",
]
