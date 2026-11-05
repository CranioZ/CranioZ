"""VtkImageAdapter — convert a Volume into a vtkImageData.

This is the only component allowed to translate the domain `Volume`
into a `vtkImageData`. It preserves:

- Origin (RAS).
- Spacing (mm).
- Direction matrix (RAS).
- Scalar data (NumPy → VTK).

The direction matrix IS applied (via SetDirectionMatrix). This is
required for correct MPR reslicing and volume rendering when the
volume is not in the canonical axial orientation (e.g., after the
LPS→RAS conversion, which flips X and Y).

The adapter does NOT mutate the `Volume`. It does NOT free the
NumPy buffer. The caller (the View) is responsible for keeping the
Volume alive while the `vtkImageData` is in use.

The adapter is stateless: it can be reused across calls. It does
not cache results.

See Medical Imaging Infrastructure §8.1, §12.1.
"""

from __future__ import annotations

import logging

import numpy as np
from vtkmodules.util.numpy_support import numpy_to_vtk
from vtkmodules.vtkCommonCore import vtkDataArray
from vtkmodules.vtkCommonDataModel import vtkImageData
from vtkmodules.vtkCommonMath import vtkMatrix3x3

from cranioz.domain.imaging.volume import IntensityScale, Volume

_logger = logging.getLogger(__name__)

# Supported NumPy dtypes. The VTK type is inferred from the NumPy
# dtype by numpy_to_vtk; this table is only used for validation and
# for logging. Do NOT pass an explicit array_type: the integer
# constants are ambiguous (VTK_SHORT == 3 == VTK_UNSIGNED_CHAR), and
# passing them has been observed to produce the wrong VTK type.
_SUPPORTED_DTYPES = frozenset(
    {
        np.dtype(np.int16),
        np.dtype(np.uint16),
        np.dtype(np.int32),
        np.dtype(np.uint32),
        np.dtype(np.float32),
    }
)


class VtkImageAdapterError(ValueError):
    """Raised when a Volume cannot be converted to vtkImageData."""


class VtkImageAdapter:
    """Converts a Volume into a vtkImageData.

    The resulting `vtkImageData` shares the NumPy buffer (deep=False).
    The caller must keep a reference to the `Volume` for the lifetime
    of the `vtkImageData`.
    """

    def to_vtk(self, volume: Volume) -> vtkImageData:
        """Convert a Volume to vtkImageData.

        Args:
            volume: the domain Volume to convert.

        Returns:
            A `vtkImageData` with the same voxel data, origin,
            spacing, and direction.

        Raises:
            VtkImageAdapterError: if the Volume's dtype is unsupported,
                or if the data shape does not match the geometry.
        """
        data = volume.data
        if data.dtype not in _SUPPORTED_DTYPES:
            raise VtkImageAdapterError(
                f"unsupported numpy dtype for VTK conversion: {data.dtype}"
            )

        # Verify the data shape matches the geometry.
        if data.shape != volume.geometry.shape_zyx:
            raise VtkImageAdapterError(
                f"Volume.data shape {data.shape} does not match "
                f"geometry.shape_zyx {volume.geometry.shape_zyx}"
            )

        # VTK expects a contiguous buffer with x fastest, then y, then z.
        # Volume.data is (nz, ny, nx), so transpose to (nx, ny, nz) and
        # ravel in C order (row-major). The result is contiguous, which
        # numpy_to_vtk(deep=0) requires to share the buffer.
        flat = np.ascontiguousarray(data.transpose(2, 1, 0)).ravel(order="C")

        _logger.debug(
            "VtkImageAdapter: numpy dtype=%s, shape=%s, contiguous=%s",
            flat.dtype,
            flat.shape,
            flat.flags["C_CONTIGUOUS"],
        )

        # Let numpy_to_vtk infer the VTK type from the NumPy dtype.
        # Do NOT pass array_type: the integer constants are ambiguous
        # and have caused the scalar array to be created as uint8.
        vtk_array: vtkDataArray = numpy_to_vtk(  # type: ignore[no-untyped-call]
            flat,
            deep=0,  # share the NumPy buffer (no copy)
        )
        vtk_array.SetName("Scalars")

        nx_d, ny_d, nz_d = volume.geometry.dimensions

        image = vtkImageData()
        image.SetDimensions(nx_d, ny_d, nz_d)
        image.SetSpacing(*volume.geometry.spacing)
        image.SetOrigin(*volume.geometry.origin)
        image.GetPointData().SetScalars(vtk_array)

        # Apply the direction matrix. Volume.geometry.direction is a
        # 3x3 tuple-of-tuples; VTK expects a vtkMatrix3x3.
        direction = volume.geometry.direction
        matrix = vtkMatrix3x3()
        for i in range(3):
            for j in range(3):
                matrix.SetElement(i, j, float(direction[i][j]))
        image.SetDirectionMatrix(matrix)

        _logger.debug(
            "VtkImageAdapter: direction matrix applied: %s",
            [[direction[i][j] for j in range(3)] for i in range(3)],
        )

        return image

    # ----- Convenience ----------------------------------------------

    @staticmethod
    def is_hu_calibrated(volume: Volume) -> bool:
        """Return True if the Volume is calibrated to HU."""
        return volume.intensity_scale is IntensityScale.HU