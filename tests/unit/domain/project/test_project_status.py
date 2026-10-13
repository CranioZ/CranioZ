"""Tests for ProjectStatus."""

from __future__ import annotations

from cranioz.domain.project.project_status import ProjectStatus


def test_members() -> None:
    expected = {"DRAFT", "ACTIVE", "ARCHIVED"}
    assert {m.name for m in ProjectStatus} == expected


def test_values() -> None:
    assert ProjectStatus.DRAFT.value == "draft"
    assert ProjectStatus.ACTIVE.value == "active"
    assert ProjectStatus.ARCHIVED.value == "archived"


def test_lookup_by_value() -> None:
    assert ProjectStatus("draft") is ProjectStatus.DRAFT
    assert ProjectStatus("active") is ProjectStatus.ACTIVE
    assert ProjectStatus("archived") is ProjectStatus.ARCHIVED
