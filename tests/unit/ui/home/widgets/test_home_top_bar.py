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


def test_help_button_emits_signal(qtbot: QtBot, bar: HomeTopBar) -> None:
    with qtbot.waitSignal(bar.help_requested, timeout=1000):
        bar._help_button.click()


def test_settings_button_emits_signal(qtbot: QtBot, bar: HomeTopBar) -> None:
    with qtbot.waitSignal(bar.settings_requested, timeout=1000):
        bar._settings_button.click()


def test_title_is_cranioz(bar: HomeTopBar) -> None:
    assert bar._title.text() == "CranioZ"
