"""Tests for ProjectAccessPolicy and AllowAllProjectAccessPolicy."""

from __future__ import annotations

from cranioz.application.project.project_access_policy import (
    AllowAllProjectAccessPolicy,
    ProjectAccessPolicy,
)
from cranioz.domain.project.project_id import ProjectId


def test_allow_all_satisfies_protocol() -> None:
    policy = AllowAllProjectAccessPolicy()
    assert isinstance(policy, ProjectAccessPolicy)


def test_allow_all_permits_create() -> None:
    policy = AllowAllProjectAccessPolicy()
    assert policy.can_create("alice") is True


def test_allow_all_permits_open() -> None:
    policy = AllowAllProjectAccessPolicy()
    assert policy.can_open("alice", ProjectId("p-001")) is True


def test_allow_all_permits_update() -> None:
    policy = AllowAllProjectAccessPolicy()
    assert policy.can_update("alice", ProjectId("p-001")) is True


def test_allow_all_permits_delete() -> None:
    policy = AllowAllProjectAccessPolicy()
    assert policy.can_delete("alice", ProjectId("p-001")) is True


def test_allow_all_ignores_actor() -> None:
    """The permissive policy is actor-agnostic."""
    policy = AllowAllProjectAccessPolicy()
    assert policy.can_create("") is True
    assert policy.can_open("", ProjectId("p-001")) is True
