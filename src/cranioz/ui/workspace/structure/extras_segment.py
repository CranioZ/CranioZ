"""ExtrasSegment — the right zone of the Workspace Top Bar.

Three buttons, left to right:

- ``⋮`` (three dots): a ``QMenu`` with application-level actions
  (Configurações, Temas, Ajuda, Atualizações, Sobre).
- Two panel-toggle glyphs: toggle Area Bottom and toggle Area Right.

The menu is auto-contained: the items are fixed and independent of
context. Each item emits a dedicated signal. The segment does not
know the application; the MainWindow connects the signals to its
existing handlers (or placeholders, until the corresponding phases
deliver real implementations).

The glyphs are textual placeholders. A future piece will replace them
with ``ThemeService.icon_name(...)`` when the icon loader exists.
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


class ExtrasSegment(QWidget):
    """Right zone of the Workspace Top Bar."""

    settings_requested = Signal()
    themes_requested = Signal()
    help_requested = Signal()
    updates_requested = Signal()
    about_requested = Signal()
    toggle_area_bottom_requested = Signal()
    toggle_area_right_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("workspace.top_bar.extras_segment")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self._menu_button = self._make_button(
            "⋮",
            "workspace.top_bar.extras_segment.menu",
            tr("workspace.top_bar.extras", "Extras"),
        )
        self._build_menu()
        self._menu_button.clicked.connect(self._on_menu_button_clicked)

        self._toggle_bottom_button = self._make_button(
            "▭",
            "workspace.top_bar.extras_segment.toggle_bottom",
            tr("workspace.top_bar.toggle_area_bottom", "Toggle Area Bottom"),
        )
        self._toggle_bottom_button.clicked.connect(self.toggle_area_bottom_requested)

        self._toggle_right_button = self._make_button(
            "▯",
            "workspace.top_bar.extras_segment.toggle_right",
            tr("workspace.top_bar.toggle_area_right", "Toggle Area Right"),
        )
        self._toggle_right_button.clicked.connect(self.toggle_area_right_requested)

        layout.addWidget(self._menu_button)
        layout.addWidget(self._toggle_bottom_button)
        layout.addWidget(self._toggle_right_button)

    # ----- Internals ------------------------------------------------

    def _make_button(self, glyph: str, object_name: str, tooltip: str) -> QPushButton:
        button = QPushButton(glyph, self)
        button.setObjectName(object_name)
        button.setFlat(True)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setToolTip(tooltip)
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
