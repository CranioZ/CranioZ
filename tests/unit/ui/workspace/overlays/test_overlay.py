"""Tests for the Overlay ABC.

The Overlay ABC is an abstract interface. To exercise it we define
a concrete subclass, ``FakeOverlay``, that implements every abstract
method with the minimal behaviour required by the contract.

The FakeOverlay uses a real QWidget (a QLabel). The tests that
instantiate it use ``qtbot`` and therefore require a QApplication.
The tests that only inspect the abstract methods do not create a
widget and could in principle run without Qt; we keep them together
for clarity.

These tests verify:

- The ABC cannot be instantiated directly.
- A concrete subclass must implement every abstract method.
- overlay_id and target_region are readable.
- widget() returns the QWidget provided by the subclass.
- reposition() records the Bounds it receives.
- set_visible() / is_visible() work as expected.
"""

from __future__ import annotations

import pytest
from PySide6.QtWidgets import QLabel, QWidget
from pytestqt.qtbot import QtBot

from cranioz.ui.workspace.areas.placement import Placement
from cranioz.ui.workspace.overlays.overlay import Overlay
from cranioz.ui.workspace.overlays.region import Bounds

# ----- Concrete test implementation ---------------------------------


class FakeOverlay(Overlay):
    """Minimal concrete Overlay used only in tests."""

    def __init__(
        self,
        overlay_id: str = "overlay.test",
        target_region: Placement = Placement.CENTRAL,
        widget: QWidget | None = None,
    ) -> None:
        self._overlay_id = overlay_id
        self._target_region = target_region
        self._widget = widget if widget is not None else QLabel("Fake")
        self._visible = True
        self._last_bounds: Bounds | None = None

    @property
    def overlay_id(self) -> str:
        return self._overlay_id

    @property
    def target_region(self) -> Placement:
        return self._target_region

    def widget(self) -> QWidget:
        return self._widget

    def reposition(self, bounds: Bounds) -> None:
        self._last_bounds = bounds

    def set_visible(self, visible: bool) -> None:
        self._visible = visible
        self._widget.setVisible(visible)

    def is_visible(self) -> bool:
        return self._visible

    # ----- Test-only accessors ---------------------------------------

    @property
    def last_bounds(self) -> Bounds | None:
        return self._last_bounds


# ----- Abstractness -------------------------------------------------


def test_overlay_is_abstract() -> None:
    with pytest.raises(TypeError):
        Overlay()  # type: ignore[abstract]


def test_concrete_overlay_can_be_instantiated(qtbot: QtBot) -> None:
    overlay = FakeOverlay()
    qtbot.addWidget(overlay.widget())
    assert isinstance(overlay, Overlay)


# ----- Identity -----------------------------------------------------


def test_overlay_id_is_readable(qtbot: QtBot) -> None:
    overlay = FakeOverlay(overlay_id="overlay.top_bar")
    qtbot.addWidget(overlay.widget())
    assert overlay.overlay_id == "overlay.top_bar"


def test_target_region_is_readable(qtbot: QtBot) -> None:
    overlay = FakeOverlay(target_region=Placement.CENTRAL)
    qtbot.addWidget(overlay.widget())
    assert overlay.target_region is Placement.CENTRAL


def test_target_region_accepts_all_placements(qtbot: QtBot) -> None:
    for placement in Placement:
        overlay = FakeOverlay(target_region=placement)
        qtbot.addWidget(overlay.widget())
        assert overlay.target_region is placement


# ----- Widget -------------------------------------------------------


def test_widget_returns_qwidget(qtbot: QtBot) -> None:
    overlay = FakeOverlay()
    widget = overlay.widget()
    qtbot.addWidget(widget)
    assert isinstance(widget, QWidget)


def test_widget_is_stable_across_calls(qtbot: QtBot) -> None:
    overlay = FakeOverlay()
    first = overlay.widget()
    second = overlay.widget()
    qtbot.addWidget(first)
    assert first is second


# ----- Reposition ---------------------------------------------------


def test_reposition_records_bounds(qtbot: QtBot) -> None:
    overlay = FakeOverlay()
    qtbot.addWidget(overlay.widget())

    bounds = Bounds(x=100.0, y=50.0, width=800.0, height=600.0)
    overlay.reposition(bounds)

    assert overlay.last_bounds == bounds


def test_reposition_accepts_placeholder_bounds(qtbot: QtBot) -> None:
    overlay = FakeOverlay()
    qtbot.addWidget(overlay.widget())

    overlay.reposition(Bounds())
    assert overlay.last_bounds is not None
    assert overlay.last_bounds.is_placeholder() is True


def test_reposition_can_be_called_multiple_times(qtbot: QtBot) -> None:
    overlay = FakeOverlay()
    qtbot.addWidget(overlay.widget())

    first = Bounds(x=0.0, y=0.0, width=100.0, height=100.0)
    second = Bounds(x=10.0, y=10.0, width=200.0, height=200.0)

    overlay.reposition(first)
    overlay.reposition(second)

    assert overlay.last_bounds == second


# ----- Visibility ---------------------------------------------------


def test_overlay_starts_visible(qtbot: QtBot) -> None:
    overlay = FakeOverlay()
    qtbot.addWidget(overlay.widget())
    assert overlay.is_visible() is True


def test_set_visible_false_hides_overlay(qtbot: QtBot) -> None:
    overlay = FakeOverlay()
    qtbot.addWidget(overlay.widget())

    overlay.set_visible(False)

    assert overlay.is_visible() is False
    assert overlay.widget().isVisible() is False


def test_set_visible_true_shows_overlay(qtbot: QtBot) -> None:
    overlay = FakeOverlay()
    qtbot.addWidget(overlay.widget())

    overlay.set_visible(False)
    overlay.set_visible(True)

    assert overlay.is_visible() is True


def test_visibility_toggle_does_not_destroy_widget(qtbot: QtBot) -> None:
    overlay = FakeOverlay()
    widget = overlay.widget()
    qtbot.addWidget(widget)

    overlay.set_visible(False)
    overlay.set_visible(True)

    # The widget instance is the same throughout.
    assert overlay.widget() is widget
