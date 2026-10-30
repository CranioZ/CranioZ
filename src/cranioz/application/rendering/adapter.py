"""RenderingAdapter — bridge between the Scene and the renderer.

The RenderingAdapter is an Application-layer port. The concrete
implementation (VTK) lives in infrastructure/rendering/.

The adapter observes Scene events (via EventBus) and updates the
rendering representation. It is the ONLY component that knows how
to translate domain objects into renderable representations.

See scene.md §26, ADR-0008 §2.4.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from cranioz.domain.scene.scene import Scene


@runtime_checkable
class RenderingAdapter(Protocol):
    """Bridge between the Scene and the renderer.

    The adapter does NOT own the Scene. It observes it and produces
    rendering representations.
    """

    def attach_scene(self, scene: Scene) -> None:
        """Attach the adapter to a Scene (or replace the current one)."""
        ...

    def detach_scene(self) -> None:
        """Detach from the current Scene."""
        ...

    def refresh(self) -> None:
        """Re-sync the rendering representation with the Scene."""
        ...
