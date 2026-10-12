"""Placement enum.

Semantic role of an Area within the Workspace layout.

Placement is construction metadata: it guides the initial layout builder
and groups Areas into Regions. It is not stored on the Area instance.
"""

from __future__ import annotations

from enum import Enum


class Placement(Enum):
    """Semantic placement of an Area in the Workspace."""

    CENTRAL = "central"
    RIGHT = "right"
    LEFT = "left"
    BOTTOM = "bottom"
