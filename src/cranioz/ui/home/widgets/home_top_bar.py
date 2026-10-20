"""HomeTopBar — the top bar of the Home Page.

Displays the menu icon, the application title, and the help/settings
icons. Every control emits a signal; nothing here executes an
operation.

The ☰ button toggles the CommunitySidebar. It does not emit a
generic "menu requested"; the sidebar is the only thing it
controls. A future application menu (if any) will be a separate
control.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QWidget,
)


class HomeTopBar(QWidget):
    """Top bar of the Home Page."""

    FIXED_HEIGHT: int = 48

    toggle_sidebar_requested = Signal()
    help_requested = Signal()
    settings_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("home_page.top_bar")
        self.setFixedHeight(self.FIXED_HEIGHT)

        self._menu_button = QPushButton("☰")
        self._menu_button.setObjectName("home_page.top_bar.menu")
        self._menu_button.setFlat(True)
        self._menu_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._menu_button.clicked.connect(self.toggle_sidebar_requested)

        self._title = QLabel("CranioZ")
        self._title.setObjectName("home_page.top_bar.title")
        title_font = self._title.font()
        title_font.setPointSize(14)
        title_font.setBold(True)
        self._title.setFont(title_font)

        self._help_button = QPushButton("?")
        self._help_button.setObjectName("home_page.top_bar.help")
        self._help_button.setFlat(True)
        self._help_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._help_button.setFixedWidth(32)
        self._help_button.clicked.connect(self.help_requested)

        self._settings_button = QPushButton("⚙")
        self._settings_button.setObjectName("home_page.top_bar.settings")
        self._settings_button.setFlat(True)
        self._settings_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._settings_button.setFixedWidth(32)
        self._settings_button.clicked.connect(self.settings_requested)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(6)
        layout.addWidget(self._menu_button)
        layout.addWidget(self._title)
        layout.addStretch(1)
        layout.addWidget(self._help_button)
        layout.addWidget(self._settings_button)
