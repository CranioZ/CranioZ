"""Labeled date input.

Wraps QDateEdit with a label. Default format dd/MM/yyyy, locale-aware.
Mirrors the layout used in Tela 2 ("Formato da data").
"""

from __future__ import annotations

from PySide6.QtCore import QDate, Signal
from PySide6.QtWidgets import QDateEdit, QHBoxLayout, QLabel, QWidget


class DateField(QWidget):
    """Labeled date input.

    Signals:
        date_changed(QDate): emitted when the user changes the date.
    """

    date_changed = Signal(QDate)

    def __init__(
        self,
        label: str = "",
        date: QDate | None = None,
        date_format: str = "dd/MM/yyyy",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._date_format = date_format

        self._label = QLabel(label, self)
        self._edit = QDateEdit(self)
        self._edit.setCalendarPopup(True)
        self._edit.setDisplayFormat(date_format)
        self._edit.setDate(date if date is not None else QDate.currentDate())
        self._edit.dateChanged.connect(self.date_changed)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        layout.addWidget(self._label)
        layout.addWidget(self._edit, 1)

        self.setAccessibleName(label)

    # ----- public API -----
    def label(self) -> str:
        return self._label.text()

    def set_label(self, text: str) -> None:
        self._label.setText(text)
        self.setAccessibleName(text)

    def date(self) -> QDate:
        return self._edit.date()

    def set_date(self, value: QDate) -> None:
        self._edit.setDate(value)

    @property
    def date_format(self) -> str:
        return self._date_format

    def set_date_format(self, fmt: str) -> None:
        self._date_format = fmt
        self._edit.setDisplayFormat(fmt)
