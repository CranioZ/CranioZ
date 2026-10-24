"""Tests for CommunitySidebar."""

from __future__ import annotations

import pytest
from pytestqt.qtbot import QtBot

from cranioz.ui.home.widgets.community_sidebar import CommunitySidebar


def test_has_five_buttons(qtbot: QtBot) -> None:
    sidebar = CommunitySidebar()
    qtbot.addWidget(sidebar)
    for key in ("community", "library", "news", "feedback", "contribute"):
        assert sidebar.button_for(key) is not None


@pytest.mark.parametrize(
    ("key", "signal_name"),
    [
        ("community", "community_requested"),
        ("library", "library_requested"),
        ("news", "news_requested"),
        ("feedback", "feedback_requested"),
        ("contribute", "contribute_requested"),
    ],
)
def test_buttons_emit_signals(qtbot: QtBot, key: str, signal_name: str) -> None:
    sidebar = CommunitySidebar()
    qtbot.addWidget(sidebar)
    signal = getattr(sidebar, signal_name)

    with qtbot.waitSignal(signal, timeout=1000):
        sidebar.button_for(key).click()
