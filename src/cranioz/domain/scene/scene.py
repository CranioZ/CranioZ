"""Scene — spatial organization of objects within a planning context.

The Scene owns:
- Membership (which object_ids are in this Scene).
- Spatial hierarchy (parent-child relationships).
- Transforms (per-object rigid transformation).
- Spatial relationships (typed links between objects).
- Reference frames.

The Scene does NOT own:
- Object lifecycle (DomainObjectStore owns it).
- Rendering (RenderingAdapter owns it).
- Selection (Application/UI concern).
- Persistence (infrastructure concern).

Invariants:
- Every member object_id must resolve to a valid DomainObjectStore
  object (checked by the Application layer before calling add_object).
- No cycles in the hierarchy.
- At most one parent per object.
- Relationships must reference valid members.

See ADR-0008, scene.md.
"""

from __future__ import annotations

import contextlib
from dataclasses import dataclass, field

from cranioz.domain.scene.relationship import SpatialRelationship
from cranioz.domain.scene.transform import Transform


class SceneError(Exception):
    """Base of all Scene errors."""


class ObjectNotInScene(SceneError):
    """Raised when referencing an object that is not a Scene member."""


class ObjectAlreadyInScene(SceneError):
    """Raised when adding an object that is already a member."""


class HierarchyCycle(SceneError):
    """Raised when a set_parent would create a cycle."""


@dataclass
class _SceneMember:
    """Internal state of a Scene member."""

    object_id: str
    parent_id: str | None = None
    transform: Transform = field(default_factory=Transform.identity)


class Scene:
    """Spatial organization of objects within a planning context."""

    def __init__(self, scene_id: str = "scene.default") -> None:
        if not scene_id:
            raise ValueError("scene_id must not be empty")
        self._scene_id = scene_id
        self._members: dict[str, _SceneMember] = {}
        self._relationships: list[SpatialRelationship] = []

    # ----- Identity -------------------------------------------------

    @property
    def scene_id(self) -> str:
        return self._scene_id

    # ----- Membership -----------------------------------------------

    def add_object(self, object_id: str) -> None:
        """Add an object to the Scene.

        The caller (Application layer) must ensure the object_id
        resolves to a valid DomainObjectStore object.

        Raises:
            ObjectAlreadyInScene: the object is already a member.
        """
        if not object_id:
            raise ValueError("object_id must not be empty")
        if object_id in self._members:
            raise ObjectAlreadyInScene(f"object already in scene: {object_id!r}")
        self._members[object_id] = _SceneMember(object_id=object_id)

    def remove_object(self, object_id: str) -> None:
        """Remove an object from the Scene.

        Also removes any relationships that reference the object,
        and detaches any children (they become root-level).

        Raises:
            ObjectNotInScene: the object is not a member.
        """
        if object_id not in self._members:
            raise ObjectNotInScene(f"object not in scene: {object_id!r}")
        # Detach children.
        for member in self._members.values():
            if member.parent_id == object_id:
                member.parent_id = None
        # Remove relationships referencing this object.
        self._relationships = [
            rel for rel in self._relationships if object_id not in (rel.source_id, rel.target_id)
        ]
        del self._members[object_id]

    def contains(self, object_id: str) -> bool:
        return object_id in self._members

    def list_objects(self) -> tuple[str, ...]:
        return tuple(self._members.keys())

    def __len__(self) -> int:
        return len(self._members)

    # ----- Hierarchy ------------------------------------------------

    def set_parent(self, child_id: str, parent_id: str) -> None:
        """Set the parent of an object.

        Raises:
            ObjectNotInScene: child or parent is not a member.
            HierarchyCycle: the parent would create a cycle.
        """
        if child_id not in self._members:
            raise ObjectNotInScene(f"child not in scene: {child_id!r}")
        if parent_id not in self._members:
            raise ObjectNotInScene(f"parent not in scene: {parent_id!r}")
        if child_id == parent_id:
            raise HierarchyCycle(f"object cannot be its own parent: {child_id!r}")
        # Check for cycles: walk up from parent_id.
        current: str | None = parent_id
        while current is not None:
            if current == child_id:
                raise HierarchyCycle(
                    f"setting parent would create a cycle: {child_id!r} -> {parent_id!r}"
                )
            member = self._members.get(current)
            current = member.parent_id if member is not None else None
        self._members[child_id].parent_id = parent_id

    def clear_parent(self, child_id: str) -> None:
        """Remove the parent of an object (it becomes root-level)."""
        if child_id not in self._members:
            raise ObjectNotInScene(f"object not in scene: {child_id!r}")
        self._members[child_id].parent_id = None

    def get_parent(self, object_id: str) -> str | None:
        if object_id not in self._members:
            raise ObjectNotInScene(f"object not in scene: {object_id!r}")
        return self._members[object_id].parent_id

    def iter_children(self, object_id: str) -> tuple[str, ...]:
        return tuple(m.object_id for m in self._members.values() if m.parent_id == object_id)

    # ----- Transforms -----------------------------------------------

    def set_transform(self, object_id: str, transform: Transform) -> None:
        if object_id not in self._members:
            raise ObjectNotInScene(f"object not in scene: {object_id!r}")
        self._members[object_id].transform = transform

    def get_transform(self, object_id: str) -> Transform:
        if object_id not in self._members:
            raise ObjectNotInScene(f"object not in scene: {object_id!r}")
        return self._members[object_id].transform

    # ----- Relationships --------------------------------------------

    def add_relationship(self, rel: SpatialRelationship) -> None:
        if rel.source_id not in self._members:
            raise ObjectNotInScene(f"source not in scene: {rel.source_id!r}")
        if rel.target_id not in self._members:
            raise ObjectNotInScene(f"target not in scene: {rel.target_id!r}")
        self._relationships.append(rel)

    def remove_relationship(self, rel: SpatialRelationship) -> None:
        with contextlib.suppress(ValueError):
            self._relationships.remove(rel)

    def list_relationships(self) -> tuple[SpatialRelationship, ...]:
        return tuple(self._relationships)

    # ----- Representation -------------------------------------------

    def __repr__(self) -> str:
        return (
            f"Scene(scene_id={self._scene_id!r}, "
            f"members={len(self._members)}, "
            f"relationships={len(self._relationships)})"
        )
