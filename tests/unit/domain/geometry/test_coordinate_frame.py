"""Tests for CoordinateFrame."""

from __future__ import annotations

import pytest

from cranioz.domain.geometry.coordinate_frame import (
    CoordinateFrame,
    CoordinateFrameError,
)


def test_identity_frame_has_expected_defaults() -> None:
    frame = CoordinateFrame.identity()
    assert frame.name == "RAS"
    assert frame.origin == (0.0, 0.0, 0.0)
    assert frame.x_axis == (1.0, 0.0, 0.0)
    assert frame.y_axis == (0.0, 1.0, 0.0)
    assert frame.z_axis == (0.0, 0.0, 1.0)


def test_custom_origin_is_accepted() -> None:
    frame = CoordinateFrame(name="local", origin=(1.0, 2.0, 3.0))
    assert frame.origin == (1.0, 2.0, 3.0)


def test_empty_name_raises() -> None:
    with pytest.raises(CoordinateFrameError, match="name must not be empty"):
        CoordinateFrame(name="")


def test_non_finite_origin_raises() -> None:
    with pytest.raises(CoordinateFrameError, match="must be finite"):
        CoordinateFrame(name="local", origin=(float("nan"), 0.0, 0.0))


def test_frame_is_frozen() -> None:
    frame = CoordinateFrame.identity()
    with pytest.raises(AttributeError):
        frame.name = "other"  # type: ignore[misc]
