"""Tests for the Toolbar widget.

These tests validate that the Toolbar materializes a ToolbarSpec
against a ToolRegistry and a ThemeService, and that user interaction
produces the expected signals.
"""

# mypy: ignore-errors
# This file exercises Qt widgets and intentionally triggers edge cases.

from __future__ import annotations

from PySide6.QtWidgets import QPushButton
from pytestqt.qtbot import QtBot

from cranioz.ui.theme.service import ThemeService
from cranioz.ui.toolbars.base import Toolbar
from cranioz.ui.toolbars.specification import ToolbarOrientation
from cranioz.ui.tools.registry.tool_definition import ToolContext
from cranioz.ui.tools.registry.tool_registry import ToolRegistry

# ----- Construction --------------------------------------------------


def test_empty_toolbar_has_no_bindings(
    qtbot: QtBot,
    tool_registry: ToolRegistry,
    theme_service: ThemeService,
    make_toolbar_spec,
) -> None:
    spec = make_toolbar_spec(tool_ids=())
    toolbar = Toolbar(spec, tool_registry, theme_service)
    qtbot.addWidget(toolbar)

    assert toolbar.bindings() == ()
    assert toolbar.tool_ids() == ()


def test_toolbar_with_one_tool_creates_one_binding(
    qtbot: QtBot,
    tool_registry: ToolRegistry,
    theme_service: ThemeService,
    make_toolbar_spec,
) -> None:
    spec = make_toolbar_spec(tool_ids=("tool.log",))
    toolbar = Toolbar(spec, tool_registry, theme_service)
    qtbot.addWidget(toolbar)

    assert toolbar.tool_ids() == ("tool.log",)


def test_toolbar_with_two_tools_preserves_order(
    qtbot: QtBot,
    tool_registry: ToolRegistry,
    theme_service: ThemeService,
    make_toolbar_spec,
) -> None:
    spec = make_toolbar_spec(tool_ids=("tool.toggle", "tool.log"))
    toolbar = Toolbar(spec, tool_registry, theme_service)
    qtbot.addWidget(toolbar)

    assert toolbar.tool_ids() == ("tool.toggle", "tool.log")


def test_toolbar_resolves_tool_instances(
    qtbot: QtBot,
    tool_registry: ToolRegistry,
    theme_service: ThemeService,
    make_toolbar_spec,
) -> None:
    spec = make_toolbar_spec(tool_ids=("tool.log",))
    toolbar = Toolbar(spec, tool_registry, theme_service)
    qtbot.addWidget(toolbar)

    binding = toolbar.bindings()[0]
    assert binding.tool is not None
    assert binding.tool.identifier == "tool.log"


# ----- Orientation ---------------------------------------------------


def test_horizontal_toolbar_renders_buttons(
    qtbot: QtBot,
    tool_registry: ToolRegistry,
    theme_service: ThemeService,
    make_toolbar_spec,
) -> None:
    spec = make_toolbar_spec(
        orientation=ToolbarOrientation.HORIZONTAL,
        tool_ids=("tool.log",),
    )
    toolbar = Toolbar(spec, tool_registry, theme_service)
    qtbot.addWidget(toolbar)

    buttons = toolbar.findChildren(QPushButton)
    assert len(buttons) == 1
    assert buttons[0].text() == "Log"


def test_vertical_toolbar_renders_buttons(
    qtbot: QtBot,
    tool_registry: ToolRegistry,
    theme_service: ThemeService,
    make_toolbar_spec,
) -> None:
    spec = make_toolbar_spec(
        orientation=ToolbarOrientation.VERTICAL,
        tool_ids=("tool.toggle",),
    )
    toolbar = Toolbar(spec, tool_registry, theme_service)
    qtbot.addWidget(toolbar)

    buttons = toolbar.findChildren(QPushButton)
    assert len(buttons) == 1
    assert buttons[0].text() == "Toggle"


