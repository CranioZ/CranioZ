"""Tests for ConfigurationLoader."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cranioz.config.loader import ConfigurationLoader
from cranioz.config.schema import ConfigError


@pytest.fixture
def defaults_dir(tmp_path: Path) -> Path:
    """Temporary directory with minimal valid configs."""
    (tmp_path / "app.json").write_text(
        json.dumps(
            {
                "app": {
                    "name": "CranioZ",
                    "version": "0.1.0",
                    "language": "pt-BR",
                    "theme": "dark",
                    "recent_projects_limit": 10,
                },
                "logging": {
                    "level": "INFO",
                    "format": "%(message)s",
                },
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "paths.json").write_text(
        json.dumps(
            {
                "paths": {
                    "project_root": None,
                    "flows_root": None,
                    "cache_root": None,
                }
            }
        ),
        encoding="utf-8",
    )
    return tmp_path


def test_load_returns_config(defaults_dir: Path) -> None:
    cfg = ConfigurationLoader(defaults_dir).load()
    assert cfg.app.name == "CranioZ"
    assert cfg.app.language == "pt-BR"
    assert cfg.app.theme == "dark"
    assert cfg.app.recent_projects_limit == 10
    assert cfg.logging.level == "INFO"
    assert cfg.paths.project_root is None


def test_missing_app_json_raises(tmp_path: Path) -> None:
    (tmp_path / "paths.json").write_text(json.dumps({"paths": {}}), encoding="utf-8")
    with pytest.raises(ConfigError, match="app.json"):
        ConfigurationLoader(tmp_path).load()


def test_missing_paths_json_raises(tmp_path: Path) -> None:
    (tmp_path / "app.json").write_text(
        json.dumps(
            {
                "app": {
                    "name": "CranioZ",
                    "version": "0.1.0",
                    "language": "pt-BR",
                    "theme": "dark",
                    "recent_projects_limit": 10,
                },
                "logging": {"level": "INFO", "format": "%(message)s"},
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ConfigError, match="paths.json"):
        ConfigurationLoader(tmp_path).load()


def test_invalid_json_raises(tmp_path: Path) -> None:
    (tmp_path / "app.json").write_text("{not json", encoding="utf-8")
    (tmp_path / "paths.json").write_text(json.dumps({"paths": {}}), encoding="utf-8")
    with pytest.raises(ConfigError, match="invalid JSON"):
        ConfigurationLoader(tmp_path).load()


def test_missing_app_section_raises(tmp_path: Path) -> None:
    (tmp_path / "app.json").write_text(json.dumps({}), encoding="utf-8")
    (tmp_path / "paths.json").write_text(json.dumps({"paths": {}}), encoding="utf-8")
    with pytest.raises(ConfigError, match="app"):
        ConfigurationLoader(tmp_path).load()