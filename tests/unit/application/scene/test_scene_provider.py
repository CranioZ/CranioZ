"""Tests for SceneProvider and InMemorySceneProvider."""

from __future__ import annotations

from cranioz.application.scene.scene_provider import (
    InMemorySceneProvider,
    SceneProvider,
)
from cranioz.domain.scene.scene import Scene


def test_satisfies_protocol() -> None:
    assert isinstance(InMemorySceneProvider(), SceneProvider)


def test_get_scene_returns_scene() -> None:
    provider = InMemorySceneProvider()
    scene = provider.get_scene()
    assert isinstance(scene, Scene)


def test_get_scene_returns_same_instance() -> None:
    provider = InMemorySceneProvider()
    assert provider.get_scene() is provider.get_scene()


def test_get_scene_with_custom_scene() -> None:
    custom = Scene(scene_id="custom")
    provider = InMemorySceneProvider(scene=custom)
    assert provider.get_scene() is custom
