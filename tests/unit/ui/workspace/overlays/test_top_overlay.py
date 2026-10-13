"""Tests for TopOverlay.

The TopOverlay is the first concrete Overlay. It materializes the
Top Bar geometry: a fixed-height widget anchored to the top of the
Central Region with small lateral and top margins.

The tests verify:

- Identity: overlay_id and target_region are stable constants.
- Widget: widget() returns the same QWidget across calls.
- Fixed height: the widget has a fixed height equal to the
  configured one.
- Reposition: given Bounds, the widget's geometry is computed with
  the documented margins and height.
- Narrow regions: the width is clamped to 0 instead of going
  negative.
- Visibility: set_visible toggles the widget's visibility without
  destroying it.
- Custom parameters: non-default height and margins work.
- content_layout(): exposes a QLayout for future content.
"""

from __future__ import annotations

import pytest
from PySide6.QtWidgets import QFrame, QLayout, QWidget
from pytestqt.qtbot import QtBot

from cranioz.ui.workspace.areas.placement import Placement
from cranioz.ui.workspace.overlays.region import Bounds
from cranioz.ui.workspace.overlays.top_overlay import (
    TopOverlay,
    TopOverlayError,
)

# ----- Fixtures -----------------------------------------------------


@pytest.fixture
def overlay(qtbot: QtBot) -> TopOverlay:
    ov = TopOverlay()
    qtbot.addWidget(ov.widget())
    return ov


# ----- Identity -----------------------------------------------------


def test_overlay_id_is_stable(overlay: TopOverlay) -> None:
    assert overlay.overlay_id == "overlay.top_bar"


def test_target_region_is_central(overlay: TopOverlay) -> None:
    assert overlay.target_region is Placement.CENTRAL


def test_class_constants_are_accessible() -> None:
    assert TopOverlay.OVERLAY_ID == "overlay.top_bar"
    assert TopOverlay.TARGET_REGION is Placement.CENTRAL
    assert TopOverlay.DEFAULT_HEIGHT == 40
    assert TopOverlay.DEFAULT_MARGIN_X == 8
    assert TopOverlay.DEFAULT_MARGIN_Y == 8


# ----- Widget -------------------------------------------------------


def test_widget_returns_qwidget(overlay: TopOverlay) -> None:
    assert isinstance(overlay.widget(), QWidget)


def test_widget_is_a_qframe(overlay: TopOverlay) -> None:
    assert isinstance(overlay.widget(), QFrame)


def test_widget_is_stable_across_calls(overlay: TopOverlay) -> None:
    assert overlay.widget() is overlay.widget()


def test_widget_has_object_name(overlay: TopOverlay) -> None:
    assert overlay.widget().objectName() == "top_overlay"


def test_widget_has_fixed_height(overlay: TopOverlay) -> None:
    widget = overlay.widget()
    assert widget.minimumHeight() == 40
    assert widget.maximumHeight() == 40


# ----- Reposition ---------------------------------------------------


def test_reposition_sets_geometry_according_to_bounds(
    overlay: TopOverlay,
) -> None:
    bounds = Bounds(x=100.0, y=50.0, width=800.0, height=600.0)
    overlay.reposition(bounds)

    geom = overlay.widget().geometry()
    # x = bounds.x + margin_x = 100 + 8 = 108
    # y = bounds.y + margin_y = 50 + 8 = 58
    # width = bounds.width - 2 * margin_x = 800 - 16 = 784
    # height = fixed_height = 40
    assert geom.x() == 108
    assert geom.y() == 58
    assert geom.width() == 784
    assert geom.height() == 40


def test_reposition_with_origin_bounds(overlay: TopOverlay) -> None:
    bounds = Bounds(x=0.0, y=0.0, width=1000.0, height=800.0)
    overlay.reposition(bounds)

    geom = overlay.widget().geometry()
    assert geom.x() == 8
    assert geom.y() == 8
    assert geom.width() == 1000 - 16
    assert geom.height() == 40


