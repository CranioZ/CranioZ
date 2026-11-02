"""Integration tests for the MainWindow Top Bar (Phase 2, Section 10.10)."""

from __future__ import annotations

import pytest

from cranioz.ui.main_window import MainWindow
from cranioz.ui.workspace.areas.placement import Placement
from cranioz.ui.workspace.structure import (
    ExtrasSegment,
    HomeSegment,
    ModulesSegment,
)


@pytest.mark.qt
@pytest.mark.integration
def test_top_bar_segments_are_injected(
    main_window_with_open_project: MainWindow,
) -> None:
    window = main_window_with_open_project
    workspace = window.current_workspace()
    assert workspace is not None

    overlay = workspace.top_overlay()
    assert overlay.left_segment().findChild(HomeSegment) is not None
    assert overlay.center_segment().findChild(ModulesSegment) is not None
    assert overlay.right_segment().findChild(ExtrasSegment) is not None


@pytest.mark.qt
@pytest.mark.integration
def test_home_toggle_left_hides_and_shows_area(
    main_window_with_open_project: MainWindow,
) -> None:
    window = main_window_with_open_project
    workspace = window.current_workspace()
    assert workspace is not None

    state = workspace.layout_state()
    assert state.is_visible(Placement.LEFT) is True

    home = workspace.top_overlay().left_segment().findChild(HomeSegment)
    assert home is not None

    home.toggle_area_left_requested.emit()
    assert state.is_visible(Placement.LEFT) is False

    home.toggle_area_left_requested.emit()
    assert state.is_visible(Placement.LEFT) is True


@pytest.mark.qt
@pytest.mark.integration
def test_extras_toggle_bottom_and_right(
    main_window_with_open_project: MainWindow,
) -> None:
    window = main_window_with_open_project
    workspace = window.current_workspace()
    assert workspace is not None

    state = workspace.layout_state()
    extras = workspace.top_overlay().right_segment().findChild(ExtrasSegment)
    assert extras is not None

    extras.toggle_area_bottom_requested.emit()
    assert state.is_visible(Placement.BOTTOM) is False
    extras.toggle_area_bottom_requested.emit()
    assert state.is_visible(Placement.BOTTOM) is True

    extras.toggle_area_right_requested.emit()
    assert state.is_visible(Placement.RIGHT) is False
    extras.toggle_area_right_requested.emit()
    assert state.is_visible(Placement.RIGHT) is True