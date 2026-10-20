"""Tests for HomeBottomBar."""

from __future__ import annotations

from pytestqt.qtbot import QtBot

from cranioz.ui.home.widgets.home_bottom_bar import HomeBottomBar
from cranioz.ui.home.widgets.start_button import StartButton


def test_bottom_bar_holds_start_button(qtbot: QtBot) -> None:
    button = StartButton()
    bar = HomeBottomBar(button)
    qtbot.addWidget(bar)
    assert bar.start_button() is button


def test_bottom_bar_has_minimum_height(qtbot: QtBot) -> None:
    bar = HomeBottomBar(StartButton())
    qtbot.addWidget(bar)
    assert bar.minimumHeight() == HomeBottomBar.MINIMUM_HEIGHT


def test_bottom_bar_is_ancestor_of_start_button(qtbot: QtBot) -> None:
    button = StartButton()
    bar = HomeBottomBar(button)
    qtbot.addWidget(bar)
    assert bar.isAncestorOf(button)


def test_bottom_bar_start_button_is_not_reparented_back(
    qtbot: QtBot,
) -> None:
    """The StartButton must be a child of HomeBottomBar after construction."""
    button = StartButton()
    bar = HomeBottomBar(button)
    qtbot.addWidget(bar)
    assert button.parent() is bar
