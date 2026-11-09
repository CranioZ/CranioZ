"""IconState enum.

Defines the visual states for which an icon can be resolved.
"""

from __future__ import annotations

from enum import StrEnum


class IconState(StrEnum):
    """Visual state of an icon."""

    DEFAULT = "default"
    HOVER = "hover"
    PRESSED = "pressed"
    SELECTED = "selected"
    DISABLED = "disabled"
