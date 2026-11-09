"""WCAG 2.2 AA contrast tests for the canonical foreground/background pairs.

Per themes-and-design-tokens.md §12.1, the following pairs must meet
4.5:1 for normal text. Each pair is tested for both DARK and LIGHT.

The pairs, in spec order:

    color.text.primary        on color.background.application   >= 4.5
    color.text.primary        on color.background.panel         >= 4.5
    color.text.primary        on color.background.elevated      >= 4.5
    color.text.secondary      on color.background.panel         >= 4.5
    color.text.inverse        on color.interactive.default      >= 4.5
    color.feedback.error      on color.background.panel         >= 4.5
    color.feedback.success    on color.background.panel         >= 4.5
    color.feedback.warning    on color.background.panel         >= 4.5
    color.feedback.information on color.background.panel        >= 4.5

The implementation follows WCAG's relative luminance formula.
"""

from __future__ import annotations

import pytest

from cranioz.ui.theme.tokens import (
    DARK_TOKENS,
    LIGHT_TOKENS,
    ThemeName,
    ThemeTokens,
)

# ----- WCAG helpers ---------------------------------------------------


def _parse_hex(color: str) -> tuple[int, int, int]:
    if len(color) != 7 or not color.startswith("#"):
        raise ValueError(f"not a #rrggbb color: {color!r}")
    return (
        int(color[1:3], 16),
        int(color[3:5], 16),
        int(color[5:7], 16),
    )


def _channel_luminance(value: int) -> float:
    s = value / 255.0
    if s <= 0.03928:
        return s / 12.92
    return float(((s + 0.055) / 1.055) ** 2.4)


def _relative_luminance(color: str) -> float:
    r, g, b = _parse_hex(color)
    return float(
        0.2126 * _channel_luminance(r)
        + 0.7152 * _channel_luminance(g)
        + 0.0722 * _channel_luminance(b)
    )


def _contrast_ratio(fg: str, bg: str) -> float:
    l1 = _relative_luminance(fg)
    l2 = _relative_luminance(bg)
    lighter, darker = (l1, l2) if l1 >= l2 else (l2, l1)
    return (lighter + 0.05) / (darker + 0.05)


# ----- Pairs ---------------------------------------------------------


_TEXT_PAIRS: list[tuple[str, str, str]] = [
    ("text_primary", "background_application", "text.primary on background.application"),
    ("text_primary", "background_panel", "text.primary on background.panel"),
    ("text_primary", "background_elevated", "text.primary on background.elevated"),
    ("text_secondary", "background_panel", "text.secondary on background.panel"),
    ("text_inverse", "interactive_default", "text.inverse on interactive.default"),
    ("feedback_error", "background_panel", "feedback.error on background.panel"),
    ("feedback_success", "background_panel", "feedback.success on background.panel"),
    ("feedback_warning", "background_panel", "feedback.warning on background.panel"),
    ("feedback_information", "background_panel", "feedback.information on background.panel"),
]


# ----- Helpers for parametrization ----------------------------------


def _themes() -> list[tuple[ThemeName, ThemeTokens]]:
    return [
        (ThemeName.DARK, DARK_TOKENS),
        (ThemeName.LIGHT, LIGHT_TOKENS),
    ]


# ----- Tests ---------------------------------------------------------


@pytest.mark.parametrize(
    ("theme_name", "tokens"),
    _themes(),
    ids=lambda v: v.value if hasattr(v, "value") else str(v),
)
@pytest.mark.parametrize(
    ("fg_field", "bg_field", "label"),
    _TEXT_PAIRS,
    ids=[label for _, _, label in _TEXT_PAIRS],
)
def test_text_contrast_aa(
    theme_name: ThemeName,
    tokens: ThemeTokens,
    fg_field: str,
    bg_field: str,
    label: str,
) -> None:
    fg = getattr(tokens.colors, fg_field)
    bg = getattr(tokens.colors, bg_field)
    ratio = _contrast_ratio(fg, bg)
    assert ratio >= 4.5, (
        f"{theme_name.value}: {label} = {ratio:.2f}:1 (fg={fg}, bg={bg}) must be >= 4.5:1"
    )


def test_sanity_black_on_white_is_21_to_1() -> None:
    """Sanity check: the WCAG formula returns 21 for black on white."""
    assert _contrast_ratio("#000000", "#FFFFFF") == pytest.approx(21.0, abs=0.01)


def test_sanity_white_on_white_is_1_to_1() -> None:
    assert _contrast_ratio("#FFFFFF", "#FFFFFF") == pytest.approx(1.0, abs=0.01)
