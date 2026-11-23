"""Unit tests for DragHandle."""

from __future__ import annotations

from PySide6.QtCore import Qt

from cranioz.ui.icons.provider import IconProvider
from cranioz.ui.widgets.lists.drag_handle import DragHandle


def test_constructs_without_provider(qtbot) -> None:
    widget = DragHandle()
    qtbot.addWidget(widget)
    assert widget.text() == "⋮⋮"
    assert widget.focusPolicy() == Qt.FocusPolicy.NoFocus
    assert widget.accessibleName() == "Drag to reorder"


def test_constructs_with_real_icon_provider(qtbot, icon_provider: IconProvider) -> None:
    widget = DragHandle(icon_provider=icon_provider)
    qtbot.addWidget(widget)
    assert widget.icon().isNull() is False
    assert widget.text() == ""


def test_constructs_with_null_icon_provider(qtbot, null_icon_provider: IconProvider) -> None:
    widget = DragHandle(icon_provider=null_icon_provider)
    qtbot.addWidget(widget)
    assert widget.text() == "⋮⋮"


def test_drag_started_emitted_on_press(qtbot, null_icon_provider: IconProvider) -> None:
    widget = DragHandle(icon_provider=null_icon_provider)
    qtbot.addWidget(widget)
    with qtbot.waitSignal(widget.drag_started, timeout=500):
        widget.pressed.emit()


def test_fixed_width(qtbot) -> None:
    widget = DragHandle()
    qtbot.addWidget(widget)
    assert widget.width() == 18
