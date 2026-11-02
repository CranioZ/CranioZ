"""VtkImageAdapter — convert a Volume into a vtkImageData.

This is the only component allowed to translate the domain `Volume`
into a `vtkImageData`. It preserves:

- Origin (RAS).
- Spacing (mm).
- Scalar data (NumPy → VTK).

The direction matrix is NOT applied. The volume is assumed to be
in the canonical axial orientation (X, Y, Z aligned with VTK axes).
This is a pragmatic simplification for the first visualization
iteration. Proper orientation handling will be added later.

The adapter does NOT mutate the `Volume`. It does NOT free the
NumPy buffer. The caller (the View) is responsible for keeping the
Volume alive while the `vtkImageData` is in use.

The adapter is stateless: it can be reused across calls. It does
not cache results.

See Medical Imaging Infrastructure §8.1, §12.1.
"""

from __future__ import annotations

import numpy as np
from vtkmodules.util.numpy_support import numpy_to_vtk
from vtkmodules.vtkCommonCore import vtkDataArray
from vtkmodules.vtkCommonDataModel import vtkImageData

from cranioz.domain.imaging.volume import IntensityScale, Volume

# Mapping from NumPy dtype to VTK scalar type.
_NUMPY_TO_VTK = {
    np.dtype(np.int16): 3,  # VTK_SHORT
    np.dtype(np.uint16): 4,  # VTK_UNSIGNED_SHORT
    np.dtype(np.int32): 5,  # VTK_INT
    np.dtype(np.uint32): 6,  # VTK_UNSIGNED_INT
    np.dtype(np.float32): 10,  # VTK_FLOAT
}


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
            and spacing.

        Raises:
            VtkImageAdapterError: if the Volume's dtype is unsupported,
                or if the data shape does not match the geometry.
        """
        data = volume.data
        if data.dtype not in _NUMPY_TO_VTK:
            raise VtkImageAdapterError(f"unsupported numpy dtype for VTK conversion: {data.dtype}")

        # Verify the data shape matches the geometry.
        if data.shape != volume.geometry.shape_zyx:
            raise VtkImageAdapterError(
                f"Volume.data shape {data.shape} does not match "
                f"geometry.shape_zyx {volume.geometry.shape_zyx}"
            )

        # Flatten in VTK's expected order (x fastest, then y, then z).
        flat = data.ravel(order="F")

        vtk_array: vtkDataArray = numpy_to_vtk(  # type: ignore[no-untyped-call]
            flat,
            deep=0,  # share the NumPy buffer (no copy)
            array_type=_NUMPY_TO_VTK[data.dtype],
        )
        vtk_array.SetName("Scalars")

        nx_d, ny_d, nz_d = volume.geometry.dimensions

        image = vtkImageData()
        image.SetDimensions(nx_d, ny_d, nz_d)
        image.SetSpacing(*volume.geometry.spacing)
        image.SetOrigin(*volume.geometry.origin)
        image.GetPointData().SetScalars(vtk_array)

        # NOT applying SetDirectionMatrix. The volume is assumed to be
        # in the canonical axial orientation.

        return image

    # ----- Convenience ----------------------------------------------

    @staticmethod
    def is_hu_calibrated(volume: Volume) -> bool:
        """Return True if the Volume is calibrated to HU."""
        return volume.intensity_scale is IntensityScale.HU
