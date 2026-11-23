"""Unit tests for FormRow."""

from __future__ import annotations

from PySide6.QtWidgets import QLabel

from cranioz.ui.widgets.forms.form_row import FormRow


def test_empty(qtbot) -> None:
    w = FormRow()
    qtbot.addWidget(w)
    assert w.fields() == []


def test_add_field_preserves_order(qtbot) -> None:
    w = FormRow()
    qtbot.addWidget(w)
    a, b = QLabel("A"), QLabel("B")
    w.add_field(a, stretch=2)
    w.add_field(b)
    assert w.fields() == [a, b]


def test_set_spacing(qtbot) -> None:
    w = FormRow()
    qtbot.addWidget(w)
    w.set_spacing(12)
    assert w.layout().spacing() == 12  # type: ignore[union-attr]
