"""Tests for HomeTopBar."""

from __future__ import annotations

from pytestqt.qtbot import QtBot

from cranioz.ui.home.widgets.home_top_bar import HomeTopBar


def test_menu_button_emits_signal(qtbot: QtBot) -> None:
    bar = HomeTopBar()
    qtbot.addWidget(bar)

    with qtbot.waitSignal(bar.menu_requested, timeout=1000):
        bar._menu_button.click()


def test_help_button_emits_signal(qtbot: QtBot) -> None:
    bar = HomeTopBar()
    qtbot.addWidget(bar)

    with qtbot.waitSignal(bar.help_requested, timeout=1000):
        bar._help_button.click()


def test_settings_button_emits_signal(qtbot: QtBot) -> None:
    bar = HomeTopBar()
    qtbot.addWidget(bar)

    with qtbot.waitSignal(bar.settings_requested, timeout=1000):
        bar._settings_button.click()


def test_title_is_cranioz(qtbot: QtBot) -> None:
    bar = HomeTopBar()
    qtbot.addWidget(bar)
    assert bar._title.text() == "CranioZ"
