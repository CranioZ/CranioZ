"""Viewport3DView — a 3D view of the Scene.

For the first version, this View renders a placeholder QLabel.
The real VTK integration (QVTKRenderWindowInteractor with a
functional RenderWindow) will be implemented in a later piece.

This placeholder allows the layout (grid 2x2, Toolbars, split
tree) to be validated without VTK's resize artifacts.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QWidget

from cranioz.ui.editors.view import View


class Viewport3DView(View):
    """A 3D view of the Scene (placeholder)."""

    def __init__(self, view_id: str = "view.viewport_3d") -> None:
        super().__init__(view_id=view_id, view_type="3d")
        self._content: QWidget | None = None

    def content_widget(self) -> QWidget:
        if self._content is None:
            self._content = QLabel(
                f"Viewport 3D\n{self.view_id}\n\n"
                "(Placeholder — VTK 3D will be implemented in a later piece)"
            )
            self._content.setObjectName(f"viewport_3d.view.{self.view_id}")
            self._content.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._content.setStyleSheet(
                "QLabel { background-color: #2a2a2a; color: #eee; font-size: 14px; padding: 24px; }"
            )
        return self._content

    def dispose(self) -> None:
        if self._content is not None:
            self._content.setParent(None)
            self._content.deleteLater()
            self._content = None
