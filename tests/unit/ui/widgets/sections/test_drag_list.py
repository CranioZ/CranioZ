"""Unit tests for DragList."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QMimeData, QPointF, Qt
from PySide6.QtGui import QDropEvent

from cranioz.ui.widgets.sections import CollapsibleSection, DragList


def _make_list(qtbot, keys: tuple[str, ...]) -> tuple[DragList, dict[str, CollapsibleSection]]:
    widget = DragList()
    qtbot.addWidget(widget)
    sections = {key: CollapsibleSection(key) for key in keys}
    for key, section in sections.items():
        widget.add_section(key, section)
    return widget, sections


def test_add_section_emits_signals_and_sets_draggable(qtbot) -> None:
    widget = DragList()
    qtbot.addWidget(widget)
    section = CollapsibleSection("Agenda")
    added: list[str] = []
    orders: list[list[str]] = []
    widget.section_added.connect(added.append)
    widget.order_changed.connect(orders.append)

    widget.add_section("agenda", section)

    assert added == ["agenda"]
    assert orders == [["agenda"]]
    assert section.draggable is True
    assert widget.acceptDrops() is True


def test_add_section_rejects_empty_and_duplicate_keys(qtbot) -> None:
    widget, _ = _make_list(qtbot, ("agenda",))
    with pytest.raises(ValueError, match="empty"):
        widget.add_section("", CollapsibleSection("Empty"))
    with pytest.raises(ValueError, match="duplicate"):
        widget.add_section("agenda", CollapsibleSection("Duplicate"))


def test_remove_section_emits_signals(qtbot) -> None:
    widget, _ = _make_list(qtbot, ("agenda", "budgets"))
    removed: list[str] = []
    orders: list[list[str]] = []
    widget.section_removed.connect(removed.append)
    widget.order_changed.connect(orders.append)

    widget.remove_section("agenda")

    assert removed == ["agenda"]
    assert orders == [["budgets"]]
    assert widget.keys() == ["budgets"]


def test_move_section_emits_key_order(qtbot) -> None:
    widget, _ = _make_list(qtbot, ("agenda", "budgets", "procedures"))
    orders: list[list[str]] = []
    widget.order_changed.connect(orders.append)

    widget.move_section("procedures", 0)

    assert widget.keys() == ["procedures", "agenda", "budgets"]
    assert orders == [["procedures", "agenda", "budgets"]]


def test_move_section_to_same_index_does_not_emit(qtbot) -> None:
    widget, _ = _make_list(qtbot, ("agenda", "budgets"))
    orders: list[list[str]] = []
    widget.order_changed.connect(orders.append)
    widget.move_section("agenda", 0)
    assert orders == []


def test_set_order_requires_complete_permutation(qtbot) -> None:
    widget, _ = _make_list(qtbot, ("agenda", "budgets"))
    widget.set_order(["budgets", "agenda"])
    assert widget.keys() == ["budgets", "agenda"]

    with pytest.raises(ValueError, match="exactly once"):
        widget.set_order(["agenda"])
    with pytest.raises(ValueError, match="exactly once"):
        widget.set_order(["agenda", "agenda"])


def test_section_lookup_and_mapping_copy(qtbot) -> None:
    widget, sections = _make_list(qtbot, ("agenda",))
    mapping = widget.sections()
    assert widget.section("agenda") is sections["agenda"]
    mapping.clear()
    assert widget.keys() == ["agenda"]


def test_drop_event_reorders_using_stable_key(qtbot) -> None:
    widget, _ = _make_list(qtbot, ("agenda", "budgets"))
    mime_data = QMimeData()
    mime_data.setData(DragList._MIME_TYPE, b"budgets")
    event = QDropEvent(
        QPointF(0, 0),
        Qt.DropAction.MoveAction,
        mime_data,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )

    widget.dropEvent(event)

    assert widget.keys() == ["budgets", "agenda"]