# ----- Icon resolution ----------------------------------------------


def test_toolbar_resolves_icon_name_via_theme(
    qtbot: QtBot,
    tool_registry: ToolRegistry,
    theme_service: ThemeService,
    make_toolbar_spec,
) -> None:
    spec = make_toolbar_spec(tool_ids=("tool.log",))
    toolbar = Toolbar(spec, tool_registry, theme_service)
    qtbot.addWidget(toolbar)

    button = toolbar.findChild(QPushButton)
    assert button is not None
    # The button stores the resolved icon name as a dynamic property.
    # The actual icon file is not loaded in this phase.
    assert button.property("icon_name") == "log"


# ----- Signals ------------------------------------------------------


def test_clicking_action_tool_emits_signal(
    qtbot: QtBot,
    tool_registry: ToolRegistry,
    theme_service: ThemeService,
    make_toolbar_spec,
) -> None:
    spec = make_toolbar_spec(tool_ids=("tool.log",))
    toolbar = Toolbar(spec, tool_registry, theme_service)
    qtbot.addWidget(toolbar)

    with qtbot.waitSignal(toolbar.tool_triggered, timeout=1000) as blocker:
        button = toolbar.findChild(QPushButton)
        assert button is not None
        button.click()

    assert blocker.args == ["tool.log"]


def test_toggling_toggle_tool_emits_signal(
    qtbot: QtBot,
    tool_registry: ToolRegistry,
    theme_service: ThemeService,
    make_toolbar_spec,
) -> None:
    spec = make_toolbar_spec(tool_ids=("tool.toggle",))
    toolbar = Toolbar(spec, tool_registry, theme_service)
    qtbot.addWidget(toolbar)

    with qtbot.waitSignal(toolbar.tool_toggled, timeout=1000) as blocker:
        button = toolbar.findChild(QPushButton)
        assert button is not None
        assert button.isCheckable()
        button.click()

    tool_id, checked = blocker.args
    assert tool_id == "tool.toggle"
    assert checked is True


# ----- Interaction guards -------------------------------------------


def test_disabled_tool_does_not_emit_signal(
    qtbot: QtBot,
    tool_registry: ToolRegistry,
    theme_service: ThemeService,
    make_toolbar_spec,
) -> None:
    spec = make_toolbar_spec(tool_ids=("tool.log",))
    ctx = ToolContext(extras={"enabled": False})
    toolbar = Toolbar(spec, tool_registry, theme_service, context=ctx)
    qtbot.addWidget(toolbar)

    emitted: list[str] = []
    toolbar.tool_triggered.connect(emitted.append)

    button = toolbar.findChild(QPushButton)
    assert button is not None
    button.click()

    assert emitted == []


def test_unavailable_tool_does_not_emit_signal(
    qtbot: QtBot,
    tool_registry: ToolRegistry,
    theme_service: ThemeService,
    make_toolbar_spec,
) -> None:
    spec = make_toolbar_spec(tool_ids=("tool.log",))
    ctx = ToolContext(extras={"available": False})
    toolbar = Toolbar(spec, tool_registry, theme_service, context=ctx)
    qtbot.addWidget(toolbar)

    emitted: list[str] = []
    toolbar.tool_triggered.connect(emitted.append)

    button = toolbar.findChild(QPushButton)
    assert button is not None
    button.click()

    assert emitted == []


# ----- Errors -------------------------------------------------------


def test_unknown_tool_id_raises(
    qtbot: QtBot,
    tool_registry: ToolRegistry,
    theme_service: ThemeService,
    make_toolbar_spec,
) -> None:
    spec = make_toolbar_spec(tool_ids=("tool.unknown",))
    try:
        toolbar = Toolbar(spec, tool_registry, theme_service)
    except KeyError as exc:
        assert "tool.unknown" in str(exc)
    else:
        qtbot.addWidget(toolbar)
        raise AssertionError("expected KeyError for unknown tool_id")
