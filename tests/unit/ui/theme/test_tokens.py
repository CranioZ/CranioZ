"""Tests for the canonical design tokens."""

from __future__ import annotations

import dataclasses
from collections.abc import Callable

import pytest

from cranioz.ui.theme.tokens import (
    DARK_TOKENS,
    LIGHT_TOKENS,
    THEME_TOKENS,
    BorderTokens,
    ColorTokens,
    DimensionTokens,
    EffectTokens,
    ElevationSpec,
    SpacingTokens,
    SurfaceTokens,
    ThemeMode,
    ThemeName,
    ThemeTokens,
    TypographyTokens,
    count_tokens,
    validate_all_themes,
    validate_tokens,
)

# ----- Enums ---------------------------------------------------------


def test_theme_mode_is_str_enum() -> None:
    assert issubclass(ThemeMode, str)
    assert ThemeMode.DARK.value == "dark"
    assert ThemeMode.LIGHT.value == "light"
    assert ThemeMode.SYSTEM.value == "system"


def test_theme_name_is_str_enum() -> None:
    assert issubclass(ThemeName, str)
    assert ThemeName.DARK.value == "dark"
    assert ThemeName.LIGHT.value == "light"


def test_theme_name_has_no_system_member() -> None:
    assert "SYSTEM" not in ThemeName.__members__


def test_theme_mode_members() -> None:
    assert {m.name for m in ThemeMode} == {"DARK", "LIGHT", "SYSTEM"}


def test_theme_name_members() -> None:
    assert {m.name for m in ThemeName} == {"DARK", "LIGHT"}


# ----- Canonical values ---------------------------------------------


def test_count_tokens_is_47() -> None:
    """Phase 2 closes at 47 tokens across 7 categories."""
    assert count_tokens() == 47


def test_theme_tokens_cover_all_concrete_names() -> None:
    assert set(THEME_TOKENS) == {ThemeName.DARK, ThemeName.LIGHT}


def test_dark_tokens_name_matches_key() -> None:
    assert DARK_TOKENS.name is ThemeName.DARK
    assert THEME_TOKENS[ThemeName.DARK] is DARK_TOKENS


def test_light_tokens_name_matches_key() -> None:
    assert LIGHT_TOKENS.name is ThemeName.LIGHT
    assert THEME_TOKENS[ThemeName.LIGHT] is LIGHT_TOKENS


# ----- Completeness across themes -----------------------------------


def _field_names(dc_type: type) -> set[str]:
    return {f.name for f in dataclasses.fields(dc_type)}


@pytest.mark.parametrize(
    "dc_type",
    [
        ColorTokens,
        TypographyTokens,
        SpacingTokens,
        DimensionTokens,
        BorderTokens,
        EffectTokens,
        SurfaceTokens,
    ],
)
def test_dark_and_light_have_identical_structure(dc_type: type) -> None:
    dark_field_names = _field_names(dc_type)
    dark_value = getattr(DARK_TOKENS, _category_for(dc_type))
    light_value = getattr(LIGHT_TOKENS, _category_for(dc_type))
    assert isinstance(dark_value, dc_type)
    assert isinstance(light_value, dc_type)
    for name in dark_field_names:
        assert hasattr(dark_value, name)
        assert hasattr(light_value, name)


def _category_for(dc_type: type) -> str:
    return {
        ColorTokens: "colors",
        TypographyTokens: "typography",
        SpacingTokens: "spacing",
        DimensionTokens: "dimensions",
        BorderTokens: "borders",
        EffectTokens: "effects",
        SurfaceTokens: "surfaces",
    }[dc_type]


# ----- Validation: happy path ---------------------------------------


def test_validate_all_themes_passes() -> None:
    validate_all_themes()


def test_validate_tokens_accepts_dark() -> None:
    validate_tokens(DARK_TOKENS)


def test_validate_tokens_accepts_light() -> None:
    validate_tokens(LIGHT_TOKENS)


# ----- Validation: failure modes ------------------------------------


def _mutated(tokens: ThemeTokens, **color_overrides: str) -> ThemeTokens:
    new_colors = dataclasses.replace(tokens.colors, **color_overrides)
    return dataclasses.replace(tokens, colors=new_colors)


def _assert_raises_with_message(
    fn: Callable[[], None],
    expected_substring: str,
) -> None:
    with pytest.raises(ValueError) as exc_info:
        fn()
    assert expected_substring in str(exc_info.value)


def test_invalid_hex_color_rejected() -> None:
    bad = _mutated(DARK_TOKENS, background_application="#XYZ")
    _assert_raises_with_message(lambda: validate_tokens(bad), "color.background_application")


def test_short_hex_color_rejected() -> None:
    bad = _mutated(DARK_TOKENS, background_application="#FFF")
    _assert_raises_with_message(lambda: validate_tokens(bad), "color.background_application")


