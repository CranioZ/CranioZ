"""ExtrasSegment — the right zone of the Workspace Top Bar.

Six buttons, left to right:

- ``⋮`` (three dots): a ``QMenu`` with application-level actions
  (Configurações, Temas, Ajuda, Atualizações, Sobre).
- Two panel-toggle glyphs: toggle Area Bottom and toggle Area Right.
- Three window controls: minimize, maximize/restore, close.

The menu is auto-contained: the items are fixed and independent of
context. Each item emits a dedicated signal. The segment does not
know the application; the MainWindow connects the signals to its
existing handlers (or placeholders, until the corresponding phases
deliver real implementations).

The window controls emit dedicated signals too. The ExtrasSegment
does not call ``showMinimized()``, ``showMaximized()``, or
``close()`` itself: those are the MainWindow's responsibility.

The glyphs are resolved via ``IconProvider``.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMenu,
    QPushButton,
    QWidget,
)

from cranioz.infrastructure.i18n import tr
from cranioz.ui.icons.provider import IconProvider


class ExtrasSegment(QWidget):
    """Right zone of the Workspace Top Bar."""

    settings_requested = Signal()
    themes_requested = Signal()
    help_requested = Signal()
    updates_requested = Signal()
    about_requested = Signal()
    toggle_area_bottom_requested = Signal()
    toggle_area_right_requested = Signal()

    # Window controls (Block 5.6). The MainWindow decides what to do:
    # showMinimized(), showMaximized()/showNormal(), close().
    minimize_requested = Signal()
    maximize_requested = Signal()
    close_requested = Signal()

    def __init__(
        self,
        icon_provider: IconProvider,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._icon_provider = icon_provider
        self.setObjectName("workspace.top_bar.extras_segment")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # ----- Extras (menu + area toggles) -----
        self._menu_button = self._make_button(
            icon_name="menu",
            object_name="workspace.top_bar.extras_segment.menu",
            tooltip=tr("workspace.top_bar.extras", "Extras"),
        )
        self._build_menu()
        self._menu_button.clicked.connect(self._on_menu_button_clicked)

        self._toggle_bottom_button = self._make_button(
            icon_name="toggle_bottom",
            object_name="workspace.top_bar.extras_segment.toggle_bottom",
            tooltip=tr("workspace.top_bar.toggle_area_bottom", "Toggle Area Bottom"),
        )
        self._toggle_bottom_button.clicked.connect(self.toggle_area_bottom_requested)

        self._toggle_right_button = self._make_button(
            icon_name="toggle_right",
            object_name="workspace.top_bar.extras_segment.toggle_right",
            tooltip=tr("workspace.top_bar.toggle_area_right", "Toggle Area Right"),
        )
        self._toggle_right_button.clicked.connect(self.toggle_area_right_requested)

        # ----- Window controls (Block 5.6) -----
        self._minimize_button = self._make_button(
            icon_name="window_minimize",
            object_name="workspace.top_bar.extras_segment.minimize",
            tooltip=tr("workspace.window.minimize", "Minimize"),
        )
        self._minimize_button.clicked.connect(self.minimize_requested)

        self._maximize_button = self._make_button(
            icon_name="window_maximize",
            object_name="workspace.top_bar.extras_segment.maximize",
            tooltip=tr("workspace.window.maximize", "Maximize"),
        )
        self._maximize_button.clicked.connect(self.maximize_requested)

        self._close_button = self._make_button(
            icon_name="window_close",
            object_name="workspace.top_bar.extras_segment.close",
            tooltip=tr("workspace.window.close", "Close"),
        )
        self._close_button.clicked.connect(self.close_requested)

        layout.addWidget(self._menu_button)
        layout.addWidget(self._toggle_bottom_button)
        layout.addWidget(self._toggle_right_button)
        layout.addWidget(self._minimize_button)
        layout.addWidget(self._maximize_button)
        layout.addWidget(self._close_button)

    # ----- Internals ------------------------------------------------

    def _make_button(
        self,
        icon_name: str,
        object_name: str,
        tooltip: str,
    ) -> QPushButton:
        button = QPushButton(self)
        button.setObjectName(object_name)
        button.setFlat(True)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setIcon(self._icon_provider.icon(icon_name))
        button.setToolTip(tooltip)
        button.setAccessibleName(tooltip)
        button.setFixedWidth(28)
        return button

    def _build_menu(self) -> None:
        self._menu = QMenu(self)
        self._menu.setObjectName("workspace.top_bar.extras_segment.menu.popup")

        self._menu.addAction(
            tr("workspace.top_bar.extras_menu.settings", "Settings")
        ).triggered.connect(self.settings_requested)
        self._menu.addAction(
            tr("workspace.top_bar.extras_menu.themes", "Themes")
        ).triggered.connect(self.themes_requested)
        self._menu.addSeparator()
        self._menu.addAction(tr("workspace.top_bar.extras_menu.help", "Help")).triggered.connect(
            self.help_requested
        )
        self._menu.addAction(
            tr("workspace.top_bar.extras_menu.updates", "Updates")
        ).triggered.connect(self.updates_requested)
        self._menu.addSeparator()
        self._menu.addAction(tr("workspace.top_bar.extras_menu.about", "About")).triggered.connect(
            self.about_requested
        )

    def _on_menu_button_clicked(self) -> None:
        bottom_left = self._menu_button.rect().bottomLeft()
        global_pos = self._menu_button.mapToGlobal(bottom_left)
        self._menu.exec(global_pos)
