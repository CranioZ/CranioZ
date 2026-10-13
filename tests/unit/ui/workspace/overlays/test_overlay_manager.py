"""Tests for OverlayManager.

The OverlayManager coordinates a set of Overlays: registration,
lookup, and repositioning when the layout changes. It does not
create Overlays and does not compute geometry.

These tests use a FakeOverlay: a concrete Overlay subclass that
records the Bounds it receives, so we can assert that
``reposition_all()`` routed the correct Bounds to the correct
Overlay.

The FakeOverlay uses a real QWidget (QLabel) because the Overlay
contract requires ``widget()`` to return a QWidget. The tests use
``qtbot`` and therefore a QApplication.
"""

from __future__ import annotations

import pytest
from PySide6.QtWidgets import QLabel, QWidget
from pytestqt.qtbot import QtBot

from cranioz.ui.workspace.areas.area import Area
from cranioz.ui.workspace.areas.placement import Placement
from cranioz.ui.workspace.overlays.overlay import Overlay
from cranioz.ui.workspace.overlays.overlay_manager import (
    OverlayManager,
    OverlayManagerError,
)
from cranioz.ui.workspace.overlays.region import Bounds, Region

# ----- Test helpers -------------------------------------------------


class FakeOverlay(Overlay):
    """Minimal Overlay that records the last Bounds it received."""

    def __init__(
        self,
        overlay_id: str,
        target_region: Placement = Placement.CENTRAL,
        widget: QWidget | None = None,
    ) -> None:
        self._overlay_id = overlay_id
        self._target_region = target_region
        self._widget = widget if widget is not None else QLabel(overlay_id)
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

    @property
    def last_bounds(self) -> Bounds | None:
        return self._last_bounds


def _region(
    region_id: str,
    placement: Placement,
    bounds: Bounds | None = None,
) -> Region:
    """Build a Region with a single synthetic Area placeholder.

    The OverlayManager never inspects the Areas, only the
    ``semantic_role`` and ``bounds``. A synthetic Area is enough.
    """

    area = Area(area_id=f"area.{region_id}", title=region_id, placement=placement)
    return Region(
        region_id=region_id,
        bounds=bounds if bounds is not None else Bounds(),
        areas=(area,),
        semantic_role=placement,
    )


@pytest.fixture
def manager() -> OverlayManager:
    return OverlayManager()


@pytest.fixture
def make_overlay(qtbot: QtBot):
    """Factory to build FakeOverlay instances and register their widgets."""

    def _factory(
        overlay_id: str,
        target_region: Placement = Placement.CENTRAL,
    ) -> FakeOverlay:
        overlay = FakeOverlay(
            overlay_id=overlay_id,
            target_region=target_region,
        )
        qtbot.addWidget(overlay.widget())
        return overlay

    return _factory


# ----- Registration -------------------------------------------------


def test_new_manager_is_empty(manager: OverlayManager) -> None:
    assert manager.overlays() == ()
    assert manager.overlay_count() == 0


def test_register_adds_overlay(manager: OverlayManager, make_overlay) -> None:
    overlay = make_overlay("overlay.top_bar")
    manager.register(overlay)

    assert manager.contains("overlay.top_bar")
    assert manager.overlay_count() == 1
    assert manager.get("overlay.top_bar") is overlay


def test_register_same_instance_is_idempotent(manager: OverlayManager, make_overlay) -> None:
    overlay = make_overlay("overlay.top_bar")
    manager.register(overlay)
    manager.register(overlay)
    assert manager.overlay_count() == 1


def test_register_different_instance_same_id_raises(manager: OverlayManager, make_overlay) -> None:
    a = make_overlay("overlay.top_bar")
    b = make_overlay("overlay.top_bar")
    manager.register(a)
    with pytest.raises(OverlayManagerError, match="different Overlay"):
        manager.register(b)


def test_register_empty_id_raises(manager: OverlayManager, qtbot: QtBot) -> None:
    # FakeOverlay permits empty ids for test purposes; the manager
    # must reject them.
    overlay = FakeOverlay(overlay_id="")
    qtbot.addWidget(overlay.widget())

    with pytest.raises(OverlayManagerError, match="must not be empty"):
        manager.register(overlay)


def test_registration_order_is_preserved(manager: OverlayManager, make_overlay) -> None:
    a = make_overlay("overlay.a")
    b = make_overlay("overlay.b")
    c = make_overlay("overlay.c")
    manager.register(a)
    manager.register(b)
    manager.register(c)

    assert manager.overlays() == (a, b, c)


# ----- Lookup -------------------------------------------------------


def test_get_unknown_returns_none(manager: OverlayManager) -> None:
    assert manager.get("overlay.unknown") is None


def test_require_returns_overlay(manager: OverlayManager, make_overlay) -> None:
    overlay = make_overlay("overlay.top_bar")
    manager.register(overlay)
    assert manager.require("overlay.top_bar") is overlay


def test_require_unknown_raises(manager: OverlayManager) -> None:
    with pytest.raises(KeyError, match="not registered"):
        manager.require("overlay.unknown")


def test_contains(manager: OverlayManager, make_overlay) -> None:
    assert manager.contains("overlay.x") is False
    manager.register(make_overlay("overlay.x"))
    assert manager.contains("overlay.x") is True


