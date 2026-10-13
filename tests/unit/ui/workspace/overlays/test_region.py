"""Tests for Region and Bounds.

Region and Bounds are pure domain structures. They do not depend on
Qt, and these tests run without a QApplication.
"""

from __future__ import annotations

import dataclasses

import pytest

from cranioz.ui.workspace.areas.area import Area
from cranioz.ui.workspace.areas.placement import Placement
from cranioz.ui.workspace.overlays.region import Bounds, Region

# ----- Helpers ------------------------------------------------------


def _area(
    area_id: str,
    placement: Placement = Placement.CENTRAL,
) -> Area:
    return Area(area_id=area_id, title=area_id, placement=placement)


# ----- Bounds -------------------------------------------------------


def test_bounds_defaults_to_zero_rectangle() -> None:
    b = Bounds()
    assert b.x == 0.0
    assert b.y == 0.0
    assert b.width == 0.0
    assert b.height == 0.0


def test_bounds_holds_all_fields() -> None:
    b = Bounds(x=10.0, y=20.0, width=100.0, height=50.0)
    assert b.x == 10.0
    assert b.y == 20.0
    assert b.width == 100.0
    assert b.height == 50.0


def test_bounds_is_frozen() -> None:
    b = Bounds()
    with pytest.raises(dataclasses.FrozenInstanceError):
        b.x = 1.0  # type: ignore[misc]


def test_bounds_default_is_placeholder() -> None:
    assert Bounds().is_placeholder() is True


def test_bounds_with_nonzero_values_is_not_placeholder() -> None:
    assert Bounds(x=1.0).is_placeholder() is False
    assert Bounds(width=1.0).is_placeholder() is False


def test_bounds_negative_width_raises() -> None:
    with pytest.raises(ValueError, match="width"):
        Bounds(width=-1.0)


def test_bounds_negative_height_raises() -> None:
    with pytest.raises(ValueError, match="height"):
        Bounds(height=-1.0)


def test_bounds_zero_width_is_valid() -> None:
    # A zero-width Bounds is allowed (e.g. a degenerate rectangle).
    Bounds(width=0.0)


def test_bounds_equality() -> None:
    a = Bounds(1.0, 2.0, 3.0, 4.0)
    b = Bounds(1.0, 2.0, 3.0, 4.0)
    assert a == b


# ----- Region -------------------------------------------------------


def test_region_holds_all_fields() -> None:
    areas = (_area("area.left", Placement.LEFT),)
    region = Region(
        region_id="left",
        bounds=Bounds(),
        areas=areas,
        semantic_role=Placement.LEFT,
    )
    assert region.region_id == "left"
    assert region.areas == areas
    assert region.semantic_role is Placement.LEFT


def test_region_empty_id_raises() -> None:
    with pytest.raises(ValueError, match="region_id"):
        Region(
            region_id="",
            bounds=Bounds(),
            areas=(_area("area.a"),),
            semantic_role=Placement.CENTRAL,
        )


def test_region_with_no_areas_raises() -> None:
    with pytest.raises(ValueError, match="at least one Area"):
        Region(
            region_id="central",
            bounds=Bounds(),
            areas=(),
            semantic_role=Placement.CENTRAL,
        )


def test_region_is_frozen() -> None:
    region = Region(
        region_id="central",
        bounds=Bounds(),
        areas=(_area("area.central"),),
        semantic_role=Placement.CENTRAL,
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        region.region_id = "other"  # type: ignore[misc]


def test_region_area_count() -> None:
    region = Region(
        region_id="central",
        bounds=Bounds(),
        areas=(
            _area("area.central.a"),
            _area("area.central.b"),
        ),
        semantic_role=Placement.CENTRAL,
    )
    assert region.area_count() == 2


def test_region_contains() -> None:
    region = Region(
        region_id="central",
        bounds=Bounds(),
        areas=(_area("area.central"),),
        semantic_role=Placement.CENTRAL,
    )
    assert region.contains("area.central") is True
    assert region.contains("area.other") is False


def test_region_with_bounds_returns_new_instance() -> None:
    region = Region(
        region_id="central",
        bounds=Bounds(),
        areas=(_area("area.central"),),
        semantic_role=Placement.CENTRAL,
    )
    real_bounds = Bounds(x=100.0, y=0.0, width=800.0, height=600.0)
    updated = region.with_bounds(real_bounds)

    assert updated is not region
    assert updated.bounds == real_bounds
    assert region.bounds.is_placeholder() is True  # original unchanged
    assert updated.areas == region.areas
    assert updated.semantic_role is region.semantic_role


def test_region_semantic_role_can_be_none() -> None:
    # Allowed for future flexibility; today always set by find_regions.
    region = Region(
        region_id="custom",
        bounds=Bounds(),
        areas=(_area("area.custom"),),
        semantic_role=None,
    )
    assert region.semantic_role is None


def test_region_repr_mentions_key_fields() -> None:
    region = Region(
        region_id="central",
        bounds=Bounds(),
        areas=(_area("area.central"),),
        semantic_role=Placement.CENTRAL,
    )
    text = repr(region)
    assert "central" in text
    assert "area.central" in text
    assert "placeholder" in text
