"""Tests for ToolbarState."""

from __future__ import annotations

import pytest

from cranioz.ui.toolbars.specification import ToolbarVisibilityMode
from cranioz.ui.toolbars.state import ToolbarState, ToolbarStateError


def test_toolbar_state_defaults() -> None:
    state = ToolbarState(toolbar_id="tb.x")
    assert state.toolbar_id == "tb.x"
    assert state.visible is True


def test_initial_for_always_is_visible() -> None:
    state = ToolbarState.initial_for("tb.x", ToolbarVisibilityMode.ALWAYS)
    assert state.visible is True


def test_initial_for_collapsible_is_visible() -> None:
    state = ToolbarState.initial_for("tb.x", ToolbarVisibilityMode.COLLAPSIBLE)
    assert state.visible is True


def test_initial_for_auto_hide_is_hidden() -> None:
    state = ToolbarState.initial_for("tb.x", ToolbarVisibilityMode.AUTO_HIDE)
    assert state.visible is False


def test_initial_for_hidden_is_hidden() -> None:
    state = ToolbarState.initial_for("tb.x", ToolbarVisibilityMode.HIDDEN)
    assert state.visible is False


def test_initial_for_unknown_mode_raises() -> None:
    with pytest.raises(ToolbarStateError, match="unknown visibility mode"):
        ToolbarState.initial_for("tb.x", "not-a-mode")  # type: ignore[arg-type]


def test_state_is_mutable() -> None:
    state = ToolbarState(toolbar_id="tb.x", visible=True)
    state.visible = False
    assert state.visible is False
