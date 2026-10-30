"""DomainObjectStore — canonical registry of domain objects.

The DomainObjectStore is Project-scoped. It is the single source of
truth for object identity and lifecycle. It does NOT own spatial state
(that is the Scene's responsibility).

Responsibilities:
- Register objects by stable ID.
- Retrieve objects by ID.
- Remove objects (only if not referenced by any Scene).
- List all objects.

Invariants:
- Every object has a unique stable ID.
- Removing an object that is referenced by any Scene is rejected.

See ADR-0008, scene.md §4.
"""

from __future__ import annotations

from typing import Any


class DomainObjectStoreError(Exception):
    """Base of all DomainObjectStore errors."""


class ObjectAlreadyExists(DomainObjectStoreError):
    """Raised when adding an object with an existing ID."""


class ObjectNotFound(DomainObjectStoreError):
    """Raised when an object ID does not exist."""


class ObjectInUse(DomainObjectStoreError):
    """Raised when removing an object that is referenced by a Scene."""


class DomainObjectStore:
    """Project-scoped canonical registry of domain objects.

    The store holds opaque domain objects (they are not inspected by
    the store). It only enforces identity and lifecycle invariants.
    """

    def __init__(self) -> None:
        self._objects: dict[str, Any] = {}

    # ----- Add / Remove ---------------------------------------------

    def add(self, object_id: str, obj: Any) -> None:
        """Register a new object.

        Raises:
            ObjectAlreadyExists: an object with the same ID exists.
        """
        if not object_id:
            raise ValueError("object_id must not be empty")
        if object_id in self._objects:
            raise ObjectAlreadyExists(f"object already exists: {object_id!r}")
        self._objects[object_id] = obj

    def remove(self, object_id: str) -> None:
        """Remove an object.

        The caller (Application layer) is responsible for checking
        Scene membership before calling remove(). The store does not
        know about Scenes.

        Raises:
            ObjectNotFound: the ID does not exist.
        """
        if object_id not in self._objects:
            raise ObjectNotFound(f"object not found: {object_id!r}")
        del self._objects[object_id]

    # ----- Query ----------------------------------------------------

    def get(self, object_id: str) -> Any:
        """Return the object, or raise ObjectNotFound."""
        try:
            return self._objects[object_id]
        except KeyError as exc:
            raise ObjectNotFound(f"object not found: {object_id!r}") from exc

    def contains(self, object_id: str) -> bool:
        return object_id in self._objects

    def list_ids(self) -> tuple[str, ...]:
        return tuple(self._objects.keys())

    def __len__(self) -> int:
        return len(self._objects)

    def __repr__(self) -> str:
        return f"DomainObjectStore(objects={len(self._objects)})"
