"""CommunitySidebar — the left vertical panel of the Home Page.

Displays five community-related actions. Each emits a signal; the
HomePage re-emits it; the MainWindow opens the appropriate URL or
dialog.

The sidebar is intentionally non-collapsible in this piece. The
prototype shows it always visible. A toggle can be added in a later
piece if users need the horizontal space.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class CommunitySidebar(QWidget):
    """Left vertical panel with community-related actions."""

    community_requested = Signal()
    library_requested = Signal()
    news_requested = Signal()
    feedback_requested = Signal()
    contribute_requested = Signal()

    _ITEMS: tuple[tuple[str, str], ...] = (
        ("Comunidade", "community"),
        ("Biblioteca de objetos", "library"),
        ("Novidades", "news"),
        ("Sugerir melhorias", "feedback"),
        ("Contribuir", "contribute"),
    )

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("home_page.community_sidebar")
        self.setFixedWidth(200)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(2)

        self._buttons: dict[str, QPushButton] = {}
        for label, key in self._ITEMS:
            button = QPushButton(label)
            button.setObjectName(f"home_page.community_sidebar.{key}")
            button.setFlat(True)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setStyleSheet("text-align: left; padding: 6px 8px;")
            layout.addWidget(button)
            self._buttons[key] = button

        self._buttons["community"].clicked.connect(self.community_requested)
        self._buttons["library"].clicked.connect(self.library_requested)
        self._buttons["news"].clicked.connect(self.news_requested)
        self._buttons["feedback"].clicked.connect(self.feedback_requested)
        self._buttons["contribute"].clicked.connect(self.contribute_requested)

        layout.addStretch(1)

    # ----- Convenience for tests -------------------------------------

    def button_for(self, key: str) -> QPushButton:
        """Return the button with the given key (used by tests)."""
        return self._buttons[key]