def test_invalid_rgba_color_rejected() -> None:
    bad = _mutated(DARK_TOKENS, text_primary="rgba(300,0,0,0.5)")
    _assert_raises_with_message(lambda: validate_tokens(bad), "color.text_primary")


def test_effect_invalid_color_rejected() -> None:
    bad_effects = dataclasses.replace(DARK_TOKENS.effects, hover_overlay="not-a-color")
    bad = dataclasses.replace(DARK_TOKENS, effects=bad_effects)
    _assert_raises_with_message(lambda: validate_tokens(bad), "effect.hover_overlay")


def test_effect_negative_blur_rejected() -> None:
    bad_spec = dataclasses.replace(DARK_TOKENS.effects.elevation_panel, blur_radius=-1)
    bad_effects = dataclasses.replace(DARK_TOKENS.effects, elevation_panel=bad_spec)
    bad = dataclasses.replace(DARK_TOKENS, effects=bad_effects)
    _assert_raises_with_message(lambda: validate_tokens(bad), "blur_radius")


def test_surface_opacity_above_one_rejected() -> None:
    bad_surfaces = dataclasses.replace(DARK_TOKENS.surfaces, opacity_toolbar=1.01)
    bad = dataclasses.replace(DARK_TOKENS, surfaces=bad_surfaces)
    _assert_raises_with_message(lambda: validate_tokens(bad), "surface.opacity_toolbar")


def test_surface_opacity_below_zero_rejected() -> None:
    bad_surfaces = dataclasses.replace(DARK_TOKENS.surfaces, opacity_modal_backdrop=-0.1)
    bad = dataclasses.replace(DARK_TOKENS, surfaces=bad_surfaces)
    _assert_raises_with_message(lambda: validate_tokens(bad), "surface.opacity_modal_backdrop")


def test_negative_spacing_rejected() -> None:
    bad_spacing = dataclasses.replace(DARK_TOKENS.spacing, md=-1)
    bad = dataclasses.replace(DARK_TOKENS, spacing=bad_spacing)
    _assert_raises_with_message(lambda: validate_tokens(bad), "spacing.md")


def test_negative_dimension_rejected() -> None:
    bad_dimensions = dataclasses.replace(DARK_TOKENS.dimensions, control_height=-1)
    bad = dataclasses.replace(DARK_TOKENS, dimensions=bad_dimensions)
    _assert_raises_with_message(lambda: validate_tokens(bad), "dimension.control_height")


def test_negative_border_rejected() -> None:
    bad_borders = dataclasses.replace(DARK_TOKENS.borders, radius_control=-1)
    bad = dataclasses.replace(DARK_TOKENS, borders=bad_borders)
    _assert_raises_with_message(lambda: validate_tokens(bad), "border.radius_control")


# ----- Semantic values: a few spot checks ---------------------------


def test_dark_and_light_have_different_backgrounds() -> None:
    assert DARK_TOKENS.colors.background_application != (LIGHT_TOKENS.colors.background_application)


def test_modal_backdrop_opacity_differs_by_theme() -> None:
    """Per the spec, modal backdrop opacity is 0.60 in DARK, 0.40 in LIGHT."""
    assert DARK_TOKENS.surfaces.opacity_modal_backdrop == 0.60
    assert LIGHT_TOKENS.surfaces.opacity_modal_backdrop == 0.40


def test_toolbar_and_popover_opacity_are_theme_invariant() -> None:
    assert DARK_TOKENS.surfaces.opacity_toolbar == (LIGHT_TOKENS.surfaces.opacity_toolbar)
    assert DARK_TOKENS.surfaces.opacity_popover == (LIGHT_TOKENS.surfaces.opacity_popover)


def test_typography_sizes_match_spec() -> None:
    for tokens in (DARK_TOKENS, LIGHT_TOKENS):
        assert tokens.typography.size_caption == 11
        assert tokens.typography.size_body == 13
        assert tokens.typography.size_label == 14
        assert tokens.typography.size_heading == 18


def test_spacing_scale_matches_spec() -> None:
    for tokens in (DARK_TOKENS, LIGHT_TOKENS):
        assert tokens.spacing.xs == 4
        assert tokens.spacing.sm == 8
        assert tokens.spacing.md == 16
        assert tokens.spacing.lg == 24
        assert tokens.spacing.xl == 32


def test_elevation_specs_are_typed() -> None:
    for tokens in (DARK_TOKENS, LIGHT_TOKENS):
        assert isinstance(tokens.effects.elevation_panel, ElevationSpec)
        assert isinstance(tokens.effects.elevation_dialog, ElevationSpec)
        assert isinstance(tokens.effects.elevation_overlay, ElevationSpec)


# ----- Immutability --------------------------------------------------


def test_theme_tokens_are_frozen() -> None:
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(DARK_TOKENS, "name", ThemeName.LIGHT)  # noqa: B010


def test_color_tokens_are_frozen() -> None:
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(DARK_TOKENS.colors, "text_primary", "#000000")  # noqa: B010
