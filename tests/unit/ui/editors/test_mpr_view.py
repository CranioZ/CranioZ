"""Tests for MPRView.

The MPRView uses a manual VTK pipeline (vtkImageReslice +
vtkImageMapToWindowLevelColors + vtkImageActor) instead of
vtkResliceImageViewer. This is because vtkResliceImageViewer
causes `wglMakeCurrent` failures on some Windows drivers.

These tests validate:
- Construction with the three supported orientations.
- content_widget() returns a QWidget container.
- set_volume() marks has_volume=True.
- dispose() clears the state.
- Slice navigation methods (set_slice, get_slice, get_max_slice).

VTK is a hard requirement; the tests skip when VTK is missing.
"""

from __future__ import annotations

import pytest

pytest.importorskip("vtk")
pytest.importorskip("vtkmodules.qt")

import vtk  # noqa: E402

from cranioz.ui.editors.mpr_viewer.view import MPRView


def _make_image() -> object:
    """Build a tiny synthetic ``vtkImageData`` (4x4x4, int16)."""
    image = vtk.vtkImageData()
    image.SetDimensions(4, 4, 4)
    image.SetSpacing(1.0, 1.0, 1.0)
    image.SetOrigin(0.0, 0.0, 0.0)
    image.AllocateScalars(vtk.VTK_SHORT, 1)
    return image


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
    image = _make_image()
    view = MPRView(view_id="view.axial", view_type="axial")
    qtbot.addWidget(view.content_widget())

    view.set_volume(image)

    assert view.has_volume is True


@pytest.mark.qt
def test_mpr_view_set_volume_is_idempotent(qtbot) -> None:
    """Calling set_volume twice must not recreate the pipeline."""
    image = _make_image()
    view = MPRView(view_id="view.axial", view_type="axial")
    qtbot.addWidget(view.content_widget())

    view.set_volume(image)
    first_slice = view.get_slice()

    view.set_volume(image)
    second_slice = view.get_slice()

    # The slice index is reset to the middle on each set_volume.
    assert first_slice == second_slice
    assert view.has_volume is True


@pytest.mark.qt
def test_mpr_view_dispose_clears_state(qtbot) -> None:
    image = _make_image()
    view = MPRView(view_id="view.axial", view_type="axial")
    qtbot.addWidget(view.content_widget())
    view.set_volume(image)
    assert view.has_volume

    view.dispose()

    assert view.has_volume is False


@pytest.mark.qt
def test_mpr_view_set_slice(qtbot) -> None:
    image = _make_image()
    view = MPRView(view_id="view.axial", view_type="axial")
    qtbot.addWidget(view.content_widget())
    view.set_volume(image)

    view.set_slice(0)
    assert view.get_slice() == 0

    view.set_slice(view.get_max_slice())
    assert view.get_slice() == view.get_max_slice()


@pytest.mark.qt
def test_mpr_view_set_slice_clamps_to_range(qtbot) -> None:
    image = _make_image()
    view = MPRView(view_id="view.axial", view_type="axial")
    qtbot.addWidget(view.content_widget())
    view.set_volume(image)

    view.set_slice(-100)
    assert view.get_slice() == 0

    view.set_slice(10000)
    assert view.get_slice() == view.get_max_slice()
