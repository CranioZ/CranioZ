"""Tests for VtkImageAdapter.

The adapter converts a `Volume` to a `vtkImageData`. These tests
verify that the conversion preserves origin, spacing, direction,
and scalar data.
"""

from __future__ import annotations

from datetime import UTC, datetime

import numpy as np
import pytest

pytest.importorskip("vtk")

from cranioz.domain.imaging.image_metadata import (  # noqa: E402
    ImageMetadata,
    ImageModality,
)
from cranioz.domain.imaging.volume import (  # noqa: E402
    IntensityScale,
    Volume,
)
from cranioz.domain.imaging.volume_geometry import (  # noqa: E402
    VolumeGeometry,
)
from cranioz.domain.imaging.volume_provenance import (  # noqa: E402
    VolumeProvenance,
)
from cranioz.infrastructure.visualization.vtk_image_adapter import (  # noqa: E402
    VtkImageAdapter,
)

# ----- Helpers ------------------------------------------------------


def _make_volume(
    shape: tuple[int, int, int] = (4, 4, 4),
    spacing: tuple[float, float, float] = (0.5, 0.5, 2.0),
    origin: tuple[float, float, float] = (100.0, 50.0, 25.0),
    dtype: type = np.int16,
) -> Volume:
    """Build a Volume with a synthetic data buffer."""
    nz, ny, nx = shape
    data = np.arange(nz * ny * nx, dtype=dtype).reshape(shape)

    geometry = VolumeGeometry.identity(
        dimensions=(nx, ny, nz),
        spacing=spacing,
        origin=origin,
    )

    return Volume(
        data=data,
        geometry=geometry,
        metadata=ImageMetadata(modality=ImageModality.CT),
        intensity_scale=IntensityScale.HU,
        provenance=VolumeProvenance(
            import_timestamp=datetime(2026, 1, 1, 12, 0, tzinfo=UTC),
        ),
        volume_id="volume-test",
    )


# ----- Conversion --------------------------------------------------


def test_to_vtk_preserves_dimensions() -> None:
    volume = _make_volume(shape=(4, 8, 16))  # nz=4, ny=8, nx=16
    adapter = VtkImageAdapter()
    image = adapter.to_vtk(volume)
    # VTK dimensions are (nx, ny, nz) = (16, 8, 4).
    assert image.GetDimensions() == (16, 8, 4)


def test_to_vtk_preserves_spacing() -> None:
    volume = _make_volume(spacing=(0.5, 0.5, 2.0))
    adapter = VtkImageAdapter()
    image = adapter.to_vtk(volume)
    assert image.GetSpacing() == pytest.approx((0.5, 0.5, 2.0), abs=1e-9)


def test_to_vtk_preserves_origin() -> None:
    volume = _make_volume(origin=(100.0, 50.0, 25.0))
    adapter = VtkImageAdapter()
    image = adapter.to_vtk(volume)
    assert image.GetOrigin() == pytest.approx((100.0, 50.0, 25.0), abs=1e-9)


def test_to_vtk_preserves_scalar_data() -> None:
    volume = _make_volume(shape=(4, 4, 4))
    adapter = VtkImageAdapter()
    image = adapter.to_vtk(volume)
    scalars = image.GetPointData().GetScalars()
    assert scalars is not None
    assert scalars.GetNumberOfTuples() == 4 * 4 * 4
    assert scalars.GetNumberOfComponents() == 1


def test_to_vtk_applies_direction_matrix() -> None:
    volume = _make_volume()
    adapter = VtkImageAdapter()
    image = adapter.to_vtk(volume)
    # GetDirectionMatrix returns a vtkMatrix3x3 (VTK 9+), not a list.
    direction_method = getattr(image, "GetDirectionMatrix", None)
    if direction_method is not None:
        matrix = direction_method()
        # The identity matrix has 1.0 on the diagonal and 0.0 elsewhere.
        assert matrix.GetElement(0, 0) == pytest.approx(1.0)
        assert matrix.GetElement(1, 1) == pytest.approx(1.0)
        assert matrix.GetElement(2, 2) == pytest.approx(1.0)
        assert matrix.GetElement(0, 1) == pytest.approx(0.0)
        assert matrix.GetElement(0, 2) == pytest.approx(0.0)


def test_is_hu_calibrated() -> None:
    volume = _make_volume()
    assert VtkImageAdapter.is_hu_calibrated(volume) is True
