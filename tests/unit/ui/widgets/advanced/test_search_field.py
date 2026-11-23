"""Unit tests for SearchField."""

from __future__ import annotations

from PySide6.QtCore import Qt

from cranioz.ui.icons.provider import IconProvider
from cranioz.ui.widgets.advanced.search_field import SearchField


def test_defaults(qtbot, icon_provider: IconProvider) -> None:
    w = SearchField(icon_provider, placeholder="Search patients")
    qtbot.addWidget(w)
    assert w.text() == ""
    assert w.accessibleName() == "Search patients"


def test_text_changed_emits(qtbot, icon_provider: IconProvider) -> None:
    w = SearchField(icon_provider)
    qtbot.addWidget(w)
    w.show()

    received: list[str] = []
    w.text_changed.connect(received.append)

    qtbot.keyClicks(w._edit, "abc")  # noqa: SLF001
    assert received == ["a", "ab", "abc"]
    assert w.text() == "abc"


def test_search_requested_on_enter(qtbot, icon_provider: IconProvider) -> None:
    w = SearchField(icon_provider)
    qtbot.addWidget(w)
    w.show()
    w.set_text("hello")
    with qtbot.waitSignal(w.search_requested, timeout=500) as blocker:
        qtbot.keyClick(w._edit, Qt.Key.Key_Return)  # noqa: SLF001
    assert blocker.args == ["hello"]


def test_clear_action(qtbot, icon_provider: IconProvider) -> None:
    w = SearchField(icon_provider)
    qtbot.addWidget(w)
    w.show()
    w.set_text("abc")
    assert w.text() == "abc"
    w.clear()
    assert w.text() == ""


def test_clear_button_hidden_when_empty(qtbot, icon_provider: IconProvider) -> None:
    w = SearchField(icon_provider)
    qtbot.addWidget(w)
    w.show()
    assert w._clear_btn.isVisible() is False  # noqa: SLF001
    w.set_text("x")
    assert w._clear_btn.isVisible() is True  # noqa: SLF001


def test_uses_real_icons(qtbot, icon_provider: IconProvider) -> None:
    w = SearchField(icon_provider)
    qtbot.addWidget(w)
    assert w._search_btn.icon().isNull() is False  # noqa: SLF001
    assert w._clear_btn.icon().isNull() is False  # noqa: SLF001
