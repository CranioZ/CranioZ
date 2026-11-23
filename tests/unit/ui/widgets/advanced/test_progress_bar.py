"""Unit tests for ProgressBar."""

from __future__ import annotations

from cranioz.ui.widgets.advanced.progress_bar import ProgressBar


def test_defaults(qtbot) -> None:
    w = ProgressBar()
    qtbot.addWidget(w)
    assert w.indeterminate is False
    assert w.isTextVisible() is True


def test_set_indeterminate_true(qtbot) -> None:
    w = ProgressBar()
    qtbot.addWidget(w)
    w.set_indeterminate(True)
    assert w.indeterminate is True
    assert (w.minimum(), w.maximum()) == (0, 0)


def test_set_indeterminate_false_restores_range(qtbot) -> None:
    w = ProgressBar()
    qtbot.addWidget(w)
    w.set_indeterminate(True)
    w.set_indeterminate(False)
    assert w.indeterminate is False
    assert (w.minimum(), w.maximum()) == (0, 100)
