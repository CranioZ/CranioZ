"""Tests for ToolSpec."""

# mypy: ignore-errors
# This file intentionally mutates frozen dataclasses to test immutability.

from __future__ import annotations

import dataclasses

import pytest

from cranioz.ui.tools.specification import ToolSpec, ToolSpecError


def test_tool_spec_minimal() -> None:
    spec = ToolSpec(identifier="tool.a", label="A")
    assert spec.identifier == "tool.a"
    assert spec.label == "A"
    assert spec.description == ""
    assert spec.icon is None
    assert spec.category is None


def test_tool_spec_with_all_fields() -> None:
    spec = ToolSpec(
        identifier="tool.a",
        label="A",
        description="Does something",
        icon="tool_a",
        category="measurement",
    )
    assert spec.description == "Does something"
    assert spec.icon == "tool_a"
    assert spec.category == "measurement"


def test_empty_identifier_raises() -> None:
    with pytest.raises(ToolSpecError, match="identifier"):
        ToolSpec(identifier="", label="A")


def test_empty_label_raises() -> None:
    with pytest.raises(ToolSpecError, match="label"):
        ToolSpec(identifier="tool.a", label="")


def test_tool_spec_is_frozen() -> None:
    spec = ToolSpec(identifier="tool.a", label="A")
    with pytest.raises(dataclasses.FrozenInstanceError):
        spec.label = "B"
