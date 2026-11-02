"""Tests for VolumeGeometry.

The geometry is the most critical piece of the imaging domain:
it defines the relationship between voxel indices and physical
coordinates. The tests cover:

- Construction and validation (dimensions, spacing, origin,
  direction orthonormality, determinant).
- Index-to-world and world-to-index mapping.
- Round-trip mapping consistency.
- Coordinate containment.
- The identity constructor.
"""

from __future__ import annotations

import dataclasses

import numpy as np
import pytest

from cranioz.domain.imaging.coordinate_system import CoordinateSystem
from cranioz.domain.imaging.volume_geometry import (
    VolumeGeometry,
    VolumeGeometryError,
)

# ----- Construction -------------------------------------------------


def test_identity_geometry() -> None:
    geom = VolumeGeometry.identity(dimensions=(10, 20, 30))
    assert geom.dimensions == (10, 20, 30)
    assert geom.spacing == (1.0, 1.0, 1.0)
    assert geom.origin == (0.0, 0.0, 0.0)
    assert geom.coordinate_system is CoordinateSystem.RAS


def test_identity_geometry_with_custom_spacing_and_origin() -> None:
    geom = VolumeGeometry.identity(
        dimensions=(10, 20, 30),
        spacing=(0.5, 0.5, 2.0),
        origin=(100.0, 50.0, 25.0),
    )
    assert geom.spacing == (0.5, 0.5, 2.0)
    assert geom.origin == (100.0, 50.0, 25.0)


def test_geometry_is_frozen() -> None:
    geom = VolumeGeometry.identity(dimensions=(10, 20, 30))
    attr = "dimensions"
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(geom, attr, (1, 2, 3))


def test_negative_dimensions_raise() -> None:
    with pytest.raises(VolumeGeometryError, match="dimensions"):
        VolumeGeometry.identity(dimensions=(-1, 10, 10))


def test_zero_dimensions_raise() -> None:
    with pytest.raises(VolumeGeometryError, match="dimensions"):
        VolumeGeometry.identity(dimensions=(0, 10, 10))


def test_negative_spacing_raises() -> None:
    with pytest.raises(VolumeGeometryError, match="spacing"):
        VolumeGeometry.identity(dimensions=(10, 10, 10), spacing=(-1.0, 1.0, 1.0))


def test_zero_spacing_raises() -> None:
    with pytest.raises(VolumeGeometryError, match="spacing"):
        VolumeGeometry.identity(dimensions=(10, 10, 10), spacing=(0.0, 1.0, 1.0))


def test_non_orthonormal_direction_raises() -> None:
    with pytest.raises(VolumeGeometryError, match="orthonormal"):
        VolumeGeometry(
            dimensions=(10, 10, 10),
            origin=(0.0, 0.0, 0.0),
            spacing=(1.0, 1.0, 1.0),
            direction=(
                (1.0, 0.0, 0.0),
                (0.0, 1.0, 0.0),
                (0.5, 0.0, 1.0),  # not orthonormal (shear)
            ),
        )


def test_direction_with_non_unit_determinant_raises() -> None:
    """A non-orthonormal matrix is rejected by the orthonormality check.

    The determinant check is a defence-in-depth validation: if the
    matrix is orthonormal, its determinant is necessarily ±1 by
    definition. A matrix that fails the orthonormality check will
    never reach the determinant check. This test documents that
    a scaled identity matrix is rejected (as orthonormal), not
    as a determinant failure.
    """
    with pytest.raises(VolumeGeometryError, match="orthonormal"):
        VolumeGeometry(
            dimensions=(10, 10, 10),
            origin=(0.0, 0.0, 0.0),
            spacing=(1.0, 1.0, 1.0),
            direction=(
                (2.0, 0.0, 0.0),
                (0.0, 2.0, 0.0),
                (0.0, 0.0, 2.0),
            ),
        )


# ----- Index <-> World ---------------------------------------------


def test_index_to_world_identity() -> None:
    geom = VolumeGeometry.identity(
        dimensions=(10, 20, 30),
        spacing=(0.5, 0.5, 2.0),
        origin=(100.0, 50.0, 25.0),
    )
    world = geom.index_to_world((0, 0, 0))
    assert world == (100.0, 50.0, 25.0)

    world = geom.index_to_world((1, 2, 3))
    assert world == pytest.approx(
        (100.5, 51.0, 31.0),
        abs=1e-9,
    )


def test_world_to_index_identity() -> None:
    geom = VolumeGeometry.identity(
        dimensions=(10, 20, 30),
        spacing=(0.5, 0.5, 2.0),
        origin=(100.0, 50.0, 25.0),
    )
    index = geom.world_to_index((100.5, 51.0, 31.0))
    assert index == pytest.approx((1.0, 2.0, 3.0), abs=1e-9)


def test_round_trip_index_world() -> None:
    geom = VolumeGeometry.identity(
        dimensions=(10, 20, 30),
        spacing=(0.5, 0.5, 2.0),
        origin=(100.0, 50.0, 25.0),
    )
    for index in [(0, 0, 0), (5, 10, 15), (9, 19, 29)]:
        world = geom.index_to_world(index)
        recovered = geom.world_to_index(world)
        assert recovered == pytest.approx(index, abs=1e-9)


def test_round_trip_with_rotated_direction() -> None:
    # 90-degree rotation around Z axis.
    geom = VolumeGeometry(
        dimensions=(10, 10, 10),
        origin=(0.0, 0.0, 0.0),
        spacing=(1.0, 1.0, 1.0),
        direction=(
            (0.0, -1.0, 0.0),
            (1.0, 0.0, 0.0),
            (0.0, 0.0, 1.0),
        ),
    )
    for index in [(0, 0, 0), (5, 5, 5), (9, 9, 9)]:
        world = geom.index_to_world(index)
        recovered = geom.world_to_index(world)
        assert recovered == pytest.approx(index, abs=1e-9)


# ----- Containment --------------------------------------------------


def test_contains_world_inside() -> None:
    geom = VolumeGeometry.identity(
        dimensions=(10, 10, 10),
        spacing=(1.0, 1.0, 1.0),
        origin=(0.0, 0.0, 0.0),
    )
    assert geom.contains_world((5.0, 5.0, 5.0))
    assert geom.contains_world((0.0, 0.0, 0.0))
    assert geom.contains_world((9.0, 9.0, 9.0))


def test_contains_world_outside() -> None:
    geom = VolumeGeometry.identity(
        dimensions=(10, 10, 10),
        spacing=(1.0, 1.0, 1.0),
        origin=(0.0, 0.0, 0.0),
    )
    assert not geom.contains_world((-0.5, 5.0, 5.0))
    assert not geom.contains_world((5.0, -0.5, 5.0))
    assert not geom.contains_world((9.5, 5.0, 5.0))


# ----- Shape accessors ---------------------------------------------


def test_shape_zyx() -> None:
    geom = VolumeGeometry.identity(dimensions=(10, 20, 30))
    assert geom.shape_zyx == (30, 20, 10)


def test_direction_array() -> None:
    geom = VolumeGeometry.identity(dimensions=(10, 10, 10))
    d = geom.direction_array
    assert isinstance(d, np.ndarray)
    assert d.shape == (3, 3)
    assert np.allclose(d, np.eye(3))
