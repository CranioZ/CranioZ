"""Tests for ThemeCompiler and CompiledStyles."""

from __future__ import annotations

import pytest
from PySide6.QtWidgets import QApplication

from cranioz.ui.theme import compiler as compiler_module
from cranioz.ui.theme.compiler import (
    CompiledStyles,
    ThemeCompiler,
    _compose_rgba,
    _hex_to_rgb,
)
from cranioz.ui.theme.tokens import (
    DARK_TOKENS,
    LIGHT_TOKENS,
    ElevationSpec,
    ThemeName,
)

# ----- _hex_to_rgb ---------------------------------------------------


class _FakeQApplication(QApplication):
    """QApplication subclass whose instance() always returns None.

    Only the static method is consulted by ThemeCompiler.apply(); the
    class is never instantiated.
    """

    @staticmethod
    def instance() -> None:
        return None


def test_hex_to_rgb_black() -> None:
    assert _hex_to_rgb("#000000") == (0, 0, 0)


def test_hex_to_rgb_white() -> None:
    assert _hex_to_rgb("#FFFFFF") == (255, 255, 255)


def test_hex_to_rgb_mixed() -> None:
    assert _hex_to_rgb("#1E1E1E") == (30, 30, 30)


def test_hex_to_rgb_rejects_short_hex() -> None:
    with pytest.raises(ValueError):
        _hex_to_rgb("#FFF")


def test_hex_to_rgb_rejects_non_hash() -> None:
    with pytest.raises(ValueError):
        _hex_to_rgb("1E1E1E")


# ----- _compose_rgba -------------------------------------------------


def test_compose_rgba_full_opacity() -> None:
    assert _compose_rgba("#1E1E1E", 1.0) == "rgba(30,30,30,1.0000)"


def test_compose_rgba_half_opacity() -> None:
    assert _compose_rgba("#252526", 0.92) == "rgba(37,37,38,0.9200)"


def test_compose_rgba_zero_opacity() -> None:
    assert _compose_rgba("#000000", 0.0) == "rgba(0,0,0,0.0000)"


# ----- compile: happy path -------------------------------------------


def test_compile_dark_returns_compiled_styles() -> None:
    compiler = ThemeCompiler()
    styles = compiler.compile(DARK_TOKENS)
    assert isinstance(styles, CompiledStyles)
    assert styles.theme_name is ThemeName.DARK
    assert styles.qss  # non-empty
    assert "toolbar" in styles.surface_colors
    assert "popover" in styles.surface_colors
    assert "modal_backdrop" in styles.surface_colors


def test_compile_light_returns_compiled_styles() -> None:
    compiler = ThemeCompiler()
    styles = compiler.compile(LIGHT_TOKENS)
    assert styles.theme_name is ThemeName.LIGHT
    assert styles.qss


def test_compile_is_deterministic() -> None:
    compiler = ThemeCompiler()
    a = compiler.compile(DARK_TOKENS)
    b = compiler.compile(DARK_TOKENS)
    assert a.qss == b.qss
    assert a.surface_colors == b.surface_colors
    assert a.elevations == b.elevations


# ----- surface composition -------------------------------------------


def test_toolbar_surface_uses_background_panel_dark() -> None:
    """Dark toolbar = #242426 at 0.92."""
    compiler = ThemeCompiler()
    styles = compiler.compile(DARK_TOKENS)
    assert styles.surface_color("toolbar") == "rgba(36,36,38,0.9200)"


def test_toolbar_surface_uses_background_panel_light() -> None:
    """Light toolbar = #FFFFFF at 0.92."""
    compiler = ThemeCompiler()
    styles = compiler.compile(LIGHT_TOKENS)
    assert styles.surface_color("toolbar") == "rgba(255,255,255,0.9200)"


def test_popover_surface_uses_background_elevated_dark() -> None:
    """Dark popover = #2C2C2E at 0.96."""
    compiler = ThemeCompiler()
    styles = compiler.compile(DARK_TOKENS)
    assert styles.surface_color("popover") == "rgba(44,44,46,0.9600)"


