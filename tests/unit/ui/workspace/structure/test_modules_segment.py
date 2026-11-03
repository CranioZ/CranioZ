"""Tests for HomeSegment (Phase 2, Section 10.10)."""

from __future__ import annotations

import pytest

from cranioz.ui.workspace.structure.home_segment import HomeSegment


@pytest.mark.qt
def test_toggle_area_left_button_emits_signal(qtbot) -> None:
    segment = HomeSegment()
    qtbot.addWidget(segment)

    with qtbot.waitSignal(segment.toggle_area_left_requested, timeout=1000):
        segment.findChild(
            type(segment._toggle_left_button),  # noqa: SLF001
            "workspace.top_bar.home_segment.toggle_left",
        ).click()


@pytest.mark.qt
def test_close_workspace_button_emits_signal(qtbot) -> None:
    segment = HomeSegment()
    qtbot.addWidget(segment)

    with qtbot.waitSignal(segment.close_workspace_requested, timeout=1000):
        segment.findChild(
            type(segment._close_workspace_button),  # noqa: SLF001
            "workspace.top_bar.home_segment.close_workspace",
        ).click()


@pytest.mark.qt
def test_menu_new_project_emits_signal(qtbot) -> None:
    segment = HomeSegment()
    qtbot.addWidget(segment)

    with qtbot.waitSignal(segment.new_project_requested, timeout=1000):
        segment._action_new_project.trigger()  # noqa: SLF001


@pytest.mark.qt
def test_menu_open_project_emits_signal(qtbot) -> None:
    segment = HomeSegment()
    qtbot.addWidget(segment)

    with qtbot.waitSignal(segment.open_project_requested, timeout=1000):
        segment._action_open_project.trigger()  # noqa: SLF001


@pytest.mark.qt
def test_menu_close_project_emits_signal(qtbot) -> None:
    segment = HomeSegment()
    qtbot.addWidget(segment)
    segment.set_project_open(True)

    with qtbot.waitSignal(segment.close_project_requested, timeout=1000):
        segment._action_close_project.trigger()  # noqa: SLF001


@pytest.mark.qt
def test_menu_import_dicom_emits_signal(qtbot) -> None:
    segment = HomeSegment()
    qtbot.addWidget(segment)
    segment.set_project_open(True)

    with qtbot.waitSignal(segment.import_files_requested, timeout=1000):
        segment._action_import_dicom.trigger()  # noqa: SLF001


@pytest.mark.qt
def test_menu_import_stl_debug_emits_signal(qtbot) -> None:
    segment = HomeSegment()
    qtbot.addWidget(segment)
    segment.set_project_open(True)

    with qtbot.waitSignal(segment.import_stl_debug_requested, timeout=1000):
        segment._action_import_stl.trigger()  # noqa: SLF001


@pytest.mark.qt
def test_context_actions_disabled_when_no_project(qtbot) -> None:
    segment = HomeSegment()
    qtbot.addWidget(segment)
    segment.set_project_open(False)

    assert not segment._action_close_project.isEnabled()  # noqa: SLF001
    assert not segment._import_menu.isEnabled()  # noqa: SLF001
    assert segment._action_new_project.isEnabled()  # noqa: SLF001
    assert segment._action_open_project.isEnabled()  # noqa: SLF001


@pytest.mark.qt
def test_context_actions_enabled_when_project_open(qtbot) -> None:
    segment = HomeSegment()
    qtbot.addWidget(segment)
    segment.set_project_open(True)

    assert segment._action_close_project.isEnabled()  # noqa: SLF001
    assert segment._import_menu.isEnabled()  # noqa: SLF001


@pytest.mark.qt
def test_project_open_state_round_trips(qtbot) -> None:
    segment = HomeSegment()
    qtbot.addWidget(segment)

    assert segment.is_project_open() is False
    segment.set_project_open(True)
    assert segment.is_project_open() is True
    segment.set_project_open(False)
    assert segment.is_project_open() is False
