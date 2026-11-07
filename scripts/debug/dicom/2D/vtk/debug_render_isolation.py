"""Debug script: isolate the VTK render pipeline layer by layer.

This script is a development tool. It is NOT part of production.

It renders FOUR separate scenes, one per window, each adding one
layer of the pipeline:

  1. A synthetic vtkImageData (gradient) via vtkImageActor.
  2. The DICOM vtkImageData (full volume) via vtkImageActor with
     DisplayExtent for slice 32.
  3. The DICOM slice via vtkImageReslice + vtkImageMapToWindowLevelColors
     + vtkImageActor.
  4. The DICOM slice via vtkImageReslice + vtkImageMapToWindowLevelColors
     + vtkImageSliceMapper + vtkImageSlice.

If (1) shows a gradient but (2) does not, the problem is the DICOM data.
If (2) shows the slice but (3) does not, the problem is the reslice.
If (3) shows the slice but (4) does not, the problem is the mapper.
If none show, the problem is the VTK/Qt environment.

Usage:

    .venv\\Scripts\\python.exe scripts\\debug\\dicom\\debug_render_isolation.py

Close each window to advance to the next.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PySide6.QtWidgets import QApplication, QMainWindow
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtkmodules.util.numpy_support import numpy_to_vtk
from vtkmodules.vtkCommonDataModel import vtkImageData
from vtkmodules.vtkImagingColor import vtkImageMapToWindowLevelColors
from vtkmodules.vtkImagingCore import vtkImageReslice
from vtkmodules.vtkRenderingCore import (
    vtkImageActor,
    vtkImageSlice,
    vtkImageSliceMapper,
    vtkRenderer,
)

from cranioz.infrastructure.imaging.dicom.dicom_series_reader import (
    DicomSeriesReader,
    DicomSeriesReaderError,
)
from cranioz.infrastructure.visualization.vtk_image_adapter import (
    VtkImageAdapter,
)

_DEFAULT_DICOM_PATH = Path(r"C:\Users\JozeiasNote2026\Downloads\TC")
_SLICE_INDEX = 32


def _make_gradient_image() -> vtkImageData:
    """Create a 100x100x1 synthetic gradient (16-bit)."""
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


def _show_scene(renderer: vtkRenderer, title: str) -> None:
    """Show a renderer in a QVTKRenderWindowInteractor window (blocking)."""
    app = QApplication.instance() or QApplication([])
    app.setStyle("Fusion")

    interactor = QVTKRenderWindowInteractor()
    render_window = interactor.GetRenderWindow()  # type: ignore[no-untyped-call]
    render_window.AddRenderer(renderer)
    render_window.SetSize(800, 800)

    window = QMainWindow()
    window.setWindowTitle(title)
    window.setCentralWidget(interactor)
    window.resize(800, 800)
    window.show()

    interactor.Initialize()
    renderer.ResetCamera()
    render_window.Render()

    app.exec()


def _scene_synthetic_gradient() -> None:
    print("\n=== 1. Synthetic gradient via vtkImageActor ===")
    image = _make_gradient_image()
    actor = vtkImageActor()
    actor.GetMapper().SetInputData(image)

    renderer = vtkRenderer()
    renderer.SetBackground(0.1, 0.1, 0.1)
    renderer.AddActor(actor)

    print(f"Gradient range: {image.GetPointData().GetScalars().GetRange()}")
    print(f"Actor bounds: {actor.GetBounds()}")
    _show_scene(renderer, "1. Synthetic gradient (vtkImageActor)")


def _scene_dicom_full_volume(volume) -> None:
    print("\n=== 2. DICOM full volume via vtkImageActor + DisplayExtent ===")
    adapter = VtkImageAdapter()
    image = adapter.to_vtk(volume)
    nx, ny, nz = image.GetDimensions()

    actor = vtkImageActor()
    actor.GetMapper().SetInputData(image)
    actor.SetDisplayExtent(0, nx - 1, 0, ny - 1, _SLICE_INDEX, _SLICE_INDEX)

    slice_range = volume.data[_SLICE_INDEX].min(), volume.data[_SLICE_INDEX].max()
    window = max(slice_range[1] - slice_range[0], 1.0)
    level = (slice_range[0] + slice_range[1]) / 2.0
    actor.GetProperty().SetColorWindow(window)
    actor.GetProperty().SetColorLevel(level)

    renderer = vtkRenderer()
    renderer.SetBackground(0.1, 0.1, 0.1)
    renderer.AddActor(actor)

    print(f"Volume range: {image.GetPointData().GetScalars().GetRange()}")
    print(f"Slice range: {slice_range}")
    print(f"W/L: window={window:.1f}, level={level:.1f}")
    print(f"Actor bounds: {actor.GetBounds()}")
    _show_scene(renderer, "2. DICOM slice via vtkImageActor + DisplayExtent")


def _scene_reslice_with_image_actor(volume) -> None:
    print("\n=== 3. DICOM slice via vtkImageReslice + vtkImageActor ===")
    adapter = VtkImageAdapter()
    image = adapter.to_vtk(volume)

    reslice = vtkImageReslice()
    reslice.SetInputData(image)
    reslice.SetOutputDimensionality(2)
    reslice.SetInterpolationModeToLinear()
    reslice.SetBackgroundLevel(0.0)
    reslice.SetResliceAxesDirectionCosines(1, 0, 0, 0, 1, 0, 0, 0, 1)
    origin = image.GetOrigin()
    spacing = image.GetSpacing()
    z = origin[2] + _SLICE_INDEX * spacing[2]
    reslice.SetResliceAxesOrigin(origin[0], origin[1], z)
    reslice.Update()

    slice_image = reslice.GetOutput()
    slice_range = slice_image.GetPointData().GetScalars().GetRange()
    window = max(slice_range[1] - slice_range[0], 1.0)
    level = (slice_range[0] + slice_range[1]) / 2.0

    window_level = vtkImageMapToWindowLevelColors()
    window_level.SetInputData(slice_image)
    window_level.SetWindow(window)
    window_level.SetLevel(level)
    window_level.Update()

    actor = vtkImageActor()
    actor.GetMapper().SetInputConnection(window_level.GetOutputPort())

    renderer = vtkRenderer()
    renderer.SetBackground(0.1, 0.1, 0.1)
    renderer.AddActor(actor)

    print(f"Slice dims: {slice_image.GetDimensions()}")
    print(f"Slice range: {slice_range}")
    print(f"W/L: window={window:.1f}, level={level:.1f}")
    print(f"Actor bounds: {actor.GetBounds()}")
    _show_scene(renderer, "3. DICOM slice via vtkImageActor + reslice")


def _scene_reslice_with_image_slice(volume) -> None:
    print("\n=== 4. DICOM slice via vtkImageSliceMapper + vtkImageSlice ===")
    adapter = VtkImageAdapter()
    image = adapter.to_vtk(volume)

    reslice = vtkImageReslice()
    reslice.SetInputData(image)
    reslice.SetOutputDimensionality(2)
    reslice.SetInterpolationModeToLinear()
    reslice.SetBackgroundLevel(0.0)
    reslice.SetResliceAxesDirectionCosines(1, 0, 0, 0, 1, 0, 0, 0, 1)
    origin = image.GetOrigin()
    spacing = image.GetSpacing()
    z = origin[2] + _SLICE_INDEX * spacing[2]
    reslice.SetResliceAxesOrigin(origin[0], origin[1], z)
    reslice.Update()

    slice_image = reslice.GetOutput()
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

    renderer = vtkRenderer()
    renderer.SetBackground(0.1, 0.1, 0.1)
    renderer.AddViewProp(image_slice)

    print(f"Slice dims: {slice_image.GetDimensions()}")
    print(f"Slice range: {slice_range}")
    print(f"W/L: window={window:.1f}, level={level:.1f}")
    print(f"ImageSlice bounds: {image_slice.GetBounds()}")
    _show_scene(renderer, "4. DICOM slice via vtkImageSlice + SliceMapper")


def main() -> int:
    dicom_path = _DEFAULT_DICOM_PATH
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
    print(f"Volume loaded: dims={volume.dimensions}")

    _scene_synthetic_gradient()
    _scene_dicom_full_volume(volume)
    _scene_reslice_with_image_actor(volume)
    _scene_reslice_with_image_slice(volume)

    print("\nAll scenes rendered. Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())