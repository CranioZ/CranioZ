"""ModuleUISpec.

Declarative UI composition produced by a Module and materialized by the
Workspace. The Workspace does not know the Module that produced it.

Rules:
- At least one Area must have Placement. CENTRAL.
- Area ids must be unique within the spec.
- Overlays are declared separately.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from cranioz.ui.workspace.areas.placement import Placement
from cranioz.ui.workspace.specs.area_spec import AreaSpec
from cranioz.ui.workspace.specs.overlay_spec import OverlaySpec


class ModuleUISpecError(ValueError):
    """Raised when a ModuleUISpec violates structural rules."""


@dataclass(frozen=True)
class ModuleUISpec:
    """Declarative UI composition produced by a Module."""

    areas: tuple[AreaSpec, ...]
    overlays: tuple[OverlaySpec, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.areas:
            raise ModuleUISpecError("ModuleUISpec must declare at least one Area")

        ids = [area.area_id for area in self.areas]
        if len(ids) != len(set(ids)):
            raise ModuleUISpecError("Area ids must be unique within a ModuleUISpec")

        if not any(area.placement is Placement.CENTRAL for area in self.areas):
            raise ModuleUISpecError(
                "ModuleUISpec must declare at least one CENTRAL Area"
            )