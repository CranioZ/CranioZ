"""StartButton — the "start planning" floating action button.

The button is a fixed-size circle, positioned by the parent HomePage
in the bottom-right corner. It is disabled (grey) until the user has
selected both a project and a flow. When both are selected, it becomes
green and enabled.

The button does not know about project_id or flow_id. It only emits
`start_requested()` when clicked. The HomePage owns the state and
emits the full `project_open_requested(project_id, flow_id)` signal.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QPushButton, QWidget

# Colors are inline for the first piece. When the ThemeService gains
# semantic colors (ADR-0003 §2.4: color("primary"), color("disabled")),
# replace these with service lookups.
_GREY = "#9e9e9e"
_GREEN = "#2ecc71"
_WHITE = "#ffffff"


class StartButton(QPushButton):
    """Floating circular button for starting a planning session."""

    start_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("home_page.start_button")
        self.setFixedSize(56, 56)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setEnabled(False)
        self._apply_style(enabled=False)
        self.clicked.connect(self.start_requested)

    def set_ready(self, ready: bool) -> None:
        """Enable (green) or disable (grey) the button."""
        self.setEnabled(ready)
        self._apply_style(enabled=ready)

    def is_ready(self) -> bool:
        """Return True if the button is currently enabled."""
        return self.isEnabled()

    def _apply_style(self, *, enabled: bool) -> None:
        color = _GREEN if enabled else _GREY
        self.setStyleSheet(
            f"QPushButton#home_page.start_button {{"
            f"  background-color: {color};"
            f"  color: {_WHITE};"
            f"  border: none;"
            f"  border-radius: 28px;"
            f"  font-size: 22px;"
            f"  font-weight: bold;"
            f"}}"
        )
        self.setText("→")
