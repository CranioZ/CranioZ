"""DicomCalibrator — apply intensity rescale and classify the scale.

The calibrator applies `RescaleSlope` and `RescaleIntercept` when
they are plausible, and classifies the resulting intensity scale:

- HU:           the values are Hounsfield Units.
- UNCALIBRATED: the values are valid but not HU (typical for CBCT).
- UNKNOWN:      the calibration cannot be established.

The calibration decision is based on:
1. The DICOM Modality (CT vs. CBCT vs. other).
2. The presence and plausibility of RescaleSlope/RescaleIntercept.
3. The observed scalar range of the data.

The calibrator does NOT modify the values in place. It returns
the rescaled array and the IntensityScale classification.

See Medical Imaging Infrastructure §4.5, §7.3.
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np

from cranioz.domain.imaging.image_metadata import ImageModality
from cranioz.domain.imaging.volume import IntensityScale

_logger = logging.getLogger(__name__)

# Plausibility thresholds for rescale parameters.
_MAX_ABS_SLOPE = 100.0
_MAX_ABS_INTERCEPT = 10000.0

# HU range check.
_HU_MIN = -2000.0
_HU_MAX = 20000.0


class DicomCalibrator:
    """Applies intensity rescale and classifies the scale."""

    def calibrate(
        self,
        raw_volume: np.ndarray,
        slices: list[Any],
    ) -> tuple[np.ndarray, IntensityScale]:
        """Apply rescale to the raw volume and classify the scale.

        Args:
            raw_volume: stacked voxel data, shape (nz, ny, nx).
            slices: source pydicom datasets (used for metadata).

        Returns:
            (calibrated_volume, intensity_scale):
                - calibrated_volume: same shape as input, dtype float32.
                - intensity_scale: the classification of the result.
        """
        slope = self._read_float(slices[0], "RescaleSlope", default=1.0)
        intercept = self._read_float(slices[0], "RescaleIntercept", default=0.0)
        modality = self._read_modality(slices[0])

        # Check plausibility of rescale parameters.
        if not self._is_plausible_rescale(slope, intercept):
            _logger.warning(
                "implausible RescaleSlope=%s, RescaleIntercept=%s; "
                "ignoring rescale and treating as uncalibrated",
                slope,
                intercept,
            )
            return raw_volume.astype(np.float32), IntensityScale.UNCALIBRATED

        # Apply rescale.
        calibrated = raw_volume.astype(np.float32) * slope + intercept

        # Classify the scale.
        if modality is ImageModality.CT:
            # Conventional CT: rescale parameters produce HU by definition.
            # Sanity-check the resulting range to catch corrupted metadata.
            data_min = float(calibrated.min())
            data_max = float(calibrated.max())
            if data_min >= _HU_MIN and data_max <= _HU_MAX:
                return calibrated, IntensityScale.HU
            _logger.warning(
                "CT volume has range (%.0f, %.0f) outside the expected HU range; "
                "treating as uncalibrated",
                data_min,
                data_max,
            )
            return calibrated, IntensityScale.UNCALIBRATED

        # CBCT and other modalities: rescale is applied, but the result
        # is NOT HU. The values are on the modality's own scale.
        return calibrated, IntensityScale.UNCALIBRATED

    # ----- Internals -------------------------------------------------

    @staticmethod
    def _read_float(ds: Any, name: str, *, default: float) -> float:
        value = getattr(ds, name, None)
        if value is None:
            return default
        try:
            return float(value)
        except (TypeError, ValueError):
            _logger.warning("could not interpret %s=%r as float; using default", name, value)
            return default

    @staticmethod
    def _read_modality(ds: Any) -> ImageModality:
        modality = getattr(ds, "Modality", None)
        if modality == "CT":
            return ImageModality.CT
        if modality in {"CBCT", "CT_CBCT"}:
            return ImageModality.CBCT
        if modality in {"MR", "MRI"}:
            return ImageModality.MRI
        return ImageModality.UNKNOWN

    @staticmethod
    def _is_plausible_rescale(slope: float, intercept: float) -> bool:
        if abs(slope) > _MAX_ABS_SLOPE:
            return False
        if abs(slope) < 1e-9:
            return False
        return abs(intercept) <= _MAX_ABS_INTERCEPT
