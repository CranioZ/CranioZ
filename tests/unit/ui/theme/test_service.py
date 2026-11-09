"""Tests for ThemeService."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject

from cranioz.infrastructure.settings.in_memory_settings_service import (
    InMemorySettingsService,
)
from cranioz.infrastructure.settings.keys import APPEARANCE_THEME_MODE
from cranioz.ui.theme import service as service_module
from cranioz.ui.theme.compiler import CompiledStyles
from cranioz.ui.theme.service import ThemeService
from cranioz.ui.theme.tokens import (
    DARK_TOKENS,
    LIGHT_TOKENS,
    ThemeMode,
    ThemeName,
    ThemeTokens,
)

# ----- Helpers -------------------------------------------------------


def _make(
    *,
    mode: ThemeMode = ThemeMode.DARK,
    settings: InMemorySettingsService | None = None,
) -> ThemeService:
    return ThemeService(
        settings=settings or InMemorySettingsService(),
        default_mode=mode,
    )


# ----- Construction and mode ------------------------------------------


def test_default_mode_is_dark() -> None:
    service = _make()
    assert service.mode() is ThemeMode.DARK
    assert service.theme() is ThemeName.DARK


def test_default_mode_can_be_light() -> None:
    service = _make(mode=ThemeMode.LIGHT)
    assert service.mode() is ThemeMode.LIGHT
    assert service.theme() is ThemeName.LIGHT


def test_persisted_mode_overrides_default() -> None:
    settings = InMemorySettingsService()
    settings.seed(APPEARANCE_THEME_MODE, ThemeMode.LIGHT.value)

    service = ThemeService(settings=settings, default_mode=ThemeMode.DARK)

    assert service.mode() is ThemeMode.LIGHT
    assert service.theme() is ThemeName.LIGHT


def test_invalid_persisted_mode_falls_back_to_default(
    caplog: pytest.LogCaptureFixture,
) -> None:
    settings = InMemorySettingsService()
    settings.seed(APPEARANCE_THEME_MODE, "not-a-theme")

    with caplog.at_level("WARNING", logger="cranioz.ui.theme.service"):
        service = ThemeService(
            settings=settings,
            default_mode=ThemeMode.DARK,
        )

    assert service.mode() is ThemeMode.DARK
    assert service.theme() is ThemeName.DARK
    assert "invalid appearance.theme_mode" in caplog.text


# ----- set_mode -------------------------------------------------------


def test_set_mode_updates_mode_and_theme() -> None:
    service = _make()
    service.set_mode(ThemeMode.LIGHT)
    assert service.mode() is ThemeMode.LIGHT
    assert service.theme() is ThemeName.LIGHT


def test_set_mode_same_mode_is_noop() -> None:
    service = _make()
    emitted: list[ThemeName] = []
    service.theme_changed.connect(emitted.append)

    service.set_mode(ThemeMode.DARK)

    assert emitted == []


def test_set_mode_emits_theme_changed() -> None:
    service = _make()
    emitted: list[ThemeName] = []
    service.theme_changed.connect(emitted.append)

    service.set_mode(ThemeMode.LIGHT)

    assert emitted == [ThemeName.LIGHT]


def test_set_mode_does_not_persist() -> None:
    settings = InMemorySettingsService()
    service = ThemeService(settings=settings, default_mode=ThemeMode.DARK)

    changes: list[str] = []
    settings.changed.connect(changes.append)

    service.set_mode(ThemeMode.LIGHT)

    # set_mode must not call settings.set(); persistence is the caller's job.
    assert changes == []
    assert settings.get(APPEARANCE_THEME_MODE, ThemeMode.DARK.value) == ThemeMode.DARK.value


# ----- tokens and accessors -------------------------------------------


def test_tokens_returns_dark_tokens() -> None:
    service = _make()
    assert service.tokens() is DARK_TOKENS


def test_tokens_returns_light_tokens() -> None:
    service = _make(mode=ThemeMode.LIGHT)
    assert service.tokens() is LIGHT_TOKENS


def test_color_returns_expected_value() -> None:
    service = _make()
    assert service.color("background_application") == "#1E1E1E"
    assert service.color("text.primary".replace(".", "_")) == "#E8E8E8"


def test_color_unknown_path_raises() -> None:
    service = _make()
    with pytest.raises(KeyError, match="unknown color token"):
        service.color("does_not_exist")


def test_dimension_returns_expected_value() -> None:
    service = _make()
    assert service.dimension("control_height") == 28
    assert service.dimension("icon_size") == 20


def test_dimension_unknown_path_raises() -> None:
    service = _make()
    with pytest.raises(KeyError, match="unknown dimension token"):
        service.dimension("does_not_exist")


def test_surface_color_toolbar_is_composed() -> None:
    service = _make()
    # Dark toolbar = background_panel #252526 at 0.92 opacity.
    assert service.surface_color("toolbar") == "rgba(37,37,38,0.9200)"


def test_surface_color_unknown_role_raises() -> None:
    service = _make()
    with pytest.raises(KeyError, match="unknown surface role"):
        service.surface_color("does_not_exist")


# ----- compiled and compiler ------------------------------------------


def test_compiled_returns_compiled_styles() -> None:
    service = _make()
    compiled = service.compiled()
    assert isinstance(compiled, CompiledStyles)
    assert compiled.theme_name is ThemeName.DARK


def test_compiler_accessor() -> None:
    service = _make()
    compiler = service.compiler()
    # Compiling the same tokens twice must produce equivalent surfaces.
    a = compiler.compile(DARK_TOKENS)
    b = compiler.compile(DARK_TOKENS)
    assert a.surface_colors == b.surface_colors
    assert a.qss == b.qss


# ----- icon_name (legacy, kept for Sprint F) --------------------------


def test_icon_name_is_identity() -> None:
    service = _make()
    assert service.icon_name("log") == "log"
    assert service.icon_name("toggle") == "toggle"


def test_icon_name_is_theme_agnostic() -> None:
    dark = _make(mode=ThemeMode.DARK)
    light = _make(mode=ThemeMode.LIGHT)
    assert dark.icon_name("x") == light.icon_name("x")


def test_empty_icon_name_raises() -> None:
    service = _make()
    with pytest.raises(ValueError, match="logical_name"):
        service.icon_name("")


# ----- theme_changed signal and system resolution --------------------


def test_system_mode_falls_back_to_dark_without_qapplication() -> None:
    """In tests without a running QGuiApplication, SYSTEM resolves to DARK."""
    service = _make(mode=ThemeMode.SYSTEM)
    assert service.theme() is ThemeName.DARK


def test_system_mode_reacts_to_color_scheme_change(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When SYSTEM is active and colorSchemeChanged fires, the theme updates."""

    forced_theme = ThemeName.LIGHT
    monkeypatch.setattr(service_module, "_resolve_system_theme", lambda: forced_theme)

    service = _make(mode=ThemeMode.SYSTEM)

    # Simulate the OS preference change by invoking the private slot.
    service._on_color_scheme_changed(None)  # noqa: SLF001

    assert service.theme() is ThemeName.LIGHT


def test_non_system_mode_ignores_color_scheme_change(
    monkeypatch: pytest.MonkeyPatch,
) -> None:

    monkeypatch.setattr(service_module, "_resolve_system_theme", lambda: ThemeName.LIGHT)

    service = _make(mode=ThemeMode.DARK)

    service._on_color_scheme_changed(None)  # noqa: SLF001

    assert service.theme() is ThemeName.DARK


# ----- invariants -----------------------------------------------------


def test_theme_service_is_a_qobject() -> None:
    service = _make()
    assert isinstance(service, QObject)


def test_tokens_type_matches_theme() -> None:
    service = _make(mode=ThemeMode.LIGHT)
    tokens: ThemeTokens = service.tokens()
    assert tokens.name is ThemeName.LIGHT


def test_theme_changed_signal_exists() -> None:
    service = _make()
    # Sanity: the signal is declared and connectable.
    service.theme_changed.connect(lambda _name: None)
