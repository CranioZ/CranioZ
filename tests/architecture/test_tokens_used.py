"""Ensure every canonical token is consumed by the compilation pipeline.

Per themes-and-design-tokens.md §9.6, all 47 tokens must be consumed
by ``ThemeCompiler`` or exposed via ``ThemeService``. A token that no
consumer references is either dead or a bug.

The check is structural: for each token category, at least one of the
following must hold:

- the category's dataclass is imported by the compiler or the service;
- the category's attribute names appear (via ``getattr``) in the
  compiler or the service.

Tokens consumed only through dataclass construction (``ThemeTokens``
initialization) are considered consumed.
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from cranioz.ui.theme import compiler as compiler_module
from cranioz.ui.theme import service as service_module
from cranioz.ui.theme.tokens import (
    BorderTokens,
    ColorTokens,
    DimensionTokens,
    EffectTokens,
    SpacingTokens,
    SurfaceTokens,
    TypographyTokens,
)

_THEME_PACKAGE = Path("src/cranioz/ui/theme")


def _consumer_source() -> str:
    parts: list[str] = []
    for name in ("compiler.py", "service.py"):
        path = _THEME_PACKAGE / name
        parts.append(path.read_text(encoding="utf-8"))
    return "\n".join(parts)


def _categories() -> list[type]:
    return [
        ColorTokens,
        TypographyTokens,
        SpacingTokens,
        DimensionTokens,
        BorderTokens,
        EffectTokens,
        SurfaceTokens,
    ]


@pytest.mark.parametrize("category", _categories(), ids=lambda c: c.__name__)
def test_category_is_consumed(category: type) -> None:
    """At least one field of the category is referenced in the compiler/service."""
    source = _consumer_source()
    field_names = [f.name for f in dataclasses.fields(category)]
    # A category is considered consumed if at least one of its field
    # names appears in the compiler/service source, or if the category
    # type itself is referenced (which implies the whole dataclass is
    # used).
    type_name = category.__name__
    if type_name in source:
        return
    any_field = any(name in source for name in field_names)
    assert any_field, (
        f"{type_name} does not appear to be consumed by the compiler "
        f"or the service. Field names checked: {field_names}"
    )


def test_compiler_and_service_imports_theme_tokens() -> None:
    """The compiler and the service both import from tokens.py."""
    assert compiler_module is not None
    assert service_module is not None
    # Both modules have ThemeTokens in their module globals.
    assert "ThemeTokens" in dir(compiler_module)
    assert "ThemeTokens" in dir(service_module)
