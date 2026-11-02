"""VolumeGeometry — spatial geometry of a 3D volume.

This is the most important class of the imaging domain. It defines
the relationship between voxel indices (i, j, k) and physical
coordinates (RAS, in millimetres).

The mapping is:

    P_world = O + D · (S ⊙ P_index)

where:
    - O is the origin (physical position of voxel 0,0,0).
    - D is the 3x3 direction matrix (orientation).
    - S is the spacing vector (sx, sy, sz).
    - P_index is the voxel index (i, j, k).
    - ⊙ is component-wise multiplication.

The direction matrix is what allows correct MPR reconstruction of
coronal and sagittal planes from an axial stack. Without it, the
reslice axes are wrong and the resulting images are distorted.

The direction matrix MUST be orthonormal (rotation only, no shear).
Gantry tilt (shear) is explicitly rejected at construction time
and must be handled by the DICOM reader (by resampling or by
rejecting the dataset).

See Medical Imaging Infrastructure §4.2, §5.3.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from cranioz.domain.imaging.coordinate_system import CoordinateSystem


class VolumeGeometryError(ValueError):
    """Raised when the volume geometry is invalid or inconsistent."""


@dataclass(frozen=True)
class VolumeGeometry:
    """Spatial geometry of a 3D volume.

    All spatial units are millimetres. The internal coordinate system
    is RAS.
    """

    #: Physical dimensions of the volume, in voxels (nx, ny, nz).
    dimensions: tuple[int, int, int]

    #: Physical position of the first voxel (0, 0, 0), in millimetres.
    origin: tuple[float, float, float]

    #: Voxel spacing along each axis, in millimetres (sx, sy, sz).
    spacing: tuple[float, float, float]

    #: 3x3 direction matrix (row-major), orthonormal.
    #: Maps voxel axes to physical axes.
    direction: tuple[
        tuple[float, float, float],
        tuple[float, float, float],
        tuple[float, float, float],
    ]

    #: Coordinate convention of `origin` and `direction`.
    coordinate_system: CoordinateSystem = CoordinateSystem.RAS

    def __post_init__(self) -> None:
        # Dimensions must be positive.
        if any(d <= 0 for d in self.dimensions):
            raise VolumeGeometryError(f"dimensions must be positive, got {self.dimensions}")

        # Spacing must be positive and finite.
        if any(s <= 0 or not math.isfinite(s) for s in self.spacing):
            raise VolumeGeometryError(f"spacing must be positive and finite, got {self.spacing}")

        # Origin must be finite.
        if any(not math.isfinite(o) for o in self.origin):
            raise VolumeGeometryError(f"origin must be finite, got {self.origin}")

        # Direction matrix must be 3x3.
        if len(self.direction) != 3 or any(len(row) != 3 for row in self.direction):
            raise VolumeGeometryError(f"direction must be a 3x3 matrix, got {self.direction}")

        # Direction matrix must be orthonormal (rotation only).
        # Check by computing D^T D and verifying it is (close to) identity.
        d = np.array(self.direction, dtype=np.float64)
        dtd = d.T @ d
        identity = np.eye(3)
        if not np.allclose(dtd, identity, atol=1e-6):
            raise VolumeGeometryError(
                "direction matrix must be orthonormal (rotation only). "
                f"Got D^T D =\n{dtd}\n"
                "Gantry tilt (shear) is not supported. "
                "Resample or reject the dataset before constructing "
                "the geometry."
            )

        # The determinant of an orthonormal matrix must be ±1.
        # A negative determinant represents a reflection, which is
        # valid for LPS-to-RAS conversion but must be handled
        # explicitly by the caller.
        det = float(np.linalg.det(d))
        if not math.isclose(abs(det), 1.0, abs_tol=1e-6):
            raise VolumeGeometryError(f"direction matrix determinant must be ±1, got {det}")

    # ----- Convenience accessors ------------------------------------

    @property
    def shape_zyx(self) -> tuple[int, int, int]:
        """Return dimensions in NumPy `[z, y, x]` order.

        This is the array order used by the Volume buffer.
        """
        nx, ny, nz = self.dimensions
        return (nz, ny, nx)

    @property
    def direction_array(self) -> np.ndarray:
        """Return the direction matrix as a NumPy 3x3 array."""
        return np.array(self.direction, dtype=np.float64)

    @property
    def origin_array(self) -> np.ndarray:
        return np.array(self.origin, dtype=np.float64)

    @property
    def spacing_array(self) -> np.ndarray:
        return np.array(self.spacing, dtype=np.float64)

    # ----- Index <-> World mapping ----------------------------------

    def index_to_world(
        self,
        index: tuple[int, int, int],
    ) -> tuple[float, float, float]:
        """Map a voxel index (i, j, k) to a physical coordinate (RAS).

        Uses the formula:

            P_world = O + D · (S ⊙ P_index)

        See Medical Imaging Infrastructure §5.3.
        """
        if len(index) != 3:
            raise ValueError(f"index must have 3 components, got {index}")

        i, j, k = index
        sx, sy, sz = self.spacing
        ox, oy, oz = self.origin
        d = self.direction_array

        # Component-wise spacing multiplication.
        scaled = np.array([i * sx, j * sy, k * sz], dtype=np.float64)

        # Apply direction matrix.
        rotated = d @ scaled

        # Translate by origin.
        world = rotated + np.array([ox, oy, oz], dtype=np.float64)

        return (float(world[0]), float(world[1]), float(world[2]))

    def world_to_index(
        self,
        world: tuple[float, float, float],
    ) -> tuple[float, float, float]:
        """Map a physical coordinate (RAS) to a voxel index (i, j, k).

        Returns floating-point indices. Callers that need integer
        indices must round explicitly and handle out-of-bounds cases.

        Uses the inverse of the index_to_world formula:

            P_index = (D^-1 · (P_world - O)) / S

        Since D is orthonormal, D^-1 = D^T.
        """
        if len(world) != 3:
            raise ValueError(f"world must have 3 components, got {world}")

        wx, wy, wz = world
        ox, oy, oz = self.origin
        sx, sy, sz = self.spacing
        d = self.direction_array

        # Translate to origin.
        relative = np.array([wx - ox, wy - oy, wz - oz], dtype=np.float64)

        # Apply inverse rotation (transpose, since D is orthonormal).
        unrotated = d.T @ relative

        # Divide by spacing.
        index = np.array(
            [unrotated[0] / sx, unrotated[1] / sy, unrotated[2] / sz],
            dtype=np.float64,
        )

        return (float(index[0]), float(index[1]), float(index[2]))

    def contains_world(
        self,
        world: tuple[float, float, float],
        *,
        tolerance: float = 1e-6,
    ) -> bool:
        """Return True if the world coordinate is inside the volume.

        A coordinate is inside if its voxel index falls within
        `[-tolerance, dimensions - 1 + tolerance]` along every axis.
        The tolerance accounts for floating-point rounding.
        """
        index = self.world_to_index(world)
        for axis, value in enumerate(index):
            if value < -tolerance:
                return False
            if value > self.dimensions[axis] - 1 + tolerance:
                return False
        return True

    # ----- Constructors ---------------------------------------------

    @classmethod
    def identity(
        cls,
        dimensions: tuple[int, int, int],
        spacing: tuple[float, float, float] = (1.0, 1.0, 1.0),
        origin: tuple[float, float, float] = (0.0, 0.0, 0.0),
    ) -> VolumeGeometry:
        """Build a geometry with an identity direction matrix.

        Useful for tests and synthetic volumes where orientation is
        irrelevant.
        """
        return cls(
            dimensions=dimensions,
            origin=origin,
            spacing=spacing,
            direction=(
                (1.0, 0.0, 0.0),
                (0.0, 1.0, 0.0),
                (0.0, 0.0, 1.0),
            ),
            coordinate_system=CoordinateSystem.RAS,
        )

    def __repr__(self) -> str:
        return (
            f"VolumeGeometry(dimensions={self.dimensions}, "
            f"spacing={self.spacing}, "
            f"origin={self.origin}, "
            f"coordinate_system={self.coordinate_system.value})"
        )
