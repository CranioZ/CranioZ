"""HomeTopBar — the top bar of the Home Page.

Displays the menu icon, the application title, the help/settings
icons, and the window controls. Every control emits a signal; nothing
here executes an operation.

The ☰ button toggles the CommunitySidebar. It does not emit a
generic "menu requested"; the sidebar is the only thing it
controls. A future application menu (if any) will be a separate
control.

The window controls (minimize, maximize, close) emit dedicated
signals. The HomeTopBar does not call showMinimized(),
showMaximized(), or close() itself: the MainWindow is responsible
(Block 5.6.1).
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QWidget,
)

from cranioz.infrastructure.i18n import tr
from cranioz.ui.icons.provider import IconProvider


class HomeTopBar(QWidget):
    """Top bar of the Home Page."""

    FIXED_HEIGHT: int = 48

    toggle_sidebar_requested = Signal()
    help_requested = Signal()
    settings_requested = Signal()

    # Window controls (Block 5.6.1)
    minimize_requested = Signal()
    maximize_requested = Signal()
    close_requested = Signal()

    def __init__(
        self,
        icon_provider: IconProvider,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("home_page.top_bar")
        self.setFixedHeight(self.FIXED_HEIGHT)

        self._menu_button = QPushButton()
        self._menu_button.setObjectName("home_page.top_bar.menu")
        self._menu_button.setFlat(True)
        self._menu_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._menu_button.setIcon(icon_provider.icon("menu"))
        self._menu_button.setToolTip(tr("homepage.top_bar.menu", "Menu"))
        self._menu_button.setAccessibleName(tr("homepage.top_bar.menu", "Menu"))
        self._menu_button.clicked.connect(self.toggle_sidebar_requested)

        self._title = QLabel(tr("core.app.name", "CranioZ"))
        self._title.setObjectName("home_page.top_bar.title")
        title_font = self._title.font()
        title_font.setPointSize(14)
        title_font.setBold(True)
        self._title.setFont(title_font)

        self._help_button = QPushButton()
        self._help_button.setObjectName("home_page.top_bar.help")
        self._help_button.setFlat(True)
        self._help_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._help_button.setFixedWidth(32)
        self._help_button.setIcon(icon_provider.icon("help"))
        self._help_button.setToolTip(tr("homepage.top_bar.help", "Help"))
        self._help_button.setAccessibleName(tr("homepage.top_bar.help", "Help"))
        self._help_button.clicked.connect(self.help_requested)

        self._settings_button = QPushButton()
        self._settings_button.setObjectName("home_page.top_bar.settings")
        self._settings_button.setFlat(True)
        self._settings_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._settings_button.setFixedWidth(32)
        self._settings_button.setIcon(icon_provider.icon("settings"))
        self._settings_button.setToolTip(tr("homepage.top_bar.settings", "Settings"))
        self._settings_button.setAccessibleName(
            tr("homepage.top_bar.settings", "Settings")
        )
        self._settings_button.clicked.connect(self.settings_requested)

        # Window controls (Block 5.6.1). 28px wide, matching the
        # ExtrasSegment buttons.
        self._minimize_button = self._make_window_button(
            icon_provider,
            icon_name="window_minimize",
            object_name="home_page.top_bar.window_minimize",
            tooltip=tr("workspace.window.minimize", "Minimize"),
        )
        self._minimize_button.clicked.connect(self.minimize_requested)

        self._maximize_button = self._make_window_button(
            icon_provider,
            icon_name="window_maximize",
            object_name="home_page.top_bar.window_maximize",
            tooltip=tr("workspace.window.maximize", "Maximize"),
        )
        self._maximize_button.clicked.connect(self.maximize_requested)

        self._close_button = self._make_window_button(
            icon_provider,
            icon_name="window_close",
            object_name="home_page.top_bar.window_close",
            tooltip=tr("workspace.window.close", "Close"),
        )
        self._close_button.clicked.connect(self.close_requested)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(6)
        layout.addWidget(self._menu_button)
        layout.addWidget(self._title)
        layout.addStretch(1)
        layout.addWidget(self._help_button)
        layout.addWidget(self._settings_button)
        layout.addWidget(self._minimize_button)
        layout.addWidget(self._maximize_button)
        layout.addWidget(self._close_button)

    # ----- Internals ------------------------------------------------

    def _make_window_button(
        self,
        icon_provider: IconProvider,
        icon_name: str,
        object_name: str,
        tooltip: str,
    ) -> QPushButton:
        button = QPushButton(self)
        button.setObjectName(object_name)
        button.setFlat(True)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setFixedWidth(28)
        button.setIcon(icon_provider.icon(icon_name))
        button.setToolTip(tooltip)
        button.setAccessibleName(tooltip)
        return button