"""WorkspaceLayoutState — runtime visibility of the Workspace Areas.

The minimum viable state needed by the Top Bar toggles (Area Left,
Area Right, Area Bottom). It is intentionally small:

- It does NOT persist.
- It is NOT serialized.
- It does NOT implement ADR-0010 (Phase 5).

It exists so that the Top Bar toggles have a single source of truth
for "is this Area currently visible?" and so that a future Phase 5
implementation of ADR-0010 can build on it without a redesign.
"""

from __future__ import annotations

from dataclasses import dataclass

from cranioz.ui.workspace.areas.placement import Placement


@dataclass
class WorkspaceLayoutState:
    """Runtime visibility of the three toggleable Areas.

    The CENTRAL Area is always visible and is not represented here:
    hiding the Central Area would leave the Workspace with no editor
    surface. The three toggles target LEFT, RIGHT and BOTTOM.
    """

    left_visible: bool = True
    right_visible: bool = True
    bottom_visible: bool = True

    def is_visible(self, placement: Placement) -> bool:
        """Return the visibility for a toggleable Placement.

        Raises KeyError for Placement.CENTRAL: the Central Area is
        not toggleable.
        """
        if placement is Placement.LEFT:
            return self.left_visible
        if placement is Placement.RIGHT:
            return self.right_visible
        if placement is Placement.BOTTOM:
            return self.bottom_visible
        raise KeyError(f"placement is not toggleable: {placement!r}")

    def set_visible(self, placement: Placement, visible: bool) -> None:
        """Set the visibility for a toggleable Placement.

        Raises KeyError for Placement.CENTRAL, for the same reason
        as ``is_visible``.
        """
        if placement is Placement.LEFT:
            self.left_visible = visible
        elif placement is Placement.RIGHT:
            self.right_visible = visible
        elif placement is Placement.BOTTOM:
            self.bottom_visible = visible
        else:
            raise KeyError(f"placement is not toggleable: {placement!r}")