def test_reposition_clamps_negative_width_to_zero(
    overlay: TopOverlay,
) -> None:
    # Region narrower than twice the margin. Expected: width = 0.
    bounds = Bounds(x=0.0, y=0.0, width=10.0, height=100.0)
    overlay.reposition(bounds)

    geom = overlay.widget().geometry()
    assert geom.width() == 0
    assert geom.height() == 40


def test_reposition_is_idempotent(overlay: TopOverlay) -> None:
    bounds = Bounds(x=10.0, y=20.0, width=500.0, height=400.0)
    overlay.reposition(bounds)
    first = overlay.widget().geometry()

    overlay.reposition(bounds)
    second = overlay.widget().geometry()

    assert first == second


def test_reposition_can_be_called_multiple_times(
    overlay: TopOverlay,
) -> None:
    overlay.reposition(Bounds(x=0.0, y=0.0, width=100.0, height=100.0))
    overlay.reposition(Bounds(x=50.0, y=60.0, width=700.0, height=600.0))

    geom = overlay.widget().geometry()
    assert geom.x() == 58
    assert geom.y() == 68
    assert geom.width() == 700 - 16


# ----- Visibility ---------------------------------------------------


def test_overlay_starts_visible(overlay: TopOverlay) -> None:
    assert overlay.is_visible() is True


def test_set_visible_false_hides_widget(overlay: TopOverlay) -> None:
    overlay.set_visible(False)
    assert overlay.is_visible() is False
    assert overlay.widget().isVisible() is False


def test_set_visible_true_shows_widget(overlay: TopOverlay) -> None:
    overlay.set_visible(False)
    overlay.set_visible(True)
    assert overlay.is_visible() is True


def test_visibility_toggle_does_not_destroy_widget(
    overlay: TopOverlay,
) -> None:
    widget = overlay.widget()
    overlay.set_visible(False)
    overlay.set_visible(True)
    assert overlay.widget() is widget


# ----- Custom parameters --------------------------------------------


def test_custom_height(qtbot: QtBot) -> None:
    ov = TopOverlay(height=60)
    qtbot.addWidget(ov.widget())

    assert ov.height == 60
    assert ov.widget().minimumHeight() == 60
    assert ov.widget().maximumHeight() == 60

    ov.reposition(Bounds(x=0.0, y=0.0, width=100.0, height=100.0))
    assert ov.widget().geometry().height() == 60


def test_custom_margins(qtbot: QtBot) -> None:
    ov = TopOverlay(margin_x=20, margin_y=15)
    qtbot.addWidget(ov.widget())

    assert ov.margin_x == 20
    assert ov.margin_y == 15

    ov.reposition(Bounds(x=100.0, y=50.0, width=800.0, height=600.0))
    geom = ov.widget().geometry()
    assert geom.x() == 120  # 100 + 20
    assert geom.y() == 65  # 50 + 15
    assert geom.width() == 800 - 40  # 800 - 2*20


def test_zero_margins(qtbot: QtBot) -> None:
    ov = TopOverlay(margin_x=0, margin_y=0)
    qtbot.addWidget(ov.widget())

    ov.reposition(Bounds(x=10.0, y=20.0, width=100.0, height=100.0))
    geom = ov.widget().geometry()
    assert geom.x() == 10
    assert geom.y() == 20
    assert geom.width() == 100


# ----- Validation ---------------------------------------------------


def test_non_positive_height_raises() -> None:
    with pytest.raises(TopOverlayError, match="height"):
        TopOverlay(height=0)
    with pytest.raises(TopOverlayError, match="height"):
        TopOverlay(height=-1)


def test_negative_margin_x_raises() -> None:
    with pytest.raises(TopOverlayError, match="margin_x"):
        TopOverlay(margin_x=-1)


def test_negative_margin_y_raises() -> None:
    with pytest.raises(TopOverlayError, match="margin_y"):
        TopOverlay(margin_y=-1)


# ----- Content layout -----------------------------------------------


def test_content_layout_returns_qlayout(overlay: TopOverlay) -> None:
    layout = overlay.content_layout()
    assert isinstance(layout, QLayout)


def test_content_layout_is_stable(overlay: TopOverlay) -> None:
    assert overlay.content_layout() is overlay.content_layout()
