"""Debug script: test VTK rendering backends for the white rectangle bug.

This script is a development tool. It is NOT part of production.

The white rectangle bug is caused by the driver OpenGL on Windows with
VTK 9 Core Profile. This script tests three renderers to identify which
one works on the current machine:

  1. vtkImageSlice + vtkImageSliceMapper (explicit mapper, 2D).
  2. vtkImageActor (default mapper, 2D).
  3. vtkImageSlice with vtkImageReslice (full pipeline).

Each test shows a gradient. If a test shows the gradient correctly,
that renderer is safe to use in CranioZ. If a test shows a white
rectangle, that renderer is broken on this machine.

Usage:

    .venv\\Scripts\\python.exe scripts\\debug\\dicom\\debug_vtk_backend_test.py
"""

from __future__ import annotations

import sys

import numpy as np
from vtkmodules.util.numpy_support import numpy_to_vtk
from vtkmodules.vtkCommonDataModel import vtkImageData
from vtkmodules.vtkRenderingCore import (
    vtkImageActor,
    vtkImageSlice,
    vtkImageSliceMapper,
    vtkRenderer,
    vtkRenderWindow,
    vtkRenderWindowInteractor,
)


def _make_gradient_image() -> vtkImageData:
    width, height = 100, 100
    data = np.zeros((1, height, width), dtype=np.int16)
    for y in range(height):
        for x in range(width):
            data[0, y, x] = (x + y) * 100
    flat = np.ascontiguousarray(data.transpose(2, 1, 0)).ravel(order="C")
    vtk_array = numpy_to_vtk(flat, deep=0)
    vtk_array.SetName("Scalars")
    image = vtkImageData()
    image.SetDimensions(width, height, 1)
    image.SetSpacing(1.0, 1.0, 1.0)
    image.SetOrigin(0.0, 0.0, 0.0)
    image.GetPointData().SetScalars(vtk_array)
    return image


def _show(title: str, actor) -> None:
    renderer = vtkRenderer()
    renderer.SetBackground(0.1, 0.1, 0.1)
    if hasattr(actor, "GetMapper"):
        renderer.AddActor(actor)
    else:
        renderer.AddViewProp(actor)

    render_window = vtkRenderWindow()
    render_window.AddRenderer(renderer)
    render_window.SetSize(800, 800)
    render_window.SetWindowName(title)

    interactor = vtkRenderWindowInteractor()
    interactor.SetRenderWindow(render_window)
    interactor.Initialize()

    renderer.ResetCamera()
    render_window.Render()

    print(f"\n[{title}]")
    print(f"  Actor bounds: {actor.GetBounds()}")
    print(f"  Renderer viewport: {renderer.GetViewport()}")
    print(f"  Camera position: {renderer.GetActiveCamera().GetPosition()}")
    print(f"  Camera focal point: {renderer.GetActiveCamera().GetFocalPoint()}")
    print("  Close the window to continue...")

    interactor.Start()


def test_1_image_slice_mapper() -> None:
    """Test 1: vtkImageSlice + vtkImageSliceMapper (explicit)."""
    image = _make_gradient_image()
    mapper = vtkImageSliceMapper()
    mapper.SetInputData(image)
    image_slice = vtkImageSlice()
    image_slice.SetMapper(mapper)
    print("\n=== Test 1: vtkImageSlice + vtkImageSliceMapper (explicit) ===")
    _show("1. vtkImageSlice + vtkImageSliceMapper", image_slice)


def test_2_image_actor() -> None:
    """Test 2: vtkImageActor (default mapper)."""
    image = _make_gradient_image()
    actor = vtkImageActor()
    actor.GetMapper().SetInputData(image)
    print("\n=== Test 2: vtkImageActor (default mapper) ===")
    _show("2. vtkImageActor", actor)


def test_3_image_reslice_slice_mapper() -> None:
    """Test 3: vtkImageReslice + vtkImageSliceMapper (full 2D pipeline)."""
    from vtkmodules.vtkImagingCore import vtkImageReslice

    image = _make_gradient_image()
    reslice = vtkImageReslice()
    reslice.SetInputData(image)
    reslice.SetOutputDimensionality(2)
    reslice.SetInterpolationModeToLinear()
    reslice.SetResliceAxesDirectionCosines(1, 0, 0, 0, 1, 0, 0, 0, 1)
    reslice.SetResliceAxesOrigin(0, 0, 0)
    reslice.Update()

    mapper = vtkImageSliceMapper()
    mapper.SetInputData(reslice.GetOutput())
    image_slice = vtkImageSlice()
    image_slice.SetMapper(mapper)
    print("\n=== Test 3: vtkImageReslice + vtkImageSliceMapper ===")
    _show("3. vtkImageReslice + vtkImageSliceMapper", image_slice)


def main() -> int:
    test_1_image_slice_mapper()
    test_2_image_actor()
    test_3_image_reslice_slice_mapper()
    print("\nAll tests completed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())