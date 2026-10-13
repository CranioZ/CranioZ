"""Tests for LayoutTree."""

# mypy: ignore-errors
# This file exercises the structural layout tree with concrete Areas.

from __future__ import annotations

import pytest

from cranioz.ui.workspace.areas.area import Area
from cranioz.ui.workspace.areas.placement import Placement
from cranioz.ui.workspace.layout.layout_tree import (
    LayoutTree,
    LayoutTreeError,
    Leaf,
    Split,
)
from cranioz.ui.workspace.specs.area_spec import AreaSpec
from cranioz.ui.workspace.specs.editor_layout_spec import (
    EditorLayoutSpec,
    SplitDirection,
)

# ----- Helpers -----------------------------------------------------


def _area(
    area_id: str,
    placement: Placement = Placement.CENTRAL,
) -> Area:
    return Area(area_id=area_id, title=area_id, placement=placement)


def _spec(area_id: str, placement: Placement, editor_id: str) -> AreaSpec:
    return AreaSpec(
        area_id=area_id,
        title=area_id,
        placement=placement,
        editor_layout=EditorLayoutSpec.leaf(editor_id),
    )


def _areas_from_specs(specs: tuple[AreaSpec, ...]) -> dict[str, Area]:
    return {s.area_id: _area(s.area_id, s.placement) for s in specs}


# ----- Nodes -------------------------------------------------------


def test_leaf_holds_area() -> None:
    a = _area("area.central")
    leaf = Leaf(area=a)
    assert leaf.area is a


def test_split_requires_two_children() -> None:
    with pytest.raises(LayoutTreeError, match="at least two children"):
        Split(
            direction=SplitDirection.HORIZONTAL,
            children=(Leaf(area=_area("area.a")),),
        )


# ----- from_specs — single central --------------------------------


def test_from_specs_single_central_is_leaf() -> None:
    spec = _spec("area.central", Placement.CENTRAL, "editor.a")
    areas = _areas_from_specs((spec,))
    tree = LayoutTree.from_specs((spec,), areas)
    assert isinstance(tree.root, Leaf)
    assert tree.root.area.area_id == "area.central"


# ----- from_specs — left + central + right ------------------------


def test_from_specs_left_central_right_is_horizontal_split() -> None:
    specs = (
        _spec("area.left", Placement.LEFT, "editor.left"),
        _spec("area.central", Placement.CENTRAL, "editor.central"),
        _spec("area.right", Placement.RIGHT, "editor.right"),
    )
    areas = _areas_from_specs(specs)
    tree = LayoutTree.from_specs(specs, areas)

    assert isinstance(tree.root, Split)
    assert tree.root.direction is SplitDirection.HORIZONTAL
    assert len(tree.root.children) == 3
    assert [leaf.area.area_id for leaf in tree.leaves()] == [
        "area.left",
        "area.central",
        "area.right",
    ]


def test_from_specs_central_only_with_two_is_horizontal() -> None:
    specs = (
        _spec("area.central.a", Placement.CENTRAL, "editor.a"),
        _spec("area.central.b", Placement.CENTRAL, "editor.b"),
    )
    areas = _areas_from_specs(specs)
    tree = LayoutTree.from_specs(specs, areas)

    assert isinstance(tree.root, Split)
    assert tree.root.direction is SplitDirection.HORIZONTAL


# ----- from_specs — with bottom ------------------------------------


def test_from_specs_with_bottom_is_vertical_split() -> None:
    specs = (
        _spec("area.central", Placement.CENTRAL, "editor.central"),
        _spec("area.bottom", Placement.BOTTOM, "editor.bottom"),
    )
    areas = _areas_from_specs(specs)
    tree = LayoutTree.from_specs(specs, areas)

    assert isinstance(tree.root, Split)
    assert tree.root.direction is SplitDirection.VERTICAL
    assert len(tree.root.children) == 2


def test_from_specs_four_areas_has_nested_split() -> None:
    specs = (
        _spec("area.left", Placement.LEFT, "editor.left"),
        _spec("area.central", Placement.CENTRAL, "editor.central"),
        _spec("area.right", Placement.RIGHT, "editor.right"),
        _spec("area.bottom", Placement.BOTTOM, "editor.bottom"),
    )
    areas = _areas_from_specs(specs)
    tree = LayoutTree.from_specs(specs, areas)

    assert isinstance(tree.root, Split)
    assert tree.root.direction is SplitDirection.VERTICAL
    top, bottom = tree.root.children
    assert isinstance(top, Split)
    assert top.direction is SplitDirection.HORIZONTAL
    assert isinstance(bottom, Leaf)


