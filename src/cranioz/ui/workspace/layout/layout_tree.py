"""LayoutTree.

N-ary tree that organizes Areas within a Workspace.

Node types:
- Leaf: contains exactly one Area.
- Split: contains two or more children (Leaf or Split) and a direction
  (HORIZONTAL or VERTICAL).

The LayoutTree is the single source of truth for structural layout.
It does not carry proportions, visibility, or active-Editor state;
those live in LayoutState.

Rules:
- A Leaf must contain an Area.
- A Split must have a direction and at least two children.
- A LayoutTree must have a root node.
- from_specs() requires at least one CENTRAL AreaSpec.
- from_specs() preserves the order of AreaSpecs in the resulting
  tree, grouped by placement:
    left-most areas → central areas → right-most areas, then bottom.
  The exact grouping algorithm is defined by the builder; the tree
  itself does not interpret placement.
"""

from __future__ import annotations

from dataclasses import dataclass

from cranioz.ui.workspace.areas.area import Area
from cranioz.ui.workspace.areas.placement import Placement
from cranioz.ui.workspace.overlays.region import Bounds, Region
from cranioz.ui.workspace.specs.area_spec import AreaSpec
from cranioz.ui.workspace.specs.editor_layout_spec import SplitDirection


class LayoutTreeError(ValueError):
    """Raised when a LayoutTree violates a structural rule."""


# ----- Nodes -------------------------------------------------------


@dataclass(frozen=True)
class Leaf:
    """A LayoutTree node that contains exactly one Area."""

    area: Area


@dataclass(frozen=True)
class Split:
    """A LayoutTree node that contains two or more children."""

    direction: SplitDirection
    children: tuple[Leaf | Split, ...]

    def __post_init__(self) -> None:
        if len(self.children) < 2:
            raise LayoutTreeError("Split must have at least two children")


LayoutNode = Leaf | Split


# ----- Tree --------------------------------------------------------


class LayoutTree:
    """The N-ary split tree that organizes Areas in a Workspace."""

    def __init__(self, root: LayoutNode) -> None:
        self._root = root

    # ----- Access ---------------------------------------------------

    @property
    def root(self) -> LayoutNode:
        return self._root

    def leaves(self) -> tuple[Leaf, ...]:
        """Return all Leaves in depth-first order."""
        result: list[Leaf] = []
        self._collect_leaves(self._root, result)
        return tuple(result)

    def areas(self) -> tuple[Area, ...]:
        """Return all Areas in depth-first order."""
        return tuple(leaf.area for leaf in self.leaves())

    def find(self, area_id: str) -> Leaf | None:
        """Return the Leaf that contains the given area_id, or None."""
        for leaf in self.leaves():
            if leaf.area.area_id == area_id:
                return leaf
        return None

    def contains(self, area_id: str) -> bool:
        """Return True if the tree contains an Area with the given id."""
        return self.find(area_id) is not None

    def area_count(self) -> int:
        """Return the number of Areas in the tree."""
        return len(self.leaves())

    # ----- Construction from specs ----------------------------------

    @classmethod
    def from_specs(
        cls,
        specs: tuple[AreaSpec, ...],
        areas: dict[str, Area],
    ) -> LayoutTree:
        """Build a LayoutTree from a list of AreaSpecs and a map of Areas.

        The map `areas` provides the concrete Area instances keyed by
        area_id. The caller (LayoutBuilder) is responsible for creating
        them from the specs.

        Rules:
        - At least one spec must have Placement.CENTRAL.
        - Every spec.area_id must exist in the `areas` map.

        Layout grouping:
        - LEFT specs (in order) → CENTRAL specs (in order) → RIGHT specs
          (in order) form a HORIZONTAL row, if any side area exists.
        - If BOTTOM specs exist, the tree becomes a VERTICAL split of
          the row and the bottom row.
        - If there is only one Area total, the tree is a single Leaf.
        """
        if not specs:
            raise LayoutTreeError("LayoutTree.from_specs requires at least one spec")

        for spec in specs:
            if spec.area_id not in areas:
                raise LayoutTreeError(f"AreaSpec references an unknown area_id: {spec.area_id}")

        left = [s for s in specs if s.placement is Placement.LEFT]
        central = [s for s in specs if s.placement is Placement.CENTRAL]
        right = [s for s in specs if s.placement is Placement.RIGHT]
        bottom = [s for s in specs if s.placement is Placement.BOTTOM]

        if not central:
            raise LayoutTreeError("LayoutTree.from_specs requires at least one CENTRAL AreaSpec")

        # Top row: LEFT + CENTRAL + RIGHT, in that order.
        top_row_specs = [*left, *central, *right]

        top_node: LayoutNode
        if len(top_row_specs) == 1:
            top_node = Leaf(area=areas[top_row_specs[0].area_id])
        else:
            top_node = Split(
                direction=SplitDirection.HORIZONTAL,
                children=tuple(Leaf(area=areas[s.area_id]) for s in top_row_specs),
            )

        if not bottom:
            return cls(top_node)

        bottom_row_specs = bottom
        bottom_node: LayoutNode
        if len(bottom_row_specs) == 1:
            bottom_node = Leaf(area=areas[bottom_row_specs[0].area_id])
        else:
            bottom_node = Split(
                direction=SplitDirection.HORIZONTAL,
                children=tuple(Leaf(area=areas[s.area_id]) for s in bottom_row_specs),
            )

        root = Split(
            direction=SplitDirection.VERTICAL,
            children=(top_node, bottom_node),
        )
        return cls(root)

    # ----- Internals ------------------------------------------------

    @staticmethod
    def _collect_leaves(node: LayoutNode, out: list[Leaf]) -> None:
        if isinstance(node, Leaf):
            out.append(node)
            return
        for child in node.children:
            LayoutTree._collect_leaves(child, out)

    # ----- Representation ------------------------------------------

    def __repr__(self) -> str:
        return f"LayoutTree(root={self._root!r})"

    # ----- Regions --------------------------------------------------

    def find_regions(self) -> tuple[Region, ...]:
        """Group the Areas of this tree into Regions by Placement.

        The method is purely structural: it does not compute any
        geometric bounds. Every returned Region has a placeholder
        Bounds (zero rectangle). The real geometry is filled in by
        the rendering layer once the widgets have been materialized.

        Regions are returned in a stable, documented order:

            LEFT, CENTRAL, RIGHT, BOTTOM

        A Placement that has no Area in this tree produces no Region.
        Every Area in the tree belongs to exactly one Region.
        """
        regions: list[Region] = []
        for placement in (
            Placement.LEFT,
            Placement.CENTRAL,
            Placement.RIGHT,
            Placement.BOTTOM,
        ):
            areas = tuple(leaf.area for leaf in self.leaves() if leaf.area.placement is placement)
            if not areas:
                continue
            regions.append(
                Region(
                    region_id=placement.value,
                    bounds=Bounds(),
                    areas=areas,
                    semantic_role=placement,
                )
            )
        return tuple(regions)
