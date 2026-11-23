"""Unit tests for CollapsibleSection."""

from __future__ import annotations

from PySide6.QtCore import QPoint, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QLabel

from cranioz.ui.icons.provider import IconProvider
from cranioz.ui.widgets.lists import DragHandle
from cranioz.ui.widgets.sections import CollapsibleSection


def test_defaults(qtbot) -> None:
    section = CollapsibleSection("Agenda")
    qtbot.addWidget(section)
    assert section.title == "Agenda"
    assert section.expanded is True
    assert section.draggable is False
    assert section.accessibleName() == "Agenda"


def test_toggle_emits_expanded_changed(qtbot) -> None:
    section = CollapsibleSection("Agenda")
    qtbot.addWidget(section)
    with qtbot.waitSignal(section.expanded_changed, timeout=500) as blocker:
        section.toggle()
    assert blocker.args == [False]
    assert section.expanded is False


def test_set_expanded_same_value_does_not_emit(qtbot) -> None:
    section = CollapsibleSection("Agenda")
    qtbot.addWidget(section)
    emitted: list[bool] = []
    section.expanded_changed.connect(emitted.append)
    section.set_expanded(True)
    assert emitted == []


def test_header_mouse_click_toggles(qtbot) -> None:
    section = CollapsibleSection("Agenda")
    qtbot.addWidget(section)
    section.show()
    QTest.mouseClick(
        section.header_widget,
        Qt.MouseButton.LeftButton,
        pos=QPoint(section.header_widget.width() - 20, 10),
    )
    assert section.expanded is False


def test_space_and_enter_toggle_header(qtbot) -> None:
    section = CollapsibleSection("Agenda")
    qtbot.addWidget(section)
    section.show()
    QTest.keyClick(section.header_widget, Qt.Key.Key_Space)
    assert section.expanded is False
    QTest.keyClick(section.header_widget, Qt.Key.Key_Return)
    assert section.expanded is True


def test_draggable_controls_handle_visibility(
    qtbot,
    null_icon_provider: IconProvider,
) -> None:
    section = CollapsibleSection(
        "Agenda",
        draggable=True,
        icon_provider=null_icon_provider,
    )
    qtbot.addWidget(section)
    handle = section.findChild(DragHandle)
    assert handle is not None
    assert handle.isHidden() is False

    section.set_draggable(False)
    assert handle.isHidden() is True
    section.set_draggable(True)
    assert handle.isHidden() is False


def test_drag_started_is_forwarded(qtbot) -> None:
    section = CollapsibleSection("Agenda", draggable=True)
    qtbot.addWidget(section)
    handle = section.findChild(DragHandle)
    assert handle is not None
    with qtbot.waitSignal(section.drag_started, timeout=500):
        handle.pressed.emit()


def test_body_widget_follows_expanded_state(qtbot) -> None:
    section = CollapsibleSection("Agenda", expanded=False)
    qtbot.addWidget(section)
    body = QLabel("Content")
    section.set_body_widget(body)
    assert section.body_widget is body
    assert body.isVisibleTo(section) is False

    section.set_expanded(True)
    assert body.isVisibleTo(section) is True
