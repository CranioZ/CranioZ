"""OverlayManager.

Registry and repositioning coordinator for Overlays within a
Workspace.

Responsibilities:

- Register and unregister Overlays by their ``overlay_id``.
- Look them up and enumerate them in a deterministic order.
- Reposition every registered Overlay when the layout changes, by
  matching each Overlay's ``target_region`` (a ``Placement``) to the
  current set of Regions and passing the Region's Bounds to
  ``Overlay.reposition()``.

Non-responsibilities:

- The manager does not create or destroy Overlays. It only tracks
  the ones it is given.
- The manager does not compute Region Bounds. It receives the
  current Regions from the Workspace / LayoutRenderer and forwards
  the Bounds as-is.
- The manager does not know about Qt layout details. Overlays own
  their widgets.

Design rules:

- A registered ``overlay_id`` is unique within a single manager.
  Registering the same instance again is idempotent; registering a
  different instance under the same id raises
  ``OverlayManagerError``.
- Registration order is preserved. ``overlays()`` returns them in
  that order, which makes repositioning deterministic.
- ``reposition_all()`` does not fail when a target Region is absent.
  If an Overlay targets a Placement for which no Region exists in
  the current tree, the Overlay is simply not repositioned. This
  matches the Workspace model: a Region may legitimately be missing
  during a module switch.
- ``clear()`` removes all registrations. It does not touch the
  Overlays themselves.
"""

from __future__ import annotations

from cranioz.ui.workspace.areas.placement import Placement
from cranioz.ui.workspace.overlays.overlay import Overlay
from cranioz.ui.workspace.overlays.region import Region


class OverlayManagerError(ValueError):
    """Raised when overlay registration violates a structural rule."""


class OverlayManager:
    """Registry and repositioning coordinator for Overlays."""

    def __init__(self) -> None:
        self._overlays: dict[str, Overlay] = {}

    # ----- Registration ---------------------------------------------

    def register(self, overlay: Overlay) -> None:
        """Register an Overlay.

        Idempotent when the same instance is registered twice under
        the same ``overlay_id``. Raises ``OverlayManagerError`` when
        a different instance is already registered under the same id.
        """
        overlay_id = overlay.overlay_id
        if not overlay_id:
            raise OverlayManagerError("overlay_id must not be empty")

        existing = self._overlays.get(overlay_id)
        if existing is overlay:
            return
        if existing is not None:
            raise OverlayManagerError(
                f"overlay_id already registered with a different Overlay: {overlay_id}"
            )
        self._overlays[overlay_id] = overlay

    def unregister(self, overlay_id: str) -> Overlay | None:
        """Remove an Overlay.

        Returns the removed Overlay, or None if the id is unknown.
        """
        return self._overlays.pop(overlay_id, None)

    # ----- Lookup ---------------------------------------------------

    def get(self, overlay_id: str) -> Overlay | None:
        """Return the Overlay with the given id, or None."""
        return self._overlays.get(overlay_id)

    def require(self, overlay_id: str) -> Overlay:
        """Return the Overlay with the given id.

        Raises KeyError if unknown.
        """
        try:
            return self._overlays[overlay_id]
        except KeyError as exc:
            raise KeyError(f"overlay_id not registered: {overlay_id}") from exc

    def contains(self, overlay_id: str) -> bool:
        """Return True if an Overlay with the given id is registered."""
        return overlay_id in self._overlays

    def overlays(self) -> tuple[Overlay, ...]:
        """Return the registered Overlays in registration order."""
        return tuple(self._overlays.values())

    def overlay_count(self) -> int:
        """Return the number of registered Overlays."""
        return len(self._overlays)

    def clear(self) -> None:
        """Remove all registered Overlays.

        The Overlay objects themselves are not destroyed; only the
        manager's references to them are dropped.
        """
        self._overlays.clear()

    # ----- Repositioning --------------------------------------------

    def reposition_all(self, regions: tuple[Region, ...]) -> None:
        """Reposition every registered Overlay according to the Regions.

        For each registered Overlay, this method looks up the Region
        whose ``semantic_role`` matches the Overlay's
        ``target_region``. If such a Region exists, the Overlay is
        repositioned with that Region's Bounds. If no Region matches,
        the Overlay is left untouched.

        The method is a no-op when no Overlays are registered. It
        does not raise if Regions are missing for some Overlays;
        missing targets are a legitimate state during a module
        switch, before the next layout has been computed.

        If two Regions share the same ``semantic_role`` (a
        pathological case that should not occur in practice), the
        first one encountered wins.
        """
        # Build a fast lookup: Placement -> Region.
        # The first Region seen for a given Placement wins, so we
        # explicitly skip assignments that would overwrite an
        # existing entry.
        region_by_placement: dict[Placement, Region] = {}
        for region in regions:
            role = region.semantic_role
            if role is None:
                continue
            if role not in region_by_placement:
                region_by_placement[role] = region

        for overlay in self._overlays.values():
            target = region_by_placement.get(overlay.target_region)
            if target is None:
                continue
            overlay.reposition(target.bounds)

    # ----- Representation -------------------------------------------

    def __repr__(self) -> str:
        return f"OverlayManager(overlays={list(self._overlays.keys())!r})"
