"""Tests for FlowRow."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QMouseEvent
from pytestqt.qtbot import QtBot

from cranioz.application.flows.definition import (
    FlowDefinition,
    FlowStep,
)
from cranioz.ui.home.widgets.flow_row import FlowRow


def _flow(flow_id: str = "f1", steps: int = 3) -> FlowDefinition:
    return FlowDefinition(
        flow_id=flow_id,
        name_key=f"flows.{flow_id}.name",
        version=1,
        steps=tuple(
            FlowStep(
                step_id=f"s{i}",
                name_key=f"flows.{flow_id}.steps.s{i}",
                module_id=f"m{i}",
            )
            for i in range(steps)
        ),
    )


def _identity(key: str) -> str:
    return key


def _click(row: FlowRow) -> None:
    """Simulate a left-button click on the row."""
    event = QMouseEvent(
        QMouseEvent.Type.MouseButtonPress,
        QPointF(5, 5),
        QPointF(5, 5),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    row.mousePressEvent(event)


@pytest.fixture
def row(qtbot: QtBot) -> FlowRow:
    r = FlowRow(_flow(), translate=_identity)
    qtbot.addWidget(r)
    return r


def test_row_holds_flow_id(row: FlowRow) -> None:
    assert row.flow_id == "f1"


def test_row_is_not_checked_by_default(row: FlowRow) -> None:
    assert row.is_checked() is False


def test_set_checked_toggles(row: FlowRow) -> None:
    row.set_checked(True)
    assert row.is_checked() is True
    row.set_checked(False)
    assert row.is_checked() is False


def test_click_selects_emits_flow_id(qtbot: QtBot) -> None:
    row = FlowRow(_flow(), translate=_identity)
    qtbot.addWidget(row)

    with qtbot.waitSignal(row.selected, timeout=1000) as blocker:
        _click(row)

    assert blocker.args[0] == "f1"
    assert row.is_checked() is True


def test_click_again_deselects_emits_none(qtbot: QtBot) -> None:
    row = FlowRow(_flow(), translate=_identity)
    qtbot.addWidget(row)
    row.set_checked(True)

    with qtbot.waitSignal(row.selected, timeout=1000) as blocker:
        _click(row)

    assert blocker.args[0] is None
    assert row.is_checked() is False
