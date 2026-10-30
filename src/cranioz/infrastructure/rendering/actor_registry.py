"""ActorRegistry — maps object_id to VTK actor.

The registry is the single source of truth for the mapping between
domain objects and their VTK representations. It does NOT own the
actors; the VTKSceneRenderer does.

See scene.md §26, §27.
"""

from __future__ import annotations

from typing import Any


class ActorRegistry:
    """Maps object_id to VTK actor (or any renderable representation)."""

    def __init__(self) -> None:
        self._actors: dict[str, Any] = {}

    def register(self, object_id: str, actor: Any) -> None:
        if not object_id:
            raise ValueError("object_id must not be empty")
        self._actors[object_id] = actor

    def unregister(self, object_id: str) -> Any | None:
        return self._actors.pop(object_id, None)

    def get(self, object_id: str) -> Any | None:
        return self._actors.get(object_id)

    def contains(self, object_id: str) -> bool:
        return object_id in self._actors

    def list_ids(self) -> tuple[str, ...]:
        return tuple(self._actors.keys())

    def clear(self) -> None:
        self._actors.clear()

    def __len__(self) -> int:
        return len(self._actors)
