"""Tests for the settings subsystem.

Covers:

- InMemorySettingsService: get/set/seed, changed signal.
- FilesystemSettingsService: load, save, round-trip, migrations,
  invalid JSON, unknown keys, type mismatch fallback.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cranioz.infrastructure.settings._store import _is_compatible
from cranioz.infrastructure.settings.errors import (
    SettingsMigrationError,
)
from cranioz.infrastructure.settings.filesystem_settings_service import (
    FilesystemSettingsService,
)
from cranioz.infrastructure.settings.in_memory_settings_service import (
    InMemorySettingsService,
)
from cranioz.infrastructure.settings.keys import (
    APPEARANCE_THEME_MODE,
    KNOWN_KEYS,
)
from cranioz.infrastructure.settings.migrator import (
    CURRENT_SCHEMA_VERSION,
    SettingsMigrator,
)

# =====================================================================
# InMemorySettingsService
# =====================================================================


def test_in_memory_get_returns_default_when_empty() -> None:
    service = InMemorySettingsService()
    assert service.get(APPEARANCE_THEME_MODE, "dark") == "dark"


def test_in_memory_set_and_get() -> None:
    service = InMemorySettingsService()
    service.set(APPEARANCE_THEME_MODE, "light")
    assert service.get(APPEARANCE_THEME_MODE, "dark") == "light"


def test_in_memory_seed_does_not_emit_changed() -> None:
    service = InMemorySettingsService()
    events: list[str] = []
    service.changed.connect(events.append)

    service.seed(APPEARANCE_THEME_MODE, "light")

    assert events == []


def test_in_memory_set_emits_changed_with_key() -> None:
    service = InMemorySettingsService()
    events: list[str] = []
    service.changed.connect(events.append)

    service.set(APPEARANCE_THEME_MODE, "light")

    assert events == [APPEARANCE_THEME_MODE]


def test_in_memory_unknown_key_raises_on_set() -> None:
    service = InMemorySettingsService()
    with pytest.raises(KeyError, match="unknown settings key"):
        service.set("not.a.key", "value")


def test_in_memory_save_and_reload_are_noops() -> None:
    service = InMemorySettingsService()
    service.set(APPEARANCE_THEME_MODE, "light")
    service.save()
    service.reload()
    # State survives: the in-memory backend has no persistence.
    assert service.get(APPEARANCE_THEME_MODE, "dark") == "light"


def test_in_memory_type_mismatch_falls_back_to_default(
    caplog: pytest.LogCaptureFixture,
) -> None:
    service = InMemorySettingsService()
    service.seed(APPEARANCE_THEME_MODE, 42)  # int, not str

    with caplog.at_level("WARNING", logger="cranioz.infrastructure.settings._store"):
        value = service.get(APPEARANCE_THEME_MODE, "dark")

    assert value == "dark"
    assert "incompatible type" in caplog.text


def test_is_compatible_rejects_bool_for_int() -> None:
    """bool is a subclass of int; the store must reject it explicitly."""
    assert _is_compatible(True, default=0) is False
    assert _is_compatible(False, default=0) is False
    assert _is_compatible(42, default=0) is True


def test_is_compatible_rejects_bool_for_float() -> None:
    assert _is_compatible(True, default=0.0) is False
    assert _is_compatible(1.5, default=0.0) is True
    assert _is_compatible(2, default=0.0) is True  # int accepted as float


# =====================================================================
# Known keys
# =====================================================================


def test_known_keys_contains_appearance_theme_mode() -> None:
    assert APPEARANCE_THEME_MODE in KNOWN_KEYS


def test_known_keys_are_dotted() -> None:
    for key in KNOWN_KEYS:
        assert "." in key, f"key {key!r} must be dotted"


# =====================================================================
# SettingsMigrator
# =====================================================================


def test_migrator_current_version_is_identity() -> None:
    migrator = SettingsMigrator()
    data = {"schema_version": CURRENT_SCHEMA_VERSION, "appearance": {}}
    assert migrator.migrate(data, CURRENT_SCHEMA_VERSION) is data


def test_migrator_rejects_newer_version() -> None:
    migrator = SettingsMigrator()
    with pytest.raises(SettingsMigrationError, match="newer than supported"):
        migrator.migrate({}, CURRENT_SCHEMA_VERSION + 1)


def test_migrator_rejects_older_version_without_rule() -> None:
    migrator = SettingsMigrator()
    with pytest.raises(SettingsMigrationError, match="no migration defined"):
        migrator.migrate({}, CURRENT_SCHEMA_VERSION - 1)


# =====================================================================
# FilesystemSettingsService
# =====================================================================


def _write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


def test_fs_missing_file_loads_defaults(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    service = FilesystemSettingsService(path=path)
    assert service.get(APPEARANCE_THEME_MODE, "dark") == "dark"
    assert not path.exists()


def test_fs_save_creates_file_and_parent_dirs(tmp_path: Path) -> None:
    path = tmp_path / "nested" / "dir" / "settings.json"
    service = FilesystemSettingsService(path=path)
    service.set(APPEARANCE_THEME_MODE, "light")
    service.save()

    assert path.is_file()
    raw = json.loads(path.read_text(encoding="utf-8"))
    assert raw["schema_version"] == CURRENT_SCHEMA_VERSION
    assert raw["appearance"]["theme_mode"] == "light"


def test_fs_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    a = FilesystemSettingsService(path=path)
    a.set(APPEARANCE_THEME_MODE, "light")
    a.save()

    b = FilesystemSettingsService(path=path)
    assert b.get(APPEARANCE_THEME_MODE, "dark") == "light"


def test_fs_reload_picks_up_external_changes(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    service = FilesystemSettingsService(path=path)
    service.set(APPEARANCE_THEME_MODE, "light")
    service.save()

    # Simulate an external process editing the file.
    document = json.loads(path.read_text(encoding="utf-8"))
    document["appearance"]["theme_mode"] = "dark"
    path.write_text(json.dumps(document), encoding="utf-8")

    service.reload()
    assert service.get(APPEARANCE_THEME_MODE, "light") == "dark"


def test_fs_reload_emits_changed_for_each_known_key(
    tmp_path: Path,
) -> None:
    path = tmp_path / "settings.json"
    service = FilesystemSettingsService(path=path)
    events: list[str] = []
    service.changed.connect(events.append)

    service.reload()

    # Every known key is re-emitted so consumers refresh.
    assert set(events) == KNOWN_KEYS


def test_fs_invalid_json_logs_warning_and_uses_defaults(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    path = tmp_path / "settings.json"
    path.write_text("{not valid json", encoding="utf-8")

    with caplog.at_level(
        "WARNING",
        logger="cranioz.infrastructure.settings.filesystem_settings_service",
    ):
        service = FilesystemSettingsService(path=path)

    assert service.get(APPEARANCE_THEME_MODE, "dark") == "dark"
    assert "cannot read settings file" in caplog.text
    # The corrupted file is NOT overwritten until save() is called.
    assert path.read_text(encoding="utf-8") == "{not valid json"


def test_fs_non_object_root_logs_warning_and_uses_defaults(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    path = tmp_path / "settings.json"
    _write_json(path, ["not", "an", "object"])

    with caplog.at_level(
        "WARNING",
        logger="cranioz.infrastructure.settings.filesystem_settings_service",
    ):
        service = FilesystemSettingsService(path=path)

    assert service.get(APPEARANCE_THEME_MODE, "dark") == "dark"
    assert "not a JSON object" in caplog.text


def test_fs_invalid_schema_version_logs_warning(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    path = tmp_path / "settings.json"
    _write_json(path, {"schema_version": "one", "appearance": {}})

    with caplog.at_level(
        "WARNING",
        logger="cranioz.infrastructure.settings.filesystem_settings_service",
    ):
        service = FilesystemSettingsService(path=path)

    assert service.get(APPEARANCE_THEME_MODE, "dark") == "dark"
    assert "invalid schema_version" in caplog.text


def test_fs_newer_schema_version_logs_warning(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    path = tmp_path / "settings.json"
    _write_json(
        path,
        {
            "schema_version": CURRENT_SCHEMA_VERSION + 1,
            "appearance": {},
        },
    )

    with caplog.at_level(
        "WARNING",
        logger="cranioz.infrastructure.settings.filesystem_settings_service",
    ):
        service = FilesystemSettingsService(path=path)

    assert service.get(APPEARANCE_THEME_MODE, "dark") == "dark"
    assert "cannot migrate" in caplog.text


def test_fs_unknown_keys_in_file_are_ignored(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    path = tmp_path / "settings.json"
    _write_json(
        path,
        {
            "schema_version": CURRENT_SCHEMA_VERSION,
            "appearance": {"theme_mode": "light"},
            "future": {"unknown_key": "value"},
        },
    )

    with caplog.at_level("WARNING", logger="cranioz.infrastructure.settings._store"):
        service = FilesystemSettingsService(path=path)

    # Known keys load.
    assert service.get(APPEARANCE_THEME_MODE, "dark") == "light"
    # Unknown keys are ignored with a warning.
    assert "ignoring unknown settings key" in caplog.text


def test_fs_non_object_section_is_ignored(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    path = tmp_path / "settings.json"
    _write_json(
        path,
        {
            "schema_version": CURRENT_SCHEMA_VERSION,
            "appearance": "not-an-object",
        },
    )

    with caplog.at_level("WARNING", logger="cranioz.infrastructure.settings._store"):
        service = FilesystemSettingsService(path=path)

    assert service.get(APPEARANCE_THEME_MODE, "dark") == "dark"
    assert "ignoring non-object settings section" in caplog.text


def test_fs_save_writes_atomically_via_tmp_file(tmp_path: Path) -> None:
    """A leftover .tmp file would indicate the atomic write did not clean up."""
    path = tmp_path / "settings.json"
    service = FilesystemSettingsService(path=path)
    service.set(APPEARANCE_THEME_MODE, "light")
    service.save()

    leftovers = list(tmp_path.glob("*.tmp"))
    assert leftovers == []


def test_fs_unknown_key_set_raises(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    service = FilesystemSettingsService(path=path)
    with pytest.raises(KeyError, match="unknown settings key"):
        service.set("not.a.key", "value")
