"""Unit tests for IconSidebar."""

from __future__ import annotations

import pytest
from PySide6.QtWidgets import QToolButton

from cranioz.ui.icons.provider import IconProvider
from cranioz.ui.widgets.navigation import IconSidebar


def _buttons(sidebar: IconSidebar) -> list[QToolButton]:
    return sidebar.findChildren(QToolButton)


def test_add_item_uses_icon_provider(qtbot, icon_provider: IconProvider) -> None:
    sidebar = IconSidebar(icon_provider)
    qtbot.addWidget(sidebar)
    sidebar.add_item("documents", "open", "Document templates")

    button = _buttons(sidebar)[0]
    assert button.icon().isNull() is False
    assert button.text() == ""
    assert button.toolTip() == "Document templates"
    assert button.accessibleName() == "Document templates"


def test_add_item_falls_back_to_text_glyph(
    qtbot,
    null_icon_provider: IconProvider,
) -> None:
    sidebar = IconSidebar(null_icon_provider)
    qtbot.addWidget(sidebar)
    sidebar.add_item("documents", "open", "Document templates")
    assert _buttons(sidebar)[0].text() == "?"


def test_click_emits_item_selected_and_sets_active(
    qtbot,
    icon_provider: IconProvider,
) -> None:
    sidebar = IconSidebar(icon_provider)
    qtbot.addWidget(sidebar)
    sidebar.add_item("agenda", "home", "Agenda")
    button = _buttons(sidebar)[0]

    with qtbot.waitSignal(sidebar.item_selected, timeout=500) as blocker:
        button.click()

    assert blocker.args == ["agenda"]
    assert sidebar.active_key() == "agenda"
    assert button.isChecked() is True


def test_set_active_is_exclusive(qtbot, icon_provider: IconProvider) -> None:
    sidebar = IconSidebar(icon_provider)
    qtbot.addWidget(sidebar)
    sidebar.add_item("agenda", "home", "Agenda")
    sidebar.add_item("budgets", "settings", "Budgets")
    first, second = _buttons(sidebar)

    sidebar.set_active("agenda")
    assert first.isChecked() is True
    assert second.isChecked() is False

    sidebar.set_active("budgets")
    assert first.isChecked() is False
    assert second.isChecked() is True


def test_rejects_empty_and_duplicate_keys(
    qtbot,
    icon_provider: IconProvider,
) -> None:
    sidebar = IconSidebar(icon_provider)
    qtbot.addWidget(sidebar)
    with pytest.raises(ValueError, match="empty"):
        sidebar.add_item("", "home", "Invalid")
    sidebar.add_item("agenda", "home", "Agenda")
    with pytest.raises(ValueError, match="duplicate"):
        sidebar.add_item("agenda", "home", "Duplicate")


def test_set_active_unknown_key_raises(qtbot, icon_provider: IconProvider) -> None:
    sidebar = IconSidebar(icon_provider)
    qtbot.addWidget(sidebar)
    with pytest.raises(KeyError):
        sidebar.set_active("missing")
