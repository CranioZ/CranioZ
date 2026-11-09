"""Ensure DARK and LIGHT contain identical token structures.

Per themes-and-design-tokens.md §3 (Principle 4): every token MUST
exist in every supported theme. Missing tokens are a compilation error.

The check is structural and runs per category:

- both themes use the same dataclass for the category;
- both themes have every field present;
- the registry contains exactly the two concrete theme names.
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
)

_CATEGORY_ATTRIBUTE: dict[type, str] = {
    ColorTokens: "colors",
    TypographyTokens: "typography",
    SpacingTokens: "spacing",
    DimensionTokens: "dimensions",
    BorderTokens: "borders",
    EffectTokens: "effects",
    SurfaceTokens: "surfaces",
}


def _field_names(dc_type: type) -> list[str]:
    return [f.name for f in dataclasses.fields(dc_type)]


@pytest.mark.parametrize(
    "category",
    list(_CATEGORY_ATTRIBUTE),
    ids=lambda c: c.__name__,
)
def test_category_has_identical_structure(category: type) -> None:
    """DARK and LIGHT use the same dataclass and expose the same fields."""
    dark_value = getattr(DARK_TOKENS, _CATEGORY_ATTRIBUTE[category])
    light_value = getattr(LIGHT_TOKENS, _CATEGORY_ATTRIBUTE[category])

    assert type(dark_value) is type(light_value)
    assert type(dark_value) is category

    dark_fields = _field_names(category)
    light_fields = _field_names(category)
    assert dark_fields == light_fields

    for name in dark_fields:
        assert hasattr(dark_value, name), (
            f"{DARK_TOKENS.name.value}.{_CATEGORY_ATTRIBUTE[category]}.{name} is missing"
        )
        assert hasattr(light_value, name), (
            f"{LIGHT_TOKENS.name.value}.{_CATEGORY_ATTRIBUTE[category]}.{name} is missing"
        )


def test_theme_tokens_have_identical_category_set() -> None:
    """Both themes expose the same top-level category attributes."""
    dark_categories = {
        name for name, _ in dataclasses.asdict(DARK_TOKENS).items() if name != "name"
    }
    light_categories = {
        name for name, _ in dataclasses.asdict(LIGHT_TOKENS).items() if name != "name"
    }
    assert dark_categories == light_categories


def test_theme_tokens_have_identical_category_count() -> None:
    """The number of categories per theme is the same (7 in Phase 2)."""
    dark_count = len(dataclasses.fields(DARK_TOKENS)) - 1  # exclude `name`
    light_count = len(dataclasses.fields(LIGHT_TOKENS)) - 1
    assert dark_count == light_count == 7


def test_both_concrete_themes_present_in_registry() -> None:
    assert set(THEME_TOKENS) == {ThemeName.DARK, ThemeName.LIGHT}


def test_registry_maps_each_name_to_matching_tokens() -> None:
    for name, tokens in THEME_TOKENS.items():
        assert tokens.name is name, f"THEME_TOKENS[{name!r}] has name {tokens.name!r}"


def test_no_extra_concrete_theme_names() -> None:
    """Phase 2 only supports DARK and LIGHT; HIGH_CONTRAST is future."""
    assert set(ThemeName) == {ThemeName.DARK, ThemeName.LIGHT}
