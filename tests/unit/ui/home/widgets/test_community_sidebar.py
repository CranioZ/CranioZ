"""Tests for CommunitySidebar."""

from __future__ import annotations

import pytest
from pytestqt.qtbot import QtBot
from tests.conftest import make_icon_provider, make_theme_service

from cranioz.ui.home.widgets.community_sidebar import CommunitySidebar
from cranioz.ui.icons.provider import IconProvider
from cranioz.ui.theme.tokens import ThemeMode


@pytest.fixture
def sidebar(qtbot: QtBot) -> CommunitySidebar:
    """A CommunitySidebar with a dark-theme IconProvider."""
    theme_service = make_theme_service(ThemeMode.DARK)
    icon_provider: IconProvider = make_icon_provider(theme_service)
    widget = CommunitySidebar(icon_provider)
    qtbot.addWidget(widget)
    return widget


def test_has_five_buttons(sidebar: CommunitySidebar) -> None:
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
def test_buttons_emit_signals(
    qtbot: QtBot, sidebar: CommunitySidebar, key: str, signal_name: str
) -> None:
    signal = getattr(sidebar, signal_name)

    with qtbot.waitSignal(signal, timeout=1000):
        sidebar.button_for(key).click()
