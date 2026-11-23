"""FormCombo: labeled combo box composite widget."""

from __future__ import annotations

from collections.abc import Sequence

from PySide6.QtCore import QEvent, Signal
from PySide6.QtWidgets import QComboBox, QLabel, QVBoxLayout, QWidget


class FormCombo(QWidget):
    """A label + QComboBox composition; emits itemData on selection change.

    Consumers interact through ``label``, ``current_index``, ``current_value``,
    the ``add_item`` / ``add_items`` / ``set_current_by_value`` methods and the
    ``current_changed`` signal. The internal QComboBox is an implementation
    detail.
    """

    current_changed = Signal(object)

    def __init__(self, label: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._label = QLabel(label, self)
        self._label.setObjectName("CraniozFormComboLabel")

        self._combo = QComboBox(self)
        self._combo.setObjectName("CraniozFormComboInput")
        self._combo.currentIndexChanged.connect(self._emit_current)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        layout.addWidget(self._label)
        layout.addWidget(self._combo)

        self.setAccessibleName(label or "Selection field")

    # ---- internals ---------------------------------------------------
    def _emit_current(self, _index: int) -> None:
        self.current_changed.emit(self.current_value)

    # ---- properties --------------------------------------------------
    @property
    def label(self) -> str:
        return self._label.text()

    @label.setter
    def label(self, value: str) -> None:
        self._label.setText(value)
        self.setAccessibleName(value or "Selection field")

    @property
    def current_index(self) -> int:
        return self._combo.currentIndex()

    @current_index.setter
    def current_index(self, value: int) -> None:
        self._combo.setCurrentIndex(value)

    @property
    def current_value(self) -> object:
        return self._combo.currentData()

    # ---- public methods ---------------------------------------------
    def add_item(self, text: str, value: object = None) -> None:
        self._combo.addItem(text, value)

    def add_items(self, items: Sequence[tuple[str, object]]) -> None:
        for text, value in items:
            self._combo.addItem(text, value)

    def clear_items(self) -> None:
        self._combo.clear()

    def set_current_by_value(self, value: object) -> bool:
        idx = self._combo.findData(value)
        if idx < 0:
            return False
        self._combo.setCurrentIndex(idx)
        return True

    def set_validity(self, valid: bool, reason: str = "") -> None:
        state = "valid" if valid else "invalid"
        self._combo.setProperty("validity", state)
        style = self._combo.style()
        if style is not None:
            style.unpolish(self._combo)
            style.polish(self._combo)
        self.setAccessibleDescription(reason if not valid else "")

    # ---- i18n --------------------------------------------------------
    def changeEvent(self, event: QEvent) -> None:  # noqa: N802
        if event.type() == QEvent.Type.LanguageChange:
            self.setAccessibleName(self._label.text() or "Selection field")
        super().changeEvent(event)
