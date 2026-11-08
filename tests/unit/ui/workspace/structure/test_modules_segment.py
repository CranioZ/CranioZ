"""Tests for ModulesSegment (Phase 2, §10.10)."""

from __future__ import annotations

import pytest

from cranioz.ui.workspace.structure.modules_segment import ModulesSegment


@pytest.mark.qt
def test_starts_empty(qtbot) -> None:
    segment = ModulesSegment()
    qtbot.addWidget(segment)

    assert segment.module_ids() == ()
    assert segment.selected_module_id() is None


@pytest.mark.qt
def test_add_button_emits_signal(qtbot) -> None:
    segment = ModulesSegment()
    qtbot.addWidget(segment)

    with qtbot.waitSignal(segment.add_module_requested, timeout=1000):
        segment._add_button.click()  # noqa: SLF001


@pytest.mark.qt
def test_set_modules_populates(qtbot) -> None:
    segment = ModulesSegment()
    qtbot.addWidget(segment)

    segment.set_modules((("tomography", "Tomography"), ("osteotomy", "Osteotomy")))

    assert segment.module_ids() == ("tomography", "osteotomy")


@pytest.mark.qt
def test_set_modules_replaces_existing(qtbot) -> None:
    segment = ModulesSegment()
    qtbot.addWidget(segment)

    segment.set_modules((("a", "A"), ("b", "B")))
    segment.set_modules((("c", "C"),))

    assert segment.module_ids() == ("c",)


@pytest.mark.qt
def test_clicking_module_emits_signal(qtbot) -> None:
    segment = ModulesSegment()
    qtbot.addWidget(segment)
    segment.set_modules((("tomography", "Tomography"),))

    with qtbot.waitSignal(segment.module_selected, timeout=1000) as blocker:
        segment._module_buttons["tomography"].click()  # noqa: SLF001

    assert blocker.args[0] == "tomography"
    assert segment.selected_module_id() == "tomography"


@pytest.mark.qt
def test_clicking_selected_module_deselects(qtbot) -> None:
    segment = ModulesSegment()
    qtbot.addWidget(segment)
    segment.set_modules((("tomography", "Tomography"),))

    # First click: select.
    segment._module_buttons["tomography"].click()  # noqa: SLF001
    assert segment.selected_module_id() == "tomography"

    # Second click: deselect.
    segment._module_buttons["tomography"].click()  # noqa: SLF001
    assert segment.selected_module_id() is None


@pytest.mark.qt
def test_set_selected_marks_button(qtbot) -> None:
    segment = ModulesSegment()
    qtbot.addWidget(segment)
    segment.set_modules((("a", "A"), ("b", "B")))

    segment.set_selected("b")

    assert segment.selected_module_id() == "b"
    assert segment._module_buttons["b"].isChecked() is True  # noqa: SLF001
    assert segment._module_buttons["a"].isChecked() is False  # noqa: SLF001


@pytest.mark.qt
def test_set_selected_none_clears(qtbot) -> None:
    segment = ModulesSegment()
    qtbot.addWidget(segment)
    segment.set_modules((("a", "A"),))
    segment.set_selected("a")

    segment.set_selected(None)

    assert segment.selected_module_id() is None
    assert segment._module_buttons["a"].isChecked() is False  # noqa: SLF001


@pytest.mark.qt
def test_set_selected_unknown_raises(qtbot) -> None:
    segment = ModulesSegment()
    qtbot.addWidget(segment)
    segment.set_modules((("a", "A"),))

    with pytest.raises(KeyError, match="unknown module_id"):
        segment.set_selected("unknown")


@pytest.mark.qt
def test_set_modules_preserves_selection_when_present(qtbot) -> None:
    segment = ModulesSegment()
    qtbot.addWidget(segment)
    segment.set_modules((("a", "A"), ("b", "B")))
    segment.set_selected("b")

    segment.set_modules((("a", "A"), ("b", "B"), ("c", "C")))

    assert segment.selected_module_id() == "b"


@pytest.mark.qt
def test_set_modules_clears_selection_when_absent(qtbot) -> None:
    segment = ModulesSegment()
    qtbot.addWidget(segment)
    segment.set_modules((("a", "A"), ("b", "B")))
    segment.set_selected("b")

    segment.set_modules((("a", "A"),))

    assert segment.selected_module_id() is None


@pytest.mark.qt
def test_only_one_module_selected_at_a_time(qtbot) -> None:
    segment = ModulesSegment()
    qtbot.addWidget(segment)
    segment.set_modules((("a", "A"), ("b", "B")))

    segment.set_selected("a")
    segment.set_selected("b")

    assert segment.selected_module_id() == "b"
    assert segment._module_buttons["a"].isChecked() is False  # noqa: SLF001
    assert segment._module_buttons["b"].isChecked() is True  # noqa: SLF001
