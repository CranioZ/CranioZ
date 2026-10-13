"""Tests for AreaManager."""

from __future__ import annotations

import pytest

from cranioz.ui.workspace.areas.area import Area
from cranioz.ui.workspace.areas.area_manager import (
    AreaManager,
    AreaManagerError,
)

# ----- Registration ------------------------------------------------


def test_register_and_get() -> None:
    manager = AreaManager()
    area = Area(area_id="area.central", title="Central")
    manager.register(area)
    assert manager.get("area.central") is area


def test_register_same_instance_is_idempotent() -> None:
    manager = AreaManager()
    area = Area(area_id="area.central", title="Central")
    manager.register(area)
    manager.register(area)  # no raise
    assert manager.area_count() == 1


def test_register_different_instance_same_id_raises() -> None:
    manager = AreaManager()
    a = Area(area_id="area.central", title="Central")
    b = Area(area_id="area.central", title="Another Central")
    manager.register(a)
    with pytest.raises(AreaManagerError, match="different Area"):
        manager.register(b)


# ----- Retrieval ---------------------------------------------------


def test_get_unknown_returns_none() -> None:
    manager = AreaManager()
    assert manager.get("area.unknown") is None


def test_require_returns_area() -> None:
    manager = AreaManager()
    area = Area(area_id="area.central", title="Central")
    manager.register(area)
    assert manager.require("area.central") is area


def test_require_unknown_raises_keyerror() -> None:
    manager = AreaManager()
    with pytest.raises(KeyError, match="not registered"):
        manager.require("area.unknown")


def test_contains() -> None:
    manager = AreaManager()
    assert not manager.contains("area.central")
    manager.register(Area(area_id="area.central", title="Central"))
    assert manager.contains("area.central")


# ----- Unregister --------------------------------------------------


def test_unregister_returns_area() -> None:
    manager = AreaManager()
    area = Area(area_id="area.central", title="Central")
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
    a = Area(area_id="area.left", title="Left")
    b = Area(area_id="area.central", title="Central")
    c = Area(area_id="area.right", title="Right")
    manager.register(a)
    manager.register(b)
    manager.register(c)
    assert manager.areas() == (a, b, c)


def test_area_count() -> None:
    manager = AreaManager()
    manager.register(Area(area_id="area.a", title="A"))
    manager.register(Area(area_id="area.b", title="B"))
    assert manager.area_count() == 2


# ----- Clear -------------------------------------------------------


def test_clear_removes_all() -> None:
    manager = AreaManager()
    manager.register(Area(area_id="area.a", title="A"))
    manager.register(Area(area_id="area.b", title="B"))
    manager.clear()
    assert manager.area_count() == 0
    assert manager.areas() == ()


def test_clear_on_empty_is_noop() -> None:
    manager = AreaManager()
    manager.clear()  # no raise
    assert manager.area_count() == 0


# ----- Representation ----------------------------------------------


def test_repr_contains_ids() -> None:
    manager = AreaManager()
    manager.register(Area(area_id="area.central", title="Central"))
    assert "area.central" in repr(manager)
