"""VtkImageAdapter — the sole bridge from Volume to vtkImageData.

Ordering contract (critical):

    Volume.data.shape == (Z, Y, X)          # NumPy convention
    vtkImageData.SetDimensions(X, Y, Z)     # VTK convention
    flat = data.ravel(order="C")            # NO transpose

Combining ``transpose(2, 1, 0)`` with ``ravel(order="C")`` corrupts
the memory layout and produces stripe artifacts in 3D rendering.
This is the only valid conversion.
"""

from __future__ import annotations

import logging

import numpy as np
import vtk
from vtkmodules.util.numpy_support import numpy_to_vtk
from vtkmodules.vtkCommonDataModel import vtkImageData

from cranioz.domain.imaging.volume import Volume

_logger = logging.getLogger(__name__)


class VtkImageAdapter:
    """Converts a CranioZ Volume into a vtkImageData.

    Contrato de ordenação:

        Volume.data.shape == (Z, Y, X)
        image.SetDimensions(nx, ny, nz)
        flat = data.ravel(order="C")  # sem transposição
    """

    def to_vtk(self, volume: Volume) -> vtkImageData:
        data = np.ascontiguousarray(volume.data, dtype=np.int16)
        nz, ny, nx = data.shape

        flat = data.ravel(order="C")

        vtk_array = numpy_to_vtk(  # type: ignore[no-untyped-call]
            flat,
            deep=True,
            array_type=vtk.VTK_SHORT,
        )

        image = vtkImageData()
        image.SetDimensions(nx, ny, nz)
        image.SetSpacing(*volume.spacing)
        image.SetOrigin(*volume.origin)
        image.GetPointData().SetScalars(vtk_array)

        direction = volume.geometry.direction
        matrix = vtk.vtkMatrix3x3()
        for i in range(3):
            for j in range(3):
                matrix.SetElement(i, j, float(direction[i][j]))
        image.SetDirectionMatrix(matrix)

        _logger.debug(
            "VtkImageAdapter: dims=%s, spacing=%s, range=%s, dtype=int16",
            image.GetDimensions(),
            image.GetSpacing(),
            vtk_array.GetRange(),
        )

        return image
