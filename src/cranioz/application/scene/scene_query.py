"""SceneQuery — read-only interface over the Scene (ADR-0008, ADR-0013).

An Editor accesses the Scene through SceneQuery. It never receives a
mutable reference. All mutations go through Commands (ADR-0007).

For the first version, this module defines the Protocol and a
reference in-memory implementation (`InMemorySceneQuery`). The
concrete adapter (backed by the real Scene) will be implemented in
Phase 4.

See editors.md §15, scene.md §24.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class SceneQuery(Protocol):
    """Read-only interface over the Scene."""

    def get_object(self, object_id: str) -> Any | None:
        """Return the object with the given ID, or None."""
        ...

    def list_objects(self) -> tuple[str, ...]:
        """Return the IDs of all objects in the Scene."""
        ...

    def contains(self, object_id: str) -> bool:
        """Return True if the object is in the Scene."""
        ...

    def get_transform(self, object_id: str) -> Any | None:
        """Return the transform of the object, or None."""
        ...


class InMemorySceneQuery:
    """Reference implementation of SceneQuery backed by a dict.

    Used by tests and by the early bootstrap before the real Scene
    is implemented. The dict is not mutated by the query; the caller
    provides it read-only.
    """

    def __init__(self) -> None:
        self._objects: dict[str, Any] = {}
        self._transforms: dict[str, Any] = {}

    def _add(
        self,
        object_id: str,
        obj: Any,
        transform: Any = None,
    ) -> None:
        """Register an object for testing."""
        self._objects[object_id] = obj
        if transform is not None:
            self._transforms[object_id] = transform

    def get_object(self, object_id: str) -> Any | None:
        return self._objects.get(object_id)

    def list_objects(self) -> tuple[str, ...]:
        return tuple(self._objects.keys())

    def contains(self, object_id: str) -> bool:
        return object_id in self._objects

    def get_transform(self, object_id: str) -> Any | None:
        return self._transforms.get(object_id)
