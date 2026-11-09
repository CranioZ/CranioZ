"""Contract: icon colors follow the active theme and state."""

from __future__ import annotations

import pytest

from cranioz.infrastructure.settings.in_memory_settings_service import (
    InMemorySettingsService,
)
from cranioz.ui.icons.state import IconState
from cranioz.ui.icons.unicode import UnicodeIconProvider
from cranioz.ui.theme.service import ThemeService
from cranioz.ui.theme.tokens import ThemeMode


@pytest.fixture
def theme_service() -> ThemeService:
    return ThemeService(settings=InMemorySettingsService())


@pytest.fixture
def provider(theme_service: ThemeService) -> UnicodeIconProvider:
    return UnicodeIconProvider(theme_service)


def test_icon_color_changes_with_theme(
    provider: UnicodeIconProvider,
    theme_service: ThemeService,
) -> None:
    """The DEFAULT state color must follow the active theme.

    This test asserts the contract at the provider level: the
    ``UnicodeIconProvider`` resolves its colors from the
    ``ThemeService``, and the ``ThemeService`` reflects the active
    theme. It does not depend on the QPainter successfully rendering
    a Unicode glyph, which is environment-dependent (the default
    font in headless CI may not cover every emoji).
    """
    color_dark = provider._color_for_state(IconState.DEFAULT).name()
    theme_service.set_mode(ThemeMode.LIGHT)
    color_light = provider._color_for_state(IconState.DEFAULT).name()
    assert color_dark != color_light


@pytest.mark.parametrize(
    ("state", "expected_token"),
    [
        (IconState.DEFAULT, "text_primary"),
        (IconState.HOVER, "interactive_hover"),
        (IconState.PRESSED, "interactive_pressed"),
        (IconState.SELECTED, "interactive_default"),
        (IconState.DISABLED, "text_disabled"),
    ],
)
def test_state_uses_expected_token(
    provider: UnicodeIconProvider,
    theme_service: ThemeService,
    state: IconState,
    expected_token: str,
) -> None:
    """Each IconState resolves the documented ColorTokens field."""
    actual = provider._color_for_state(state).name()
    expected = theme_service.color(expected_token)
    assert actual.lower() == expected.lower()
