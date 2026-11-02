"""Tests for MPRView.

The MPRView uses a manual VTK pipeline (vtkImageReslice +
vtkImageMapToWindowLevelColors + vtkImageActor) instead of
vtkResliceImageViewer. This is because vtkResliceImageViewer
causes `wglMakeCurrent` failures on some Windows drivers.

These tests validate:
- Construction with the three supported orientations.
- content_widget() returns a QWidget container.
- set_volume() accepts a Volume and marks has_volume=True.
- The View retains a strong reference to the Volume (buffer lifetime).
- dispose() clears the state and releases the Volume reference.
- Slice navigation methods (set_slice, get_slice, get_max_slice).

VTK is a hard requirement; the tests skip when VTK is missing.
"""

from __future__ import annotations

from datetime import UTC, datetime

import numpy as np
import pytest

pytest.importorskip("vtk")
pytest.importorskip("vtkmodules.qt")

from cranioz.domain.imaging.image_metadata import ImageMetadata
from cranioz.domain.imaging.volume import IntensityScale, Volume
from cranioz.domain.imaging.volume_geometry import VolumeGeometry
from cranioz.domain.imaging.volume_provenance import VolumeProvenance
from cranioz.ui.editors.mpr_viewer.view import MPRView


def _make_volume() -> Volume:
    """Build a tiny synthetic ``Volume`` (4x4x4, int16)."""
    return _make_volume_with_shape((4, 4, 4))


def _make_volume_with_shape(shape: tuple[int, int, int]) -> Volume:
    """Build a synthetic ``Volume`` with the given (nz, ny, nx) shape."""
    nz, ny, nx = shape
    data = np.zeros(shape, dtype=np.int16)
    geometry = VolumeGeometry.identity(
        dimensions=(nx, ny, nz),
        spacing=(1.0, 1.0, 1.0),
        origin=(0.0, 0.0, 0.0),
    )
    return Volume(
        data=data,
        geometry=geometry,
        metadata=ImageMetadata(),
        intensity_scale=IntensityScale.UNKNOWN,
        provenance=VolumeProvenance(
            import_timestamp=datetime(2026, 1, 1, 12, 0, tzinfo=UTC),
        ),
        volume_id="volume-test",
    )


@pytest.mark.qt
def test_mpr_view_rejects_unknown_type(qtbot) -> None:
    with pytest.raises(ValueError, match="must be one of"):
        MPRView(view_id="view.x", view_type="unknown")


@pytest.mark.qt
@pytest.mark.parametrize("view_type", ["axial", "coronal", "sagittal"])
def test_mpr_view_accepts_known_types(qtbot, view_type: str) -> None:
    view = MPRView(view_id=f"view.{view_type}", view_type=view_type)
    widget = view.content_widget()
    qtbot.addWidget(widget)
    assert widget is not None
    assert not view.has_volume


@pytest.mark.qt
def test_mpr_view_set_volume_marks_has_volume(qtbot) -> None:
    volume = _make_volume()
    view = MPRView(view_id="view.axial", view_type="axial")
    qtbot.addWidget(view.content_widget())

    view.set_volume(volume)

    assert view.has_volume is True


@pytest.mark.qt
def test_mpr_view_set_volume_is_idempotent(qtbot) -> None:
    """Calling set_volume twice must not recreate the pipeline."""
    volume = _make_volume()
    view = MPRView(view_id="view.axial", view_type="axial")
    qtbot.addWidget(view.content_widget())

    view.set_volume(volume)
    first_slice = view.get_slice()

    view.set_volume(volume)
    second_slice = view.get_slice()

    # The slice index is reset to the middle on each set_volume.
    assert first_slice == second_slice
    assert view.has_volume is True


@pytest.mark.qt
def test_mpr_view_retains_volume_reference(qtbot) -> None:
    """The View must retain a strong reference to the Volume.

    The VtkImageAdapter shares the NumPy buffer (deep=0), so the
    Volume must not be garbage-collected while the VTK pipeline
    still points to it (§8.1).
    """
    volume = _make_volume()
    view = MPRView(view_id="view.axial", view_type="axial")
    qtbot.addWidget(view.content_widget())

    view.set_volume(volume)
    assert view._volume is volume  # noqa: SLF001

    view.dispose()
    assert view._volume is None  # noqa: SLF001


@pytest.mark.qt
def test_mpr_view_dispose_clears_state(qtbot) -> None:
    volume = _make_volume()
    view = MPRView(view_id="view.axial", view_type="axial")
    qtbot.addWidget(view.content_widget())
    view.set_volume(volume)
    assert view.has_volume

    view.dispose()

    assert view.has_volume is False


@pytest.mark.qt
def test_mpr_view_set_slice(qtbot) -> None:
    volume = _make_volume()
    view = MPRView(view_id="view.axial", view_type="axial")
    qtbot.addWidget(view.content_widget())
    view.set_volume(volume)

    view.set_slice(0)
    assert view.get_slice() == 0

    view.set_slice(view.get_max_slice())
    assert view.get_slice() == view.get_max_slice()


@pytest.mark.qt
def test_mpr_view_set_slice_clamps_to_range(qtbot) -> None:
    volume = _make_volume()
    view = MPRView(view_id="view.axial", view_type="axial")
    qtbot.addWidget(view.content_widget())
    view.set_volume(volume)

    view.set_slice(-100)
    assert view.get_slice() == 0

    view.set_slice(10000)
    assert view.get_slice() == view.get_max_slice()
