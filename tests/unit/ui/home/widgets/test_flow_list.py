"""Tests for FlowList."""

from __future__ import annotations

from pytestqt.qtbot import QtBot

from cranioz.ui.home.widgets.flow_list import FlowList


def test_starts_empty(qtbot: QtBot) -> None:
    flow_list = FlowList()
    qtbot.addWidget(flow_list)
    assert flow_list.flow_count() == 0
    assert flow_list.selected_flow_id() is None


def test_manage_button_emits_signal(qtbot: QtBot) -> None:
    flow_list = FlowList()
    qtbot.addWidget(flow_list)

    with qtbot.waitSignal(flow_list.manage_flows_requested, timeout=1000):
        flow_list._manage_button.click()


def test_set_flows_populates(qtbot: QtBot) -> None:
    flow_list = FlowList()
    qtbot.addWidget(flow_list)
    flow_list.set_flows(
        [("orthognathic", "Cirurgia Ortognática"), ("implants", "Implantes")]
    )
    assert flow_list.flow_count() == 2


def test_selecting_flow_emits_signal(qtbot: QtBot) -> None:
    flow_list = FlowList()
    qtbot.addWidget(flow_list)
    flow_list.set_flows([("orthognathic", "Cirurgia Ortognática")])

    with qtbot.waitSignal(flow_list.flow_selected, timeout=1000) as blocker:
        flow_list._flow_buttons["orthognathic"].click()

    assert blocker.args[0] == "orthognathic"


def test_deselecting_flow_emits_none(qtbot: QtBot) -> None:
    flow_list = FlowList()
    qtbot.addWidget(flow_list)
    flow_list.set_flows([("orthognathic", "Cirurgia Ortognática")])
    flow_list._flow_buttons["orthognathic"].click()  # select

    with qtbot.waitSignal(flow_list.flow_selected, timeout=1000) as blocker:
        flow_list._flow_buttons["orthognathic"].click()  # deselect

    assert blocker.args[0] is None
