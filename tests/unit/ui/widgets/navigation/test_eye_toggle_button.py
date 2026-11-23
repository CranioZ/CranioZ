"""Unit tests for EyeToggleButton."""

from __future__ import annotations

from cranioz.ui.icons.provider import IconProvider
from cranioz.ui.widgets.navigation.eye_toggle_button import (
    EyeToggleButton,
)


def test_starts_checked(qtbot, icon_provider: IconProvider) -> None:
    w = EyeToggleButton(icon_provider)
    qtbot.addWidget(w)
    assert w.isChecked() is True
    assert w.isCheckable() is True


def test_toggle_emits_visibility_changed(qtbot, icon_provider: IconProvider) -> None:
    w = EyeToggleButton(icon_provider)
    qtbot.addWidget(w)
    with qtbot.waitSignal(w.visibility_changed, timeout=500) as blocker:
        w.toggle()
    assert blocker.args == [False]


def test_accessible_name_reflects_state(qtbot, icon_provider: IconProvider) -> None:
    w = EyeToggleButton(icon_provider)
    qtbot.addWidget(w)
    assert w.accessibleName() == "Visible"
    w.toggle()
    assert w.accessibleName() == "Hidden"


def test_uses_real_icon_when_provider_returns_non_null(qtbot, icon_provider: IconProvider) -> None:
    w = EyeToggleButton(icon_provider)
    qtbot.addWidget(w)
    assert w.icon().isNull() is False
    assert w.text() == ""


def test_falls_back_to_text_glyph_when_icon_is_null(
    qtbot, null_icon_provider: IconProvider
) -> None:
    w = EyeToggleButton(null_icon_provider)
    qtbot.addWidget(w)
    assert w.text() == "👁"
    w.toggle()
    assert w.text() == "⊘"
