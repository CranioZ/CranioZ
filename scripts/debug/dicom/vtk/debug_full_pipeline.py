"""Full pipeline debug: from DICOM folder to on-screen rendering.

This script is a development tool. It is NOT part of production.

It executes the complete pipeline step by step, with detailed prints
and sanity checks at each stage:

  1. File selection.
  2. DICOM series reading.
  3. Volume construction.
  4. VtkImageAdapter conversion (Volume -> vtkImageData).
  5. Slice extraction via vtkImageReslice.
  6. Window/Level computation.
  7. Rendering via vtkImageActor in a native vtkRenderWindow.

At each step, it prints the key parameters and verifies them against
expected invariants. If a step fails, the script stops and reports
exactly which step failed and why.

It also saves two artifacts for external inspection:

  - <dicom_folder>/debug_volume.vti  (the full volume as VTI)
  - <dicom_folder>/debug_slice.png   (the axial slice as PNG)

If the window is white but the .png shows the anatomy, the problem is
the VTK/Qt renderer (driver, OpenGL context). If the .png is also
white/empty, the problem is earlier in the pipeline.

Usage:

    .venv\\Scripts\\python.exe scripts\\debug\\dicom\\debug_full_pipeline.py [path_to_dicom_folder]

Run this DIRECTLY (not via pytest). Close the window to exit.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import vtk
from vtkmodules.util.numpy_support import numpy_to_vtk, vtk_to_numpy
from vtkmodules.vtkCommonDataModel import vtkImageData
from vtkmodules.vtkIOImage import vtkPNGWriter
from vtkmodules.vtkIOXML import vtkXMLImageDataWriter
from vtkmodules.vtkImagingColor import vtkImageMapToWindowLevelColors
from vtkmodules.vtkImagingCore import vtkImageReslice
from vtkmodules.vtkRenderingCore import (
    vtkImageActor,
    vtkRenderer,
    vtkRenderWindow,
    vtkRenderWindowInteractor,
    vtkWindowToImageFilter,
)

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


def _header(step: str) -> None:
    print()
    print("=" * 70)
    print(f"  {step}")
    print("=" * 70)


def _check(condition: bool, message: str) -> None:
    status = "OK" if condition else "FAIL"
    print(f"  [{status}] {message}")
    if not condition:
        raise SystemExit(1)


def _log_image_data(image: vtkImageData, label: str) -> None:
    print(f"  --- {label} ---")
    print(f"  dimensions: {image.GetDimensions()}")
    print(f"  spacing:    {image.GetSpacing()}")
    print(f"  origin:     {image.GetOrigin()}")
    scalars = image.GetPointData().GetScalars()
    if scalars is not None:
        print(f"  scalars:    {scalars.GetNumberOfTuples()} tuples")
        print(f"  scalar type: {scalars.GetDataTypeAsString()}")
        print(f"  range:      {scalars.GetRange()}")
    else:
        print("  scalars:    None")


def step_1_select_file(dicom_path: Path) -> None:
    _header("STEP 1: File selection")
    print(f"  Path: {dicom_path}")
    _check(dicom_path.is_dir(), f"Path is a directory: {dicom_path}")
    dcm_count = len(list(dicom_path.glob("*.dcm")))
    print(f"  .dcm files: {dcm_count}")
    _check(dcm_count > 0, f"At least one .dcm file found in {dicom_path}")


def step_2_read_dicom(dicom_path: Path):
    _header("STEP 2: DICOM series reading")
    reader = DicomSeriesReader()
    try:
        volume, report = reader.read(dicom_path)
    except DicomSeriesReaderError as exc:
        print(f"  [FAIL] DicomSeriesReaderError: {exc}")
        raise SystemExit(1)

    print(f"  Report: {report.summary()}")
    _check(report.success, "Import report says success")
    _check(volume is not None, "Volume was constructed")
    print(f"  Volume: dims={volume.dimensions}, spacing={volume.spacing}")
    print(f"  Origin: {volume.origin}")
    print(f"  Intensity scale: {volume.intensity_scale.value}")
    print(f"  Data dtype: {volume.data.dtype}")
    print(f"  Data shape: {volume.data.shape}")
    print(f"  Data range: ({volume.data.min()}, {volume.data.max()})")
    _check(volume.data.ndim == 3, "Volume.data is 3D")
    _check(volume.data.size > 0, "Volume.data is non-empty")
    return volume


def step_3_convert_to_vtk(volume):
    _header("STEP 3: VtkImageAdapter (Volume -> vtkImageData)")
    adapter = VtkImageAdapter()
    image = adapter.to_vtk(volume)
    _log_image_data(image, "vtkImageData from VtkImageAdapter")

    scalars = image.GetPointData().GetScalars()
    _check(scalars is not None, "Scalars were set on the vtkImageData")
    _check(
        scalars.GetDataTypeAsString() in ("short", "unsigned short", "int", "unsigned int", "float"),
        f"Scalar type is a supported numeric type (got {scalars.GetDataTypeAsString()})",
    )
    _check(
        scalars.GetNumberOfTuples() == int(np.prod(volume.dimensions)),
        "Scalar count matches volume dimensions",
    )
    return image


def step_4_save_vti(image: vtkImageData, dicom_path: Path) -> None:
    _header("STEP 4: Save vtkImageData to .vti")
    vti_path = dicom_path / "debug_volume.vti"
    writer = vtkXMLImageDataWriter()
    writer.SetFileName(str(vti_path))
    writer.SetInputData(image)
    writer.Write()
    print(f"  Saved: {vti_path}")
    _check(vti_path.is_file(), f"VTI file exists: {vti_path}")


def step_5_extract_slice(image: vtkImageData, slice_index: int):
    _header(f"STEP 5: Slice extraction (axial, slice {slice_index})")
    reslice = vtkImageReslice()
    reslice.SetInputData(image)
    reslice.SetOutputDimensionality(2)
    reslice.SetInterpolationModeToLinear()
    reslice.SetBackgroundLevel(0.0)
    reslice.SetResliceAxesDirectionCosines(1, 0, 0, 0, 1, 0, 0, 0, 1)

    dims = image.GetDimensions()
    spacing = image.GetSpacing()
    origin = image.GetOrigin()
    z = origin[2] + slice_index * spacing[2]
    print(f"  Slice {slice_index}: origin_z={origin[2]:.4f}, spacing_z={spacing[2]:.4f}, reslice_z={z:.4f}")
    reslice.SetResliceAxesOrigin(origin[0], origin[1], z)
    reslice.Update()

    slice_image = reslice.GetOutput()
    _log_image_data(slice_image, "vtkImageData from vtkImageReslice")

    slice_dims = slice_image.GetDimensions()
    _check(slice_dims[2] == 1, f"Slice is 2D (dims[2]=1), got {slice_dims}")
    _check(slice_dims[0] == dims[0], f"Slice width matches volume ({slice_dims[0]} == {dims[0]})")
    _check(slice_dims[1] == dims[1], f"Slice height matches volume ({slice_dims[1]} == {dims[1]})")

    slice_scalars = slice_image.GetPointData().GetScalars()
    _check(slice_scalars is not None, "Slice has scalars")
    slice_range = slice_scalars.GetRange()
    _check(slice_range[0] != slice_range[1], f"Slice is not uniform (range={slice_range})")
    return slice_image


def step_6_window_level(slice_image: vtkImageData):
    _header("STEP 6: Window/Level computation")
    slice_scalars = slice_image.GetPointData().GetScalars()
    slice_range = slice_scalars.GetRange()
    window = max(slice_range[1] - slice_range[0], 1.0)
    level = (slice_range[0] + slice_range[1]) / 2.0
    print(f"  Slice range: {slice_range}")
    print(f"  Window: {window:.1f}")
    print(f"  Level: {level:.1f}")
    _check(window > 0, "Window is positive")

    window_level = vtkImageMapToWindowLevelColors()
    window_level.SetInputData(slice_image)
    window_level.SetWindow(window)
    window_level.SetLevel(level)
    window_level.Update()

    wl_output = window_level.GetOutput()
    _log_image_data(wl_output, "vtkImageData from vtkImageMapToWindowLevelColors")
    return window_level


def step_7_save_slice_png(window_level, dicom_path: Path) -> None:
    _header("STEP 7: Save slice to PNG (independent of VTK renderer)")
    png_path = dicom_path / "debug_slice.png"
    writer = vtkPNGWriter()
    writer.SetFileName(str(png_path))
    writer.SetInputConnection(window_level.GetOutputPort())
    writer.Write()
    print(f"  Saved: {png_path}")
    _check(png_path.is_file(), f"PNG file exists: {png_path}")


def step_8_render(image: vtkImageData, slice_image: vtkImageData, window_level) -> None:
    _header("STEP 8: Render via vtkImageActor (native VTK window)")
    actor = vtkImageActor()
    actor.GetMapper().SetInputConnection(window_level.GetOutputPort())
    print(f"  Actor bounds: {actor.GetBounds()}")
    _check(actor.GetBounds()[1] > 0, "Actor has positive width")
    _check(actor.GetBounds()[3] > 0, "Actor has positive height")

    renderer = vtkRenderer()
    renderer.SetBackground(0.1, 0.1, 0.1)
    renderer.AddActor(actor)

    render_window = vtkRenderWindow()
    render_window.AddRenderer(renderer)
    render_window.SetSize(800, 800)
    render_window.SetWindowName(f"Full Pipeline Debug - Axial slice {_SLICE_INDEX}")
    render_window.SetMultiSamples(0)

    interactor = vtkRenderWindowInteractor()
    interactor.SetRenderWindow(render_window)
    interactor.Initialize()

    renderer.ResetCamera()
    camera = renderer.GetActiveCamera()
    print(f"  Camera position: {camera.GetPosition()}")
    print(f"  Camera focal point: {camera.GetFocalPoint()}")
    print(f"  Camera clipping range: {camera.GetClippingRange()}")

    render_window.Render()

    # Save a screenshot of the rendered window as well, to compare
    # with the .png from step 7.
    screenshot_path = Path(r"C:\Users\JozeiasNote2026\Downloads\TC") / "debug_render_screenshot.png"
    w2i = vtkWindowToImageFilter()
    w2i.SetInput(render_window)
    w2i.Update()
    writer = vtkPNGWriter()
    writer.SetFileName(str(screenshot_path))
    writer.SetInputConnection(w2i.GetOutputPort())
    writer.Write()
    print(f"  Saved render screenshot: {screenshot_path}")

    print()
    print("  Close the window to exit.")
    interactor.Start()


def main() -> int:
    if len(sys.argv) > 2:
        print("Usage: debug_full_pipeline.py [path_to_dicom_folder]")
        return 1
    dicom_path = Path(sys.argv[1]) if len(sys.argv) == 2 else _DEFAULT_DICOM_PATH

    print()
    print("#" * 70)
    print("#  CranioZ - Full DICOM Pipeline Debug")
    print("#" * 70)

    step_1_select_file(dicom_path)
    volume = step_2_read_dicom(dicom_path)
    image = step_3_convert_to_vtk(volume)
    step_4_save_vti(image, dicom_path)
    slice_image = step_5_extract_slice(image, _SLICE_INDEX)
    window_level = step_6_window_level(slice_image)
    step_7_save_slice_png(window_level, dicom_path)
    step_8_render(image, slice_image, window_level)

    print()
    print("#" * 70)
    print("#  All steps completed.")
    print("#" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())