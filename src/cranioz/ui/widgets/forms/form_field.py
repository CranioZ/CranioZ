"""FormField: labeled text input composite widget."""

from __future__ import annotations

from PySide6.QtCore import QEvent, Signal
from PySide6.QtWidgets import QLabel, QLineEdit, QVBoxLayout, QWidget


class FormField(QWidget):
    """A label + QLineEdit composition with a high-level public API.

    Consumers interact through ``label``, ``text``, ``placeholder``,
    ``read_only`` and the ``text_changed`` / ``editing_finished`` signals.
    The internal QLineEdit is an implementation detail.
    """

    text_changed = Signal(str)
    editing_finished = Signal(str)

    def __init__(self, label: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._label = QLabel(label, self)
        self._label.setObjectName("CraniozFormFieldLabel")

        self._line_edit = QLineEdit(self)
        self._line_edit.setObjectName("CraniozFormFieldInput")
        self._line_edit.textChanged.connect(self.text_changed)
        self._line_edit.editingFinished.connect(self._on_editing_finished)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        layout.addWidget(self._label)
        layout.addWidget(self._line_edit)

        self.setAccessibleName(label or "Text field")

    # ---- internals ---------------------------------------------------
    def _on_editing_finished(self) -> None:
        self.editing_finished.emit(self._line_edit.text())

    # ---- properties --------------------------------------------------
    @property
    def label(self) -> str:
        return self._label.text()

    @label.setter
    def label(self, value: str) -> None:
        self._label.setText(value)
        self.setAccessibleName(value or "Text field")

    @property
    def text(self) -> str:
        return self._line_edit.text()

    @text.setter
    def text(self, value: str) -> None:
        self._line_edit.setText(value)

    @property
    def placeholder(self) -> str:
        return self._line_edit.placeholderText()

    @placeholder.setter
    def placeholder(self, value: str) -> None:
        self._line_edit.setPlaceholderText(value)

    @property
    def read_only(self) -> bool:
        return self._line_edit.isReadOnly()

    @read_only.setter
    def read_only(self, value: bool) -> None:
        self._line_edit.setReadOnly(value)

    # ---- public methods ---------------------------------------------
    def set_label(self, text: str) -> None:
        self.label = text

    def set_text(self, text: str) -> None:
        self.text = text

    def clear(self) -> None:
        self._line_edit.clear()

    def set_validity(self, valid: bool, reason: str = "") -> None:
        """Apply visual validity feedback and set accessible description."""
        state = "valid" if valid else "invalid"
        self._line_edit.setProperty("validity", state)
        style = self._line_edit.style()
        if style is not None:
            style.unpolish(self._line_edit)
            style.polish(self._line_edit)
        self.setAccessibleDescription(reason if not valid else "")

    # ---- i18n --------------------------------------------------------
    def changeEvent(self, event: QEvent) -> None:  # noqa: N802
        if event.type() == QEvent.Type.LanguageChange:
            self.setAccessibleName(self._label.text() or "Text field")
        super().changeEvent(event)
