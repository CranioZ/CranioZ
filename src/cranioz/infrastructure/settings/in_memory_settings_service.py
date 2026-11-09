"""In-memory SettingsService.

Intended for tests and debug scripts. ``save()`` and ``reload()`` are
no-ops that only log a debug line.
"""

from __future__ import annotations

import logging
from typing import Any, TypeVar

from PySide6.QtCore import QObject, Signal

from cranioz.infrastructure.settings._store import SettingsStore
from cranioz.infrastructure.settings.migrator import (
    CURRENT_SCHEMA_VERSION,
    SettingsMigrator,
)

T = TypeVar("T")

_logger = logging.getLogger(__name__)


class InMemorySettingsService(QObject):
    """SettingsService backed by memory only."""

    changed = Signal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._store = SettingsStore(schema_version=CURRENT_SCHEMA_VERSION)
        self._migrator = SettingsMigrator()

    # ----- SettingsService --------------------------------------------

    def get(self, key: str, default: T) -> T:
        return self._store.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._store.set(key, value)
        self.changed.emit(key)

    def save(self) -> None:
        _logger.debug("InMemorySettingsService.save(): no-op")

    def reload(self) -> None:
        _logger.debug("InMemorySettingsService.reload(): no-op")

    # ----- Test helpers ----------------------------------------------

    def seed(self, key: str, value: Any) -> None:
        """Set a value without emitting ``changed``.

        Used by tests that need to pre-populate state.
        """
        self._store.set(key, value)
