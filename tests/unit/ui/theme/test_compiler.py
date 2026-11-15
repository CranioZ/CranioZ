"""Tests for ThemeCompiler and CompiledStyles.

Block 5.7:
- The RGBA composition now emits the CSS/QSS percentage form
  (``rgba(r,g,b,X.XX%)``) instead of the non-standard decimal form.
- ``CompiledStyles`` wraps its maps in ``MappingProxyType``; mutation
  attempts raise ``TypeError``.
- ``_hex_to_rgb`` uses a regex, so invalid characters produce a
  useful error message.
"""

from __future__ import annotations

import pytest
from PySide6.QtWidgets import QApplication

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


def test_hex_to_rgb_black() -> None:
    assert _hex_to_rgb("#000000") == (0, 0, 0)


def test_hex_to_rgb_white() -> None:
    assert _hex_to_rgb("#FFFFFF") == (255, 255, 255)


def test_hex_to_rgb_mixed() -> None:
    assert _hex_to_rgb("#1E1E1E") == (30, 30, 30)


def test_hex_to_rgb_rejects_short_hex() -> None:
    with pytest.raises(ValueError, match="Invalid color"):
        _hex_to_rgb("#FFF")


def test_hex_to_rgb_rejects_non_hash() -> None:
    with pytest.raises(ValueError, match="Invalid color"):
        _hex_to_rgb("1E1E1E")


def test_hex_to_rgb_rejects_invalid_chars() -> None:
    with pytest.raises(ValueError, match="Invalid color"):
        _hex_to_rgb("#GGGGGG")


def test_hex_to_rgb_rejects_long_string() -> None:
    with pytest.raises(ValueError, match="Invalid color"):
        _hex_to_rgb("#1E1E1E1E")


# ----- _compose_rgba -------------------------------------------------


def test_compose_rgba_full_opacity() -> None:
    assert _compose_rgba("#1E1E1E", 1.0) == "rgba(30,30,30,100.00%)"


def test_compose_rgba_half_opacity() -> None:
    assert _compose_rgba("#252526", 0.92) == "rgba(37,37,38,92.00%)"


def test_compose_rgba_zero_opacity() -> None:
    assert _compose_rgba("#000000", 0.0) == "rgba(0,0,0,0.00%)"


def test_compose_rgba_decimal_opacity() -> None:
    """A fractional opacity is formatted with two decimal places."""
    assert _compose_rgba("#000000", 0.333) == "rgba(0,0,0,33.30%)"


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


# ----- surface composition (Block 5.7 palette) -----------------------


def test_toolbar_surface_uses_background_panel_dark() -> None:
    """Dark toolbar = #2A3038 at 0.92."""
    compiler = ThemeCompiler()
    styles = compiler.compile(DARK_TOKENS)
    assert styles.surface_color("toolbar") == "rgba(42,48,56,92.00%)"


def test_toolbar_surface_uses_background_panel_light() -> None:
    """Light toolbar = #FFFFFF at 0.92."""
    compiler = ThemeCompiler()
    styles = compiler.compile(LIGHT_TOKENS)
    assert styles.surface_color("toolbar") == "rgba(255,255,255,92.00%)"


def test_popover_surface_uses_background_elevated_dark() -> None:
    """Dark popover = #353C46 at 0.96."""
    compiler = ThemeCompiler()
    styles = compiler.compile(DARK_TOKENS)
    assert styles.surface_color("popover") == "rgba(53,60,70,96.00%)"


def test_modal_backdrop_uses_different_opacity_per_theme() -> None:
    """Dark = #000000 at 60%, Light = #000000 at 40%."""
    compiler = ThemeCompiler()
    dark = compiler.compile(DARK_TOKENS)
    light = compiler.compile(LIGHT_TOKENS)
    assert dark.surface_color("modal_backdrop") == "rgba(0,0,0,60.00%)"
    assert light.surface_color("modal_backdrop") == "rgba(0,0,0,40.00%)"


def test_surface_color_unknown_role_raises() -> None:
    compiler = ThemeCompiler()
    styles = compiler.compile(DARK_TOKENS)
    with pytest.raises(KeyError, match="unknown surface role"):
        styles.surface_color("not-a-role")


# ----- surface immutability (Block 5.7) ------------------------------


def test_surface_colors_mapping_is_immutable() -> None:
    """``surface_colors`` is a ``MappingProxyType``: mutation raises."""
    compiler = ThemeCompiler()
    styles = compiler.compile(DARK_TOKENS)
    with pytest.raises(TypeError):
        styles.surface_colors["toolbar"] = "red"  # type: ignore[index]


def test_elevations_mapping_is_immutable() -> None:
    """``elevations`` is a ``MappingProxyType``: mutation raises."""
    compiler = ThemeCompiler()
    styles = compiler.compile(DARK_TOKENS)
    with pytest.raises(TypeError):
        styles.elevations["panel"] = None  # type: ignore[index]


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


# ----- apply: no QApplication (documented as not unit-testable) -----
#
# NOTE: the "no QApplication" branch of ``ThemeCompiler.apply`` is
# defensive (it logs a warning and returns). It cannot be tested
# reliably in a PySide6 session because patching ``QApplication``
# (either the symbol or its ``instance`` static method) interacts
# with the Qt binding in ways that vary between PySide6 versions.
#
# The contract "apply() must not crash when called without a
# QApplication" is covered by:
#   1. the defensive ``if not isinstance(app, QApplication)`` in
#      ``ThemeCompiler.apply``;
#   2. the production boot order in ``__main__.py``, which creates
#      the QApplication before any ``apply()`` call.
#
# A unit test for this branch would test the mocking library, not
# the compiler. See Block 5.7 review notes.
