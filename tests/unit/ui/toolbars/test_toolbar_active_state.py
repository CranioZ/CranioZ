"""Tests for Toolbar.set_active / set_expanded / chevron (Bloco 2).

Covers the presentation-policy surface added in Bloco 2:

- ``set_active(False)`` on an ``ACTIVE_ONLY`` toolbar attaches a
  ``QGraphicsOpacityEffect`` with ``opacity == 0.5``.
- ``set_active(True)`` removes the effect.
- Buttons remain clickable while the toolbar is inactivated.
- ``set_active`` is a no-op for non-``ACTIVE_ONLY`` toolbars.
- ``set_expanded(False)`` on a ``COLLAPSIBLE`` toolbar hides the
  items, shows the title label, and shrinks the toolbar.
- ``set_expanded(True)`` restores the items and hides the title.
- ``set_expanded`` is a no-op for non-``COLLAPSIBLE`` toolbars.
- Clicking the chevron flips the expanded state and emits
  ``expanded_changed``.

Each test uses ``qtbot`` (which pulls ``qapp``) because the Toolbar
instantiates ``QPushButton`` and ``QLabel`` widgets.
"""

from __future__ import annotations

import pytest
from PySide6.QtWidgets import QGraphicsOpacityEffect, QLabel, QPushButton
from pytestqt.qtbot import QtBot
from tests.conftest import make_icon_provider

from cranioz.ui.icons.provider import IconProvider
from cranioz.ui.theme.service import ThemeService
from cranioz.ui.toolbars.base import Toolbar
from cranioz.ui.toolbars.specification import (
    ToolbarOrientation,
    ToolbarSpec,
    ToolbarVisibilityMode,
)
from cranioz.ui.tools.registry.tool_registry import ToolRegistry


# ----- Fixtures ------------------------------------------------------


@pytest.fixture
def toolbar_factory(
    qtbot: QtBot,
    tool_registry: ToolRegistry,
    theme_service: ThemeService,
):
    """Build a Toolbar with a ThemeService-bound IconProvider.

    Kept local to this module so the factory's signature is explicit
    about the ``visibility_mode`` it forwards. The shared
    ``toolbar_factory`` in ``test_toolbar.py`` is fine for behaviour
    that does not depend on visibility policy.
    """
    icon_provider: IconProvider = make_icon_provider(theme_service)

    def _factory(
        *,
        visibility_mode: ToolbarVisibilityMode,
        tool_ids: tuple[str, ...] = ("tool.log",),
        orientation: ToolbarOrientation = ToolbarOrientation.HORIZONTAL,
    ) -> Toolbar:
        spec = ToolbarSpec(
            toolbar_id="tb.test",
            title="Test Toolbar",
            orientation=orientation,
            tool_ids=tool_ids,
            visibility_mode=visibility_mode,
        )
        widget = Toolbar(
            spec,
            tool_registry,
            theme_service,
            icon_provider=icon_provider,
        )
        qtbot.addWidget(widget)
        return widget

    return _factory


# ----- set_active (ACTIVE_ONLY) --------------------------------------


def test_set_active_false_applies_opacity_effect(toolbar_factory) -> None:
    toolbar = toolbar_factory(visibility_mode=ToolbarVisibilityMode.ACTIVE_ONLY)

    toolbar.set_active(False)

    effect = toolbar.graphicsEffect()
    assert isinstance(effect, QGraphicsOpacityEffect)
    assert effect.opacity() == 0.5
    assert toolbar.is_active() is False


def test_set_active_true_removes_opacity_effect(toolbar_factory) -> None:
    toolbar = toolbar_factory(visibility_mode=ToolbarVisibilityMode.ACTIVE_ONLY)
    toolbar.set_active(False)
    assert toolbar.graphicsEffect() is not None

    toolbar.set_active(True)

    assert toolbar.graphicsEffect() is None
    assert toolbar.is_active() is True


def test_set_active_false_keeps_buttons_clickable(
    qtbot: QtBot,
    toolbar_factory,
) -> None:
    """The opacity effect is visual only; interaction must be unaffected."""
    toolbar = toolbar_factory(visibility_mode=ToolbarVisibilityMode.ACTIVE_ONLY)
    toolbar.show()
    qtbot.waitExposed(toolbar)
    toolbar.set_active(False)

    emitted: list[str] = []
    toolbar.tool_triggered.connect(emitted.append)

    button = toolbar.findChild(QPushButton, "toolbar.item.tool.log")
    assert button is not None
    assert button.isVisibleTo(toolbar)
    assert button.isEnabled()
    button.click()

    assert emitted == ["tool.log"]


