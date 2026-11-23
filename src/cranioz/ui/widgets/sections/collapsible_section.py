"""Expandable section with an optional drag handle."""

from __future__ import annotations

from typing import override

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent, QMouseEvent
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from cranioz.ui.icons.provider import IconProvider
from cranioz.ui.widgets.lists.drag_handle import DragHandle


class _SectionHeader(QWidget):
    """Clickable header shared by the CollapsibleSection implementation."""

    clicked = Signal()

    def __init__(
        self,
        title: str,
        drag_handle: DragHandle,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("CraniozCollapsibleSectionHeader")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self._drag_handle = drag_handle
        self._arrow = QLabel(self)
        self._title = QLabel(self)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(8)
        layout.addWidget(self._drag_handle)
        layout.addWidget(self._arrow)
        layout.addWidget(self._title, 1)

        self.set_title(title)

    def set_title(self, title: str) -> None:
        self._title.setText(title)
        self.setAccessibleName(title or self.tr("Section"))

    def set_expanded(self, expanded: bool) -> None:
        self._arrow.setText("▼" if expanded else "▶")
        self.setAccessibleDescription(self.tr("Expanded") if expanded else self.tr("Collapsed"))

    @override
    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self.rect().contains(
            event.position().toPoint()
        ):
            self.clicked.emit()
        super().mouseReleaseEvent(event)

    @override
    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() in (Qt.Key.Key_Space, Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.clicked.emit()
            event.accept()
            return
        super().keyPressEvent(event)


class CollapsibleSection(QFrame):
    """Reusable section with a clickable header and expandable body.

    Signals:
        expanded_changed(bool): emitted when the expanded state changes.
        drag_started: forwarded from the optional left-side drag handle.
    """

    expanded_changed = Signal(bool)
    drag_started = Signal()

    def __init__(
        self,
        title: str = "",
        expanded: bool = True,
        draggable: bool = False,
        icon_provider: IconProvider | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setProperty("class", "card")

        self._expanded = bool(expanded)
        self._draggable = bool(draggable)
        self._drag_handle = DragHandle(icon_provider, self)
        self._header = _SectionHeader(title, self._drag_handle, self)

        self._body_container = QWidget(self)
        self._body_layout = QVBoxLayout(self._body_container)
        self._body_layout.setContentsMargins(8, 8, 8, 8)
        self._body_layout.setSpacing(8)
        self._body_widget: QWidget | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._header)
        layout.addWidget(self._body_container)

        self._drag_handle.setVisible(self._draggable)
        self._drag_handle.drag_started.connect(self.drag_started.emit)
        self._header.clicked.connect(self.toggle)
        self._apply_expanded()
        self.setAccessibleName(title or self.tr("Section"))

    @property
    def title(self) -> str:
        return self._header.accessibleName()

    def set_title(self, title: str) -> None:
        self._header.set_title(title)
        self.setAccessibleName(title or self.tr("Section"))

    @property
    def expanded(self) -> bool:
        return self._expanded

    def set_expanded(self, expanded: bool) -> None:
        if self._expanded == expanded:
            return
        self._expanded = expanded
        self._apply_expanded()
        self.expanded_changed.emit(expanded)

    def toggle(self) -> None:
        self.set_expanded(not self._expanded)

    @property
    def draggable(self) -> bool:
        return self._draggable

    def set_draggable(self, draggable: bool) -> None:
        self._draggable = draggable
        self._drag_handle.setVisible(draggable)

    @property
    def header_widget(self) -> QWidget:
        return self._header

    @property
    def body_widget(self) -> QWidget | None:
        return self._body_widget

    def set_body_widget(self, widget: QWidget | None) -> None:
        if widget is self._body_widget:
            return
        if self._body_widget is not None:
            self._body_layout.removeWidget(self._body_widget)
            self._body_widget.hide()
            self._body_widget.setParent(None)
        self._body_widget = widget
        if widget is not None:
            self._body_layout.addWidget(widget)
            widget.show()

    def _apply_expanded(self) -> None:
        self._header.set_expanded(self._expanded)
        self._body_container.setVisible(self._expanded)
