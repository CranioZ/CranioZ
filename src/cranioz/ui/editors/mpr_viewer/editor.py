"""MPRViewerEditor — 2D MPR viewer.

The editor displays axial, sagittal, or coronal slices of a Volume.
For the first version, it displays a placeholder label. A future
version will use VTK's vtkResliceImageViewer.

See editors.md §12, scene.md §50.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QWidget

from cranioz.ui.editors.base_editor import Editor
from cranioz.ui.editors.editor_context import EditorContext


class MPRViewerEditor(Editor):
    """2D MPR viewer (axial, sagittal, or coronal)."""

    def __init__(
        self,
        editor_id: str = "editor.mpr_axial",
        title: str = "MPR Viewer",
    ) -> None:
        super().__init__(editor_id=editor_id, title=title)
        self._content: QWidget | None = None
        self._context: EditorContext | None = None

    def initialize(self, context: EditorContext) -> None:
        self._context = context

    def content_widget(self) -> QWidget:
        if self._content is None:
            self._content = QLabel(
                f"MPR Viewer\n{self.editor_id}\n\n(Placeholder — VTK MPR will be implemented next)"
            )
            self._content.setObjectName(f"mpr_viewer.content.{self.editor_id}")
            self._content.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._content.setStyleSheet(
                "QLabel { background-color: #2a2a2a; color: #eee; font-size: 14px; padding: 24px; }"
            )
        return self._content
