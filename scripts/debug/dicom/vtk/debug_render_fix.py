"""Debug script: minimal VTK render with explicit camera and clipping.

This script is a development tool. It is NOT part of production.

Key fix: explicitly set the camera's clipping range to include the
slice's z position. The default ResetCamera() computes a clipping
range based on the slice bounds, but the slice is at z=6.6 and the
camera is at z=218, so the clipping range (204, 235) excludes the
slice.

Usage:

    .venv\\Scripts\\python.exe scripts\\debug_render_fix.py [path_to_dicom_folder]

Close the window to exit.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMainWindow
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtkmodules.vtkImagingColor import vtkImageMapToWindowLevelColors
from vtkmodules.vtkImagingCore import vtkImageReslice
from vtkmodules.vtkRenderingCore import vtkImageSlice, vtkImageSliceMapper, vtkRenderer

from cranioz.infrastructure.imaging.dicom.dicom_series_reader import (
    DicomSeriesReader,
    DicomSeriesReaderError,
)
from cranioz.infrastructure.visualization.vtk_image_adapter import (
    VtkImageAdapter,
)

_DEFAULT_DICOM_PATH = Path(r"C:\Users\JozeiasNote2026\Downloads\TC")
_SLICE_INDEX = 32


def main() -> int:
    if len(sys.argv) > 2:
        print("Usage: debug_render_fix.py [path_to_dicom_folder]")
        return 1

    dicom_path = Path(sys.argv[1]) if len(sys.argv) == 2 else _DEFAULT_DICOM_PATH
    if not dicom_path.is_dir():
        print(f"Not a directory: {dicom_path}")
        return 1

    print(f"Loading DICOM series from {dicom_path}...")
    reader = DicomSeriesReader()
    try:
        volume, report = reader.read(dicom_path)
    except DicomSeriesReaderError as exc:
        print(f"Failed to load DICOM: {exc}")
        return 1

    print(f"Volume loaded: dims={volume.dimensions}, spacing={volume.spacing}")

    adapter = VtkImageAdapter()
    image = adapter.to_vtk(volume)

    reslice = vtkImageReslice()
    reslice.SetInputData(image)
    reslice.SetOutputDimensionality(2)
    reslice.SetInterpolationModeToLinear()
    reslice.SetBackgroundLevel(0.0)
    reslice.SetResliceAxesDirectionCosines(
        1, 0, 0,
        0, 1, 0,
        0, 0, 1,
    )
    dims = image.GetDimensions()
    spacing = image.GetSpacing()
    origin = image.GetOrigin()
    z = origin[2] + _SLICE_INDEX * spacing[2]
    reslice.SetResliceAxesOrigin(origin[0], origin[1], z)
    reslice.Update()

    slice_image = reslice.GetOutput()
    print(f"Slice dims: {slice_image.GetDimensions()}")
    print(f"Slice origin: {slice_image.GetOrigin()}")
    print(f"Slice spacing: {slice_image.GetSpacing()}")
    print(f"Slice range: {slice_image.GetPointData().GetScalars().GetRange()}")

    slice_range = slice_image.GetPointData().GetScalars().GetRange()
    window = max(slice_range[1] - slice_range[0], 1.0)
    level = (slice_range[0] + slice_range[1]) / 2.0

    window_level = vtkImageMapToWindowLevelColors()
    window_level.SetInputData(slice_image)
    window_level.SetWindow(window)
    window_level.SetLevel(level)
    window_level.Update()

    mapper = vtkImageSliceMapper()
    mapper.SetInputConnection(window_level.GetOutputPort())

    image_slice = vtkImageSlice()
    image_slice.SetMapper(mapper)
    print(f"ImageSlice bounds: {image_slice.GetBounds()}")

    renderer = vtkRenderer()
    renderer.SetBackground(0.1, 0.1, 0.1)
    renderer.AddViewProp(image_slice)

    app = QApplication.instance() or QApplication([])
    app.setStyle("Fusion")

    interactor = QVTKRenderWindowInteractor()
    render_window = interactor.GetRenderWindow()
    render_window.AddRenderer(renderer)
    render_window.SetSize(800, 800)

    window = QMainWindow()
    window.setWindowTitle(f"CranioZ - Render Fix (slice {_SLICE_INDEX})")
    window.setCentralWidget(interactor)
    window.resize(800, 800)
    window.show()

    interactor.Initialize()

    # Explicit camera setup: position above the slice, look at slice center,
    # and set a clipping range that includes the slice.
    bounds = image_slice.GetBounds()  # (xmin, xmax, ymin, ymax, zmin, zmax)
    cx = (bounds[0] + bounds[1]) / 2.0
    cy = (bounds[2] + bounds[3]) / 2.0
    cz = (bounds[4] + bounds[5]) / 2.0
    print(f"Slice center: ({cx:.2f}, {cy:.2f}, {cz:.2f})")

    camera = renderer.GetActiveCamera()
    # Position the camera 100mm above the slice.
    camera.SetPosition(cx, cy, cz + 100.0)
    camera.SetFocalPoint(cx, cy, cz)
    camera.SetViewUp(0, 1, 0)
    # Explicit clipping range: near=1, far=1000 (covers the slice at cz).
    camera.SetClippingRange(1.0, 1000.0)
    camera.SetParallelProjection(True)
    # Set the parallel scale to fit the slice.
    width = bounds[1] - bounds[0]
    height = bounds[3] - bounds[2]
    camera.SetParallelScale(max(width, height) * 0.6)

    print(f"Camera position: {camera.GetPosition()}")
    print(f"Camera focal point: {camera.GetFocalPoint()}")
    print(f"Camera clipping range: {camera.GetClippingRange()}")
    print(f"Camera parallel scale: {camera.GetParallelScale()}")

    render_window.Render()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())