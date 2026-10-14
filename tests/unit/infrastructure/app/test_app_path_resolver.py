"""Tests for AppPathResolver."""

from __future__ import annotations

from pathlib import Path

import pytest

from cranioz.config.schema import PathsConfig
from cranioz.infrastructure.app.app_path_resolver import (
    AppPathInaccessible,
    AppPathResolver,
)

# ----- Helpers ------------------------------------------------------


def _paths_config(
    *,
    project_root: str | None = None,
    flows_root: str | None = None,
    cache_root: str | None = None,
) -> PathsConfig:
    return PathsConfig(
        project_root=project_root,
        flows_root=flows_root,
        cache_root=cache_root,
    )


def _initialize(
    tmp_path: Path,
    *,
    project_root: str | None = None,
    flows_root: str | None = None,
    cache_root: str | None = None,
) -> AppPathResolver:
    """Build a resolver with all roots pointed at tmp_path subdirs.

    Any root not overridden gets a tmp_path subdirectory, so tests
    never touch the user's real home directory.
    """
    cfg = _paths_config(
        project_root=project_root or str(tmp_path / "projects"),
        flows_root=flows_root or str(tmp_path / "flows"),
        cache_root=cache_root or str(tmp_path / "cache"),
    )
    resolver = AppPathResolver()
    resolver.initialize(cfg)
    return resolver


# ----- Initialization -----------------------------------------------


def test_initialize_creates_directories(tmp_path: Path) -> None:
    resolver = _initialize(tmp_path)

    assert resolver.projects_root.is_dir()
    assert resolver.flows_root.is_dir()
    assert resolver.cache_root.is_dir()


def test_initialize_uses_configured_paths(tmp_path: Path) -> None:
    projects = tmp_path / "my_projects"
    flows = tmp_path / "my_flows"
    cache = tmp_path / "my_cache"

    resolver = AppPathResolver()
    resolver.initialize(
        _paths_config(
            project_root=str(projects),
            flows_root=str(flows),
            cache_root=str(cache),
        )
    )

    assert resolver.projects_root == projects
    assert resolver.flows_root == flows
    assert resolver.cache_root == cache


def test_initialize_uses_defaults_when_none(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))

    resolver = AppPathResolver()
    resolver.initialize(_paths_config())

    assert resolver.projects_root == (tmp_path / "Documents" / "CranioZ" / "Projects")
    assert resolver.flows_root == (tmp_path / "Documents" / "CranioZ" / "Flows")
    assert resolver.cache_root == tmp_path / ".cranioz" / "Cache"


def test_initialize_without_create_fails_if_missing(tmp_path: Path) -> None:
    missing = tmp_path / "does_not_exist"

    resolver = AppPathResolver()
    with pytest.raises(AppPathInaccessible, match="does not exist"):
        resolver.initialize(
            _paths_config(
                project_root=str(missing),
                flows_root=str(tmp_path / "flows"),
                cache_root=str(tmp_path / "cache"),
            ),
            create=False,
        )


def test_initialize_fails_if_path_is_a_file(tmp_path: Path) -> None:
    file_path = tmp_path / "not_a_dir"
    file_path.write_text("x", encoding="utf-8")

    resolver = AppPathResolver()
    with pytest.raises(AppPathInaccessible, match="not a directory"):
        resolver.initialize(
            _paths_config(
                project_root=str(file_path),
                flows_root=str(tmp_path / "flows"),
                cache_root=str(tmp_path / "cache"),
            ),
            create=False,
        )


# ----- Accessors before initialization ------------------------------


def test_projects_root_before_initialize_raises() -> None:
    resolver = AppPathResolver()
    with pytest.raises(AppPathInaccessible, match="not initialized"):
        _ = resolver.projects_root


def test_flows_root_before_initialize_raises() -> None:
    resolver = AppPathResolver()
    with pytest.raises(AppPathInaccessible, match="not initialized"):
        _ = resolver.flows_root


def test_cache_root_before_initialize_raises() -> None:
    resolver = AppPathResolver()
    with pytest.raises(AppPathInaccessible, match="not initialized"):
        _ = resolver.cache_root


# ----- resolve_in_projects_root -------------------------------------


def test_resolve_in_projects_root(tmp_path: Path) -> None:
    resolver = _initialize(tmp_path)
    resolved = resolver.resolve_in_projects_root("abc/imaging/ct")
    assert resolved == (resolver.projects_root / "abc" / "imaging" / "ct").resolve()


def test_resolve_in_projects_root_rejects_traversal(tmp_path: Path) -> None:
    resolver = _initialize(tmp_path)
    with pytest.raises(AppPathInaccessible, match="escapes"):
        resolver.resolve_in_projects_root("../outside")


def test_resolve_in_projects_root_rejects_absolute_escape(
    tmp_path: Path,
) -> None:
    resolver = _initialize(tmp_path)
    with pytest.raises(AppPathInaccessible, match="escapes"):
        resolver.resolve_in_projects_root("../../../etc/passwd")


def test_resolve_in_projects_root_before_initialize_raises() -> None:
    resolver = AppPathResolver()
    with pytest.raises(AppPathInaccessible, match="not initialized"):
        resolver.resolve_in_projects_root("anything")
