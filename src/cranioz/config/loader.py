"""ConfigurationLoader.

Loads system configuration from src/cranioz/config/defaults/.
Does not load user preferences; that is the responsibility of settings/.

Rules:
- The loader reads the defaults packaged with the application.
- The loader does not resolve physical OS paths.
- The loader returns a validated Config.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from cranioz.config.schema import Config, ConfigError, build_config

_DEFAULTS_DIR = Path(__file__).parent / "defaults"


class ConfigurationLoader:
    """Loads and validates the system configuration."""

    def __init__(self, defaults_dir: Path | None = None) -> None:
        self._defaults_dir = defaults_dir or _DEFAULTS_DIR

    def load(self) -> Config:
        """Load app.json and paths.json, validate, and return a Config."""
        app_data = self._read_json("app.json")
        paths_data = self._read_json("paths.json")

        try:
            return build_config(app_data, paths_data)
        except ConfigError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise ConfigError(f"failed to build configuration: {exc}") from exc

    def _read_json(self, filename: str) -> dict[str, Any]:
        path = self._defaults_dir / filename
        if not path.exists():
            raise ConfigError(f"configuration file not found: {path}")

        try:
            with path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
        except json.JSONDecodeError as exc:
            raise ConfigError(f"invalid JSON in {path}: {exc}") from exc

        if not isinstance(data, dict):
            raise ConfigError(f"unexpected content in {path}: expected object")
        return data