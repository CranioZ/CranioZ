"""Horizontal form container for arbitrary child widgets."""

from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QWidget


class FormRow(QWidget):
    """Horizontal form container used for two-column layouts in Tela 2."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(8)
        self._fields: list[QWidget] = []

    def add_field(self, widget: QWidget, stretch: int = 1) -> None:
        self._fields.append(widget)
        self._layout.addWidget(widget, stretch)

    def fields(self) -> list[QWidget]:
        return list(self._fields)

    def set_spacing(self, px: int) -> None:
        self._layout.setSpacing(px)
