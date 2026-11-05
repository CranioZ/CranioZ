"""Debug script: minimal VTK render to isolate the renderer/interactor.

This script is a development tool. It is NOT part of production.

It:
1. Loads a DICOM series.
2. Converts the Volume to vtkImageData via VtkImageAdapter.
3. Takes the axial slice 32 by setting the vtkImageActor's DisplayExtent.
4. Renders in a minimal QVTKRenderWindowInteractor.

No vtkImageReslice, no vtkImageMapToWindowLevelColors, no MPRView.
Just a vtkImageActor with an extent that selects slice 32.

Usage:

    .venv\\Scripts\\python.exe scripts\\debug_render_minimal.py [path_to_dicom_folder]

Close the window to exit.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMainWindow
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtkmodules.vtkImagingColor import vtkImageMapToWindowLevelColors
from vtkmodules.vtkRenderingCore import vtkImageActor, vtkRenderer

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
        print("Usage: debug_render_minimal.py [path_to_dicom_folder]")
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
    print(f"Intensity scale: {volume.intensity_scale.value}")

    # 1. Convert to vtkImageData.
    adapter = VtkImageAdapter()
    image = adapter.to_vtk(volume)
    print(f"vtkImageData dims: {image.GetDimensions()}")
    print(f"vtkImageData range: {image.GetPointData().GetScalars().GetRange()}")

    # 2. W/L from the slice. We don't have the slice yet, so compute
    #    the range of the z=32 slice by extracting it via numpy.
    slice_data = volume.data[_SLICE_INDEX, :, :]
    slice_min = float(slice_data.min())
    slice_max = float(slice_data.max())
    window = max(slice_max - slice_min, 1.0)
    level = (slice_min + slice_max) / 2.0
    print(f"Slice {_SLICE_INDEX} range (numpy): ({slice_min:.1f}, {slice_max:.1f})")
    print(f"W/L: window={window:.1f}, level={level:.1f}")

    # 3. Window/Level mapper.
    window_level = vtkImageMapToWindowLevelColors()
    window_level.SetInputData(image)
    window_level.SetWindow(window)
    window_level.SetLevel(level)
    window_level.Update()

    # 4. vtkImageActor, with DisplayExtent selecting slice 32.
    dims = image.GetDimensions()  # (nx, ny, nz)
    nx, ny, nz = dims[0], dims[1], dims[2]
    actor = vtkImageActor()
    actor.GetMapper().SetInputConnection(window_level.GetOutputPort())
    actor.SetDisplayExtent(0, nx - 1, 0, ny - 1, _SLICE_INDEX, _SLICE_INDEX)
    print(f"Actor display extent: {actor.GetDisplayExtent()}")
    print(f"Actor bounds: {actor.GetBounds()}")

    # 5. Renderer.
    renderer = vtkRenderer()
    renderer.SetBackground(0.1, 0.1, 0.1)
    renderer.AddActor(actor)

    app = QApplication.instance() or QApplication([])
    app.setStyle("Fusion")

    interactor = QVTKRenderWindowInteractor()
    render_window = interactor.GetRenderWindow()
    render_window.AddRenderer(renderer)
    render_window.SetSize(800, 800)

    window = QMainWindow()
    window.setWindowTitle(f"CranioZ - Minimal Render Debug (Axial slice {_SLICE_INDEX})")
    window.setCentralWidget(interactor)
    window.resize(800, 800)
    window.show()

    interactor.Initialize()

    # 6. Reset camera AFTER the actor has bounds.
    renderer.ResetCamera()
    camera = renderer.GetActiveCamera()
    print(f"Camera position: {camera.GetPosition()}")
    print(f"Camera focal point: {camera.GetFocalPoint()}")
    print(f"Camera clipping range: {camera.GetClippingRange()}")

    render_window.Render()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())