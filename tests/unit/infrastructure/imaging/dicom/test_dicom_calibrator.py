"""Tests for DicomCalibrator."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pytest

from cranioz.domain.imaging.volume import IntensityScale
from cranioz.infrastructure.imaging.dicom.dicom_calibrator import (
    DicomCalibrator,
)

# ----- Helpers ------------------------------------------------------


@dataclass
class FakeDataset:
    Modality: str = "CT"
    RescaleSlope: float | None = 1.0
    RescaleIntercept: float | None = -1024.0


def _raw_volume(min_val: int = 0, max_val: int = 2000) -> np.ndarray:
    return np.linspace(min_val, max_val, num=4 * 4 * 4, dtype=np.float32).reshape(4, 4, 4)


# ----- CT (HU) ------------------------------------------------------


def test_ct_with_rescale_classifies_as_hu() -> None:
    cal = DicomCalibrator()
    raw = _raw_volume(0, 2000)
    slices = [FakeDataset(Modality="CT", RescaleSlope=1.0, RescaleIntercept=-1024.0)]
    calibrated, scale = cal.calibrate(raw, slices)
    assert scale is IntensityScale.HU
    assert calibrated.min() == pytest.approx(-1024.0, abs=1.0)
    assert calibrated.max() == pytest.approx(976.0, abs=1.0)


def test_ct_without_rescale_uses_defaults() -> None:
    cal = DicomCalibrator()
    raw = _raw_volume(-1024, 1000)
    slices = [FakeDataset(Modality="CT", RescaleSlope=None, RescaleIntercept=None)]
    _, scale = cal.calibrate(raw, slices)
    # With slope=1, intercept=0, values stay in [-1024, 1000]
    # which is within the HU range.
    assert scale is IntensityScale.HU


# ----- CBCT (uncalibrated) -----------------------------------------


def test_cbct_with_rescale_classifies_as_uncalibrated() -> None:
    cal = DicomCalibrator()
    raw = _raw_volume(0, 4000)
    slices = [FakeDataset(Modality="CBCT", RescaleSlope=1.0, RescaleIntercept=0.0)]
    _, scale = cal.calibrate(raw, slices)
    assert scale is IntensityScale.UNCALIBRATED


def test_cbct_with_implausible_rescale_classifies_as_uncalibrated() -> None:
    cal = DicomCalibrator()
    raw = _raw_volume(0, 4000)
    # Implausibly large intercept.
    slices = [FakeDataset(Modality="CBCT", RescaleSlope=1.0, RescaleIntercept=99999.0)]
    _, scale = cal.calibrate(raw, slices)
    assert scale is IntensityScale.UNCALIBRATED


# ----- Other modalities --------------------------------------------


def test_unknown_modality_classifies_as_uncalibrated() -> None:
    cal = DicomCalibrator()
    raw = _raw_volume(0, 1000)
    slices = [FakeDataset(Modality="XX", RescaleSlope=1.0, RescaleIntercept=0.0)]
    _, scale = cal.calibrate(raw, slices)
    assert scale is IntensityScale.UNCALIBRATED
