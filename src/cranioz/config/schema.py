"""Configuration schema and validation.

Defines required keys and accepted types.
No external dependencies; explicit validation only.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class ConfigError(Exception):
    """Configuration error: missing key, invalid type, or inconsistent value."""


@dataclass(frozen=True)
class AppConfig:
    name: str
    language: str
    theme: str
    recent_projects_limit: int


@dataclass(frozen=True)
class PathsConfig:
    project_root: str | None
    flows_root: str | None
    cache_root: str | None


@dataclass(frozen=True)
class LoggingConfig:
    level: str
    format: str


@dataclass(frozen=True)
class Config:
    app: AppConfig
    paths: PathsConfig
    logging: LoggingConfig


def _require(data: dict[str, Any], key: str, context: str) -> Any:
    if key not in data:
        raise ConfigError(f"missing key: {context}.{key}")
    return data[key]


def _require_type(value: Any, expected: type | tuple[type, ...], context: str) -> None:
    if not isinstance(value, expected):
        raise ConfigError(
            f"invalid type at {context}: expected {expected}, got {type(value)}"
        )


def build_config(app_data: dict[str, Any], paths_data: dict[str, Any]) -> Config:
    app_section = _require(app_data, "app", "root")
    _require_type(app_section, dict, "root.app")

    logging_section = _require(app_data, "logging", "root")
    _require_type(logging_section, dict, "root.logging")

    paths_section = _require(paths_data, "paths", "root")
    _require_type(paths_section, dict, "root.paths")

    app = AppConfig(
        name=_require(app_section, "name", "app"),
        language=_require(app_section, "language", "app"),
        theme=_require(app_section, "theme", "app"),
        recent_projects_limit=_require(app_section, "recent_projects_limit", "app"),
    )

    _require_type(app.recent_projects_limit, int, "app.recent_projects_limit")

    logging_cfg = LoggingConfig(
        level=_require(logging_section, "level", "logging"),
        format=_require(logging_section, "format", "logging"),
    )

    paths = PathsConfig(
        project_root=paths_section.get("project_root"),
        flows_root=paths_section.get("flows_root"),
        cache_root=paths_section.get("cache_root"),
    )

    return Config(app=app, paths=paths, logging=logging_cfg)