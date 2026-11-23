"""Generic visible/hidden checkbox."""

from __future__ import annotations

from PySide6.QtWidgets import QCheckBox, QWidget


class VisibilityToggle(QCheckBox):
    """Generic 'visible / hidden' semantic control."""

    def __init__(self, text: str = "", parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setChecked(True)
        self.setAccessibleName(text or self.tr("Visible"))
