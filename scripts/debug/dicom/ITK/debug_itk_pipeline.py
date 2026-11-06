"""Debug script: render DICOM via SimpleITK -> vtkImageData -> vtk pipeline.

This script is a development tool. It is NOT part of production.

Purpose: isolate whether the DICOM visualization bug lives in:
  (a) the geometry construction of the current `Volume` (direction matrix,
      origin, spacing, slice ordering), or
  (b) the VTK render pipeline (vtkImageReslice, vtkImageMapToWindowLevelColors,
      vtkImageSliceMapper, camera).

It loads the same DICOM series twice:
  1. Via SimpleITK (which handles geometry and LPS->RAS natively).
  2. Via the current `DicomSeriesReader` + `VtkImageAdapter`.

It converts the SimpleITK geometry to RAS (LPS->RAS reflection) so that
both pipelines produce a `vtkImageData` with the same coordinate
convention. It then renders both through the SAME VTK pipeline and
prints both geometries side by side. If SimpleITK renders and the
current pipeline does not, the bug is in (a). If neither renders, the
bug is in (b).

Usage:

    .venv\\Scripts\\python.exe scripts\\debug\\dicom\\debug_itk_pipeline.py [path_to_dicom_folder]

Close each window to advance to the next scene.
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
from vtkmodules.util.numpy_support import numpy_to_vtk, vtk_to_numpy
from vtkmodules.vtkCommonDataModel import vtkImageData
from vtkmodules.vtkCommonMath import vtkMatrix3x3
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

try:
    import SimpleITK as sitk  # noqa: F401
except ImportError as exc:
    raise SystemExit(
        "SimpleITK is required for this debug script.\n"
        "Install it with: uv sync --extra debug-itk\n"
        f"(original error: {exc})"
    ) from exc

# ---- VTK / OpenGL configuration (must run before QApplication) -----
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

# LPS -> RAS reflection (x -> -x, y -> -y, z -> z). This is the same
# conversion applied by DicomSorter when building VolumeGeometry.
_LPS_TO_RAS = np.array(
    [
        [-1.0, 0.0, 0.0],
        [0.0, -1.0, 0.0],
        [0.0, 0.0, 1.0],
    ],
    dtype=np.float64,
)


# ----- SimpleITK -> vtkImageData conversion -------------------------
def sitk_to_vtk(sitk_image) -> vtkImageData:
    """Convert a SimpleITK image to vtkImageData in RAS space.

    SimpleITK keeps the DICOM LPS convention: direction is `diag(1,1,1)`
    for a standard axial stack, and origin is `ImagePositionPatient`.
    CranioZ's `Volume` domain uses RAS, so `DicomSeriesReader` converts
    the geometry to RAS. To compare the two pipelines fairly, this
    function performs the same LPS->RAS conversion here.
    """
    size = sitk_image.GetSize()       # (nx, ny, nz) in LPS
    spacing = sitk_image.GetSpacing()  # (sx, sy, sz)
    origin = sitk_image.GetOrigin()    # (ox, oy, oz) in LPS
    direction = sitk_image.GetDirection()  # 9-tuple, row-major 3x3 in LPS

    # Convert the geometry to RAS.
    d_lps = np.array(direction, dtype=np.float64).reshape(3, 3)
    d_ras = _LPS_TO_RAS @ d_lps
    o_ras = _LPS_TO_RAS @ np.array(origin, dtype=np.float64)

    # Pixels are (nz, ny, nx) in C-order.
    pixels = sitk.GetArrayFromImage(sitk_image)

    # VTK wants x-fastest: transpose to (nx, ny, nz) then ravel in C-order.
    flat = np.ascontiguousarray(pixels.transpose(2, 1, 0)).ravel(order="C")

    # numpy_to_vtk infers the VTK type from the numpy dtype. Do NOT pass
    # an explicit array_type; see VtkImageAdapter for the rationale.
    vtk_array = numpy_to_vtk(flat, deep=0)
    vtk_array.SetName("Scalars")

    image = vtkImageData()
    image.SetDimensions(int(size[0]), int(size[1]), int(size[2]))
    image.SetSpacing(float(spacing[0]), float(spacing[1]), float(spacing[2]))
    image.SetOrigin(float(o_ras[0]), float(o_ras[1]), float(o_ras[2]))
    image.GetPointData().SetScalars(vtk_array)

    matrix = vtkMatrix3x3()
    for i in range(3):
        for j in range(3):
            matrix.SetElement(i, j, float(d_ras[i, j]))
    image.SetDirectionMatrix(matrix)

    return image


def _load_via_sitk(dicom_path: Path) -> vtkImageData:
    names = sitk.ImageSeriesReader.GetGDCMSeriesFileNames(str(dicom_path))
    if not names:
        raise RuntimeError(f"no DICOM series found in {dicom_path}")

    reader = sitk.ImageSeriesReader()
    reader.SetFileNames(names)
    # Preserve raw geometry; do not force orthogonal direction.
    reader.SetOutputPixelType(sitk.sitkFloat32)
    sitk_image = reader.Execute()

    print(f"[SITK] size={sitk_image.GetSize()} spacing={sitk_image.GetSpacing()}")
    print(f"[SITK] origin={sitk_image.GetOrigin()}")
    print(f"[SITK] direction={sitk_image.GetDirection()}")

    return sitk_to_vtk(sitk_image)


def _load_via_current(dicom_path: Path) -> vtkImageData:
    reader = DicomSeriesReader()
    try:
        volume, report = reader.read(dicom_path)
    except DicomSeriesReaderError as exc:
        raise RuntimeError(f"current reader failed: {exc}") from exc

    print(f"[CUR]  volume dims={volume.dimensions} spacing={volume.spacing}")
    print(f"[CUR]  origin={volume.origin}")
    print(f"[CUR]  direction={volume.geometry.direction}")

    adapter = VtkImageAdapter()
    return adapter.to_vtk(volume)


def _print_vtk_geometry(image: vtkImageData, label: str) -> None:
    print(f"--- {label} vtkImageData ---")
    print(f"  dims: {image.GetDimensions()}")
    print(f"  spacing: {image.GetSpacing()}")
    print(f"  origin: {image.GetOrigin()}")
    m = image.GetDirectionMatrix()
    print(
        "  direction: "
        f"({m.GetElement(0,0):.3f},{m.GetElement(0,1):.3f},{m.GetElement(0,2):.3f}; "
        f"{m.GetElement(1,0):.3f},{m.GetElement(1,1):.3f},{m.GetElement(1,2):.3f}; "
        f"{m.GetElement(2,0):.3f},{m.GetElement(2,1):.3f},{m.GetElement(2,2):.3f})"
    )
    scalars = image.GetPointData().GetScalars()
    if scalars is not None:
        print(f"  scalars: {scalars.GetNumberOfTuples()} tuples, "
              f"type={scalars.GetDataTypeAsString()}, "
              f"range={scalars.GetRange()}")


# ----- Render pipeline ----------------------------------------------
def _compute_percentile_wl(
    slice_image: vtkImageData,
    p_low: float = 1.0,
    p_high: float = 99.0,
) -> tuple[float, float]:
    """Compute a clinical W/L using percentiles of the slice.

    For an uncalibrated CBCT volume, the raw range (-6114..16383) is
    dominated by air and metal. A fixed clinical W/L (e.g. 400/40 for
    soft tissue) saturates the tissue to black/white. Percentiles of
    the slice keep the soft-tissue contrast visible without hard-coded
    HU assumptions.

    vtkDataArray.GetVoidPointer() returns an int (memory address), not
    a bytes object, so np.frombuffer cannot be used directly. The
    supported bridge is vtk_to_numpy, which returns a numpy.ndarray
    view over the VTK buffer.
    """
    scalars = slice_image.GetPointData().GetScalars()
    if scalars is None:
        return 1.0, 0.0

    arr = vtk_to_numpy(scalars).astype(np.float64, copy=False)
    p1, p99 = np.percentile(arr, [p_low, p_high])
    window = max(float(p99 - p1), 1.0)
    level = float((p1 + p99) / 2.0)
    return window, level


def _build_scene(image: vtkImageData, slice_index: int, title: str):
    """Build the VTK scene for one axial slice of `image`.

    The reslice axes are the columns of the image's direction matrix
    (X, Y, Z axes in RAS). The reslice origin is the *center* of the
    slice in world space:

        world = origin + direction @ (0, 0, slice_index * spacing_z)

    The output extent MUST be set explicitly to (nx-1, ny-1, 0) so
    that vtkImageReslice produces a 2D slice of the requested size.
    SetOutputOrigin MUST NOT be set: the origin is derived from the
    reslice origin and the output extent, and forcing it to (0,0,0)
    shifts the slice by half its width/height (the -79.8 x/y bug).
    """
    dims = image.GetDimensions()
    S = np.array(image.GetSpacing(), dtype=np.float64)
    O = np.array(image.GetOrigin(), dtype=np.float64)

    m = image.GetDirectionMatrix()
    D = np.array(
        [[m.GetElement(i, j) for j in range(3)] for i in range(3)],
        dtype=np.float64,
    )
    x_axis = D[:, 0]
    y_axis = D[:, 1]
    normal = D[:, 2]

    # Slice center in world space: O + D @ (0, 0, k * sz).
    offset_local = np.array([0.0, 0.0, slice_index * S[2]], dtype=np.float64)
    world = O + D @ offset_local

    # Axial slice dimensions.
    nx, ny = dims[0], dims[1]
    sx, sy = S[0], S[1]

    print(f"[{title}] slice index = {slice_index}, world = {world}")
    print(f"[{title}] slice dims = ({nx}, {ny}, 1), "
          f"size = ({(nx - 1) * sx:.2f}, {(ny - 1) * sy:.2f}) mm")

    reslice = vtkImageReslice()
    reslice.SetInputData(image)
    reslice.SetOutputDimensionality(2)
    reslice.SetInterpolationModeToLinear()
    reslice.SetBackgroundLevel(0.0)

    reslice.SetResliceAxesDirectionCosines(
        float(x_axis[0]), float(x_axis[1]), float(x_axis[2]),
        float(y_axis[0]), float(y_axis[1]), float(y_axis[2]),
        float(normal[0]), float(normal[1]), float(normal[2]),
    )
    reslice.SetResliceAxesOrigin(
        float(world[0]), float(world[1]), float(world[2]),
    )

    # Force a 2D output of dimensions (nx, ny, 1). Do NOT call
    # SetOutputOrigin: vtkImageReslice derives the output origin from
    # the reslice origin and the extent, which places the visible
    # slice in [0, (nx-1)*sx] x [0, (ny-1)*sy]. Setting output origin
    # to (0,0,0) shifts the slice by half its extent (the -79.8 bug).
    reslice.SetOutputExtent(0, nx - 1, 0, ny - 1, 0, 0)
    reslice.SetOutputSpacing(float(sx), float(sy), 1.0)
    reslice.Update()

    slice_image = reslice.GetOutput()
    print(f"[{title}] slice origin = {slice_image.GetOrigin()}, "
          f"bounds = {slice_image.GetBounds()}")

    # Clinical W/L from the slice's own percentiles. For an uncalibrated
    # CBCT volume, a fixed W/L (400/40) saturates the tissue. Percentiles
    # keep the contrast visible without hard-coded HU assumptions.
    window, level = _compute_percentile_wl(slice_image)
    print(f"[{title}] W/L (percentile) = ({window:.1f}, {level:.1f})")

    window_level = vtkImageMapToWindowLevelColors()
    window_level.SetInputConnection(reslice.GetOutputPort())
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

    return renderer, window_level, mapper, image_slice, title


def _show_scene(renderer, window_level, mapper, image_slice, title: str) -> None:
    app = QApplication.instance() or QApplication([])
    app.setStyle("Fusion")

    interactor = QVTKRenderWindowInteractor()
    render_window = interactor.GetRenderWindow()
    render_window.AddRenderer(renderer)
    render_window.SetSize(800, 800)

    window = QMainWindow()
    window.setWindowTitle(title)
    window.setCentralWidget(interactor)
    window.resize(800, 800)
    window.show()

    interactor.Initialize()
    interactor.SetInteractorStyle(vtkInteractorStyleImage())

    def _initial_render() -> None:
        if interactor.width() <= 0 or interactor.height() <= 0:
            QTimer.singleShot(50, _initial_render)
            return

        window_level.Update()
        mapper.Update()

        bounds = image_slice.GetBounds()
        print(f"[{title}] ImageSlice bounds: {bounds}")

        # Bail out if bounds are degenerate (no geometry yet).
        if (
            not all(np.isfinite(bounds))
            or bounds[0] == bounds[1]
            or bounds[2] == bounds[3]
        ):
            QTimer.singleShot(50, _initial_render)
            return

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

        render_window.Render()

    QTimer.singleShot(0, _initial_render)
    app.exec()

    interactor.Finalize()
    interactor.setParent(None)
    interactor.deleteLater()


def main() -> int:
    if len(sys.argv) > 2:
        print("Usage: debug_itk_pipeline.py [path_to_dicom_folder]")
        return 1

    dicom_path = Path(sys.argv[1]) if len(sys.argv) == 2 else _DEFAULT_DICOM_PATH
    if not dicom_path.is_dir():
        print(f"Not a directory: {dicom_path}")
        return 1

    # 1. Load via SimpleITK (geometry converted to RAS).
    print(f"Loading DICOM with SimpleITK from {dicom_path}...")
    itk_image = _load_via_sitk(dicom_path)
    _print_vtk_geometry(itk_image, "SITK")

    # 2. Load via the current pipeline (already in RAS).
    print(f"\nLoading DICOM with current DicomSeriesReader from {dicom_path}...")
    cur_image = _load_via_current(dicom_path)
    _print_vtk_geometry(cur_image, "CUR")

    # 3. Render both scenes, sequentially (close each window to advance).
    print("\nRendering SimpleITK scene. Close the window to advance.")
    r1, wl1, m1, s1, t1 = _build_scene(itk_image, _SLICE_INDEX, "SimpleITK")
    _show_scene(r1, wl1, m1, s1, t1)

    print("Rendering current-pipeline scene. Close the window to exit.")
    r2, wl2, m2, s2, t2 = _build_scene(cur_image, _SLICE_INDEX, "Current DicomSeriesReader")
    _show_scene(r2, wl2, m2, s2, t2)

    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())