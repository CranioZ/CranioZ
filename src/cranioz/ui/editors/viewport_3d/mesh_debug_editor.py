# src/cranioz/ui/editors/viewport_3d/mesh_debug_editor.py

"""MeshDebugEditor — minimal Editor that hosts a single Viewport3DView.
...
"""

from __future__ import annotations

from PySide6.QtWidgets import QWidget

from cranioz.ui.editors.base_editor import Editor
from cranioz.ui.editors.view import View
from cranioz.ui.editors.viewport_3d.view import Viewport3DView

MESH_DEBUG_EDITOR_ID = "editor.mesh_debug"


class MeshDebugEditor(Editor):
    """Editor hosting a single ``Viewport3DView`` for STL validation."""

    def __init__(
        self,
        editor_id: str = MESH_DEBUG_EDITOR_ID,
        title: str = "Mesh Debug",
    ) -> None:
        super().__init__(editor_id=editor_id, title=title)
        self._viewport: Viewport3DView | None = None

    def _ensure_viewport(self) -> Viewport3DView:
        """Create the viewport lazily if it does not exist."""
        if self._viewport is None:
            self._viewport = Viewport3DView(view_id="view.mesh_debug.3d")
        return self._viewport

    # ----- Views (ADR-0013) -----------------------------------------

    def views(self) -> tuple[View, ...]:
        return (self._ensure_viewport(),)

    # ----- Content ---------------------------------------------------

    def content_widget(self) -> QWidget:
        return self._ensure_viewport().content_widget()

    # ----- Lifecycle -------------------------------------------------

    def dispose(self) -> None:
        # Dispose the current viewport, if any, without destroying
        # the Editor's ability to recreate one.
        if self._viewport is not None:
            self._viewport.dispose()
            self._viewport = None
