"""Static drag affordance for reorderable lists."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QToolButton, QWidget

from cranioz.ui.icons.provider import IconProvider
from cranioz.ui.icons.state import IconState


class DragHandle(QToolButton):
    """Static drag affordance.

    Signals:
        drag_started: emitted on press. Parent widgets own the actual drag.
    """

    drag_started = Signal()

    def __init__(
        self,
        icon_provider: IconProvider | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._icons = icon_provider
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.setAutoRaise(True)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setFixedWidth(18)
        self.setAccessibleName(self.tr("Drag to reorder"))

        if icon_provider is not None:
            self.setIcon(icon_provider.icon("drag", state=IconState.DEFAULT))
            if self.icon().isNull():
                self.setText(icon_provider.text_glyph("drag") or "⋮⋮")
        else:
            self.setText("⋮⋮")

        self.pressed.connect(self.drag_started)
