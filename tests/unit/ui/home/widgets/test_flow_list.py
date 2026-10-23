"""Tests for FlowList."""

from __future__ import annotations

from pytestqt.qtbot import QtBot

from cranioz.application.flows.definition import (
    FlowDefinition,
    FlowStep,
)
from cranioz.ui.home.widgets.flow_list import FlowList


def _flow(flow_id: str, steps: int = 2) -> FlowDefinition:
    return FlowDefinition(
        flow_id=flow_id,
        name_key=f"flows.{flow_id}.name",
        version=1,
        steps=tuple(
            FlowStep(
                step_id=f"{flow_id}_s{i}",
                name_key=f"flows.{flow_id}.steps.s{i}",
                module_id=f"m{i}",
            )
            for i in range(steps)
        ),
    )


def test_starts_empty(qtbot: QtBot) -> None:
    flow_list = FlowList()
    qtbot.addWidget(flow_list)
    assert flow_list.flow_count() == 0
    assert flow_list.selected_flow_id() is None


def test_manage_button_emits_signal(qtbot: QtBot) -> None:
    flow_list = FlowList()
    qtbot.addWidget(flow_list)

    with qtbot.waitSignal(
        flow_list.manage_flows_requested, timeout=1000
    ):
        flow_list._manage_button.click()


def test_set_flows_populates(qtbot: QtBot) -> None:
    flow_list = FlowList()
    qtbot.addWidget(flow_list)
    flow_list.set_flows((_flow("a"), _flow("b")))
    assert flow_list.flow_count() == 2


def test_selecting_flow_emits_signal(qtbot: QtBot) -> None:
    flow_list = FlowList()
    qtbot.addWidget(flow_list)
    flow_list.set_flows((_flow("a"),))

    with qtbot.waitSignal(flow_list.flow_selected, timeout=1000) as blocker:
        flow_list._on_row_selected("a")

    assert blocker.args[0] == "a"
    assert flow_list.selected_flow_id() == "a"


def test_deselecting_flow_emits_none(qtbot: QtBot) -> None:
    flow_list = FlowList()
    qtbot.addWidget(flow_list)
    flow_list.set_flows((_flow("a"),))
    flow_list._on_row_selected("a")

    with qtbot.waitSignal(flow_list.flow_selected, timeout=1000) as blocker:
        flow_list._on_row_selected(None)

    assert blocker.args[0] is None
    assert flow_list.selected_flow_id() is None


def test_set_flows_clears_selection(qtbot: QtBot) -> None:
    flow_list = FlowList()
    qtbot.addWidget(flow_list)
    flow_list.set_flows((_flow("a"),))
    flow_list._on_row_selected("a")
    assert flow_list.selected_flow_id() == "a"

    flow_list.set_flows((_flow("b"),))
    assert flow_list.selected_flow_id() is None


def test_selecting_a_second_flow_deselects_the_first(
    qtbot: QtBot,
) -> None:
    """Only one flow is selected at a time."""
    flow_list = FlowList()
    qtbot.addWidget(flow_list)
    flow_list.set_flows((_flow("a"), _flow("b")))

    flow_list._on_row_selected("a")
    assert flow_list._rows["a"].is_checked() is True
    assert flow_list._rows["b"].is_checked() is False

    flow_list._on_row_selected("b")
    assert flow_list._rows["a"].is_checked() is False
    assert flow_list._rows["b"].is_checked() is True
    assert flow_list.selected_flow_id() == "b"
