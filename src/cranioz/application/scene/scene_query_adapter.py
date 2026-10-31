"""SceneQueryAdapter — real SceneQuery backed by a Scene.

Implements the ``SceneQuery`` Protocol (application/scene/scene_query.py)
by querying the ``Scene`` (domain/scene/scene.py). The adapter is
read-only: it never mutates the Scene. All mutations go through
Commands (ADR-0007).

This adapter belongs to the Infrastructure layer because it bridges
the Application port (SceneQuery) to the Domain entity (Scene). In the
future, it may also expose transforms and relationships from the
Scene.

See ADR-0008, scene.md, editors.md §15.
"""

from __future__ import annotations

from typing import Any

from cranioz.domain.scene.scene import Scene


class SceneQueryAdapter:
    """SceneQuery implementation backed by a Scene."""

    def __init__(self, scene: Scene) -> None:
        self._scene = scene

    def get_object(self, object_id: str) -> Any | None:
        """Return the object with the given ID, or None.

        The Scene does not own the object payload (DomainObjectStore
        does). The adapter returns the object_id if it is a member of
        the Scene, and None otherwise. The caller (the View) resolves
        the actual object through the DomainObjectStore (future piece).
        """
        if not self._scene.contains(object_id):
            return None
        return object_id

    def list_objects(self) -> tuple[str, ...]:
        """Return the IDs of all objects in the Scene."""
        return self._scene.list_objects()

    def contains(self, object_id: str) -> bool:
        """Return True if the object is in the Scene."""
        return self._scene.contains(object_id)

    def get_transform(self, object_id: str) -> Any | None:
        """Return the transform of the object, or None.

        The Scene stores a Transform per member. The adapter returns
        it if the object is in the Scene; None otherwise.
        """
        if not self._scene.contains(object_id):
            return None
        return self._scene.get_transform(object_id)
