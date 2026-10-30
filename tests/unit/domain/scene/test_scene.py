"""Tests for Scene."""

from __future__ import annotations

import pytest

from cranioz.domain.scene.relationship import SpatialRelationship
from cranioz.domain.scene.scene import (
    HierarchyCycle,
    ObjectAlreadyInScene,
    ObjectNotInScene,
    Scene,
)
from cranioz.domain.scene.transform import Transform, Vector3


def test_add_and_contains() -> None:
    scene = Scene()
    scene.add_object("o-1")
    assert scene.contains("o-1")
    assert len(scene) == 1


def test_add_duplicate_raises() -> None:
    scene = Scene()
    scene.add_object("o-1")
    with pytest.raises(ObjectAlreadyInScene):
        scene.add_object("o-1")


def test_remove() -> None:
    scene = Scene()
    scene.add_object("o-1")
    scene.remove_object("o-1")
    assert not scene.contains("o-1")


def test_set_parent() -> None:
    scene = Scene()
    scene.add_object("parent")
    scene.add_object("child")
    scene.set_parent("child", "parent")
    assert scene.get_parent("child") == "parent"
    assert scene.iter_children("parent") == ("child",)


def test_set_parent_cycle_raises() -> None:
    scene = Scene()
    scene.add_object("a")
    scene.add_object("b")
    scene.set_parent("b", "a")
    with pytest.raises(HierarchyCycle):
        scene.set_parent("a", "b")


def test_set_parent_unknown_raises() -> None:
    scene = Scene()
    scene.add_object("a")
    with pytest.raises(ObjectNotInScene):
        scene.set_parent("a", "unknown")


def test_set_transform() -> None:
    scene = Scene()
    scene.add_object("o-1")
    t = Transform(translation=Vector3(1.0, 2.0, 3.0))
    scene.set_transform("o-1", t)
    assert scene.get_transform("o-1") == t


def test_add_relationship() -> None:
    scene = Scene()
    scene.add_object("a")
    scene.add_object("b")
    rel = SpatialRelationship(
        relationship_type="attached_to",
        source_id="a",
        target_id="b",
    )
    scene.add_relationship(rel)
    assert rel in scene.list_relationships()


def test_remove_object_clears_relationships() -> None:
    scene = Scene()
    scene.add_object("a")
    scene.add_object("b")
    scene.add_relationship(
        SpatialRelationship(
            relationship_type="rel",
            source_id="a",
            target_id="b",
        )
    )
    scene.remove_object("a")
    assert scene.list_relationships() == ()
