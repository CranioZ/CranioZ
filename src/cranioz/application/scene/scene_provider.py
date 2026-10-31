"""SceneProvider — loads the Scene for a project (Phase 4).

The SceneProvider is an Application-layer port. It answers:
"Which Scene belongs to this project?"

Implementations:
- ``InMemorySceneProvider``: reference implementation for tests. Holds
  a single Scene in memory.
- ``FilesystemSceneProvider``: infrastructure adapter (to be
  implemented when Scene serialization is ready). Loads the Scene from
  ``scene.json``.

For the first version, only the in-memory implementation is provided.
The Scene is created empty; the actual loading from disk is deferred
to a later piece (Phase 4, Scene serialization).

See ADR-0008, scene.md.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from cranioz.domain.scene.scene import Scene


@runtime_checkable
class SceneProvider(Protocol):
    """Provides the Scene for the active project."""

    def get_scene(self) -> Scene:
        """Return the Scene for the active project.

        The Scene is the spatial organization of objects. It does not
        own the objects (DomainObjectStore owns them). For the first
        version, the Scene is empty; objects will be added by the
        application (via Commands) as the user imports data.
        """
        ...


class InMemorySceneProvider:
    """Reference implementation of ``SceneProvider``.

    Holds a single Scene in memory. Used by tests and by the early
    bootstrap before ``FilesystemSceneProvider`` exists.
    """

    def __init__(self, scene: Scene | None = None) -> None:
        self._scene = scene if scene is not None else Scene(scene_id="scene.default")

    def get_scene(self) -> Scene:
        return self._scene
