"""Unit tests for VisibilityToggle."""

from __future__ import annotations

from cranioz.ui.widgets.navigation.visibility_toggle import (
    VisibilityToggle,
)


def test_defaults(qtbot) -> None:
    w = VisibilityToggle("Show tab")
    qtbot.addWidget(w)
    assert w.text() == "Show tab"
    assert w.isChecked() is True
    assert w.accessibleName() == "Show tab"


def test_toggled_signal(qtbot) -> None:
    w = VisibilityToggle("X")
    qtbot.addWidget(w)
    with qtbot.waitSignal(w.toggled, timeout=500) as blocker:
        w.toggle()
    assert blocker.args == [False]


def test_empty_text_uses_default_accessible_name(qtbot) -> None:
    w = VisibilityToggle()
    qtbot.addWidget(w)
    assert w.accessibleName() == "Visible"
