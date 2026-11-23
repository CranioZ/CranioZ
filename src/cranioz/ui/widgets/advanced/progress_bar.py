"""QProgressBar wrapper with indeterminate support."""

from __future__ import annotations

from PySide6.QtWidgets import QProgressBar, QWidget


class ProgressBar(QProgressBar):
    """Standard QProgressBar with an explicit indeterminate mode."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setTextVisible(True)

    @property
    def indeterminate(self) -> bool:
        return self.minimum() == 0 and self.maximum() == 0

    def set_indeterminate(self, value: bool) -> None:
        if value:
            self.setRange(0, 0)
        else:
            self.setRange(0, 100)
