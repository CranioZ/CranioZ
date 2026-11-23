"""Unit tests for SignaturePreview."""

from __future__ import annotations

import pytest
from PySide6.QtGui import QPixmap

from cranioz.ui.widgets.forms import SignaturePreview


@pytest.fixture
def preview(qtbot):
    widget = SignaturePreview()
    qtbot.addWidget(widget)
    return widget


def test_empty_state(preview):
    assert preview.has_signature is False
    assert preview.signature is None


def test_set_signature_emits_and_marks_has_signature(preview, qtbot):
    pixmap = QPixmap(50, 20)
    pixmap.fill()
    with qtbot.waitSignal(preview.signature_changed, timeout=500):
        preview.set_signature(pixmap)
    assert preview.has_signature is True


def test_clear_emits_and_returns_to_empty(preview, qtbot):
    pixmap = QPixmap(50, 20)
    pixmap.fill()
    preview.set_signature(pixmap)
    with qtbot.waitSignal(preview.signature_changed, timeout=500):
        preview.clear()
    assert preview.has_signature is False


def test_set_null_pixmap_treated_as_empty(preview, qtbot):
    null = QPixmap()
    with qtbot.waitSignal(preview.signature_changed, timeout=500):
        preview.set_signature(null)
    assert preview.has_signature is False


def test_clear_on_empty_does_not_emit(preview, qtbot):
    with qtbot.assertNotEmitted(preview.signature_changed):
        preview.clear()


def test_minimum_size(preview):
    assert preview.minimumWidth() >= 200
    assert preview.minimumHeight() >= 80


def test_accessible_name(preview):
    assert preview.accessibleName() == "Signature preview"
