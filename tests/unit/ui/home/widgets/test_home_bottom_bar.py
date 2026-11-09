"""Tests for HomeBottomBar."""

from __future__ import annotations

import pytest
from pytestqt.qtbot import QtBot
from tests.conftest import make_icon_provider, make_theme_service

from cranioz.ui.home.widgets.home_bottom_bar import HomeBottomBar
from cranioz.ui.home.widgets.start_button import StartButton
from cranioz.ui.icons.provider import IconProvider
from cranioz.ui.theme.tokens import ThemeMode


@pytest.fixture
def start_button() -> StartButton:
    """A StartButton with a dark-theme IconProvider.

    NOT registered with qtbot: HomeBottomBar reparents the button and
    owns its lifetime. Registering both would cause a double-close at
    teardown (RuntimeError: C++ object already deleted).
    """
    theme_service = make_theme_service(ThemeMode.DARK)
    icon_provider: IconProvider = make_icon_provider(theme_service)
    return StartButton(icon_provider)


def test_bottom_bar_holds_start_button(qtbot: QtBot, start_button: StartButton) -> None:
    bar = HomeBottomBar(start_button)
    qtbot.addWidget(bar)
    assert bar.start_button() is start_button


def test_bottom_bar_has_minimum_height(qtbot: QtBot, start_button: StartButton) -> None:
    bar = HomeBottomBar(start_button)
    qtbot.addWidget(bar)
    assert bar.minimumHeight() == HomeBottomBar.MINIMUM_HEIGHT


def test_bottom_bar_is_ancestor_of_start_button(qtbot: QtBot, start_button: StartButton) -> None:
    bar = HomeBottomBar(start_button)
    qtbot.addWidget(bar)
    assert bar.isAncestorOf(start_button)


def test_bottom_bar_start_button_is_not_reparented_back(
    qtbot: QtBot, start_button: StartButton
) -> None:
    """The StartButton must be a child of HomeBottomBar after construction."""
    bar = HomeBottomBar(start_button)
    qtbot.addWidget(bar)
    assert start_button.parent() is bar
