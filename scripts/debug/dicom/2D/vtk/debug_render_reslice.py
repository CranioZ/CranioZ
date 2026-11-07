"""Debug script: minimal VTK render with vtkImageReslice + vtkImageSliceMapper.

This script is a development tool. It is NOT part of production.

It:
1. Loads a DICOM series.
2. Converts the Volume to vtkImageData via VtkImageAdapter.
3. Extracts axial slice 32 via vtkImageReslice.
4. Renders the slice via vtkImageSliceMapper + vtkImageSlice.

The explicit vtkImageSliceMapper is the key: vtkImageActor's default
mapper (vtkImageSliceMapper) needs to be configured explicitly in
some VTK versions. This is the reference pipeline for MPRView: if it
renders here, the renderer/camera/OpenGL context are healthy and any
remaining MPRView failure is in its own wiring.

Usage:

    .venv\\Scripts\\python.exe scripts\\debug\\dicom\\debug_render_reslice.py [path_to_dicom_folder]

Close the window to exit.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import vtk
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QSurfaceFormat
from PySide6.QtWidgets import QApplication, QMainWindow
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtkmodules.vtkImagingColor import vtkImageMapToWindowLevelColors
from vtkmodules.vtkImagingCore import vtkImageReslice
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleImage
from vtkmodules.vtkRenderingCore import (
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

# ---- VTK / OpenGL configuration -------------------------------------
# These MUST run before the first QApplication is created. Qt reads
# the global QSurfaceFormat and the AA_ShareOpenGLContexts attribute
# exactly once, at application startup. If they are set after the
# QApplication, they are silently ignored and QVTKRenderWindowInteractor
# fails to render (white widget, no VTK output), which is exactly the
# symptom this script is meant to diagnose. Mirrors src/cranioz/__main__.py.
vtk.vtkObject.GlobalWarningDisplayOff()
os.environ.setdefault("VTK_DEFAULT_OPENGL_WINDOW", "vtkWin32OpenGLRenderWindow")
os.environ.setdefault("VTK_REPORT_OPENGL_ERRORS", "1")

QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)

_fmt = QSurfaceFormat()
_fmt.setDepthBufferSize(24)
_fmt.setStencilBufferSize(8)
_fmt.setVersion(3, 2)
_fmt.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)
QSurfaceFormat.setDefaultFormat(_fmt)

_DEFAULT_DICOM_PATH = Path(r"C:\Users\JozeiasNote2026\Downloads\TC")
_SLICE_INDEX = 32


def _reslice_axes_from_volume(volume) -> tuple[float, ...]:
    """Return the 9 direction cosines for an axial slice.

    Uses the volume's direction matrix (columns are the RAS axes) so
    that the reslice plane follows the anatomical orientation instead
    of assuming identity. The VtkImageAdapter already applied the
    volume's direction matrix to vtkImageData via SetDirectionMatrix;
    using the SAME direction matrix here aligns the reslice plane with
    the (already-rotated) vtkImageData. Using identity here would cause
    the reslice to look for the slice in the wrong coordinate space
    (the one BEFORE the direction matrix was applied) and produce an
    empty/banded image.

    For an axial view, the in-plane axes are the volume's X and Y
    columns; the slice normal is the Z column.
    """
    d = np.array(volume.geometry.direction, dtype=np.float64)
    x_axis = d[:, 0]
    y_axis = d[:, 1]
    normal = d[:, 2]
    return (
        float(x_axis[0]), float(x_axis[1]), float(x_axis[2]),
        float(y_axis[0]), float(y_axis[1]), float(y_axis[2]),
        float(normal[0]), float(normal[1]), float(normal[2]),
    )


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
    #
    # The reslice axes come from the volume's direction matrix. The
    # VtkImageAdapter already applied the same direction matrix to
    # vtkImageData via SetDirectionMatrix, so the reslice plane is
    # aligned with the anatomical axes of the (already-rotated) volume.
    # Using identity here would cause a DOUBLE rotation and produce
    # horizontal banding instead of a clean axial slice.
    reslice = vtkImageReslice()
    reslice.SetInputData(image)
    reslice.SetOutputDimensionality(2)
    reslice.SetInterpolationModeToLinear()
    reslice.SetBackgroundLevel(0.0)
    reslice.SetResliceAxesDirectionCosines(*_reslice_axes_from_volume(volume))

    dims = image.GetDimensions()
    spacing = image.GetSpacing()
    origin = image.GetOrigin()
    z = origin[2] + _SLICE_INDEX * spacing[2]
    reslice.SetResliceAxesOrigin(origin[0], origin[1], z)
    reslice.Update()

    slice_image = reslice.GetOutput()
    print(f"Slice dims: {slice_image.GetDimensions()}")
    print(f"Slice range: {slice_image.GetPointData().GetScalars().GetRange()}")

    # 3. W/L from the slice. Use the slice scalar range (not the whole
    # volume) so that outliers (air, metal) do not dominate the
    # mapping and flatten the image.
    slice_range = slice_image.GetPointData().GetScalars().GetRange()
    window = max(slice_range[1] - slice_range[0], 1.0)
    level = (slice_range[0] + slice_range[1]) / 2.0
    print(f"W/L: window={window:.1f}, level={level:.1f}")

    window_level = vtkImageMapToWindowLevelColors()
    # Use SetInputConnection, not SetInputData: the window/level must be
    # part of the reactive pipeline, not a one-shot snapshot of the
    # reslice output. This is what MPRView does.
    window_level.SetInputConnection(reslice.GetOutputPort())
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
    window.setWindowTitle(
        f"CranioZ - Render Debug (Reslice + SliceMapper, slice {_SLICE_INDEX})"
    )
    window.setCentralWidget(interactor)
    window.resize(800, 800)
    window.show()

    # Initialize the interactor AFTER show(), so the OpenGL context
    # exists. Setting the image interactor style keeps the render
    # pipeline healthy while disabling pan/zoom/rotate.
    interactor.Initialize()
    interactor.SetInteractorStyle(vtkInteractorStyleImage())

    # Defer the first render to the next event-loop iteration, once
    # the interactor has real geometry. Configure the camera
    # EXPLICITLY (not via ResetCamera()) so the clipping range covers
    # the slice's z position.
    def _initial_render() -> None:
        if interactor.width() <= 0 or interactor.height() <= 0:
            QTimer.singleShot(50, _initial_render)
            return

        # Force the pipeline to update so the slice bounds are
        # populated before the camera is configured.
        window_level.Update()
        mapper.Update()

        bounds = image_slice.GetBounds()
        print(f"ImageSlice bounds: {bounds}")

        cx = (bounds[0] + bounds[1]) / 2.0
        cy = (bounds[2] + bounds[3]) / 2.0
        cz = (bounds[4] + bounds[5]) / 2.0

        camera = renderer.GetActiveCamera()
        camera.SetPosition(cx, cy, cz + 100.0)
        camera.SetFocalPoint(cx, cy, cz)
        camera.SetViewUp(0, 1, 0)
        camera.SetClippingRange(1.0, 1000.0)
        camera.SetParallelProjection(True)

        width = bounds[1] - bounds[0]
        height = bounds[3] - bounds[2]
        camera.SetParallelScale(max(width, height) * 0.6)
        renderer.ResetCameraClippingRange()

        print(f"Camera position: {camera.GetPosition()}")
        print(f"Camera focal point: {camera.GetFocalPoint()}")
        print(f"Camera clipping range: {camera.GetClippingRange()}")

        render_window.Render()

    QTimer.singleShot(0, _initial_render)

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())