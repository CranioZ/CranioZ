"""Vertical icon navigation bar."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QButtonGroup, QToolButton, QVBoxLayout, QWidget

from cranioz.ui.icons.provider import IconProvider
from cranioz.ui.icons.state import IconState


class IconSidebar(QWidget):
    """Vertical navigation bar with mutually exclusive icon items.

    Signals:
        item_selected(str): emitted when the user selects an item.
    """

    item_selected = Signal(str)

    def __init__(
        self,
        icon_provider: IconProvider | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._icons = icon_provider
        self._buttons: dict[str, QToolButton] = {}
        self._icon_names: dict[str, str] = {}
        self._active_key: str | None = None

        self._button_group = QButtonGroup(self)
        self._button_group.setExclusive(True)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(6)
        self._layout.addStretch(1)
        self.setAccessibleName(self.tr("Navigation sidebar"))

    def add_item(self, key: str, icon_name: str, tooltip: str) -> None:
        if not key:
            raise ValueError("navigation item key must not be empty")
        if key in self._buttons:
            raise ValueError(f"duplicate navigation item key: {key!r}")

        button = QToolButton(self)
        button.setObjectName("CraniozIconSidebarItem")
        button.setProperty("class", "secondary")
        button.setCheckable(True)
        button.setAutoRaise(True)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setToolTip(tooltip)
        button.setAccessibleName(tooltip or key)
        button.clicked.connect(
            lambda checked=False, item_key=key: self._on_button_clicked(
                item_key,
                checked,
            )
        )

        self._buttons[key] = button
        self._icon_names[key] = icon_name
        self._button_group.addButton(button)
        self._layout.insertWidget(
            len(self._buttons) - 1,
            button,
            alignment=Qt.AlignmentFlag.AlignHCenter,
        )
        self._refresh_button(key)

    def set_active(self, key: str) -> None:
        button = self._buttons[key]
        self._active_key = key
        button.setChecked(True)
        for item_key in self._buttons:
            self._refresh_button(item_key)

    def active_key(self) -> str | None:
        return self._active_key

    def refresh_icons(self) -> None:
        """Re-request every icon from the provider."""
        for key in self._buttons:
            self._refresh_button(key)

    def _on_button_clicked(self, key: str, checked: bool = False) -> None:
        if not checked:
            return
        self._active_key = key
        for item_key in self._buttons:
            self._refresh_button(item_key)
        self.item_selected.emit(key)

    def _refresh_button(self, key: str) -> None:
        button = self._buttons[key]
        icon_name = self._icon_names[key]
        state = IconState.SELECTED if self._active_key == key else IconState.DEFAULT
        if self._icons is not None:
            button.setIcon(self._icons.icon(icon_name, state=state))
        button.setText("")
        if button.icon().isNull():
            fallback = self._icons.text_glyph(icon_name) if self._icons else "?"
            button.setText(fallback or "?")
