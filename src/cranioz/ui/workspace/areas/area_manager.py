"""AreaManager.

Registry of Area instances within a Workspace.

Rules:
- The manager registers Area instances, not types.
- The manager preserves insertion order when listing Areas.
- Re-registering the same instance under the same area_id is
  idempotent. Registering a different instance with the same
  area_id raises ValueError.
- get() returns None for unknown ids. require() raises KeyError.
- The manager does not create Areas. Construction of Areas is the
  responsibility of the LayoutBuilder.
- The manager does not decide visibility, activation, or layout.
  It only tracks which Areas exist in this Workspace instance.
- The manager does not enforce the "at least one CENTRAL Area"
  invariant by itself, but it exposes helpers (count_by_placement,
  has_central) that the Workspace uses to enforce it.

The AreaManager is per-Workspace. Two Workspaces have two managers.
"""

from __future__ import annotations

from cranioz.ui.workspace.areas.area import Area
from cranioz.ui.workspace.areas.placement import Placement


class AreaManagerError(ValueError):
    """Raised when area registration violates a structural rule."""


class AreaManager:
    """Registry of Area instances."""

    def __init__(self) -> None:
        self._areas: dict[str, Area] = {}

    def register(self, area: Area) -> None:
        """Register an Area.

        Idempotent for the same instance. Raises AreaManagerError when
        a different Area is already registered under the same area_id.
        """
        area_id = area.area_id
        existing = self._areas.get(area_id)
        if existing is area:
            return
        if existing is not None:
            raise AreaManagerError(f"area_id already registered with a different Area: {area_id}")
        self._areas[area_id] = area

    def unregister(self, area_id: str) -> Area | None:
        """Remove an Area. Returns the removed Area, or None if unknown."""
        return self._areas.pop(area_id, None)

    def get(self, area_id: str) -> Area | None:
        """Return the Area with the given area_id, or None."""
        return self._areas.get(area_id)

    def require(self, area_id: str) -> Area:
        """Return the Area with the given area_id.

        Raises KeyError if unknown.
        """
        try:
            return self._areas[area_id]
        except KeyError as exc:
            raise KeyError(f"area_id not registered: {area_id}") from exc

    def contains(self, area_id: str) -> bool:
        """Return True if an Area with the given id is registered."""
        return area_id in self._areas

    def areas(self) -> tuple[Area, ...]:
        """Return the registered Areas in insertion order."""
        return tuple(self._areas.values())

    def area_count(self) -> int:
        """Return the number of registered Areas."""
        return len(self._areas)

    def count_by_placement(self, placement: Placement) -> int:
        """Return the number of registered Areas with the given placement."""
        return sum(1 for area in self._areas.values() if area.placement is placement)

    def has_central(self) -> bool:
        """Return True if at least one CENTRAL Area is registered."""
        return self.count_by_placement(Placement.CENTRAL) > 0

    def clear(self) -> None:
        """Remove all registered Areas.

        Used during Workspace shutdown and during module switches.
        """
        self._areas.clear()

    def __repr__(self) -> str:
        return f"AreaManager(areas={list(self._areas.keys())!r})"
