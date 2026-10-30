"""SceneBridge — synchronizes Scene events with the VTK renderer.

The bridge subscribes to Scene events (ObjectAdded, ObjectRemoved,
ObjectTransformed) and calls the VTKSceneRenderer's refresh().

See scene.md §26, §51.
"""

from __future__ import annotations

from cranioz.application.event_bus import EventBus
from cranioz.domain.scene.scene import Scene
from cranioz.infrastructure.rendering.vtk_scene_renderer import (
    VTKSceneRenderer,
)


class SceneBridge:
    """Synchronizes Scene events with the VTK renderer."""

    def __init__(
        self,
        renderer: VTKSceneRenderer,
        event_bus: EventBus,
    ) -> None:
        self._renderer = renderer
        self._event_bus = event_bus
        # Future: subscribe to Scene events (ObjectAdded, etc.)
        # For now, the renderer's refresh() is called manually.

    def attach_scene(self, scene: Scene) -> None:
        self._renderer.attach_scene(scene)

    def detach_scene(self) -> None:
        self._renderer.detach_scene()

    def refresh(self) -> None:
        self._renderer.refresh()
