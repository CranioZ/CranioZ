"""Tests for ProjectPathResolver."""

from __future__ import annotations

from pathlib import Path

import pytest

from cranioz.infrastructure.project_path_resolver import (
    ProjectPathResolver,
    ProjectRootInaccessible,
)


def test_initialize_creates_directory(tmp_path: Path) -> None:
    target = tmp_path / "nested" / "projects"
    resolver = ProjectPathResolver()

    resolved = resolver.initialize(str(target))

    assert resolved == target
    assert target.is_dir()
    assert resolver.project_root == target


def test_initialize_uses_default_when_none(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    resolver = ProjectPathResolver()

    resolved = resolver.initialize(None)

    expected = tmp_path / "Documents" / "CranioZ" / "Projects"
    assert resolved == expected
    assert expected.is_dir()


def test_initialize_without_create_fails_if_missing(tmp_path: Path) -> None:
    target = tmp_path / "does_not_exist"
    resolver = ProjectPathResolver()

    with pytest.raises(ProjectRootInaccessible, match="does not exist"):
        resolver.initialize(str(target), create=False)


def test_initialize_fails_if_path_is_a_file(tmp_path: Path) -> None:
    file_path = tmp_path / "not_a_dir"
    file_path.write_text("x", encoding="utf-8")
    resolver = ProjectPathResolver()

    with pytest.raises(ProjectRootInaccessible, match="not a directory"):
        resolver.initialize(str(file_path), create=False)


def test_resolve_relative_path(tmp_path: Path) -> None:
    resolver = ProjectPathResolver()
    resolver.initialize(str(tmp_path))

    resolved = resolver.resolve("imaging/ct")

    assert resolved == (tmp_path / "imaging" / "ct").resolve()


def test_resolve_rejects_traversal(tmp_path: Path) -> None:
    resolver = ProjectPathResolver()
    resolver.initialize(str(tmp_path))

    with pytest.raises(ProjectRootInaccessible, match="escapes"):
        resolver.resolve("../outside")


def test_project_root_before_initialize_raises() -> None:
    resolver = ProjectPathResolver()
    with pytest.raises(ProjectRootInaccessible, match="not initialized"):
        _ = resolver.project_root


def test_resolve_before_initialize_raises() -> None:
    resolver = ProjectPathResolver()
    with pytest.raises(ProjectRootInaccessible, match="not initialized"):
        resolver.resolve("anything")
