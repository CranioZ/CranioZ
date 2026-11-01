"""Tests for Viewport3DView.

The Viewport3DView wraps a ``QVTKRenderWindowInteractor`` and renders
a 3D outline of the volume via ``vtkOutlineFilter``. These tests
exercise the View contract and the set_volume integration.

VTK is a hard requirement for the module; tests skip when VTK is
missing.
"""

from __future__ import annotations

import pytest

pytest.importorskip("vtk")
pytest.importorskip("vtkmodules.qt")

import vtk  # noqa: E402

from cranioz.ui.editors.viewport_3d.view import Viewport3DView


def _make_image() -> object:
    """Build a tiny synthetic ``vtkImageData`` (4x4x4, int16)."""

    image = vtk.vtkImageData()
    image.SetDimensions(4, 4, 4)
    image.SetSpacing(1.0, 1.0, 1.0)
    image.SetOrigin(0.0, 0.0, 0.0)
    image.AllocateScalars(vtk.VTK_SHORT, 1)
    return image


@pytest.mark.qt
def test_viewport_3d_content_widget_returns_container(qtbot) -> None:
    view = Viewport3DView(view_id="view.3d")
    widget = view.content_widget()
    qtbot.addWidget(widget)
    assert widget is not None
    assert not view.has_volume
    assert view.renderer is None


@pytest.mark.qt
def test_viewport_3d_set_volume_marks_has_volume(qtbot) -> None:
    image = _make_image()
    view = Viewport3DView(view_id="view.3d")
    qtbot.addWidget(view.content_widget())

    view.set_volume(image)

    assert view.has_volume is True
    assert view.renderer is not None


@pytest.mark.qt
def test_viewport_3d_set_volume_is_idempotent(qtbot) -> None:
    """Calling set_volume twice must not recreate the renderer."""
    image = _make_image()
    view = Viewport3DView(view_id="view.3d")
    qtbot.addWidget(view.content_widget())

    view.set_volume(image)
    first_renderer = view.renderer

    view.set_volume(image)
    assert view.renderer is first_renderer
    assert view.has_volume is True


@pytest.mark.qt
def test_viewport_3d_dispose_clears_state(qtbot) -> None:
    image = _make_image()
    view = Viewport3DView(view_id="view.3d")
    qtbot.addWidget(view.content_widget())
    view.set_volume(image)
    assert view.has_volume

    view.dispose()

    assert view.has_volume is False
    assert view.renderer is None
