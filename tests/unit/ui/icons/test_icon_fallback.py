"""Contract: unknown icon names return '?' and log a warning."""

import logging

import pytest

from cranioz.infrastructure.settings.in_memory_settings_service import InMemorySettingsService
from cranioz.ui.icons.unicode import UnicodeIconProvider
from cranioz.ui.theme.service import ThemeService


@pytest.fixture
def provider(qapp) -> UnicodeIconProvider:
    service = ThemeService(
        settings=InMemorySettingsService(),
    )
    return UnicodeIconProvider(service)


def test_unknown_icon_returns_fallback(provider, caplog) -> None:
    with caplog.at_level(logging.WARNING, logger="cranioz.ui.icons.unicode"):
        icon = provider.icon("does_not_exist")
    assert not icon.isNull()
    assert "unknown icon name 'does_not_exist'" in caplog.text


def test_unknown_text_glyph_returns_question_mark(provider) -> None:
    assert provider.text_glyph("does_not_exist") == "?"
