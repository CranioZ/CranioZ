"""STL import and export.

STL is the initial external mesh interchange format. It carries no
units and no coordinate frame, so the caller must supply both. The
importer never silently assumes millimetres or RAS.

The reader does not weld vertices. Two vertices with identical
coordinates remain distinct in the resulting ``Mesh`` unless the
caller explicitly welds them (out of scope for this block).

See the ``Geometry Infrastructure`` architecture document, §4.5
and §9.3.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from vtkmodules.util.numpy_support import vtk_to_numpy
from vtkmodules.vtkCommonCore import vtkPoints
from vtkmodules.vtkCommonDataModel import vtkCellArray, vtkPolyData
from vtkmodules.vtkIOGeometry import (
    vtkSTLReader,
    vtkSTLWriter,
)

from cranioz.domain.geometry.coordinate_frame import CoordinateFrame
from cranioz.domain.geometry.mesh import Mesh
from cranioz.infrastructure.geometry.adapters.vtk.polydata import (
    mesh_to_polydata,
)


class StlReadError(RuntimeError):
    """Raised when an STL file cannot be read or is malformed."""


class StlWriteError(RuntimeError):
    """Raised when a Mesh cannot be written as STL."""


def read_stl(
    path: str | Path,
    *,
    unit_scale: float = 1.0,
    coordinate_frame: CoordinateFrame | None = None,
) -> Mesh:
    """Read an STL file and return a canonical ``Mesh``.

    Args:
        path: filesystem path to the STL file.
        unit_scale: factor applied to every vertex coordinate. The STL
            format carries no unit information; the caller declares it.
            For example, pass ``0.1`` for an STL whose coordinates are
            in tenths of a millimetre.
        coordinate_frame: the frame to record on the resulting ``Mesh``.
            Defaults to ``CoordinateFrame.identity()`` (RAS). The
            reader does not transform the coordinates; ``unit_scale``
            is the only numeric transformation applied.

    Raises:
        StlReadError: if the file cannot be read, is empty, or its
            geometry cannot be interpreted as a triangular mesh.
    """
    file_path = Path(path).expanduser()
    if not file_path.is_file():
        raise StlReadError(f"STL file not found: {file_path}")
    if unit_scale <= 0 or not np.isfinite(unit_scale):
        raise StlReadError(f"unit_scale must be a positive finite number, got {unit_scale}")

    reader = vtkSTLReader()
    reader.SetFileName(str(file_path))
    reader.Update()
    poly = reader.GetOutput()

    if poly is None or poly.GetNumberOfPoints() == 0:
        raise StlReadError(f"STL file is empty or unreadable: {file_path}")

    vertices = _read_vertices(poly, unit_scale)
    faces = _read_faces(poly)

    frame = coordinate_frame if coordinate_frame is not None else CoordinateFrame.identity()
    return Mesh(vertices=vertices, faces=faces, coordinate_frame=frame)


def write_stl(
    mesh: Mesh,
    path: str | Path,
) -> None:
    """Write a ``Mesh`` to an STL file.

    The writer assumes the ``Mesh`` vertices are already in the
    coordinate frame the caller wants to export. No unit conversion is
    applied: the caller must scale the vertices before calling this
    function if the target STL expects a different unit.

    The STL format discards the ``CoordinateFrame`` and any attributes.
    Only geometry is preserved.

    Raises:
        StlWriteError: if the file cannot be written.
    """
    file_path = Path(path).expanduser()

    poly = mesh_to_polydata(mesh)
    writer = vtkSTLWriter()
    writer.SetFileName(str(file_path))
    writer.SetInputData(poly)
    try:
        writer.Write()
    except Exception as exc:
        raise StlWriteError(f"cannot write STL to {file_path}: {exc}") from exc


# ----- Internals ---------------------------------------------------


def _read_vertices(poly: vtkPolyData, unit_scale: float) -> np.ndarray:
    vtk_points: vtkPoints = poly.GetPoints()
    if vtk_points is None or vtk_points.GetNumberOfPoints() == 0:
        raise StlReadError("STL contains no vertices")
    raw = vtk_to_numpy(vtk_points.GetData())  # type: ignore[no-untyped-call]
    vertices = raw.astype(np.float32, copy=True)
    if unit_scale != 1.0:
        vertices *= np.float32(unit_scale)
    return np.asarray(vertices, dtype=np.float32)


def _read_faces(poly: vtkPolyData) -> np.ndarray:
    vtk_cells: vtkCellArray = poly.GetPolys()
    if vtk_cells is None or vtk_cells.GetNumberOfCells() == 0:
        raise StlReadError("STL contains no triangles")

    raw = vtk_to_numpy(vtk_cells.GetData())  # type: ignore[no-untyped-call]
    # vtkCellArray's legacy representation is flat:
    # [3, i0, i1, i2, 3, i3, i4, i5, ...].
    # The reader for STL always emits triangles, so every prefix is 3.
    if raw.size % 4 != 0:
        raise StlReadError(f"unexpected cell array length: {raw.size}")
    triangles = raw.reshape(-1, 4)
    if not np.all(triangles[:, 0] == 3):
        raise StlReadError("STL contains non-triangular cells")
    faces = triangles[:, 1:].astype(np.uint32, copy=True)
    return np.asarray(faces, dtype=np.uint32)
