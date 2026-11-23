"""Vertical list of CollapsibleSection widgets with stable string keys."""

from __future__ import annotations

from typing import override

from PySide6.QtCore import QMimeData, QPoint, Qt, Signal
from PySide6.QtGui import QDrag, QDragEnterEvent, QDragMoveEvent, QDropEvent
from PySide6.QtWidgets import QVBoxLayout, QWidget

from cranioz.ui.widgets.sections.collapsible_section import CollapsibleSection


class DragList(QWidget):
    """Reorderable vertical container for CollapsibleSection children.

    Sections are identified by stable string keys. Signals:
        order_changed(list[str]): keys in current order.
        section_added(str): emitted after a section is added.
        section_removed(str): emitted after a section is removed.
    """

    order_changed = Signal(list)
    section_added = Signal(str)
    section_removed = Signal(str)

    _MIME_TYPE = "application/x-cranioz-drag-list-section"

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._sections: dict[str, CollapsibleSection] = {}
        self._order: list[str] = []
        self._connected_section_ids: set[int] = set()

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(8)
        self._layout.addStretch(1)
        self.setAcceptDrops(True)
        self.setAccessibleName(self.tr("Reorderable section list"))

    def add_section(self, key: str, section: CollapsibleSection) -> None:
        if not key:
            raise ValueError("section key must not be empty")
        if key in self._sections:
            raise ValueError(f"duplicate section key: {key!r}")

        self._sections[key] = section
        self._order.append(key)
        section.set_draggable(True)
        section_id = id(section)
        if section_id not in self._connected_section_ids:
            section.drag_started.connect(self._on_section_drag_started)
            self._connected_section_ids.add(section_id)
        self._layout.insertWidget(len(self._order) - 1, section)
        self.section_added.emit(key)
        self.order_changed.emit(self.keys())

    def remove_section(self, key: str) -> None:
        section = self._sections.pop(key)
        self._order.remove(key)
        self._layout.removeWidget(section)
        section.hide()
        section.setParent(None)
        self.section_removed.emit(key)
        self.order_changed.emit(self.keys())

    def move_section(self, key: str, new_index: int) -> None:
        if key not in self._sections:
            raise KeyError(key)
        if not 0 <= new_index < len(self._order):
            raise IndexError("new_index is outside the section list")

        old_index = self._order.index(key)
        if old_index == new_index:
            return
        self._order.pop(old_index)
        self._order.insert(new_index, key)
        self._rebuild_layout()
        self.order_changed.emit(self.keys())

    def set_order(self, keys: list[str]) -> None:
        """Apply a complete order.

        The supplied keys must be a permutation of the current keys.
        """
        if len(keys) != len(self._order) or set(keys) != set(self._sections):
            raise ValueError("keys must contain each section key exactly once")
        if keys == self._order:
            return
        self._order = list(keys)
        self._rebuild_layout()
        self.order_changed.emit(self.keys())

    def keys(self) -> list[str]:
        return list(self._order)

    def sections(self) -> dict[str, CollapsibleSection]:
        return dict(self._sections)

    def section(self, key: str) -> CollapsibleSection:
        return self._sections[key]

    @override
    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasFormat(self._MIME_TYPE):
            event.acceptProposedAction()
            return
        super().dragEnterEvent(event)

    @override
    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        if event.mimeData().hasFormat(self._MIME_TYPE):
            event.acceptProposedAction()
            return
        super().dragMoveEvent(event)

    @override
    def dropEvent(self, event: QDropEvent) -> None:
        key = self._key_from_mime_data(event.mimeData())
        if key is None or key not in self._sections:
            event.ignore()
            return

        old_index = self._order.index(key)
        raw_target = self._drop_index(float(event.position().y()))
        new_index = raw_target - 1 if raw_target > old_index else raw_target
        if new_index != old_index:
            self._order.pop(old_index)
            self._order.insert(new_index, key)
            self._rebuild_layout()
            self.order_changed.emit(self.keys())
        event.acceptProposedAction()

    def _on_section_drag_started(self) -> None:
        sender = self.sender()
        for key, section in self._sections.items():
            if section is sender:
                self._start_drag(key)
                return

    def _start_drag(self, key: str) -> None:
        mime_data = QMimeData()
        mime_data.setData(self._MIME_TYPE, key.encode("utf-8"))

        drag = QDrag(self)
        drag.setMimeData(mime_data)
        pixmap = self._sections[key].grab()
        drag.setPixmap(pixmap)
        drag.setHotSpot(QPoint(12, 12))
        drag.exec(Qt.DropAction.MoveAction)

    def _drop_index(self, y: float) -> int:
        index = 0
        for key in self._order:
            section = self._sections[key]
            if section.isVisible() and y > section.geometry().center().y():
                index += 1
        return index

    def _key_from_mime_data(self, mime_data: QMimeData) -> str | None:
        if not mime_data.hasFormat(self._MIME_TYPE):
            return None
        try:
            payload = mime_data.data(self._MIME_TYPE).data()
            return bytes(payload).decode("utf-8")
        except UnicodeDecodeError:
            return None

    def _rebuild_layout(self) -> None:
        for section in self._sections.values():
            self._layout.removeWidget(section)
        for index, key in enumerate(self._order):
            self._layout.insertWidget(index, self._sections[key])
