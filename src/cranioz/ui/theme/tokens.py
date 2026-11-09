"""Semantic design tokens for the CranioZ Appearance System.

This module is the single source of truth for token *values*. Widgets
MUST consume tokens via ``ThemeService`` and ``ThemeCompiler``; they
MUST NOT import ``DARK_TOKENS`` / ``LIGHT_TOKENS`` directly.

Specification: docs/architecture/appearance/themes-and-design-tokens.md

Rules enforced by ``validate_tokens``:

- Every token present in every theme (completeness).
- Colors in ``#rrggbb`` or ``rgba(...)`` form.
- Opacity in [0.0, 1.0].
- Dimensions, spacings, radii, border widths >= 0.
- Elevation specifications well-formed.

The token set is closed for Phase 2 (47 tokens, 7 categories).
Adding a token requires a PR that updates the specification and the
token count in §5 of the specification document.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, fields
from enum import StrEnum
from typing import Final

# ---------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------


class ThemeMode(StrEnum):
    """User-selectable theme configuration mode.

    ``SYSTEM`` is a configuration mode, not a concrete theme. It is
    resolved by ``ThemeService`` into a ``ThemeName``.
    """

    DARK = "dark"
    LIGHT = "light"
    SYSTEM = "system"


class ThemeName(StrEnum):
    """Concrete theme identifier.

    ``SYSTEM`` MUST never appear here. ``HIGH_CONTRAST`` is reserved for
    a future phase.
    """

    DARK = "dark"
    LIGHT = "light"


# ---------------------------------------------------------------------
# Token dataclasses (7 categories)
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class ColorTokens:
    background_application: str
    background_panel: str
    background_elevated: str
    background_input: str

    text_primary: str
    text_secondary: str
    text_disabled: str
    text_inverse: str

    border_default: str
    border_subtle: str
    border_focus: str

    interactive_default: str
    interactive_hover: str
    interactive_pressed: str
    interactive_selected: str

    feedback_information: str
    feedback_success: str
    feedback_warning: str
    feedback_error: str


@dataclass(frozen=True)
class TypographyTokens:
    family_interface: str
    size_caption: int
    size_body: int
    size_label: int
    size_heading: int
    weight_regular: int
    weight_medium: int
    weight_semibold: int


@dataclass(frozen=True)
class SpacingTokens:
    xs: int
    sm: int
    md: int
    lg: int
    xl: int


@dataclass(frozen=True)
class DimensionTokens:
    control_height: int
    icon_size: int


@dataclass(frozen=True)
class BorderTokens:
    width_default: int
    width_focus: int
    radius_control: int
    radius_panel: int
    radius_dialog: int


@dataclass(frozen=True)
class ElevationSpec:
    offset_x: int
    offset_y: int
    blur_radius: int
    color: str


@dataclass(frozen=True)
class EffectTokens:
    hover_overlay: str
    selection_highlight: str
    elevation_panel: ElevationSpec
    elevation_dialog: ElevationSpec
    elevation_overlay: ElevationSpec


@dataclass(frozen=True)
class SurfaceTokens:
    opacity_toolbar: float
    opacity_popover: float
    opacity_modal_backdrop: float


@dataclass(frozen=True)
class ThemeTokens:
    name: ThemeName
    colors: ColorTokens
    typography: TypographyTokens
    spacing: SpacingTokens
    dimensions: DimensionTokens
    borders: BorderTokens
    effects: EffectTokens
    surfaces: SurfaceTokens


# ---------------------------------------------------------------------
# Canonical values (47 tokens per theme)
# ---------------------------------------------------------------------


DARK_TOKENS: Final[ThemeTokens] = ThemeTokens(
    name=ThemeName.DARK,
    colors=ColorTokens(
        background_application="#1E1E1E",
        background_panel="#252526",
        background_elevated="#2D2D30",
        background_input="#1A1A1A",
        text_primary="#E8E8E8",
        text_secondary="#A8A8A8",
        text_disabled="#5A5A5A",
        text_inverse="#FFFFFF",
        border_default="#3A3A3C",
        border_subtle="#2E2E30",
        border_focus="#4A90D9",
        interactive_default="#1F5FCC",
        interactive_hover="#4A8AFF",
        interactive_pressed="#1F4FB8",
        interactive_selected="#2C5FCC",
        feedback_information="#4A90D9",
        feedback_success="#4CAF50",
        feedback_warning="#FFA726",
        feedback_error="#FF6B6B",
    ),
    typography=TypographyTokens(
        family_interface='"Segoe UI", "Inter", sans-serif',
        size_caption=11,
        size_body=13,
        size_label=14,
        size_heading=18,
        weight_regular=400,
        weight_medium=500,
        weight_semibold=600,
    ),
    spacing=SpacingTokens(xs=4, sm=8, md=16, lg=24, xl=32),
    dimensions=DimensionTokens(control_height=28, icon_size=20),
    borders=BorderTokens(
        width_default=1,
        width_focus=2,
        radius_control=4,
        radius_panel=6,
        radius_dialog=8,
    ),
    effects=EffectTokens(
        hover_overlay="rgba(255,255,255,0.04)",
        selection_highlight="rgba(58,122,254,0.24)",
        elevation_panel=ElevationSpec(
            offset_x=0, offset_y=1, blur_radius=3, color="rgba(0,0,0,0.40)"
        ),
        elevation_dialog=ElevationSpec(
            offset_x=0, offset_y=4, blur_radius=12, color="rgba(0,0,0,0.50)"
        ),
        elevation_overlay=ElevationSpec(
            offset_x=0, offset_y=8, blur_radius=24, color="rgba(0,0,0,0.60)"
        ),
    ),
    surfaces=SurfaceTokens(
        opacity_toolbar=0.92,
        opacity_popover=0.96,
        opacity_modal_backdrop=0.60,
    ),
)


LIGHT_TOKENS: Final[ThemeTokens] = ThemeTokens(
    name=ThemeName.LIGHT,
    colors=ColorTokens(
        background_application="#F4F4F4",
        background_panel="#FFFFFF",
        background_elevated="#FAFAFA",
        background_input="#FFFFFF",
        text_primary="#1A1A1A",
        text_secondary="#555555",
        text_disabled="#AAAAAA",
        text_inverse="#FFFFFF",
        border_default="#D0D0D0",
        border_subtle="#E8E8E8",
        border_focus="#2563EB",
        interactive_default="#2563EB",
        interactive_hover="#3B82F6",
        interactive_pressed="#1E40AF",
        interactive_selected="#1D4ED8",
        feedback_information="#2563EB",
        feedback_success="#2E7D32",
        feedback_warning="#9A4D00",
        feedback_error="#B42318",
    ),
    typography=TypographyTokens(
        family_interface='"Segoe UI", "Inter", sans-serif',
        size_caption=11,
        size_body=13,
        size_label=14,
        size_heading=18,
        weight_regular=400,
        weight_medium=500,
        weight_semibold=600,
    ),
    spacing=SpacingTokens(xs=4, sm=8, md=16, lg=24, xl=32),
    dimensions=DimensionTokens(control_height=28, icon_size=20),
    borders=BorderTokens(
        width_default=1,
        width_focus=2,
        radius_control=4,
        radius_panel=6,
        radius_dialog=8,
    ),
    effects=EffectTokens(
        hover_overlay="rgba(0,0,0,0.04)",
        selection_highlight="rgba(37,99,235,0.20)",
        elevation_panel=ElevationSpec(
            offset_x=0, offset_y=1, blur_radius=3, color="rgba(0,0,0,0.10)"
        ),
        elevation_dialog=ElevationSpec(
            offset_x=0, offset_y=4, blur_radius=12, color="rgba(0,0,0,0.15)"
        ),
        elevation_overlay=ElevationSpec(
            offset_x=0, offset_y=8, blur_radius=24, color="rgba(0,0,0,0.20)"
        ),
    ),
    surfaces=SurfaceTokens(
        opacity_toolbar=0.92,
        opacity_popover=0.96,
        opacity_modal_backdrop=0.40,
    ),
)


THEME_TOKENS: Final[dict[ThemeName, ThemeTokens]] = {
    ThemeName.DARK: DARK_TOKENS,
    ThemeName.LIGHT: LIGHT_TOKENS,
}


# ---------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------


_COLOR_HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")
_COLOR_RGBA_RE = re.compile(
    r"^rgba\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*"
    r"(0|1|0?\.\d+)\s*\)$"
)


def _is_valid_color(value: str) -> bool:
    """Return True if ``value`` is a valid ``#rrggbb`` or ``rgba(...)`` color."""
    if _COLOR_HEX_RE.match(value):
        return True
    match = _COLOR_RGBA_RE.match(value)
    if not match:
        return False
    r, g, b, a = match.groups()
    if not all(0 <= int(c) <= 255 for c in (r, g, b)):
        return False
    try:
        return 0.0 <= float(a) <= 1.0
    except ValueError:
        return False


