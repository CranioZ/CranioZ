"""OverlaySpec.

Declarative description of an Overlay declared by a Module.

Overlays are floating layers managed by the Workspace. They are not
Areas. An OverlaySpec is data; the Workspace materializes it.
"""

from __future__ import annotations

from dataclasses import dataclass

from cranioz.ui.workspace.areas.placement import Placement


class OverlaySpecError(ValueError):
    """Raised when an OverlaySpec violates structural rules."""


@dataclass(frozen=True)
class OverlaySpec:
    """Declarative description of an Overlay."""

    overlay_id: str
    title: str
    target_region: Placement

    def __post_init__(self) -> None:
        if not self.overlay_id:
            raise OverlaySpecError("overlay_id must not be empty")
        if not self.title:
            raise OverlaySpecError("title must not be empty")
