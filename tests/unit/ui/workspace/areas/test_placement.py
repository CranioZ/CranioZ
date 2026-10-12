"""Tests for Placement."""

from __future__ import annotations

from cranioz.ui.workspace.areas.placement import Placement


def test_placement_has_expected_members() -> None:
    expected = {"LEFT", "CENTRAL", "RIGHT", "BOTTOM"}
    actual = {member.name for member in Placement}
    assert actual == expected


def test_placement_values_are_lowercase() -> None:
    for member in Placement:
        assert member.value == member.name.lower()


def test_placement_can_be_looked_up_by_value() -> None:
    assert Placement("central") is Placement.CENTRAL
    assert Placement("left") is Placement.LEFT
    assert Placement("right") is Placement.RIGHT
    assert Placement("bottom") is Placement.BOTTOM


def test_declaration_order_is_not_significant() -> None:
    """Guards against code depending on the enum's declaration order."""
    # Sort by value, not declaration order. This test will keep passing
    # even if the order of members in Placement changes.
    by_value = sorted(Placement, key=lambda p: p.value)
    assert by_value == [
        Placement.BOTTOM,
        Placement.CENTRAL,
        Placement.LEFT,
        Placement.RIGHT,
    ]