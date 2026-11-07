"""Debug script: test VTK rendering without Qt.

This script is a development tool. It is NOT part of production.

It renders a synthetic gradient using a native vtkRenderWindow (no Qt).
If this works but the Qt version does not, the problem is the
QVTKRenderWindowInteractor / Qt integration. If this does not work
either, the problem is the OpenGL driver.

Usage:

    .venv\\Scripts\\python.exe scripts\\debug\\dicom\\debug_render_pure_vtk.py
"""

from __future__ import annotations

import sys

import numpy as np
import vtk
from vtkmodules.util.numpy_support import numpy_to_vtk
from vtkmodules.vtkCommonDataModel import vtkImageData
from vtkmodules.vtkRenderingCore import (
    vtkImageActor,
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


def main() -> int:
    print("Creating synthetic gradient...")
    image = _make_gradient_image()
    print(f"Gradient range: {image.GetPointData().GetScalars().GetRange()}")

    actor = vtkImageActor()
    actor.GetMapper().SetInputData(image)
    print(f"Actor bounds: {actor.GetBounds()}")

    renderer = vtkRenderer()
    renderer.SetBackground(0.1, 0.1, 0.1)
    renderer.AddActor(actor)

    render_window = vtkRenderWindow()
    render_window.AddRenderer(renderer)
    render_window.SetSize(800, 800)
    render_window.SetWindowName("Pure VTK — Synthetic gradient")

    interactor = vtkRenderWindowInteractor()
    interactor.SetRenderWindow(render_window)
    interactor.Initialize()

    renderer.ResetCamera()
    render_window.Render()

    print("Window shown. Close it to exit.")
    interactor.Start()
    return 0


if __name__ == "__main__":
    sys.exit(main())