def _validate_colors(tokens: ThemeTokens) -> None:
    for f in fields(ColorTokens):
        value = getattr(tokens.colors, f.name)
        if not _is_valid_color(value):
            raise ValueError(f"color.{f.name}: invalid color {value!r} (theme {tokens.name.value})")


def _validate_effects(tokens: ThemeTokens) -> None:
    for f in fields(EffectTokens):
        value = getattr(tokens.effects, f.name)
        if isinstance(value, ElevationSpec):
            if not _is_valid_color(value.color):
                raise ValueError(
                    f"effect.{f.name}.color: invalid color {value.color!r} "
                    f"(theme {tokens.name.value})"
                )
            if value.blur_radius < 0:
                raise ValueError(
                    f"effect.{f.name}.blur_radius must be >= 0 (theme {tokens.name.value})"
                )
        elif not _is_valid_color(value):
            raise ValueError(
                f"effect.{f.name}: invalid color {value!r} (theme {tokens.name.value})"
            )


def _validate_surfaces(tokens: ThemeTokens) -> None:
    for f in fields(SurfaceTokens):
        value = getattr(tokens.surfaces, f.name)
        if not (0.0 <= value <= 1.0):
            raise ValueError(
                f"surface.{f.name}: opacity {value!r} out of [0.0, 1.0] (theme {tokens.name.value})"
            )


