"""DicomSorter — order DICOM slices and compute the direction matrix.

The sorter is responsible for two things:

1. **Ordering.** Slices must be ordered by their physical position
   along the slice normal, not by filename or InstanceNumber.
2. **Direction matrix.** From `ImageOrientationPatient` (two
   orthogonal vectors) and the slice normal (cross product), the
   sorter derives the 3x3 direction matrix in RAS.

DICOM uses LPS. The sorter converts to RAS explicitly, at this
boundary. Nothing else in the codebase needs to know about LPS.

The direction matrix produced here is orthonormal (rotation only).
Gantry tilt (shear) is detected and rejected as unsupported.

See Medical Imaging Infrastructure §5.2, §5.3, §5.6.
"""

from __future__ import annotations

import logging
import math
from typing import Any

import numpy as np

_logger = logging.getLogger(__name__)

# DICOM LPS -> RAS conversion matrix: flip first two axes.
_LPS_TO_RAS = np.array(
    [
        [-1.0, 0.0, 0.0],
        [0.0, -1.0, 0.0],
        [0.0, 0.0, 1.0],
    ]
)

# Tolerance for orthonormality check (direction matrix).
_ORTHONORMAL_TOLERANCE = 1e-4

# Tolerance for detecting gantry tilt (shear).
_SHEAR_TOLERANCE = 1e-3


class DicomSorterError(ValueError):
    """Raised when slices cannot be sorted or the geometry is invalid."""


class DicomSorter:
    """Sorts DICOM slices and computes the direction matrix."""

    def sort(
        self,
        slices: list[Any],
    ) -> tuple[list[Any], np.ndarray]:
        """Sort slices and return (sorted_slices, direction_matrix_ras).

        Args:
            slices: list of pydicom Datasets with `ImagePositionPatient`
                and (ideally) `ImageOrientationPatient`.

        Returns:
            (sorted_slices, direction_ras):
                - sorted_slices: ordered by physical position along the
                  slice normal (ascending).
                - direction_ras: 3x3 orthonormal matrix mapping voxel
                  axes to RAS physical axes.

        Raises:
            DicomSorterError: if the geometry cannot be determined or
                is unsupported (gantry tilt, non-orthogonal orientation).
        """
        if not slices:
            raise DicomSorterError("cannot sort an empty slice list")

        orientation = self._read_orientation(slices[0])
        direction_lps = self._compute_direction_lps(orientation)
        direction_ras = _LPS_TO_RAS @ direction_lps

        # Order slices by projection onto the slice normal.
        normal_lps = direction_lps[:, 2]
        positions = [self._read_position(s) for s in slices]
        projections = [float(np.dot(p, normal_lps)) for p in positions]

        # Check for duplicate positions (which would mean the same
        # slice was loaded twice).
        if len({round(v, 6) for v in projections}) != len(projections):
            raise DicomSorterError(
                "duplicate slice positions detected; the series contains "
                "duplicated instances or the geometry is corrupted"
            )

        # Sort by projection (ascending).
        sorted_pairs = sorted(zip(projections, slices, strict=True), key=lambda t: t[0])
        sorted_slices = [s for _, s in sorted_pairs]

        # Validate gantry tilt: the slice normal must be parallel to
        # the direction of travel between consecutive slices.
        self._validate_shear(direction_lps, sorted_slices)

        return sorted_slices, direction_ras

    # ----- Internals -------------------------------------------------

    @staticmethod
    def _read_orientation(ds: Any) -> tuple[float, ...]:
        """Return `ImageOrientationPatient` as a 6-tuple."""
        orientation = getattr(ds, "ImageOrientationPatient", None)
        if orientation is None or len(orientation) != 6:
            raise DicomSorterError(
                "ImageOrientationPatient is missing or invalid; cannot determine volume orientation"
            )
        return tuple(float(v) for v in orientation)

    @staticmethod
    def _compute_direction_lps(orientation: tuple[float, ...]) -> np.ndarray:
        """Compute the 3x3 direction matrix in LPS.

        `ImageOrientationPatient` has 6 values: the row direction
        (3) and the column direction (3). The slice normal is their
        cross product.

        The columns of the returned matrix are (row, col, normal).
        """
        row = np.array(orientation[0:3], dtype=np.float64)
        col = np.array(orientation[3:6], dtype=np.float64)

        # Normalize (DICOM says they should be unit vectors, but be safe).
        row /= np.linalg.norm(row)
        col /= np.linalg.norm(col)

        # Check orthogonality.
        dot = float(np.dot(row, col))
        if abs(dot) > _ORTHONORMAL_TOLERANCE:
            raise DicomSorterError(
                f"ImageOrientationPatient row and column are not "
                f"orthogonal (dot product = {dot:.6f})"
            )

        normal = np.cross(row, col)

        return np.column_stack([row, col, normal])

    @staticmethod
    def _read_position(ds: Any) -> np.ndarray:
        """Return `ImagePositionPatient` as a 3-vector in LPS."""
        position = getattr(ds, "ImagePositionPatient", None)
        if position is None or len(position) != 3:
            raise DicomSorterError(
                "ImagePositionPatient is missing or invalid; cannot determine slice position"
            )
        return np.array([float(v) for v in position], dtype=np.float64)

    @staticmethod
    def _validate_shear(direction_lps: np.ndarray, sorted_slices: list[Any]) -> None:
        """Detect gantry tilt (shear).

        If the direction of travel between consecutive slices is not
        parallel to the slice normal, the stack has a shear component
        (gantry tilt). A direction matrix constrained to orthonormal
        axes cannot represent this shear, so we reject it.
        """
        if len(sorted_slices) < 2:
            return

        normal = direction_lps[:, 2]
        p0 = DicomSorter._read_position(sorted_slices[0])
        p1 = DicomSorter._read_position(sorted_slices[1])
        travel = p1 - p0

        travel_norm = np.linalg.norm(travel)
        if travel_norm < 1e-9:
            raise DicomSorterError(
                "consecutive slices have identical positions; cannot determine slice spacing"
            )
        travel_unit = travel / travel_norm

        # The travel direction should be parallel to the normal.
        # If the angle between them is greater than a threshold,
        # the stack has shear.
        cos_angle = float(np.dot(travel_unit, normal))
        if abs(cos_angle) < 1.0 - _SHEAR_TOLERANCE:
            angle_deg = math.degrees(math.acos(min(1.0, abs(cos_angle))))
            raise DicomSorterError(
                f"gantry tilt (shear) detected: travel direction deviates "
                f"{angle_deg:.2f}° from the slice normal. "
                "This dataset cannot be represented with an orthonormal "
                "direction matrix. Resample or reject the dataset."
            )
