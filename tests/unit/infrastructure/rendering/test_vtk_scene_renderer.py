"""Tests for VTKSceneRenderer (headless).

These tests require VTK to be installed. They do NOT require a
display (they use vtkRenderer without a render window).
"""

from cranioz.domain.scene.scene import Scene
from cranioz.domain.scene.transform import Transform, Vector3
from cranioz.infrastructure.rendering.vtk_scene_renderer import (
    VTKSceneRenderer,
)


def test_attach_scene_adds_actors() -> None:
    renderer = VTKSceneRenderer()
    scene = Scene()
    scene.add_object("o-1")
    renderer.attach_scene(scene)
    assert renderer.actor_registry.contains("o-1")


def test_remove_object_removes_actor() -> None:
    renderer = VTKSceneRenderer()
    scene = Scene()
    scene.add_object("o-1")
    renderer.attach_scene(scene)
    scene.remove_object("o-1")
    renderer.refresh()
    assert not renderer.actor_registry.contains("o-1")


def test_transform_updates_actor_position() -> None:
    renderer = VTKSceneRenderer()
    scene = Scene()
    scene.add_object("o-1")
    renderer.attach_scene(scene)
    scene.set_transform("o-1", Transform(translation=Vector3(1.0, 2.0, 3.0)))
    renderer.refresh()
    actor = renderer.actor_registry.get("o-1")
    assert actor is not None
    pos = actor.GetPosition()
    assert pos == (1.0, 2.0, 3.0)
