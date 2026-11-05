"""Debug script: minimal VTK render with vtkImageReslice + vtkImageSliceMapper.

This script is a development tool. It is NOT part of production.

It:
1. Loads a DICOM series.
2. Converts the Volume to vtkImageData via VtkImageAdapter.
3. Extracts axial slice 32 via vtkImageReslice.
4. Renders the slice via vtkImageSliceMapper + vtkImageSlice.

The explicit vtkImageSliceMapper is the key: vtkImageActor's default
mapper (vtkImageSliceMapper) needs to be configured explicitly in
some VTK versions.

Usage:

    .venv\\Scripts\\python.exe scripts\\debug_render_reslice.py [path_to_dicom_folder]

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
        print("Usage: debug_render_reslice.py [path_to_dicom_folder]")
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

    # 1. Convert to vtkImageData.
    adapter = VtkImageAdapter()
    image = adapter.to_vtk(volume)
    print(f"vtkImageData dims: {image.GetDimensions()}")
    print(f"vtkImageData range: {image.GetPointData().GetScalars().GetRange()}")

    # 2. Extract the axial slice via vtkImageReslice.
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
    print(f"Slice range: {slice_image.GetPointData().GetScalars().GetRange()}")

    # 3. W/L from the slice.
    slice_range = slice_image.GetPointData().GetScalars().GetRange()
    window = max(slice_range[1] - slice_range[0], 1.0)
    level = (slice_range[0] + slice_range[1]) / 2.0
    print(f"W/L: window={window:.1f}, level={level:.1f}")

    window_level = vtkImageMapToWindowLevelColors()
    window_level.SetInputData(slice_image)
    window_level.SetWindow(window)
    window_level.SetLevel(level)
    window_level.Update()

    # 4. Render via vtkImageSliceMapper + vtkImageSlice (NOT vtkImageActor).
    mapper = vtkImageSliceMapper()
    mapper.SetInputConnection(window_level.GetOutputPort())

    image_slice = vtkImageSlice()
    image_slice.SetMapper(mapper)

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
    window.setWindowTitle(f"CranioZ - Render Debug (Reslice + SliceMapper, slice {_SLICE_INDEX})")
    window.setCentralWidget(interactor)
    window.resize(800, 800)
    window.show()

    interactor.Initialize()

    renderer.ResetCamera()
    camera = renderer.GetActiveCamera()
    print(f"Camera position: {camera.GetPosition()}")
    print(f"Camera focal point: {camera.GetFocalPoint()}")
    print(f"Camera clipping range: {camera.GetClippingRange()}")

    render_window.Render()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())