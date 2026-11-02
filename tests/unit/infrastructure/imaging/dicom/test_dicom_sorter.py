"""Tests for DicomSorter.

The sorter is responsible for ordering slices and computing the
direction matrix. These tests use synthetic pydicom Datasets.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

import numpy as np
import pytest

from cranioz.infrastructure.imaging.dicom.dicom_sorter import (
    DicomSorter,
    DicomSorterError,
)

# ----- Helpers ------------------------------------------------------


@dataclass
class FakeDataset:
    """Minimal pydicom Dataset stand-in for tests."""

    ImagePositionPatient: list[float]
    ImageOrientationPatient: list[float]
    Rows: int = 4
    Columns: int = 4


def _axial_dataset(z: float) -> FakeDataset:
    """A standard axial slice at height `z`."""
    return FakeDataset(
        ImagePositionPatient=[0.0, 0.0, z],
        ImageOrientationPatient=[1.0, 0.0, 0.0, 0.0, 1.0, 0.0],
    )


class _MissingOrientationDataset:
    """Dataset with position but no orientation."""

    ImagePositionPatient: ClassVar[list[float]] = [0.0, 0.0, 0.0]


class _MissingPositionDataset:
    """Dataset with orientation but no position."""

    ImageOrientationPatient: ClassVar[list[float]] = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0]


class _TiltedDataset:
    """Dataset with a shear between consecutive slices."""

    Rows: ClassVar[int] = 4
    Columns: ClassVar[int] = 4
    ImageOrientationPatient: ClassVar[list[float]] = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0]

    def __init__(self, x: float, z: float) -> None:
        self.ImagePositionPatient = [x, 0.0, z]


# ----- Sorting ------------------------------------------------------


def test_sort_axial_ascending() -> None:
    sorter = DicomSorter()
    slices = [_axial_dataset(2.0), _axial_dataset(0.0), _axial_dataset(1.0)]
    sorted_slices, _ = sorter.sort(slices)
    z_values = [s.ImagePositionPatient[2] for s in sorted_slices]
    assert z_values == [0.0, 1.0, 2.0]


def test_sort_axial_descending_input() -> None:
    sorter = DicomSorter()
    slices = [_axial_dataset(3.0), _axial_dataset(2.0), _axial_dataset(1.0)]
    sorted_slices, _ = sorter.sort(slices)
    z_values = [s.ImagePositionPatient[2] for s in sorted_slices]
    assert z_values == [1.0, 2.0, 3.0]


def test_sort_duplicate_positions_raise() -> None:
    sorter = DicomSorter()
    slices = [_axial_dataset(0.0), _axial_dataset(0.0)]
    with pytest.raises(DicomSorterError, match="duplicate"):
        sorter.sort(slices)


# ----- Direction matrix ---------------------------------------------


def test_direction_axial_identity_ras() -> None:
    """An axial stack with standard orientation yields identity RAS."""
    sorter = DicomSorter()
    slices = [_axial_dataset(0.0), _axial_dataset(1.0)]
    _, direction_ras = sorter.sort(slices)
    # DICOM row=(1,0,0) LPS, col=(0,1,0) LPS, normal=(0,0,1) LPS.
    # LPS->RAS flips X and Y, so we expect diag(-1,-1,1) @ identity
    # which for the axial identity is diag(-1,-1,1).
    expected = np.diag([-1.0, -1.0, 1.0])
    assert np.allclose(direction_ras, expected, atol=1e-9)


def test_direction_is_orthonormal() -> None:
    sorter = DicomSorter()
    slices = [_axial_dataset(0.0), _axial_dataset(1.0)]
    _, direction = sorter.sort(slices)
    assert np.allclose(direction.T @ direction, np.eye(3), atol=1e-9)
    assert abs(np.linalg.det(direction)) == pytest.approx(1.0)


def test_missing_orientation_raises() -> None:
    sorter = DicomSorter()
    with pytest.raises(DicomSorterError, match="ImageOrientationPatient"):
        sorter.sort([_MissingOrientationDataset()])


def test_missing_position_raises() -> None:
    sorter = DicomSorter()
    with pytest.raises(DicomSorterError, match="ImagePositionPatient"):
        sorter.sort([_MissingPositionDataset()])


def test_empty_list_raises() -> None:
    sorter = DicomSorter()
    with pytest.raises(DicomSorterError, match="empty"):
        sorter.sort([])


# ----- Gantry tilt --------------------------------------------------


def test_gantry_tilt_detected() -> None:
    """A shear between consecutive slices must be rejected."""
    sorter = DicomSorter()
    slices = [
        _TiltedDataset(0.0, 0.0),
        _TiltedDataset(1.0, 1.0),
        _TiltedDataset(2.0, 2.0),
    ]
    with pytest.raises(DicomSorterError, match="tilt"):
        sorter.sort(slices)
