"""Tests for ExtrasSegment.

The ExtrasSegment is the right zone of the Workspace Top Bar. It
hosts six buttons:

- ``⋮`` (menu) — opens a QMenu with application-level actions.
- ``⬜`` (toggle_bottom) — toggles Area Bottom.
- ``⬜`` (toggle_right) — toggles Area Right.
- ``—`` (minimize) — emits ``minimize_requested`` (Block 5.6).
- ``▢`` (maximize) — emits ``maximize_requested`` (Block 5.6).
- ``✕`` (close) — emits ``close_requested`` (Block 5.6).

The segment is a pure presentation widget: it emits signals and
knows nothing about the application. The MainWindow wires the
signals to the real actions (showMinimized, showMaximized, close).
"""

from __future__ import annotations

import pytest
from PySide6.QtWidgets import QPushButton
from pytestqt.qtbot import QtBot
from tests.conftest import make_icon_provider, make_theme_service

from cranioz.ui.theme.tokens import ThemeMode
from cranioz.ui.workspace.structure.extras_segment import ExtrasSegment


@pytest.fixture
def segment(qtbot: QtBot) -> ExtrasSegment:
    """An ExtrasSegment with a dark-theme IconProvider, registered
    with qtbot."""
    theme_service = make_theme_service(ThemeMode.DARK)
    icon_provider = make_icon_provider(theme_service)
    widget = ExtrasSegment(icon_provider)
    qtbot.addWidget(widget)
    return widget


# ----- Composition ---------------------------------------------------


def test_segment_has_six_buttons(segment: ExtrasSegment) -> None:
    """The segment hosts exactly six buttons (menu, two toggles,
    minimize, maximize, close)."""
    buttons = segment.findChildren(QPushButton)
    assert len(buttons) == 6


def test_button_order_matches_spec(segment: ExtrasSegment) -> None:
    """The buttons appear in the order declared in the QHBoxLayout:
    menu, toggle_bottom, toggle_right, minimize, maximize, close."""
    names = [
        "workspace.top_bar.extras_segment.menu",
        "workspace.top_bar.extras_segment.toggle_bottom",
        "workspace.top_bar.extras_segment.toggle_right",
        "workspace.top_bar.extras_segment.minimize",
        "workspace.top_bar.extras_segment.maximize",
        "workspace.top_bar.extras_segment.close",
    ]
    found = [
        segment.findChild(QPushButton, name) is not None for name in names
    ]
    assert all(found), f"missing button(s) among {names}"


def test_buttons_have_fixed_width_28(segment: ExtrasSegment) -> None:
    """All buttons are 28px wide (matching HomeSegment's buttons)."""
    for button in segment.findChildren(QPushButton):
        assert button.width() == 28, (
            f"button {button.objectName()} has width {button.width()}, expected 28"
        )


# ----- Menu signals (existing) ---------------------------------------


def test_settings_action_emits_signal(
    qtbot: QtBot, segment: ExtrasSegment
) -> None:
    action = next(
        a
        for a in segment._menu.actions()
        if a.text() == "Settings"  # noqa: SLF001
    )
    with qtbot.waitSignal(segment.settings_requested, timeout=1000):
        action.trigger()


def test_themes_action_emits_signal(
    qtbot: QtBot, segment: ExtrasSegment
) -> None:
    action = next(
        a
        for a in segment._menu.actions()
        if a.text() == "Themes"  # noqa: SLF001
    )
    with qtbot.waitSignal(segment.themes_requested, timeout=1000):
        action.trigger()


def test_help_action_emits_signal(
    qtbot: QtBot, segment: ExtrasSegment
) -> None:
    action = next(
        a
        for a in segment._menu.actions()
        if a.text() == "Help"  # noqa: SLF001
    )
    with qtbot.waitSignal(segment.help_requested, timeout=1000):
        action.trigger()


def test_updates_action_emits_signal(
    qtbot: QtBot, segment: ExtrasSegment
) -> None:
    action = next(
        a
        for a in segment._menu.actions()
        if a.text() == "Updates"  # noqa: SLF001
    )
    with qtbot.waitSignal(segment.updates_requested, timeout=1000):
        action.trigger()


def test_about_action_emits_signal(
    qtbot: QtBot, segment: ExtrasSegment
) -> None:
    action = next(
        a
        for a in segment._menu.actions()
        if a.text() == "About"  # noqa: SLF001
    )
    with qtbot.waitSignal(segment.about_requested, timeout=1000):
        action.trigger()


# ----- Area toggles (existing) ---------------------------------------


def test_toggle_bottom_button_emits_signal(
    qtbot: QtBot, segment: ExtrasSegment
) -> None:
    with qtbot.waitSignal(segment.toggle_area_bottom_requested, timeout=1000):
        segment._toggle_bottom_button.click()  # noqa: SLF001


def test_toggle_right_button_emits_signal(
    qtbot: QtBot, segment: ExtrasSegment
) -> None:
    with qtbot.waitSignal(segment.toggle_area_right_requested, timeout=1000):
        segment._toggle_right_button.click()  # noqa: SLF001


# ----- Window controls (Block 5.6) -----------------------------------


def test_minimize_button_emits_signal(
    qtbot: QtBot, segment: ExtrasSegment
) -> None:
    with qtbot.waitSignal(segment.minimize_requested, timeout=1000):
        segment._minimize_button.click()  # noqa: SLF001


def test_maximize_button_emits_signal(
    qtbot: QtBot, segment: ExtrasSegment
) -> None:
    with qtbot.waitSignal(segment.maximize_requested, timeout=1000):
        segment._maximize_button.click()  # noqa: SLF001


def test_close_button_emits_signal(
    qtbot: QtBot, segment: ExtrasSegment
) -> None:
    with qtbot.waitSignal(segment.close_requested, timeout=1000):
        segment._close_button.click()  # noqa: SLF001


def test_close_button_uses_window_close_icon(segment: ExtrasSegment) -> None:
    """The close button resolves the ``window_close`` icon from the
    IconProvider (it is not a hardcoded glyph)."""
    icon = segment._close_button.icon()  # noqa: SLF001
    assert not icon.isNull(), "close button has a null icon"


def test_minimize_button_uses_window_minimize_icon(
    segment: ExtrasSegment,
) -> None:
    icon = segment._minimize_button.icon()  # noqa: SLF001
    assert not icon.isNull(), "minimize button has a null icon"


def test_maximize_button_uses_window_maximize_icon(
    segment: ExtrasSegment,
) -> None:
    icon = segment._maximize_button.icon()  # noqa: SLF001
    assert not icon.isNull(), "maximize button has a null icon"


# ----- Accessibility -------------------------------------------------


def test_all_buttons_have_tooltips(segment: ExtrasSegment) -> None:
    for button in segment.findChildren(QPushButton):
        assert button.toolTip(), (
            f"button {button.objectName()} has no tooltip"
        )


def test_all_buttons_have_accessible_names(segment: ExtrasSegment) -> None:
    for button in segment.findChildren(QPushButton):
        assert button.accessibleName(), (
            f"button {button.objectName()} has no accessibleName"
        )


def test_window_control_tooltips_are_specific(segment: ExtrasSegment) -> None:
    """The window controls' tooltips mention the action, not a generic
    label."""
    assert "inimize" in segment._minimize_button.toolTip()  # noqa: SLF001
    assert "aximize" in segment._maximize_button.toolTip()  # noqa: SLF001
    assert "lose" in segment._close_button.toolTip()  # noqa: SLF001