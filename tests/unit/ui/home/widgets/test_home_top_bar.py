"""Tests for HomeTopBar."""

from __future__ import annotations

import pytest
from pytestqt.qtbot import QtBot
from tests.conftest import make_icon_provider, make_theme_service

from cranioz.ui.home.widgets.home_top_bar import HomeTopBar
from cranioz.ui.icons.provider import IconProvider
from cranioz.ui.theme.tokens import ThemeMode


@pytest.fixture
def bar(qtbot: QtBot) -> HomeTopBar:
    """A HomeTopBar with a dark-theme IconProvider, registered with qtbot."""
    theme_service = make_theme_service(ThemeMode.DARK)
    icon_provider: IconProvider = make_icon_provider(theme_service)
    widget = HomeTopBar(icon_provider)
    qtbot.addWidget(widget)
    return widget


def test_menu_button_emits_toggle_signal(qtbot: QtBot, bar: HomeTopBar) -> None:
    with qtbot.waitSignal(bar.toggle_sidebar_requested, timeout=1000):
        bar._menu_button.click()


def test_top_bar_has_fixed_height(bar: HomeTopBar) -> None:
    assert bar.height() == HomeTopBar.FIXED_HEIGHT


def test_action_buttons_use_icon_variant(bar: HomeTopBar) -> None:
    buttons = (
        bar._menu_button,
        bar._logs_button,
        bar._help_button,
        bar._settings_button,
    )

    assert all(button.property("class") == "icon" for button in buttons)


def test_help_button_emits_signal(qtbot: QtBot, bar: HomeTopBar) -> None:
    with qtbot.waitSignal(bar.help_requested, timeout=1000):
        bar._help_button.click()


def test_logs_button_emits_signal(qtbot: QtBot, bar: HomeTopBar) -> None:
    with qtbot.waitSignal(bar.logs_requested, timeout=1000):
        bar._logs_button.click()


def test_settings_button_emits_signal(qtbot: QtBot, bar: HomeTopBar) -> None:
    with qtbot.waitSignal(bar.settings_requested, timeout=1000):
        bar._settings_button.click()


def test_logo_is_rendered_from_svg(bar: HomeTopBar) -> None:
    pixmap = bar._title.pixmap()

    assert pixmap.isNull() is False
    assert pixmap.size().width() == 80
    assert pixmap.size().height() == 16
    assert bar._title.accessibleName() == "CranioZ"


@pytest.mark.qt
def test_minimize_button_emits_signal(qtbot: QtBot, bar: HomeTopBar) -> None:
    with qtbot.waitSignal(bar.minimize_requested, timeout=1000):
        bar._minimize_button.click()  # noqa: SLF001


@pytest.mark.qt
def test_maximize_button_emits_signal(qtbot: QtBot, bar: HomeTopBar) -> None:
    with qtbot.waitSignal(bar.maximize_requested, timeout=1000):
        bar._maximize_button.click()  # noqa: SLF001


@pytest.mark.qt
def test_close_button_emits_signal(qtbot: QtBot, bar: HomeTopBar) -> None:
    with qtbot.waitSignal(bar.close_requested, timeout=1000):
        bar._close_button.click()  # noqa: SLF001


@pytest.mark.qt
def test_window_buttons_have_fixed_width_28(bar: HomeTopBar) -> None:
    assert bar._minimize_button.width() == 28  # noqa: SLF001
    assert bar._maximize_button.width() == 28  # noqa: SLF001
    assert bar._close_button.width() == 28  # noqa: SLF001


@pytest.mark.qt
def test_window_buttons_have_icons(bar: HomeTopBar) -> None:
    assert not bar._minimize_button.icon().isNull()  # noqa: SLF001
    assert not bar._maximize_button.icon().isNull()  # noqa: SLF001
    assert not bar._close_button.icon().isNull()  # noqa: SLF001
