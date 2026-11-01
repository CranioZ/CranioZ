"""Tests for MPRView.

The MPRView wraps a ``vtkResliceImageViewer``. These tests exercise
the View contract (content_widget, dispose, has_volume) and the
set_volume integration with a synthetic ``vtkImageData``.

VTK is a hard requirement for the MPRView module itself (imported
at the top of the module). The tests skip when VTK is not installed
so the rest of the suite can run in minimal CI environments.
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
    assert view.image_viewer is None


@pytest.mark.qt
def test_mpr_view_set_volume_marks_has_volume(qtbot) -> None:
    image = _make_image()
    view = MPRView(view_id="view.axial", view_type="axial")
    qtbot.addWidget(view.content_widget())

    view.set_volume(image)

    assert view.has_volume is True
    assert view.image_viewer is not None


@pytest.mark.qt
def test_mpr_view_set_volume_is_idempotent(qtbot) -> None:
    """Calling set_volume twice must not recreate the viewer."""
    image = _make_image()
    view = MPRView(view_id="view.axial", view_type="axial")
    qtbot.addWidget(view.content_widget())

    view.set_volume(image)
    first_viewer = view.image_viewer

    view.set_volume(image)
    assert view.image_viewer is first_viewer
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
    assert view.image_viewer is None
