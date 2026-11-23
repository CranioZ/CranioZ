"""Unit tests for DateField."""

from __future__ import annotations

from PySide6.QtCore import QDate

from cranioz.ui.widgets.forms.date_field import DateField


def test_defaults(qtbot) -> None:
    w = DateField("Birth date")
    qtbot.addWidget(w)
    assert w.label() == "Birth date"
    assert w.date_format == "dd/MM/yyyy"
    assert w.date() == QDate.currentDate()
    assert w.accessibleName() == "Birth date"


def test_custom_date(qtbot) -> None:
    w = DateField("X", date=QDate(1990, 1, 15))
    qtbot.addWidget(w)
    assert w.date() == QDate(1990, 1, 15)


def test_set_date_emits_changed(qtbot) -> None:
    w = DateField("X", date=QDate(2000, 1, 1))
    qtbot.addWidget(w)
    with qtbot.waitSignal(w.date_changed, timeout=500) as blocker:
        w.set_date(QDate(2001, 2, 3))
    assert blocker.args == [QDate(2001, 2, 3)]


def test_set_date_format(qtbot) -> None:
    w = DateField("X")
    qtbot.addWidget(w)
    w.set_date_format("yyyy-MM-dd")
    assert w.date_format == "yyyy-MM-dd"


def test_set_label_updates_accessible_name(qtbot) -> None:
    w = DateField("A")
    qtbot.addWidget(w)
    w.set_label("B")
    assert w.label() == "B"
    assert w.accessibleName() == "B"
