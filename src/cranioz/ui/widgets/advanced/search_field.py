"""Search input with leading glyph and trailing clear action."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLineEdit, QToolButton, QWidget

from cranioz.ui.icons.provider import IconProvider
from cranioz.ui.icons.state import IconState


class SearchField(QWidget):
    """Search composite.

    Signals:
        search_requested(str): emitted on Enter or search button click.
        text_changed(str): emitted on every keystroke.
    """

    search_requested = Signal(str)
    text_changed = Signal(str)

    def __init__(
        self,
        icon_provider: IconProvider,
        placeholder: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._icons = icon_provider

        self._edit = QLineEdit(self)
        self._edit.setPlaceholderText(placeholder)
        self._edit.setClearButtonEnabled(False)
        self._edit.returnPressed.connect(self._emit_search)
        self._edit.textChanged.connect(self.text_changed)

        self._search_btn = self._make_button("search")
        self._search_btn.clicked.connect(self._emit_search)

        self._clear_btn = self._make_button("clear")
        self._clear_btn.clicked.connect(self.clear)
        self._clear_btn.setVisible(False)

        # Connect only after _clear_btn exists; mypy then knows its type.
        self._edit.textChanged.connect(lambda t: self._clear_btn.setVisible(bool(t)))

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        layout.addWidget(self._search_btn)
        layout.addWidget(self._edit, 1)
        layout.addWidget(self._clear_btn)

        self.setAccessibleName(placeholder or self.tr("Search"))

    def _make_button(self, icon_name: str) -> QToolButton:
        btn = QToolButton(self)
        btn.setAutoRaise(True)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setIcon(self._icons.icon(icon_name, state=IconState.DEFAULT))
        if btn.icon().isNull():
            btn.setText(self._icons.text_glyph(icon_name) or "?")
        return btn

    def _emit_search(self) -> None:
        self.search_requested.emit(self._edit.text())

    # ----- public API -----
    def text(self) -> str:
        return self._edit.text()

    def set_text(self, value: str) -> None:
        self._edit.setText(value)

    def clear(self) -> None:
        self._edit.clear()