def test_set_active_is_noop_for_always(toolbar_factory) -> None:
    """ALWAYS toolbars ignore set_active; they are never dimmed."""
    toolbar = toolbar_factory(visibility_mode=ToolbarVisibilityMode.ALWAYS)

    toolbar.set_active(False)

    assert toolbar.graphicsEffect() is None
    assert toolbar.is_active() is True


def test_set_active_is_noop_for_collapsible(toolbar_factory) -> None:
    """COLLAPSIBLE toolbars are controlled by set_expanded, not set_active."""
    toolbar = toolbar_factory(visibility_mode=ToolbarVisibilityMode.COLLAPSIBLE)

    toolbar.set_active(False)

    assert toolbar.graphicsEffect() is None
    assert toolbar.is_active() is True


# ----- set_expanded (COLLAPSIBLE) ------------------------------------


def test_set_expanded_false_collapses(
    qtbot: QtBot,
    toolbar_factory,
) -> None:
    toolbar = toolbar_factory(visibility_mode=ToolbarVisibilityMode.COLLAPSIBLE)
    toolbar.show()
    qtbot.waitExposed(toolbar)

    toolbar.set_expanded(False)

    assert toolbar.is_expanded() is False
    # Item buttons are inside the items container, which is hidden.
    for binding in toolbar.bindings():
        assert not binding.widget.isVisibleTo(toolbar)
    # The title label is now visible and carries the toolbar's title.
    title = toolbar.findChild(QLabel, "toolbar.tb.test.title")
    assert title is not None
    assert title.isVisibleTo(toolbar)
    assert title.text() == "Test Toolbar"


def test_set_expanded_true_restores(
    qtbot: QtBot,
    toolbar_factory,
) -> None:
    toolbar = toolbar_factory(visibility_mode=ToolbarVisibilityMode.COLLAPSIBLE)
    toolbar.show()
    qtbot.waitExposed(toolbar)
    toolbar.set_expanded(False)

    toolbar.set_expanded(True)

    assert toolbar.is_expanded() is True
    for binding in toolbar.bindings():
        assert binding.widget.isVisibleTo(toolbar)
    title = toolbar.findChild(QLabel, "toolbar.tb.test.title")
    assert title is not None
    assert not title.isVisibleTo(toolbar)

def test_set_expanded_is_noop_for_always(toolbar_factory) -> None:
    toolbar = toolbar_factory(visibility_mode=ToolbarVisibilityMode.ALWAYS)

    toolbar.set_expanded(False)

    assert toolbar.is_expanded() is True
    for binding in toolbar.bindings():
        assert binding.widget.isVisibleTo(toolbar)


def test_set_expanded_is_noop_for_active_only(toolbar_factory) -> None:
    """ACTIVE_ONLY toolbars are controlled by set_active, not set_expanded."""
    toolbar = toolbar_factory(visibility_mode=ToolbarVisibilityMode.ACTIVE_ONLY)

    toolbar.set_expanded(False)

    assert toolbar.is_expanded() is True


# ----- Chevron -------------------------------------------------------


def test_chevron_click_flips_expanded_state(
    qtbot: QtBot,
    toolbar_factory,
) -> None:
    toolbar = toolbar_factory(visibility_mode=ToolbarVisibilityMode.COLLAPSIBLE)
    assert toolbar.is_expanded() is True

    chevron = toolbar.findChild(QPushButton, "toolbar.tb.test.chevron")
    assert chevron is not None

    with qtbot.waitSignal(toolbar.expanded_changed, timeout=1000) as blocker:
        chevron.click()

    assert blocker.args == [False]
    assert toolbar.is_expanded() is False

    # Second click expands it again.
    with qtbot.waitSignal(toolbar.expanded_changed, timeout=1000) as blocker:
        chevron.click()

    assert blocker.args == [True]
    assert toolbar.is_expanded() is True


def test_no_chevron_for_non_collapsible_modes(toolbar_factory) -> None:
    for mode in (
        ToolbarVisibilityMode.ALWAYS,
        ToolbarVisibilityMode.ACTIVE_ONLY,
        ToolbarVisibilityMode.AUTO_HIDE,
        ToolbarVisibilityMode.HIDDEN,
    ):
        toolbar = toolbar_factory(visibility_mode=mode)
        chevron = toolbar.findChild(QPushButton, "toolbar.tb.test.chevron")
        assert chevron is None, f"{mode} must not have a chevron"