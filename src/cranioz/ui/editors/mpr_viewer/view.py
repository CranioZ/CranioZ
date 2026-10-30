"""MPRView — a 2D MPR view (axial, coronal, or sagittal).

This is a View, not an Editor. It is hosted by an Editor (e.g.,
TomographyEditor) that coordinates it with other Views.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QWidget

from cranioz.ui.editors.view import View


class MPRView(View):
    """A 2D MPR view."""

    def __init__(
        self,
        view_id: str = "view.mpr_axial",
        view_type: str = "axial",
    ) -> None:
        super().__init__(view_id=view_id, view_type=view_type)
        self._content: QWidget | None = None

    def content_widget(self) -> QWidget:
        if self._content is None:
            self._content = QLabel(
                f"MPR {self.view_type.title()}\n{self.view_id}\n\n"
                "(Placeholder — VTK MPR will be implemented next)"
            )
            self._content.setObjectName(f"mpr.view.{self.view_id}")
            self._content.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._content.setStyleSheet(
                "QLabel { background-color: #2a2a2a; color: #eee; font-size: 14px; padding: 24px; }"
            )
        return self._content
