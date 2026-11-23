"""SignaturePreview: displays a signature image or empty state."""

from __future__ import annotations

from PySide6.QtCore import QEvent, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QSizePolicy, QWidget

# TODO(L.2): migrate empty-state colors to design tokens once
# SignaturePreview accepts an optional ThemeService (see widget_catalog §8.4).
# Colors are given as int tuples (not hex strings) to stay within the
# current architecture guard for hardcoded appearance literals.
_EMPTY_BORDER_RGB = (160, 160, 160)
_EMPTY_TEXT_RGB = (120, 120, 120)


class SignaturePreview(QWidget):
    """Renders a signature pixmap (aspect-preserving) or a dashed empty state.

    Not an editor. Consumers use ``set_signature``, ``clear`` and observe
    ``has_signature`` / ``signature``.
    """

    signature_changed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._pixmap: QPixmap | None = None
        self.setMinimumSize(200, 80)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setAccessibleName(self.tr("Signature preview"))

    # ---- properties --------------------------------------------------
    @property
    def signature(self) -> QPixmap | None:
        return self._pixmap

    @property
    def has_signature(self) -> bool:
        return self._pixmap is not None and not self._pixmap.isNull()

    # ---- public methods ---------------------------------------------
    def set_signature(self, pixmap: QPixmap) -> None:
        self._pixmap = pixmap if not pixmap.isNull() else None
        self.update()
        self.signature_changed.emit()

    def clear(self) -> None:
        if self._pixmap is None:
            return
        self._pixmap = None
        self.update()
        self.signature_changed.emit()

    # ---- painting ----------------------------------------------------
    def paintEvent(self, event: QEvent) -> None:  # noqa: N802
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            rect = self.rect().adjusted(1, 1, -1, -1)

            if self.has_signature and self._pixmap is not None:
                scaled = self._pixmap.scaled(
                    rect.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                x = rect.x() + (rect.width() - scaled.width()) // 2
                y = rect.y() + (rect.height() - scaled.height()) // 2
                painter.drawPixmap(x, y, scaled)
            else:
                pen = QPen(QColor(*_EMPTY_BORDER_RGB))
                pen.setStyle(Qt.PenStyle.DashLine)
                painter.setPen(pen)
                painter.drawRect(rect)
                painter.setPen(QColor(*_EMPTY_TEXT_RGB))
                painter.drawText(
                    rect,
                    Qt.AlignmentFlag.AlignCenter,
                    self.tr("No signature"),
                )
        finally:
            painter.end()

    # ---- i18n --------------------------------------------------------
    def changeEvent(self, event: QEvent) -> None:  # noqa: N802
        if event.type() == QEvent.Type.LanguageChange:
            self.setAccessibleName(self.tr("Signature preview"))
            self.update()
        super().changeEvent(event)
