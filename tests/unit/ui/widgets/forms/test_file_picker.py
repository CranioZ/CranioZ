"""Unit tests for FilePicker."""

from __future__ import annotations

import pytest
from PySide6.QtWidgets import QToolButton

from cranioz.ui.widgets.forms import FilePicker, FilePickerMode


@pytest.fixture
def picker(qtbot):
    widget = FilePicker(label="Profile picture", mode=FilePickerMode.OPEN_FILE)
    qtbot.addWidget(widget)
    return widget


def test_default_state(picker):
    assert picker.label == "Profile picture"
    assert picker.path == ""
    assert picker.mode is FilePickerMode.OPEN_FILE


def test_set_path_emits(picker, qtbot, tmp_path):
    safe_path = str(tmp_path / "a.png")
    with qtbot.waitSignal(picker.path_changed, timeout=500) as blocker:
        picker.set_path(safe_path)
    assert blocker.args == [safe_path]
    assert picker.path == safe_path


def test_set_same_path_does_not_emit(picker, qtbot, tmp_path):
    safe_path = str(tmp_path / "a.png")
    picker.set_path(safe_path)
    with qtbot.assertNotEmitted(picker.path_changed):
        picker.set_path(safe_path)


def test_clear(picker, qtbot):
    picker.set_path("/x")
    with qtbot.waitSignal(picker.path_changed, timeout=500) as blocker:
        picker.clear()
    assert blocker.args == [""]
    assert picker.path == ""


def test_directory_mode(qtbot):
    widget = FilePicker(mode=FilePickerMode.OPEN_DIRECTORY)
    qtbot.addWidget(widget)
    assert widget.mode is FilePickerMode.OPEN_DIRECTORY


def test_save_mode(qtbot):
    widget = FilePicker(mode=FilePickerMode.SAVE_FILE)
    qtbot.addWidget(widget)
    assert widget.mode is FilePickerMode.SAVE_FILE


def test_accessible_name_reflects_label(picker):
    assert picker.accessibleName() == "Profile picture"


def test_browse_button_is_secondary(qtbot):
    widget = FilePicker(label="X")
    qtbot.addWidget(widget)
    button = widget.findChild(QToolButton, "CraniozFilePickerBrowse")
    assert button is not None
    assert button.property("class") == "secondary"
