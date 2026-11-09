"""Filesystem SettingsService.

Persists a single JSON document at ``user_settings_path``.

Behaviour on load:

- File missing -> empty in-memory state (``get`` returns defaults).
- File unreadable / invalid JSON / unknown schema -> WARNING,
  empty in-memory state, the file is NOT overwritten until the next
  explicit ``save()``.
- File at an older schema -> migrated via ``SettingsMigrator``.

The service never raises from the constructor. Appearance configuration
MUST NOT prevent the application from starting.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, TypeVar

from PySide6.QtCore import QObject, Signal

from cranioz.infrastructure.settings._store import SettingsStore
from cranioz.infrastructure.settings.errors import SettingsMigrationError
from cranioz.infrastructure.settings.keys import KNOWN_KEYS
from cranioz.infrastructure.settings.migrator import (
    CURRENT_SCHEMA_VERSION,
    SettingsMigrator,
)

T = TypeVar("T")

_logger = logging.getLogger(__name__)


class FilesystemSettingsService(QObject):
    """SettingsService backed by a JSON file."""

    changed = Signal(str)

    def __init__(
        self,
        path: Path,
        *,
        migrator: SettingsMigrator | None = None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._path = path
        self._migrator = migrator or SettingsMigrator()
        self._store = SettingsStore(schema_version=CURRENT_SCHEMA_VERSION)
        self._load()

    # ----- SettingsService --------------------------------------------

    def get(self, key: str, default: T) -> T:
        return self._store.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._store.set(key, value)
        self.changed.emit(key)

    def save(self) -> None:
        document = self._store.to_document()
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self._path.with_suffix(self._path.suffix + ".tmp")
            with tmp.open("w", encoding="utf-8") as fh:
                json.dump(document, fh, indent=2, sort_keys=True)
                fh.write("\n")
            tmp.replace(self._path)
        except OSError as exc:
            _logger.warning(
                "cannot write settings file %s: %s",
                self._path,
                exc,
            )

    def reload(self) -> None:
        self._store = SettingsStore(schema_version=CURRENT_SCHEMA_VERSION)
        self._load()
        # Re-emit for every known key so consumers refresh.

        for key in sorted(KNOWN_KEYS):
            self.changed.emit(key)

    # ----- Internal ---------------------------------------------------

    def _load(self) -> None:
        if not self._path.exists():
            _logger.debug(
                "settings file %s does not exist; using defaults",
                self._path,
            )
            return

        try:
            with self._path.open("r", encoding="utf-8") as fh:
                document = json.load(fh)
        except (OSError, json.JSONDecodeError) as exc:
            _logger.warning(
                "cannot read settings file %s: %s; using defaults",
                self._path,
                exc,
            )
            return

        if not isinstance(document, dict):
            _logger.warning(
                "settings file %s is not a JSON object; using defaults",
                self._path,
            )
            return

        raw_version = document.get("schema_version", 0)
        if not isinstance(raw_version, int) or raw_version < 0:
            _logger.warning(
                "settings file %s has invalid schema_version %r; using defaults",
                self._path,
                raw_version,
            )
            return

        try:
            migrated = self._migrator.migrate(document, raw_version)
        except SettingsMigrationError as exc:
            _logger.warning(
                "cannot migrate settings file %s: %s; using defaults",
                self._path,
                exc,
            )
            return

        self._store = SettingsStore.from_document(migrated, schema_version=CURRENT_SCHEMA_VERSION)