# ----- Unregister ---------------------------------------------------


def test_unregister_returns_overlay(manager: OverlayManager, make_overlay) -> None:
    overlay = make_overlay("overlay.a")
    manager.register(overlay)

    removed = manager.unregister("overlay.a")
    assert removed is overlay
    assert not manager.contains("overlay.a")


def test_unregister_unknown_returns_none(manager: OverlayManager) -> None:
    assert manager.unregister("overlay.unknown") is None


def test_unregister_does_not_destroy_widget(
    manager: OverlayManager, make_overlay, qtbot: QtBot
) -> None:
    overlay = make_overlay("overlay.a")
    widget = overlay.widget()
    qtbot.addWidget(widget)

    manager.register(overlay)
    manager.unregister("overlay.a")

    # The widget instance is unchanged; the manager only dropped
    # its reference to the Overlay.
    assert overlay.widget() is widget


# ----- Clear --------------------------------------------------------


def test_clear_removes_all(manager: OverlayManager, make_overlay) -> None:
    manager.register(make_overlay("overlay.a"))
    manager.register(make_overlay("overlay.b"))

    manager.clear()

    assert manager.overlay_count() == 0
    assert manager.overlays() == ()


def test_clear_on_empty_is_noop(manager: OverlayManager) -> None:
    manager.clear()
    assert manager.overlay_count() == 0


# ----- Repositioning ------------------------------------------------


def test_reposition_all_with_no_overlays_is_noop(
    manager: OverlayManager,
) -> None:
    manager.reposition_all(())  # must not raise


def test_reposition_all_with_no_regions_is_noop(manager: OverlayManager, make_overlay) -> None:
    overlay = make_overlay("overlay.a", target_region=Placement.CENTRAL)
    manager.register(overlay)

    manager.reposition_all(())

    assert overlay.last_bounds is None


def test_reposition_all_routes_bounds_by_placement(manager: OverlayManager, make_overlay) -> None:
    central = make_overlay("overlay.central", target_region=Placement.CENTRAL)
    bottom = make_overlay("overlay.bottom", target_region=Placement.BOTTOM)
    manager.register(central)
    manager.register(bottom)

    central_bounds = Bounds(x=100.0, y=50.0, width=800.0, height=600.0)
    bottom_bounds = Bounds(x=0.0, y=650.0, width=1000.0, height=200.0)
    regions = (
        _region("central", Placement.CENTRAL, central_bounds),
        _region("bottom", Placement.BOTTOM, bottom_bounds),
    )

    manager.reposition_all(regions)

    assert central.last_bounds == central_bounds
    assert bottom.last_bounds == bottom_bounds


def test_reposition_all_leaves_overlays_without_matching_region(
    manager: OverlayManager, make_overlay
) -> None:
    # The overlay targets CENTRAL, but the current layout has no
    # CENTRAL region.
    overlay = make_overlay("overlay.central", target_region=Placement.CENTRAL)
    manager.register(overlay)

    regions = (_region("left", Placement.LEFT),)
    manager.reposition_all(regions)

    assert overlay.last_bounds is None


def test_reposition_all_skips_regions_without_semantic_role(
    manager: OverlayManager, make_overlay
) -> None:
    overlay = make_overlay("overlay.central", target_region=Placement.CENTRAL)
    manager.register(overlay)

    # A Region with semantic_role=None should never be used to route
    # bounds; find_regions() always sets it, but defensive code is
    # still correct.
    area = Area(area_id="area.x", title="x", placement=Placement.CENTRAL)
    orphan = Region(
        region_id="orphan",
        bounds=Bounds(x=1.0, y=1.0, width=1.0, height=1.0),
        areas=(area,),
        semantic_role=None,
    )
    manager.reposition_all((orphan,))

    assert overlay.last_bounds is None


def test_reposition_all_can_be_called_multiple_times(manager: OverlayManager, make_overlay) -> None:
    overlay = make_overlay("overlay.central", target_region=Placement.CENTRAL)
    manager.register(overlay)

    first = Bounds(x=0.0, y=0.0, width=100.0, height=100.0)
    second = Bounds(x=10.0, y=10.0, width=200.0, height=200.0)

    manager.reposition_all((_region("central", Placement.CENTRAL, first),))
    assert overlay.last_bounds == first

    manager.reposition_all((_region("central", Placement.CENTRAL, second),))
    assert overlay.last_bounds == second


def test_reposition_all_uses_first_matching_region_if_duplicated(
    manager: OverlayManager, make_overlay
) -> None:
    # A pathological case: two regions with the same semantic_role.
    # The manager should deterministically pick one (the first seen).
    overlay = make_overlay("overlay.central", target_region=Placement.CENTRAL)
    manager.register(overlay)

    first = Bounds(x=0.0, y=0.0, width=10.0, height=10.0)
    second = Bounds(x=0.0, y=0.0, width=20.0, height=20.0)

    manager.reposition_all(
        (
            _region("central.a", Placement.CENTRAL, first),
            _region("central.b", Placement.CENTRAL, second),
        )
    )

    assert overlay.last_bounds == first


# ----- Representation -----------------------------------------------


def test_repr_contains_registered_ids(manager: OverlayManager, make_overlay) -> None:
    manager.register(make_overlay("overlay.a"))
    text = repr(manager)
    assert "overlay.a" in text