# ----- from_specs — errors ----------------------------------------


def test_from_specs_without_central_raises() -> None:
    specs = (
        _spec("area.left", Placement.LEFT, "editor.left"),
        _spec("area.right", Placement.RIGHT, "editor.right"),
    )
    areas = _areas_from_specs(specs)
    with pytest.raises(LayoutTreeError, match="CENTRAL"):
        LayoutTree.from_specs(specs, areas)


def test_from_specs_empty_raises() -> None:
    with pytest.raises(LayoutTreeError, match="at least one spec"):
        LayoutTree.from_specs((), {})


def test_from_specs_missing_area_raises() -> None:
    specs = (_spec("area.central", Placement.CENTRAL, "editor.central"),)
    with pytest.raises(LayoutTreeError, match="unknown area_id"):
        LayoutTree.from_specs(specs, {})


# ----- Traversal ---------------------------------------------------


def test_areas_returns_in_depth_first_order() -> None:
    specs = (
        _spec("area.left", Placement.LEFT, "editor.left"),
        _spec("area.central", Placement.CENTRAL, "editor.central"),
        _spec("area.right", Placement.RIGHT, "editor.right"),
    )
    areas = _areas_from_specs(specs)
    tree = LayoutTree.from_specs(specs, areas)

    assert [a.area_id for a in tree.areas()] == [
        "area.left",
        "area.central",
        "area.right",
    ]


def test_find_returns_leaf() -> None:
    specs = (
        _spec("area.left", Placement.LEFT, "editor.left"),
        _spec("area.central", Placement.CENTRAL, "editor.central"),
    )
    areas = _areas_from_specs(specs)
    tree = LayoutTree.from_specs(specs, areas)

    leaf = tree.find("area.central")
    assert leaf is not None
    assert leaf.area.area_id == "area.central"


def test_find_unknown_returns_none() -> None:
    specs = (_spec("area.central", Placement.CENTRAL, "editor.central"),)
    areas = _areas_from_specs(specs)
    tree = LayoutTree.from_specs(specs, areas)

    assert tree.find("area.unknown") is None


def test_contains() -> None:
    specs = (_spec("area.central", Placement.CENTRAL, "editor.central"),)
    areas = _areas_from_specs(specs)
    tree = LayoutTree.from_specs(specs, areas)

    assert tree.contains("area.central")
    assert not tree.contains("area.other")


def test_area_count() -> None:
    specs = (
        _spec("area.left", Placement.LEFT, "editor.left"),
        _spec("area.central", Placement.CENTRAL, "editor.central"),
        _spec("area.right", Placement.RIGHT, "editor.right"),
    )
    areas = _areas_from_specs(specs)
    tree = LayoutTree.from_specs(specs, areas)

    assert tree.area_count() == 3


# ----- Placement propagation ---------------------------------------


def test_leaves_carry_areas_with_correct_placement() -> None:
    specs = (
        _spec("area.left", Placement.LEFT, "editor.left"),
        _spec("area.central", Placement.CENTRAL, "editor.central"),
        _spec("area.right", Placement.RIGHT, "editor.right"),
        _spec("area.bottom", Placement.BOTTOM, "editor.bottom"),
    )
    areas = _areas_from_specs(specs)
    tree = LayoutTree.from_specs(specs, areas)

    by_id = {leaf.area.area_id: leaf.area.placement for leaf in tree.leaves()}
    assert by_id["area.left"] is Placement.LEFT
    assert by_id["area.central"] is Placement.CENTRAL
    assert by_id["area.right"] is Placement.RIGHT
    assert by_id["area.bottom"] is Placement.BOTTOM


# ----- find_regions -------------------------------------------------


def test_find_regions_single_central() -> None:
    specs = (_spec("area.central", Placement.CENTRAL, "editor.central"),)
    areas = _areas_from_specs(specs)
    tree = LayoutTree.from_specs(specs, areas)

    regions = tree.find_regions()

    assert len(regions) == 1
    assert regions[0].region_id == "central"
    assert regions[0].semantic_role is Placement.CENTRAL
    assert [a.area_id for a in regions[0].areas] == ["area.central"]


