"""HomeTopBar — the top bar of the Home Page.

Displays the menu icon, the main_window title, the help/settings
icons, and the window controls. Every control emits a signal; nothing
here executes an operation.

The ☰ button toggles the CommunitySidebar. It does not emit a
generic "menu requested"; the sidebar is the only thing it
controls. A future main_window menu (if any) will be a separate
control.

The window controls (minimize, maximize, close) emit dedicated
signals. The HomeTopBar does not call showMinimized(),
showMaximized(), or close() itself: the MainWindow is responsible
(Block 5.6.1).

Block 5.5 fix: the __init__ was refactored to extract
``_build_menu_button``, ``_build_title``, ``_build_help_button``,
``_build_settings_button``, ``_build_window_controls`` and
``_build_layout``. The original __init__ had 52 statements (Ruff
PLR0915 limit is 50); the extracted methods keep each block small
and the code easier to read. Behavior is unchanged.
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

        self._icon_provider = icon_provider

        # Build the widgets. Each helper returns the widget and
        # wires its signal.
        self._menu_button = self._build_menu_button()
        self._title = self._build_title()
        self._help_button = self._build_help_button()
        self._settings_button = self._build_settings_button()
        (
            self._minimize_button,
            self._maximize_button,
            self._close_button,
        ) = self._build_window_controls()
        self._build_layout()

    # ----- Widget builders -----------------------------------------

    def _build_menu_button(self) -> QPushButton:
        button = QPushButton()
        button.setObjectName("home_page.top_bar.menu")
        button.setFlat(True)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setIcon(self._icon_provider.icon("sidebar_toggle"))
        button.setToolTip(tr("homepage.top_bar.menu", "Menu"))
        button.setAccessibleName(tr("homepage.top_bar.menu", "Menu"))
        button.clicked.connect(self.toggle_sidebar_requested)
        return button

    def _build_title(self) -> QLabel:
        title = QLabel(tr("core.app.name", "CranioZ"))
        title.setObjectName("home_page.top_bar.title")
        font = title.font()
        font.setPointSize(14)
        font.setBold(True)
        title.setFont(font)
        return title

    def _build_help_button(self) -> QPushButton:
        button = QPushButton()
        button.setObjectName("home_page.top_bar.help")
        button.setFlat(True)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setFixedWidth(32)
        button.setIcon(self._icon_provider.icon("help"))
        button.setToolTip(tr("homepage.top_bar.help", "Help"))
        button.setAccessibleName(tr("homepage.top_bar.help", "Help"))
        button.clicked.connect(self.help_requested)
        return button

    def _build_settings_button(self) -> QPushButton:
        button = QPushButton()
        button.setObjectName("home_page.top_bar.settings")
        button.setFlat(True)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setFixedWidth(32)
        button.setIcon(self._icon_provider.icon("settings"))
        button.setToolTip(tr("homepage.top_bar.settings", "Settings"))
        button.setAccessibleName(tr("homepage.top_bar.settings", "Settings"))
        button.clicked.connect(self.settings_requested)
        return button

    def _build_window_controls(self) -> tuple[QPushButton, QPushButton, QPushButton]:
        """Build the minimize, maximize and close buttons."""
        minimize = self._make_window_button(
            icon_name="window_minimize",
            object_name="home_page.top_bar.window_minimize",
            tooltip=tr("workspace.window.minimize", "Minimize"),
        )
        minimize.clicked.connect(self.minimize_requested)

        maximize = self._make_window_button(
            icon_name="window_maximize",
            object_name="home_page.top_bar.window_maximize",
            tooltip=tr("workspace.window.maximize", "Maximize"),
        )
        maximize.clicked.connect(self.maximize_requested)

        close = self._make_window_button(
            icon_name="window_close",
            object_name="home_page.top_bar.window_close",
            tooltip=tr("workspace.window.close", "Close"),
        )
        close.clicked.connect(self.close_requested)

        return minimize, maximize, close

    def _build_layout(self) -> None:
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
        icon_name: str,
        object_name: str,
        tooltip: str,
    ) -> QPushButton:
        button = QPushButton(self)
        button.setObjectName(object_name)
        button.setFlat(True)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setFixedWidth(28)
        button.setIcon(self._icon_provider.icon(icon_name))
        button.setToolTip(tooltip)
        button.setAccessibleName(tooltip)
        return button
