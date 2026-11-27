"""IconState enum.

Defines the visual states for which an icon can be resolved.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Final


class IconState(StrEnum):
    """Visual state of an icon."""

    DEFAULT = "default"
    HOVER = "hover"
    PRESSED = "pressed"
    SELECTED = "selected"
    DISABLED = "disabled"


_STATE_COLOR_TOKENS: Final[dict[IconState, str]] = {
    IconState.DEFAULT: "text_primary",
    IconState.HOVER: "interactive_hover",
    IconState.PRESSED: "interactive_pressed",
    IconState.SELECTED: "interactive_default",
    IconState.DISABLED: "text_disabled",
}


def color_token_for_state(state: IconState) -> str:
    """Return the canonical color-token name for an icon state."""
    return _STATE_COLOR_TOKENS[state]