def _validate_spacing(tokens: ThemeTokens) -> None:
    for f in fields(SpacingTokens):
        if getattr(tokens.spacing, f.name) < 0:
            raise ValueError(f"spacing.{f.name} must be >= 0 (theme {tokens.name.value})")


def _validate_dimensions(tokens: ThemeTokens) -> None:
    for f in fields(DimensionTokens):
        if getattr(tokens.dimensions, f.name) < 0:
            raise ValueError(f"dimension.{f.name} must be >= 0 (theme {tokens.name.value})")


def _validate_borders(tokens: ThemeTokens) -> None:
    for f in fields(BorderTokens):
        if getattr(tokens.borders, f.name) < 0:
            raise ValueError(f"border.{f.name} must be >= 0 (theme {tokens.name.value})")


def validate_tokens(tokens: ThemeTokens) -> None:
    """Validate a single ThemeTokens instance.

    Raises ``ValueError`` with the offending token path on failure.
    """
    _validate_colors(tokens)
    _validate_effects(tokens)
    _validate_surfaces(tokens)
    _validate_spacing(tokens)
    _validate_dimensions(tokens)
    _validate_borders(tokens)


def validate_all_themes() -> None:
    """Validate every theme and cross-theme structural consistency."""
    for name, tokens in THEME_TOKENS.items():
        if tokens.name != name:
            raise ValueError(f"THEME_TOKENS[{name!r}] has name {tokens.name!r}")
        validate_tokens(tokens)


def count_tokens() -> int:
    """Return the total number of tokens across the 7 categories.

    Phase 2 target: 47. Used by the completeness test.
    """
    return (
        len(fields(ColorTokens))
        + len(fields(TypographyTokens))
        + len(fields(SpacingTokens))
        + len(fields(DimensionTokens))
        + len(fields(BorderTokens))
        + len(fields(EffectTokens))
        + len(fields(SurfaceTokens))
    )
