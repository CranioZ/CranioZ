"""Tests for ToolbarSpec."""

from __future__ import annotations

import pytest

from cranioz.ui.toolbars.specification import (
    ToolbarOrientation,
    ToolbarSpec,
    ToolbarSpecError,
    ToolbarVisibilityMode,
)


def test_toolbar_spec_defaults() -> None:
    spec = ToolbarSpec(toolbar_id="tb.x", title="X")
    assert spec.toolbar_id == "tb.x"
    assert spec.title == "X"
    assert spec.orientation is ToolbarOrientation.HORIZONTAL
    assert spec.tool_ids == ()
    assert spec.visibility_mode is ToolbarVisibilityMode.ALWAYS


def test_toolbar_spec_with_all_fields() -> None:
    spec = ToolbarSpec(
        toolbar_id="tb.y",
        title="Y",
        orientation=ToolbarOrientation.VERTICAL,
        tool_ids=("tool.a", "tool.b"),
        visibility_mode=ToolbarVisibilityMode.AUTO_HIDE,
    )
    assert spec.orientation is ToolbarOrientation.VERTICAL
    assert spec.tool_ids == ("tool.a", "tool.b")
    assert spec.visibility_mode is ToolbarVisibilityMode.AUTO_HIDE


def test_empty_toolbar_id_raises() -> None:
    with pytest.raises(ToolbarSpecError, match="toolbar_id"):
        ToolbarSpec(toolbar_id="", title="X")


def test_empty_title_raises() -> None:
    with pytest.raises(ToolbarSpecError, match="title"):
        ToolbarSpec(toolbar_id="tb.x", title="")


def test_visibility_mode_members() -> None:
    expected = {"ALWAYS", "COLLAPSIBLE", "AUTO_HIDE", "HIDDEN"}
    actual = {member.name for member in ToolbarVisibilityMode}
    assert actual == expected


def test_orientation_members() -> None:
    expected = {"HORIZONTAL", "VERTICAL"}
    actual = {member.name for member in ToolbarOrientation}
    assert actual == expected
