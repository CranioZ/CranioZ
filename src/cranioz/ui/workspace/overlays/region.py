"""Region.

A Region is a geometric grouping of Areas within a Workspace.

The concept exists to give Overlays a target: an Overlay is positioned
over a Region, not over an individual Area. This decouples the Overlay
from the current number and arrangement of Areas.

Two concepts are defined here:

- ``Bounds``: a plain geometric rectangle. It is deliberately NOT
  ``PySide6.QtCore.QRect``. The layout tree and the Region are pure
  domain structures; they do not depend on Qt. The LayoutRenderer is
  responsible for converting ``Bounds`` to a Qt geometry when it
  materializes widgets.

- ``Region``: a named group of Areas that share a semantic role
  (LEFT, CENTRAL, RIGHT, BOTTOM).

A Region is *derived* from the LayoutTree, not stored on it. The
LayoutTree owns the Areas; the Region is a projection of them.

Bounds lifecycle:

- ``LayoutTree.find_regions()`` produces Regions with a *placeholder*
  Bounds (zero rectangle). The association between Areas and Regions
  is structural and can be computed without Qt.

- The real Bounds can only be computed after the LayoutRenderer has
  materialized the Area widgets and Qt has assigned them their actual
  geometry. A future piece (OverlayManager or Workspace) will fill
  the Bounds in.

This separation keeps the pure model (LayoutTree, Region) testable
without a QApplication, and confines geometry to the rendering layer.
"""

from __future__ import annotations

from dataclasses import dataclass

from cranioz.ui.workspace.areas.area import Area
from cranioz.ui.workspace.areas.placement import Placement

# ----- Bounds -------------------------------------------------------


@dataclass(frozen=True)
class Bounds:
    """A geometric rectangle in screen coordinates.

    The unit is left unspecified here because Bounds is a pure
    geometry value. In practice it is pixels, as provided by Qt.
    A future piece may introduce a coordinate-system tag if needed.

    A Bounds with all fields at zero is a valid placeholder: it
    means "the real geometry has not been computed yet".
    """

    x: float = 0.0
    y: float = 0.0
    width: float = 0.0
    height: float = 0.0

    def is_placeholder(self) -> bool:
        """Return True if the Bounds has not been populated yet.

        Used by tests and by the OverlayManager to distinguish a
        Region whose geometry is known from one whose geometry has
        not yet been computed.
        """
        return self == _PLACEHOLDER_BOUNDS

    def __post_init__(self) -> None:
        if self.width < 0:
            raise ValueError(f"Bounds.width must be non-negative, got {self.width}")
        if self.height < 0:
            raise ValueError(f"Bounds.height must be non-negative, got {self.height}")


_PLACEHOLDER_BOUNDS = Bounds()


# ----- Region -------------------------------------------------------


@dataclass(frozen=True)
class Region:
    """A named group of Areas that share a semantic role.

    A Region is a *projection* of a subset of a LayoutTree. It is
    produced by ``LayoutTree.find_regions()`` and is intentionally
    immutable: any change to the layout produces a new set of Regions.

    Fields:

    - ``region_id``: stable identifier. It equals the Placement value
      ("left", "central", "right", "bottom"). Using the Placement
      value as the id ensures the Region identity is consistent with
      the semantic role the tree already uses.

    - ``bounds``: geometric rectangle that contains every Area in the
      Region. It is a placeholder until the LayoutRenderer (or the
      Workspace) computes the real geometry.

    - ``areas``: the Areas that belong to the Region, in the order
      they appear in the LayoutTree. The order is deterministic and
      matches the depth-first order of the tree.

    - ``semantic_role``: the Placement this Region was derived from.
      It is guaranteed to be non-None because a Region only exists
      for a Placement that has at least one Area. It is exposed as
      Optional for future flexibility (a Region could theoretically
      be derived from a non-Placement rule), but today it is always
      set.
    """

    region_id: str
    bounds: Bounds
    areas: tuple[Area, ...]
    semantic_role: Placement | None

    def __post_init__(self) -> None:
        if not self.region_id:
            raise ValueError("region_id must not be empty")
        if not self.areas:
            raise ValueError(f"Region {self.region_id!r} must contain at least one Area")

    def area_count(self) -> int:
        """Return the number of Areas in this Region."""
        return len(self.areas)

    def contains(self, area_id: str) -> bool:
        """Return True if the given area_id belongs to this Region."""
        return any(area.area_id == area_id for area in self.areas)

    def with_bounds(self, bounds: Bounds) -> Region:
        """Return a new Region with the given Bounds.

        Used by the LayoutRenderer / Workspace to produce a Region
        whose geometry is known, without mutating the original.
        """
        return Region(
            region_id=self.region_id,
            bounds=bounds,
            areas=self.areas,
            semantic_role=self.semantic_role,
        )

    def __repr__(self) -> str:
        return (
            f"Region(region_id={self.region_id!r}, "
            f"areas={[a.area_id for a in self.areas]!r}, "
            f"bounds={'placeholder' if self.bounds.is_placeholder() else self.bounds!r}, "
            f"semantic_role={self.semantic_role.value if self.semantic_role else None!r})"
        )
