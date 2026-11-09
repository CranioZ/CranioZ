"""Ensure tokens accessed via ``getattr`` exist in the canonical set.

The compiler and the service use ``getattr(tokens.colors, name)`` and
similar reflective access. This test verifies that every attribute
name referenced in those files exists in the corresponding dataclass.

A typo in a token name would otherwise silently produce ``AttributeError``
at runtime on the first compile, or — worse — silently pass if a
fallback is added later. This test catches the typo at CI time.
"""

from __future__ import annotations

import ast
import dataclasses
from pathlib import Path
from typing import Any

from cranioz.ui.theme.compiler import (  # noqa: PLC2701 - test only
    _SURFACE_BASE_COLOR_TOKEN,
    _SURFACE_OPACITY_TOKEN,
)
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

_CATEGORY_BY_FIELD: dict[str, type] = {
    "colors": ColorTokens,
    "typography": TypographyTokens,
    "spacing": SpacingTokens,
    "dimensions": DimensionTokens,
    "borders": BorderTokens,
    "effects": EffectTokens,
    "surfaces": SurfaceTokens,
}


def _field_names_by_token_path() -> dict[str, set[str]]:
    """Map ``"<category>" -> field name set``."""
    return {category: {f.name for f in _fields(dc)} for category, dc in _CATEGORY_BY_FIELD.items()}


def _fields(dc_type: type) -> tuple[Any, ...]:
    return dataclasses.fields(dc_type)


def _referenced_attributes() -> list[tuple[str, str, int]]:
    """Return ``(category, attribute, lineno)`` for ``<cat>.<attr>`` usage.

    Only literal ``<object>.<attribute>`` accesses are detected. That
    covers the reflection patterns used by the compiler and the service,
    which access tokens via local variables named after the category
    (``tokens.colors``, ``tokens.surfaces``, etc.).
    """
    refs: list[tuple[str, str, int]] = []
    for filename in ("compiler.py", "service.py"):
        path = _THEME_PACKAGE / filename
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Attribute)
                and isinstance(node.value, ast.Attribute)
                and isinstance(node.value.value, ast.Name)
                and node.value.value.id == "tokens"
                and node.value.attr in _CATEGORY_BY_FIELD
            ):
                refs.append((node.value.attr, node.attr, node.lineno))
    return refs


def test_all_referenced_token_attributes_exist() -> None:
    available = _field_names_by_token_path()
    missing: list[str] = []
    for category, attr, lineno in _referenced_attributes():
        if attr not in available[category]:
            missing.append(
                f"compiler/service:{lineno}: tokens.{category}.{attr} "
                f"does not exist in {_CATEGORY_BY_FIELD[category].__name__}"
            )
    assert not missing, (
        "Unknown token attributes referenced by the compiler/service:\n" + "\n".join(missing)
    )


def test_string_token_paths_resolve() -> None:
    """The compiler stores token names as strings; verify each exists."""
    color_fields = {f.name for f in _fields(ColorTokens)}
    for role, token in _SURFACE_BASE_COLOR_TOKEN.items():
        assert token in color_fields, (
            f"_SURFACE_BASE_COLOR_TOKEN[{role!r}] = {token!r} is not a ColorTokens field"
        )

    surface_fields = {f.name for f in _fields(SurfaceTokens)}
    for role, token in _SURFACE_OPACITY_TOKEN.items():
        assert token in surface_fields, (
            f"_SURFACE_OPACITY_TOKEN[{role!r}] = {token!r} is not a SurfaceTokens field"
        )
