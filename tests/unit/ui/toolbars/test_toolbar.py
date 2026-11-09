"""Tests for the Toolbar widget.

These tests validate that the Toolbar materializes a ToolbarSpec
against a ToolRegistry and a ThemeService, and that user interaction
produces the expected signals.
"""

# mypy: ignore-errors
# This file exercises Qt widgets and intentionally triggers edge cases.

from __future__ import annotations

from collections.abc import Callable

import pytest
from PySide6.QtWidgets import QPushButton
from pytestqt.qtbot import QtBot
from tests.conftest import make_icon_provider

from cranioz.ui.icons.provider import IconProvider
from cranioz.ui.theme.service import ThemeService
from cranioz.ui.toolbars.base import Toolbar
from cranioz.ui.toolbars.specification import ToolbarOrientation
from cranioz.ui.tools.registry.tool_definition import ToolContext
from cranioz.ui.tools.registry.tool_registry import ToolRegistry

# ----- Fixtures ------------------------------------------------------


@pytest.fixture
def toolbar_factory(
    qtbot: QtBot,
    tool_registry: ToolRegistry,
    theme_service: ThemeService,
) -> Callable[..., Toolbar]:
    """Build a Toolbar with a ThemeService-bound IconProvider.

    Tests that need to assert on the icon resolution get the same
    ThemeService the IconProvider is built from. Tests that pass a
    custom context use the ``context=`` keyword.
    """
    icon_provider: IconProvider = make_icon_provider(theme_service)

    def _factory(
        spec,
        *,
        context: ToolContext | None = None,
    ) -> Toolbar:
        if context is not None:
            widget = Toolbar(
                spec,
                tool_registry,
                theme_service,
                icon_provider=icon_provider,
                context=context,
            )
        else:
            widget = Toolbar(
                spec,
                tool_registry,
                theme_service,
                icon_provider=icon_provider,
            )
        qtbot.addWidget(widget)
        return widget

    return _factory


# ----- Construction --------------------------------------------------


def test_empty_toolbar_has_no_bindings(
    toolbar_factory,
    make_toolbar_spec,
) -> None:
    spec = make_toolbar_spec(tool_ids=())
    toolbar = toolbar_factory(spec)

    assert toolbar.bindings() == ()
    assert toolbar.tool_ids() == ()


def test_toolbar_with_one_tool_creates_one_binding(
    toolbar_factory,
    make_toolbar_spec,
) -> None:
    spec = make_toolbar_spec(tool_ids=("tool.log",))
    toolbar = toolbar_factory(spec)

    assert toolbar.tool_ids() == ("tool.log",)


def test_toolbar_with_two_tools_preserves_order(
    toolbar_factory,
    make_toolbar_spec,
) -> None:
    spec = make_toolbar_spec(tool_ids=("tool.toggle", "tool.log"))
    toolbar = toolbar_factory(spec)

    assert toolbar.tool_ids() == ("tool.toggle", "tool.log")


def test_toolbar_resolves_tool_instances(
    toolbar_factory,
    make_toolbar_spec,
) -> None:
    spec = make_toolbar_spec(tool_ids=("tool.log",))
    toolbar = toolbar_factory(spec)

    binding = toolbar.bindings()[0]
    assert binding.tool is not None
    assert binding.tool.identifier == "tool.log"


# ----- Orientation ---------------------------------------------------


def test_horizontal_toolbar_renders_buttons(
    toolbar_factory,
    make_toolbar_spec,
) -> None:
    spec = make_toolbar_spec(
        orientation=ToolbarOrientation.HORIZONTAL,
        tool_ids=("tool.log",),
    )
    toolbar = toolbar_factory(spec)

    buttons = toolbar.findChildren(QPushButton)
    assert len(buttons) == 1
    assert buttons[0].text() == "Log"


def test_vertical_toolbar_renders_buttons(
    toolbar_factory,
    make_toolbar_spec,
) -> None:
    spec = make_toolbar_spec(
        orientation=ToolbarOrientation.VERTICAL,
        tool_ids=("tool.toggle",),
    )
    toolbar = toolbar_factory(spec)

    buttons = toolbar.findChildren(QPushButton)
    assert len(buttons) == 1
    assert buttons[0].text() == "Toggle"


# ----- Icon resolution ----------------------------------------------


def test_toolbar_resolves_icon_via_icon_provider(
    toolbar_factory,
    make_toolbar_spec,
) -> None:
    spec = make_toolbar_spec(tool_ids=("tool.log",))
    toolbar = toolbar_factory(spec)

    button = toolbar.findChild(QPushButton)
    assert button is not None
    # The button has a real QIcon resolved by the IconProvider.
    # (Before Sprint F, the plan was to store the icon name as a
    # dynamic property; Sprint F replaced that with
    # icon_provider.icon().)
    assert button.icon().isNull() is False


# ----- Signals ------------------------------------------------------


def test_clicking_action_tool_emits_signal(
    qtbot: QtBot,
    toolbar_factory,
    make_toolbar_spec,
) -> None:
    spec = make_toolbar_spec(tool_ids=("tool.log",))
    toolbar = toolbar_factory(spec)

    with qtbot.waitSignal(toolbar.tool_triggered, timeout=1000) as blocker:
        button = toolbar.findChild(QPushButton)
        assert button is not None
        button.click()

    assert blocker.args == ["tool.log"]


def test_toggling_toggle_tool_emits_signal(
    qtbot: QtBot,
    toolbar_factory,
    make_toolbar_spec,
) -> None:
    spec = make_toolbar_spec(tool_ids=("tool.toggle",))
    toolbar = toolbar_factory(spec)

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
    toolbar_factory,
    make_toolbar_spec,
) -> None:
    spec = make_toolbar_spec(tool_ids=("tool.log",))
    ctx = ToolContext(extras={"enabled": False})
    toolbar = toolbar_factory(spec, context=ctx)

    emitted: list[str] = []
    toolbar.tool_triggered.connect(emitted.append)

    button = toolbar.findChild(QPushButton)
    assert button is not None
    button.click()

    assert emitted == []


def test_unavailable_tool_does_not_emit_signal(
    toolbar_factory,
    make_toolbar_spec,
) -> None:
    spec = make_toolbar_spec(tool_ids=("tool.log",))
    ctx = ToolContext(extras={"available": False})
    toolbar = toolbar_factory(spec, context=ctx)

    emitted: list[str] = []
    toolbar.tool_triggered.connect(emitted.append)

    button = toolbar.findChild(QPushButton)
    assert button is not None
    button.click()

    assert emitted == []


# ----- Errors -------------------------------------------------------


def test_unknown_tool_id_raises(
    toolbar_factory,
    make_toolbar_spec,
) -> None:
    spec = make_toolbar_spec(tool_ids=("tool.unknown",))
    try:
        toolbar_factory(spec)
    except KeyError as exc:
        assert "tool.unknown" in str(exc)
    else:
        raise AssertionError("expected KeyError for unknown tool_id")
