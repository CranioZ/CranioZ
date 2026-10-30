"""Tests for Scene serialization round-trip."""

from cranioz.domain.scene.scene import Scene
from cranioz.domain.scene.transform import Transform, Vector3
from cranioz.infrastructure.scene.scene_serialization import (
    scene_from_dict,
    scene_to_dict,
)


def test_round_trip() -> None:
    scene = Scene(scene_id="scene.test")
    scene.add_object("o-1")
    scene.add_object("o-2")
    scene.set_parent("o-2", "o-1")
    scene.set_transform("o-1", Transform(translation=Vector3(1.0, 2.0, 3.0)))
    reconstructed = scene_from_dict(scene_to_dict(scene))
    assert reconstructed.scene_id == "scene.test"
    assert set(reconstructed.list_objects()) == {"o-1", "o-2"}
    assert reconstructed.get_parent("o-2") == "o-1"
    assert reconstructed.get_transform("o-1").translation == Vector3(1.0, 2.0, 3.0)
