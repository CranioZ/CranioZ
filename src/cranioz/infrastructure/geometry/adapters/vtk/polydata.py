"""``Mesh`` → ``vtkPolyData`` conversion.

The adapter reads the canonical ``Mesh`` arrays without mutating them.
The resulting ``vtkPolyData`` shares the vertex buffer when the dtype
and contiguity requirements are satisfied; otherwise it copies. In
both cases, the caller must keep the ``Mesh`` alive for the lifetime
of the VTK object that references it.

See the ``Geometry Infrastructure`` architecture document, §11.
"""

from __future__ import annotations

import numpy as np
from vtkmodules.util.numpy_support import (
    numpy_to_vtk,
    numpy_to_vtkIdTypeArray,
)
from vtkmodules.vtkCommonCore import vtkPoints
from vtkmodules.vtkCommonDataModel import vtkCellArray, vtkPolyData

from cranioz.domain.geometry.mesh import Mesh

#: VTK scalar types for the supported vertex dtypes.
_VERTEX_NUMPY_TO_VTK = {
    np.dtype(np.float32): 10,  # VTK_FLOAT
    np.dtype(np.float64): 11,  # VTK_DOUBLE
}


def mesh_to_polydata(mesh: Mesh) -> vtkPolyData:
    """Convert a canonical ``Mesh`` into a ``vtkPolyData``.

    The conversion preserves vertex coordinates and triangle topology.
    No unit conversion and no coordinate-frame transformation are
    applied: the caller is responsible for both.

    The vertex buffer may be shared with the ``Mesh`` (zero-copy)
    when the dtype and contiguity match VTK's requirements. The
    caller must keep the ``Mesh`` alive for the lifetime of the
    returned ``vtkPolyData``.

    Args:
        mesh: the canonical mesh.

    Raises:
        ValueError: if the ``Mesh`` vertex dtype is not supported
            (the ``Mesh`` constructor should have already rejected it,
            but this adapter validates defensively).
    """
    vertex_dtype = mesh.vertices.dtype
    if vertex_dtype not in _VERTEX_NUMPY_TO_VTK:
        raise ValueError(f"unsupported vertex dtype for VTK conversion: {vertex_dtype}")

    # vtkPoints requires a contiguous, Fortran-order buffer for the
    # interleaved (x0, y0, z0, x1, y1, z1, ...) representation.
    flat_vertices = np.ascontiguousarray(mesh.vertices, dtype=vertex_dtype)

    vtk_array = numpy_to_vtk(  # type: ignore[no-untyped-call]
        flat_vertices,
        deep=0,  # share the buffer
        array_type=_VERTEX_NUMPY_TO_VTK[vertex_dtype],
    )
    vtk_points = vtkPoints()
    vtk_points.SetData(vtk_array)

    # vtkCellArray expects [count, i0, i1, i2, count, ...] as a
    # vtkIdTypeArray. numpy_to_vtkIdTypeArray produces the correct
    # array type for ImportLegacyFormat.
    n_faces = mesh.face_count
    connectivity = np.empty((n_faces, 4), dtype=np.int64)
    connectivity[:, 0] = 3
    connectivity[:, 1:] = mesh.faces.astype(np.int64, copy=False)
    vtk_cells = vtkCellArray()
    vtk_cells.ImportLegacyFormat(
        numpy_to_vtkIdTypeArray(  # type: ignore[no-untyped-call]
            connectivity.ravel(),
            deep=1,  # VTK owns the copy; the Mesh is not mutated
        )
    )

    poly = vtkPolyData()
    poly.SetPoints(vtk_points)
    poly.SetPolys(vtk_cells)
    return poly
