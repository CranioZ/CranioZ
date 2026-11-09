"""Settings errors."""

from __future__ import annotations


class SettingsError(Exception):
    """Base error for the settings subsystem."""


class SettingsMigrationError(SettingsError):
    """Raised when a settings file cannot be migrated to the current schema."""