def test_modal_backdrop_uses_different_opacity_per_theme() -> None:
    """Dark = #000000 at 0.60, Light = #000000 at 0.40."""
    compiler = ThemeCompiler()
    dark = compiler.compile(DARK_TOKENS)
    light = compiler.compile(LIGHT_TOKENS)
    assert dark.surface_color("modal_backdrop") == "rgba(0,0,0,0.6000)"
    assert light.surface_color("modal_backdrop") == "rgba(0,0,0,0.4000)"


def test_surface_color_unknown_role_raises() -> None:
    compiler = ThemeCompiler()
    styles = compiler.compile(DARK_TOKENS)
    with pytest.raises(KeyError, match="unknown surface role"):
        styles.surface_color("not-a-role")


# ----- elevations ----------------------------------------------------


def test_elevations_are_exposed() -> None:
    compiler = ThemeCompiler()
    styles = compiler.compile(DARK_TOKENS)
    assert isinstance(styles.elevation("panel"), ElevationSpec)
    assert isinstance(styles.elevation("dialog"), ElevationSpec)
    assert isinstance(styles.elevation("overlay"), ElevationSpec)


def test_elevation_panel_values_dark() -> None:
    compiler = ThemeCompiler()
    styles = compiler.compile(DARK_TOKENS)
    panel = styles.elevation("panel")
    assert panel.offset_x == 0
    assert panel.offset_y == 1
    assert panel.blur_radius == 3
    assert panel.color == "rgba(0,0,0,0.40)"


def test_elevation_unknown_role_raises() -> None:
    compiler = ThemeCompiler()
    styles = compiler.compile(DARK_TOKENS)
    with pytest.raises(KeyError, match="unknown elevation role"):
        styles.elevation("not-a-role")


# ----- QSS sanity ----------------------------------------------------


def test_qss_contains_background_color() -> None:
    compiler = ThemeCompiler()
    styles = compiler.compile(DARK_TOKENS)
    assert DARK_TOKENS.colors.background_application in styles.qss


def test_qss_contains_border_radius() -> None:
    compiler = ThemeCompiler()
    styles = compiler.compile(DARK_TOKENS)
    assert f"border-radius: {DARK_TOKENS.borders.radius_control}px" in styles.qss


def test_qss_differs_between_themes() -> None:
    compiler = ThemeCompiler()
    dark_qss = compiler.compile(DARK_TOKENS).qss
    light_qss = compiler.compile(LIGHT_TOKENS).qss
    assert dark_qss != light_qss


# ----- apply: with QApplication (uses qapp fixture) ------------------


def test_apply_sets_application_stylesheet(qapp: QApplication) -> None:
    compiler = ThemeCompiler()
    styles = compiler.compile(DARK_TOKENS)

    # Reset any stylesheet from other tests.
    qapp.setStyleSheet("")
    assert qapp.styleSheet() == ""

    compiler.apply(styles)

    assert qapp.styleSheet() == styles.qss


def test_apply_replaces_previous_stylesheet(qapp: QApplication) -> None:
    compiler = ThemeCompiler()
    dark = compiler.compile(DARK_TOKENS)
    light = compiler.compile(LIGHT_TOKENS)

    compiler.apply(dark)
    assert qapp.styleSheet() == dark.qss

    compiler.apply(light)
    assert qapp.styleSheet() == light.qss


# ----- apply: without QApplication ----------------------------------


def test_apply_without_qapplication_logs_warning(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """When no QApplication exists, apply() logs a warning and returns."""
    monkeypatch.setattr(
        compiler_module,
        "QApplication",
        _FakeQApplication,
    )

    compiler = ThemeCompiler()
    styles = compiler.compile(DARK_TOKENS)

    with caplog.at_level("WARNING", logger="cranioz.ui.theme.compiler"):
        compiler.apply(styles)

    assert "skipping global stylesheet application" in caplog.text