def test_find_regions_left_central_right() -> None:
    specs = (
        _spec("area.left", Placement.LEFT, "editor.left"),
        _spec("area.central", Placement.CENTRAL, "editor.central"),
        _spec("area.right", Placement.RIGHT, "editor.right"),
    )
    areas = _areas_from_specs(specs)
    tree = LayoutTree.from_specs(specs, areas)

    regions = tree.find_regions()

    assert [r.region_id for r in regions] == ["left", "central", "right"]
    assert [r.semantic_role for r in regions] == [
        Placement.LEFT,
        Placement.CENTRAL,
        Placement.RIGHT,
    ]


def test_find_regions_returns_in_stable_order() -> None:
    """The order is LEFT, CENTRAL, RIGHT, BOTTOM regardless of spec order."""
    specs = (
        _spec("area.bottom", Placement.BOTTOM, "editor.bottom"),
        _spec("area.right", Placement.RIGHT, "editor.right"),
        _spec("area.central", Placement.CENTRAL, "editor.central"),
        _spec("area.left", Placement.LEFT, "editor.left"),
    )
    areas = _areas_from_specs(specs)
    tree = LayoutTree.from_specs(specs, areas)

    regions = tree.find_regions()

    assert [r.region_id for r in regions] == [
        "left",
        "central",
        "right",
        "bottom",
    ]


def test_find_regions_groups_multiple_central_areas() -> None:
    """A complex central region may contain more than one Area."""
    specs = (
        _spec("area.central.a", Placement.CENTRAL, "editor.a"),
        _spec("area.central.b", Placement.CENTRAL, "editor.b"),
    )
    areas = _areas_from_specs(specs)
    tree = LayoutTree.from_specs(specs, areas)

    regions = tree.find_regions()

    assert len(regions) == 1
    assert regions[0].region_id == "central"
    assert [a.area_id for a in regions[0].areas] == [
        "area.central.a",
        "area.central.b",
    ]


def test_find_regions_skips_placements_with_no_areas() -> None:
    """Only placements that have at least one Area produce a Region."""
    specs = (
        _spec("area.central", Placement.CENTRAL, "editor.central"),
        _spec("area.bottom", Placement.BOTTOM, "editor.bottom"),
    )
    areas = _areas_from_specs(specs)
    tree = LayoutTree.from_specs(specs, areas)

    regions = tree.find_regions()

    assert [r.region_id for r in regions] == ["central", "bottom"]
    # "left" and "right" do not appear because there is no Area there.


def test_find_regions_bounds_are_placeholders() -> None:
    """find_regions() does not compute geometry.

    Every returned Region has a placeholder Bounds (zero rectangle).
    The LayoutRenderer will fill the real Bounds once widgets exist.
    """
    specs = (
        _spec("area.left", Placement.LEFT, "editor.left"),
        _spec("area.central", Placement.CENTRAL, "editor.central"),
    )
    areas = _areas_from_specs(specs)
    tree = LayoutTree.from_specs(specs, areas)

    regions = tree.find_regions()

    for region in regions:
        assert region.bounds.is_placeholder() is True


def test_find_regions_every_area_belongs_to_exactly_one_region() -> None:
    specs = (
        _spec("area.left", Placement.LEFT, "editor.left"),
        _spec("area.central", Placement.CENTRAL, "editor.central"),
        _spec("area.right", Placement.RIGHT, "editor.right"),
        _spec("area.bottom", Placement.BOTTOM, "editor.bottom"),
    )
    areas = _areas_from_specs(specs)
    tree = LayoutTree.from_specs(specs, areas)

    regions = tree.find_regions()

    seen: list[str] = []
    for region in regions:
        seen.extend(a.area_id for a in region.areas)
    assert sorted(seen) == sorted(["area.left", "area.central", "area.right", "area.bottom"])
    assert len(seen) == len(set(seen))  # no duplicates


def test_find_regions_areas_are_in_depth_first_order() -> None:
    specs = (
        _spec("area.left.a", Placement.LEFT, "editor.a"),
        _spec("area.left.b", Placement.LEFT, "editor.b"),
        _spec("area.central", Placement.CENTRAL, "editor.central"),
    )
    areas = _areas_from_specs(specs)
    tree = LayoutTree.from_specs(specs, areas)

    regions = tree.find_regions()

    left = next(r for r in regions if r.region_id == "left")
    assert [a.area_id for a in left.areas] == [
        "area.left.a",
        "area.left.b",
    ]
