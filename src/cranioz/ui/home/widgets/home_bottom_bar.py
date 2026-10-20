"""HomeBottomBar — the bottom bar of the Home Page.

A horizontal bar at the bottom of the Home Page's right column. It
contains the StartButton, aligned to the right.

Why a bar and not a floating button:

The StartButton marks the commit of a planning session ("I have
selected a project and a flow; take me to the Workspace"). Placing it
as a floating FAB over the FlowList covered the content and made the
button feel like a layer, not a step. Making it the fourth horizontal
bar of the right column — below TopBar, ProjectTable and FlowList —
keeps the layout symmetric (top bar + bottom bar), and gives the
StartButton a dedicated, non-overlapping region.

Layout:
    ┌────────────┬──────────────────────┐
    │            │ HomeTopBar           │
    │ Community  ├──────────────────────┤
    │ Sidebar    │ ProjectTable         │
    │            ├──────────────────────┤
    │            │ FlowList             │
    │            ├──────────────────────┤
    │            │ HomeBottomBar [→]    │
    └────────────┴──────────────────────┘
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QWidget,
)

from cranioz.ui.home.widgets.start_button import StartButton


class HomeBottomBar(QWidget):
    """Bottom bar of the Home Page, hosting the StartButton."""

    MINIMUM_HEIGHT: int = 56

    def __init__(
        self,
        start_button: StartButton,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("home_page.bottom_bar")
        self.setMinimumHeight(self.MINIMUM_HEIGHT)
        self._start_button = start_button
        # addWidget reparents the button and positions it; do NOT
        # call setParent manually (that would fight the layout).

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(0)
        layout.addStretch(1)
        layout.addWidget(self._start_button, alignment=Qt.AlignmentFlag.AlignRight)

    # ----- Convenience ----------------------------------------------

    def start_button(self) -> StartButton:
        """Return the hosted StartButton (used by tests and the HomePage)."""
        return self._start_button
