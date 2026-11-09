"""Ensure theme values conform to their declared types.

Per themes-and-design-tokens.md §8, every ThemeTokens instance MUST be
validated before being used. This test runs the production validator
and additionally checks some structural invariants that the validator
does not cover (e.g. TypographyTokens sizes are ints, not bools).
"""

from __future__ import annotations

import dataclasses

import pytest

from cranioz.ui.theme.tokens import (
    DARK_TOKENS,
    LIGHT_TOKENS,
    THEME_TOKENS,
    BorderTokens,
    ColorTokens,
    DimensionTokens,
    EffectTokens,
    SpacingTokens,
    SurfaceTokens,
    ThemeName,
    TypographyTokens,
    validate_all_themes,
    validate_tokens,
)


def test_validate_all_themes_passes() -> None:
    validate_all_themes()


@pytest.mark.parametrize("theme", list(THEME_TOKENS), ids=lambda t: t.value)
def test_validate_tokens_passes_per_theme(theme: ThemeName) -> None:
    validate_tokens(THEME_TOKENS[theme])


def test_color_tokens_are_strings() -> None:
    for tokens in (DARK_TOKENS, LIGHT_TOKENS):
        for f in dataclasses.fields(ColorTokens):
            value = getattr(tokens.colors, f.name)
            assert isinstance(value, str), f"{tokens.name.value}.colors.{f.name} is not a str"


def test_typography_sizes_are_ints_not_bools() -> None:
    for tokens in (DARK_TOKENS, LIGHT_TOKENS):
        for f in dataclasses.fields(TypographyTokens):
            value = getattr(tokens.typography, f.name)
            if f.name.startswith("size_") or f.name.startswith("weight_"):
                assert isinstance(value, int) and not isinstance(value, bool)
                assert value > 0


def test_spacing_and_dimension_values_are_non_negative_ints() -> None:
    for tokens in (DARK_TOKENS, LIGHT_TOKENS):
        for f in dataclasses.fields(SpacingTokens):
            value = getattr(tokens.spacing, f.name)
            assert isinstance(value, int) and value >= 0
        for f in dataclasses.fields(DimensionTokens):
            value = getattr(tokens.dimensions, f.name)
            assert isinstance(value, int) and value >= 0


def test_border_values_are_non_negative_ints() -> None:
    for tokens in (DARK_TOKENS, LIGHT_TOKENS):
        for f in dataclasses.fields(BorderTokens):
            value = getattr(tokens.borders, f.name)
            assert isinstance(value, int) and value >= 0


def test_surface_opacities_are_in_range() -> None:
    for tokens in (DARK_TOKENS, LIGHT_TOKENS):
        for f in dataclasses.fields(SurfaceTokens):
            value = getattr(tokens.surfaces, f.name)
            assert isinstance(value, float)
            assert 0.0 <= value <= 1.0


def test_effect_elevations_have_non_negative_geometry() -> None:
    for tokens in (DARK_TOKENS, LIGHT_TOKENS):
        for f in dataclasses.fields(EffectTokens):
            value = getattr(tokens.effects, f.name)
            if not hasattr(value, "blur_radius"):
                continue
            assert value.blur_radius >= 0
            # offset may be negative in principle (elevation upward), but
            # our current tokens use non-negative offsets.
            assert value.offset_x >= 0
            assert value.offset_y >= 0


def test_theme_tokens_are_frozen() -> None:
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(DARK_TOKENS, "name", ThemeName.LIGHT)  # noqa: B010
