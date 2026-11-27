"""Contract tests for the SVG icon provider."""

from __future__ import annotations

import logging
from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication

from cranioz.infrastructure.settings.in_memory_settings_service import (
    InMemorySettingsService,
)
from cranioz.ui.icons.catalog import SVG_ICON_ASSETS
from cranioz.ui.icons.state import IconState
from cranioz.ui.icons.svg import SvgIconProvider, default_svg_icons_root
from cranioz.ui.icons.unicode import UnicodeIconProvider
from cranioz.ui.theme.service import ThemeService
from cranioz.ui.theme.tokens import ThemeMode


@pytest.fixture
def theme_service() -> ThemeService:
    return ThemeService(settings=InMemorySettingsService())


@pytest.fixture
def fallback_provider(theme_service: ThemeService) -> UnicodeIconProvider:
    return UnicodeIconProvider(theme_service)


@pytest.fixture
def provider(
    qapp: QApplication,
    theme_service: ThemeService,
    fallback_provider: UnicodeIconProvider,
) -> SvgIconProvider:
    return SvgIconProvider(
        theme_service=theme_service,
        icons_root=default_svg_icons_root(),
        fallback_provider=fallback_provider,
    )


@pytest.mark.parametrize("name", tuple(SVG_ICON_ASSETS))
def test_catalog_svg_assets_render_visible_pixels(
    provider: SvgIconProvider,
    name: str,
) -> None:
    image = provider.icon(name, size=24).pixmap(24, 24).toImage()

    assert image.isNull() is False
    assert any(
        image.pixelColor(x, y).alpha() > 0
        for x in range(image.width())
        for y in range(image.height())
    )


def test_theme_change_recolors_and_invalidates_cached_icons(
    provider: SvgIconProvider,
    theme_service: ThemeService,
) -> None:
    dark = provider.icon("professional_profile", size=24)
    dark_image = dark.pixmap(24, 24).toImage()

    theme_service.set_mode(ThemeMode.LIGHT)
    light = provider.icon("professional_profile", size=24)
    light_image = light.pixmap(24, 24).toImage()

    assert light is not dark
    assert light_image != dark_image


def test_selected_state_uses_a_different_rendered_color(
    provider: SvgIconProvider,
) -> None:
    default_image = provider.icon("settings", size=24).pixmap(24, 24).toImage()
    selected_image = (
        provider.icon("settings", size=24, state=IconState.SELECTED).pixmap(24, 24).toImage()
    )

    assert selected_image != default_image


def test_window_control_states_use_distinct_icons(provider: SvgIconProvider) -> None:
    maximize = provider.icon("window_maximize", size=24).pixmap(24, 24).toImage()
    fullscreen = provider.icon("window_fullscreen", size=24).pixmap(24, 24).toImage()
    restore = provider.icon("window_restore", size=24).pixmap(24, 24).toImage()

    assert maximize != fullscreen
    assert maximize != restore
    assert fullscreen != restore


def test_wide_svg_preserves_its_aspect_ratio(provider: SvgIconProvider) -> None:
    icon = provider.icon("cranioz", size=20)
    image = icon.pixmap(100, 20).toImage()

    assert image.isNull() is False
    assert image.width() == 100
    assert image.height() == 20
    assert any(
        image.pixelColor(x, y).alpha() > 0
        for x in range(image.width())
        for y in range(image.height())
    )


def test_missing_svg_delegates_to_unicode_fallback(
    provider: SvgIconProvider,
    fallback_provider: UnicodeIconProvider,
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level(logging.DEBUG, logger="cranioz.ui.icons.svg"):
        icon = provider.icon("save", size=20)

    assert icon.isNull() is False
    assert provider.text_glyph("save") == fallback_provider.text_glyph("save")
    assert "missing asset" in caplog.text
    assert all(record.levelno < logging.WARNING for record in caplog.records)


def test_invalid_svg_uses_fallback_and_logs(
    qapp: QApplication,
    tmp_path: Path,
    theme_service: ThemeService,
    fallback_provider: UnicodeIconProvider,
    caplog: pytest.LogCaptureFixture,
) -> None:
    icons_root = tmp_path / "icons"
    icons_root.mkdir()
    (icons_root / "invalid.svg").write_text(
        "<svg xmlns='http://www.w3.org/2000/svg' fill='currentColor'><broken>",
        encoding="utf-8",
    )
    provider = SvgIconProvider(
        theme_service=theme_service,
        icons_root=icons_root,
        fallback_provider=fallback_provider,
    )

    with caplog.at_level(logging.ERROR):
        icon = provider.icon("invalid", size=20)

    assert icon.isNull() is False
    assert "invalid SVG icon" in caplog.text


def test_catalog_assets_are_source_recolorable() -> None:
    icons_root = default_svg_icons_root()

    for relative_path in SVG_ICON_ASSETS.values():
        source = (icons_root / relative_path).read_text(encoding="utf-8")
        assert "currentColor" in source
