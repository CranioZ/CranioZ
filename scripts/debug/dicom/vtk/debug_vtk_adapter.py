"""Debug script: test the VtkImageAdapter and vtkImageReslice in isolation.

This script is a development tool. It is NOT part of production.

It:
1. Loads a DICOM series.
2. Converts the Volume to vtkImageData via VtkImageAdapter.
3. Saves the vtkImageData to a .vti file for inspection.
4. Feeds the vtkImageData into a minimal vtkImageReslice pipeline.
5. Renders the result (axial slice 32) in a minimal QVTKRenderWindowInteractor window.

This isolates the DICOM -> Volume -> VtkImageAdapter -> vtkImageReslice
pipeline from the MPRView, Workspace, and Scene.

Usage:

    .venv\\Scripts\\python.exe scripts\\debug_vtk_adapter.py [path_to_dicom_folder]

Close the window to exit.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMainWindow
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtkmodules.vtkCommonDataModel import vtkImageData
from vtkmodules.vtkIOXML import vtkXMLImageDataWriter
from vtkmodules.vtkImagingColor import vtkImageMapToWindowLevelColors
from vtkmodules.vtkImagingCore import vtkImageReslice
from vtkmodules.vtkRenderingCore import vtkImageActor, vtkRenderer

from cranioz.infrastructure.imaging.dicom.dicom_series_reader import (
    DicomSeriesReader,
    DicomSeriesReaderError,
)
from cranioz.infrastructure.visualization.vtk_image_adapter import (
    VtkImageAdapter,
)

#: Default DICOM folder for manual debugging. Override via the command line.
_DEFAULT_DICOM_PATH = Path(r"C:\Users\JozeiasNote2026\Downloads\TC")

#: Axial slice index to render (0-based).
_SLICE_INDEX = 32


def _log_image_data(image: vtkImageData, label: str) -> None:
    print(f"--- {label} ---")
    print(f"  dimensions: {image.GetDimensions()}")
    print(f"  spacing:    {image.GetSpacing()}")
    print(f"  origin:     {image.GetOrigin()}")
    scalar = image.GetPointData().GetScalars()
    if scalar is not None:
        print(f"  scalars:    {scalar.GetNumberOfTuples()} tuples")
        print(f"  scalar type: {scalar.GetDataTypeAsString()}")
        print(f"  range:      {scalar.GetRange()}")
    else:
        print("  scalars:    None")


def main() -> int:
    if len(sys.argv) > 2:
        print("Usage: debug_vtk_adapter.py [path_to_dicom_folder]")
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
    _log_image_data(image, "vtkImageData from VtkImageAdapter")

    # 2. Save to .vti for external inspection.
    vti_path = dicom_path / "debug_volume.vti"
    writer = vtkXMLImageDataWriter()
    writer.SetFileName(str(vti_path))
    writer.SetInputData(image)
    writer.Write()
    print(f"Saved vti to {vti_path}")

    # 3. Minimal reslice pipeline (axial, fixed axes), slice 32.
    reslice = vtkImageReslice()
    reslice.SetInputData(image)
    reslice.SetOutputDimensionality(2)
    reslice.SetInterpolationModeToLinear()
    reslice.SetBackgroundLevel(0.0)
    # Axial: identity axes.
    reslice.SetResliceAxesDirectionCosines(
        1, 0, 0,
        0, 1, 0,
        0, 0, 1,
    )
    # Position at slice 32 (0-based).
    dims = image.GetDimensions()
    spacing = image.GetSpacing()
    origin = image.GetOrigin()
    z = origin[2] + _SLICE_INDEX * spacing[2]
    print(
        f"Axial slice {_SLICE_INDEX}: origin_z={origin[2]:.4f}, "
        f"spacing_z={spacing[2]:.4f}, reslice_origin_z={z:.4f}"
    )
    reslice.SetResliceAxesOrigin(origin[0], origin[1], z)
    reslice.Update()

    _log_image_data(reslice.GetOutput(), "vtkImageData from vtkImageReslice")

    # 4. Window/Level: use the range of the *resliced slice*, not the
    # whole volume. For CBCT, the global range is dominated by air
    # (-6114) and metal/bone (16383), and using it makes the slice
    # look uniform white.
    slice_scalars = reslice.GetOutput().GetPointData().GetScalars()
    slice_range = slice_scalars.GetRange()
    window = max(slice_range[1] - slice_range[0], 1.0)
    level = (slice_range[0] + slice_range[1]) / 2.0
    print(f"Slice range: {slice_range}")
    print(f"W/L: window={window:.1f}, level={level:.1f}")

    window_level = vtkImageMapToWindowLevelColors()
    window_level.SetInputConnection(reslice.GetOutputPort())
    window_level.SetWindow(window)
    window_level.SetLevel(level)

    actor = vtkImageActor()
    actor.GetMapper().SetInputConnection(window_level.GetOutputPort())

    renderer = vtkRenderer()
    renderer.SetBackground(0.0, 0.0, 0.0)
    renderer.AddActor(actor)

    app = QApplication.instance() or QApplication([])
    app.setStyle("Fusion")

    interactor = QVTKRenderWindowInteractor()
    interactor.GetRenderWindow().AddRenderer(renderer)
    interactor.GetRenderWindow().SetSize(800, 800)
    renderer.ResetCamera()

    window = QMainWindow()
    window.setWindowTitle(f"CranioZ - VtkImageAdapter Debug (Axial slice {_SLICE_INDEX})")
    window.setCentralWidget(interactor)
    window.resize(800, 800)
    window.show()

    interactor.Initialize()
    interactor.GetRenderWindow().Render()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())