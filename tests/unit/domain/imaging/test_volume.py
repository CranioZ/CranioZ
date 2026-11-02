"""Tests for Volume.

The Volume is the aggregate root of the imaging domain. The tests
cover:

- Construction and validation (data shape, dtype, geometry coherence).
- Intensity scale classification (HU, UNCALIBRATED, UNKNOWN).
- Scalar range.
- Sampling at physical coordinates.
- Repr.
"""

from __future__ import annotations

from datetime import UTC, datetime

import numpy as np
import pytest

from cranioz.domain.imaging.image_metadata import (
    ImageMetadata,
    ImageModality,
)
from cranioz.domain.imaging.volume import (
    IntensityScale,
    Volume,
    VolumeError,
)
from cranioz.domain.imaging.volume_geometry import VolumeGeometry
from cranioz.domain.imaging.volume_provenance import VolumeProvenance

# ----- Helpers ------------------------------------------------------


def _make_provenance() -> VolumeProvenance:
    return VolumeProvenance(
        import_timestamp=datetime(2026, 1, 1, 12, 0, tzinfo=UTC),
    )


def _make_volume(
    *,
    shape: tuple[int, int, int] = (4, 4, 4),
    dtype: type = np.int16,
    intensity_scale: IntensityScale = IntensityScale.HU,
) -> Volume:
    """Build a Volume with a synthetic data buffer."""
    # shape is (nz, ny, nx).
    nz, ny, nx = shape
    data = np.arange(nz * ny * nx, dtype=dtype).reshape(shape)

    geometry = VolumeGeometry.identity(
        dimensions=(nx, ny, nz),
        spacing=(1.0, 1.0, 1.0),
        origin=(0.0, 0.0, 0.0),
    )

    return Volume(
        data=data,
        geometry=geometry,
        metadata=ImageMetadata(modality=ImageModality.CT),
        intensity_scale=intensity_scale,
        provenance=_make_provenance(),
        volume_id="volume-test",
    )


# ----- Construction -------------------------------------------------


def test_volume_holds_all_fields() -> None:
    vol = _make_volume()
    assert vol.volume_id == "volume-test"
    assert vol.data.shape == (4, 4, 4)
    assert vol.intensity_scale is IntensityScale.HU


def test_volume_data_must_be_numpy() -> None:
    with pytest.raises(VolumeError, match=r"numpy\.ndarray"):
        Volume(
            data=[[[0]]],  # type: ignore[arg-type]
            geometry=VolumeGeometry.identity(dimensions=(1, 1, 1)),
            metadata=ImageMetadata(),
            intensity_scale=IntensityScale.UNKNOWN,
            provenance=_make_provenance(),
            volume_id="v",
        )


def test_volume_data_must_be_3d() -> None:
    with pytest.raises(VolumeError, match="3D"):
        Volume(
            data=np.zeros((4, 4), dtype=np.int16),
            geometry=VolumeGeometry.identity(dimensions=(4, 4, 1)),
            metadata=ImageMetadata(),
            intensity_scale=IntensityScale.UNKNOWN,
            provenance=_make_provenance(),
            volume_id="v",
        )


def test_volume_data_shape_must_match_geometry() -> None:
    with pytest.raises(VolumeError, match="shape"):
        Volume(
            data=np.zeros((4, 4, 4), dtype=np.int16),
            geometry=VolumeGeometry.identity(dimensions=(5, 5, 5)),
            metadata=ImageMetadata(),
            intensity_scale=IntensityScale.UNKNOWN,
            provenance=_make_provenance(),
            volume_id="v",
        )


def test_volume_dtype_must_be_supported() -> None:
    with pytest.raises(VolumeError, match="dtype"):
        Volume(
            data=np.zeros((4, 4, 4), dtype=np.float64),
            geometry=VolumeGeometry.identity(dimensions=(4, 4, 4)),
            metadata=ImageMetadata(),
            intensity_scale=IntensityScale.UNKNOWN,
            provenance=_make_provenance(),
            volume_id="v",
        )


def test_volume_id_must_not_be_empty() -> None:
    with pytest.raises(VolumeError, match="volume_id"):
        Volume(
            data=np.zeros((4, 4, 4), dtype=np.int16),
            geometry=VolumeGeometry.identity(dimensions=(4, 4, 4)),
            metadata=ImageMetadata(),
            intensity_scale=IntensityScale.UNKNOWN,
            provenance=_make_provenance(),
            volume_id="",
        )


# ----- Intensity scale ---------------------------------------------


def test_is_hu_calibrated_true() -> None:
    vol = _make_volume(intensity_scale=IntensityScale.HU)
    assert vol.is_hu_calibrated is True


def test_is_hu_calibrated_false_for_uncalibrated() -> None:
    vol = _make_volume(intensity_scale=IntensityScale.UNCALIBRATED)
    assert vol.is_hu_calibrated is False


def test_is_hu_calibrated_false_for_unknown() -> None:
    vol = _make_volume(intensity_scale=IntensityScale.UNKNOWN)
    assert vol.is_hu_calibrated is False


# ----- Scalar range -------------------------------------------------


def test_scalar_range() -> None:
    vol = _make_volume()
    assert vol.scalar_range == (0.0, 63.0)  # 4*4*4 - 1


# ----- Sampling -----------------------------------------------------


def test_sample_world_inside() -> None:
    vol = _make_volume()
    # With identity geometry, voxel (i, j, k) is at world (i, j, k).
    value = vol.sample_world((1.0, 2.0, 3.0))
    expected = vol.data[3, 2, 1]
    assert value == float(expected)


def test_sample_world_outside_returns_none() -> None:
    vol = _make_volume()
    assert vol.sample_world((-1.0, 0.0, 0.0)) is None
    assert vol.sample_world((100.0, 0.0, 0.0)) is None


# ----- Accessors ---------------------------------------------------


def test_dimensions_and_spacing() -> None:
    vol = _make_volume()
    assert vol.dimensions == (4, 4, 4)
    assert vol.spacing == (1.0, 1.0, 1.0)


def test_repr_mentions_key_fields() -> None:
    vol = _make_volume()
    text = repr(vol)
    assert "volume-test" in text
    assert "hu" in text
