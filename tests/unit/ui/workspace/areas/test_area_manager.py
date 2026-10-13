"""Tests for AreaManager."""

# mypy: ignore-errors

from __future__ import annotations

import pytest

from cranioz.ui.workspace.areas.area import Area
from cranioz.ui.workspace.areas.area_manager import (
    AreaManager,
    AreaManagerError,
)
from cranioz.ui.workspace.areas.placement import Placement


def _area(
    area_id: str,
    placement: Placement = Placement.CENTRAL,
) -> Area:
    return Area(area_id=area_id, title=area_id, placement=placement)


# ----- Registration ------------------------------------------------


def test_register_and_get() -> None:
    manager = AreaManager()
    area = _area("area.central")
    manager.register(area)
    assert manager.get("area.central") is area


def test_register_same_instance_is_idempotent() -> None:
    manager = AreaManager()
    area = _area("area.central")
    manager.register(area)
    manager.register(area)  # no raise
    assert manager.area_count() == 1


def test_register_different_instance_same_id_raises() -> None:
    manager = AreaManager()
    a = _area("area.central")
    b = _area("area.central")
    manager.register(a)
    with pytest.raises(AreaManagerError, match="different Area"):
        manager.register(b)


# ----- Retrieval ---------------------------------------------------


def test_get_unknown_returns_none() -> None:
    manager = AreaManager()
    assert manager.get("area.unknown") is None


def test_require_returns_area() -> None:
    manager = AreaManager()
    area = _area("area.central")
    manager.register(area)
    assert manager.require("area.central") is area


def test_require_unknown_raises_keyerror() -> None:
    manager = AreaManager()
    with pytest.raises(KeyError, match="not registered"):
        manager.require("area.unknown")


def test_contains() -> None:
    manager = AreaManager()
    assert not manager.contains("area.central")
    manager.register(_area("area.central"))
    assert manager.contains("area.central")


# ----- Unregister --------------------------------------------------


def test_unregister_returns_area() -> None:
    manager = AreaManager()
    area = _area("area.central")
    manager.register(area)
    removed = manager.unregister("area.central")
    assert removed is area
    assert not manager.contains("area.central")


def test_unregister_unknown_returns_none() -> None:
    manager = AreaManager()
    assert manager.unregister("area.unknown") is None


# ----- Listing -----------------------------------------------------


def test_new_manager_is_empty() -> None:
    manager = AreaManager()
    assert manager.areas() == ()
    assert manager.area_count() == 0


def test_areas_preserve_insertion_order() -> None:
    manager = AreaManager()
    a = _area("area.left", Placement.LEFT)
    b = _area("area.central", Placement.CENTRAL)
    c = _area("area.right", Placement.RIGHT)
    manager.register(a)
    manager.register(b)
    manager.register(c)
    assert manager.areas() == (a, b, c)


def test_area_count() -> None:
    manager = AreaManager()
    manager.register(_area("area.a"))
    manager.register(_area("area.b"))
    assert manager.area_count() == 2


# ----- Placement-aware helpers -------------------------------------


def test_count_by_placement() -> None:
    manager = AreaManager()
    manager.register(_area("area.left", Placement.LEFT))
    manager.register(_area("area.central.a", Placement.CENTRAL))
    manager.register(_area("area.central.b", Placement.CENTRAL))
    manager.register(_area("area.right", Placement.RIGHT))

    assert manager.count_by_placement(Placement.LEFT) == 1
    assert manager.count_by_placement(Placement.CENTRAL) == 2
    assert manager.count_by_placement(Placement.RIGHT) == 1
    assert manager.count_by_placement(Placement.BOTTOM) == 0


def test_has_central() -> None:
    manager = AreaManager()
    assert manager.has_central() is False
    manager.register(_area("area.central"))
    assert manager.has_central() is True


# ----- Clear -------------------------------------------------------


def test_clear_removes_all() -> None:
    manager = AreaManager()
    manager.register(_area("area.a"))
    manager.register(_area("area.b"))
    manager.clear()
    assert manager.area_count() == 0
    assert manager.areas() == ()
    assert manager.has_central() is False


def test_clear_on_empty_is_noop() -> None:
    manager = AreaManager()
    manager.clear()
    assert manager.area_count() == 0


# ----- Representation ----------------------------------------------


def test_repr_contains_ids() -> None:
    manager = AreaManager()
    manager.register(_area("area.central"))
    assert "area.central" in repr(manager)
