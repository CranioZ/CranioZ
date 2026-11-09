"""StartButton — the "start planning" floating action button.

The button is a fixed-size circle, positioned by the parent HomePage
in the bottom-right corner. It is disabled (grey) until the user has
selected both a project and a flow. When both are selected, it becomes
green and enabled.

The button does not know about project_id or flow_id. It only emits
`start_requested()` when clicked. The HomePage owns the state and
emits the full `project_open_requested(project_id, flow_id)` signal.

Styling is owned by the global QSS emitted by ``ThemeCompiler``. The
button only toggles its ``state`` property (``enabled`` / ``disabled``)
and repolishes itself; it never calls ``setStyleSheet``.

The icon is resolved via ``IconProvider``. The state color is handled
by the QSS rule keyed on the ``state`` property; the icon itself uses
``IconState.DEFAULT`` because the QSS provides the visual state.

The objectName uses underscores, not dots. Qt Style Sheets treat "."
as a class separator; a QSS selector ``#home_page.start_button``
would not match an objectName of ``"home_page.start_button"``. The
underscore form matches literally. See the QSS documentation on
selector syntax.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QPushButton, QWidget

from cranioz.infrastructure.i18n import tr
from cranioz.ui.icons.provider import IconProvider


class StartButton(QPushButton):
    """Floating circular button for starting a planning session."""

    start_requested = Signal()

    def __init__(
        self,
        icon_provider: IconProvider,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("home_page_start_button")
        self.setFixedSize(56, 56)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAccessibleName(tr("homepage.start_button.label", "Start"))
        self.setEnabled(False)
        self.setIcon(icon_provider.icon("start"))
        self.setProperty("state", "disabled")
        self._repolish()
        self.clicked.connect(self.start_requested)

    def set_ready(self, ready: bool) -> None:
        """Enable (green) or disable (grey) the button."""
        self.setEnabled(ready)
        self.setProperty("state", "enabled" if ready else "disabled")
        self._repolish()

    def is_ready(self) -> bool:
        """Return True if the button is currently enabled."""
        return self.isEnabled()

    def _repolish(self) -> None:
        """Re-evaluate the stylesheet after a dynamic property changed."""
        style = self.style()
        if style is not None:
            style.unpolish(self)
            style.polish(self)
