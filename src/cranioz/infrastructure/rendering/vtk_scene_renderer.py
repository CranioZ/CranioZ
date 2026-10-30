"""VTKSceneRenderer — manages the VTK rendering context.

The renderer owns:
- The vtkRenderer.
- The ActorRegistry (mapping object_id -> actor).
- The VTKActorFactory (creating actors from domain objects).

The renderer does NOT own the Scene. It observes it via the
RenderingAdapter.

VTK is an optional dependency. The import is deferred to
``__init__`` so that the application can boot without VTK
installed; the error is raised only when a renderer is actually
instantiated.

See scene.md §26, §50.
"""

from __future__ import annotations

from typing import Any

from cranioz.domain.scene.scene import Scene
from cranioz.infrastructure.rendering.actor_registry import ActorRegistry
from cranioz.infrastructure.rendering.vtk_actor_factory import (
    VTKActorFactory,
)


class VTKSceneRenderer:
    """Manages the VTK rendering context for a Scene."""

    def __init__(self) -> None:
        try:
            import vtk  # noqa: PLC0415 - deferred import to allow boot without VTK
        except ImportError as exc:
            raise RuntimeError("VTK is not installed. Install it with 'pip install vtk'.") from exc
        self._vtk = vtk
        self._renderer = vtk.vtkRenderer()
        self._renderer.SetBackground(0.1, 0.1, 0.2)  # dark blue
        self._actor_registry = ActorRegistry()
        self._actor_factory = VTKActorFactory()
        self._scene: Scene | None = None

    # ----- Public API -----------------------------------------------

    @property
    def renderer(self) -> Any:
        return self._renderer

    @property
    def actor_registry(self) -> ActorRegistry:
        return self._actor_registry

    def attach_scene(self, scene: Scene) -> None:
        self._scene = scene
        self._sync()

    def detach_scene(self) -> None:
        self._scene = None
        self._clear_actors()

    def refresh(self) -> None:
        self._sync()

    # ----- Internals ------------------------------------------------

    def _sync(self) -> None:
        """Re-sync the VTK actors with the Scene."""
        if self._scene is None:
            return
        scene_ids = set(self._scene.list_objects())
        registry_ids = set(self._actor_registry.list_ids())

        # Remove actors for objects no longer in the Scene.
        for object_id in registry_ids - scene_ids:
            self._remove_actor(object_id)

        # Add actors for new objects.
        for object_id in scene_ids - registry_ids:
            self._add_actor(object_id)

        # Update transforms for all objects.
        for object_id in scene_ids:
            self._update_transform(object_id)

    def _add_actor(self, object_id: str) -> None:
        actor = self._actor_factory.create_mesh_actor(object_id)
        self._actor_registry.register(object_id, actor)
        self._renderer.AddActor(actor)

    def _remove_actor(self, object_id: str) -> None:
        actor = self._actor_registry.unregister(object_id)
        if actor is not None:
            self._renderer.RemoveActor(actor)

    def _update_transform(self, object_id: str) -> None:
        if self._scene is None:
            return
        actor = self._actor_registry.get(object_id)
        if actor is None:
            return
        transform = self._scene.get_transform(object_id)
        # Placeholder: apply translation only (rotation via quaternion
        # will be added once the domain transform supports it).
        actor.SetPosition(
            transform.translation.x,
            transform.translation.y,
            transform.translation.z,
        )

    def _clear_actors(self) -> None:
        for object_id in list(self._actor_registry.list_ids()):
            self._remove_actor(object_id)
