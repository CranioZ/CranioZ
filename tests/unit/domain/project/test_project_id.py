"""Tests for ProjectId."""

from __future__ import annotations

import dataclasses

import pytest

from cranioz.domain.project.project_id import ProjectId


def test_project_id_holds_value() -> None:
    pid = ProjectId("abc-123")
    assert pid.value == "abc-123"


def test_project_id_is_frozen() -> None:
    pid = ProjectId("abc")
    attr = "value"
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(pid, attr, "other")


def test_empty_value_raises() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        ProjectId("")


def test_whitespace_only_value_raises() -> None:
    with pytest.raises(ValueError, match="whitespace"):
        ProjectId("   ")
    with pytest.raises(ValueError, match="whitespace"):
        ProjectId("\t\n")


def test_equality_by_value() -> None:
    a = ProjectId("abc")
    b = ProjectId("abc")
    assert a == b


def test_different_ids_are_not_equal() -> None:
    assert ProjectId("abc") != ProjectId("xyz")


def test_str_returns_value() -> None:
    assert str(ProjectId("abc-123")) == "abc-123"


def test_repr_mentions_value() -> None:
    assert "abc-123" in repr(ProjectId("abc-123"))


def test_hashable() -> None:
    # Frozen dataclasses are hashable, which makes ProjectId usable
    # as a dict key.
    d = {ProjectId("a"): 1, ProjectId("b"): 2}
    assert d[ProjectId("a")] == 1
