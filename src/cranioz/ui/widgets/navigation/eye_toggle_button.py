"""Checkable eye icon used to toggle tab visibility (Tela 7)."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QToolButton, QWidget

from cranioz.ui.icons.provider import IconProvider
from cranioz.ui.icons.state import IconState


class EyeToggleButton(QToolButton):
    """Visibility toggle.

    Uses an injected IconProvider (eye-open / eye-closed). Falls back to
    text glyphs when the provider has no icon for the requested name.

    Signals:
        visibility_changed(bool): emitted after toggled(bool).
    """

    visibility_changed = Signal(bool)

    def __init__(
        self,
        icon_provider: IconProvider,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._icons = icon_provider
        self.setCheckable(True)
        self.setChecked(True)
        self.setAutoRaise(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._refresh()
        self.toggled.connect(self._on_toggled)

    def _icon_name(self) -> str:
        return "eye-open" if self.isChecked() else "eye-closed"

    def _refresh(self) -> None:
        name = self._icon_name()
        self.setIcon(self._icons.icon(name, state=IconState.DEFAULT))
        self.setText("")
        if self.icon().isNull():
            # Fallback to a text glyph if the provider has no icon.
            self.setText(self._icons.text_glyph(name) or "•")
        self.setAccessibleName(self.tr("Visible") if self.isChecked() else self.tr("Hidden"))

    def _on_toggled(self, checked: bool) -> None:
        self._refresh()
        self.visibility_changed.emit(checked)
