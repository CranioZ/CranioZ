"""Volume — the aggregate root of the medical imaging domain.

A Volume combines:
- The voxel buffer (NumPy array in `[z, y, x]` order).
- The spatial geometry (VolumeGeometry).
- The DICOM-derived metadata (ImageMetadata).
- The intensity calibration classification (IntensityScale).
- The provenance record (VolumeProvenance).

The Volume does NOT depend on VTK, pydicom, ITK, or Qt. It is pure
Python + NumPy. The VTK adapter (in Infrastructure) converts a
Volume to a vtkImageData when needed.

IntensityScale is the single source of truth for "are these values
Hounsfield Units?". The reader is responsible for setting it
correctly. A Volume classified as UNCALIBRATED must not be used for
HU-based operations (window/level presets, segmentation thresholds)
without explicit acknowledgment.

See Medical Imaging Infrastructure §4.1, §4.5.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import numpy as np

from cranioz.domain.imaging.image_metadata import ImageMetadata
from cranioz.domain.imaging.volume_geometry import VolumeGeometry
from cranioz.domain.imaging.volume_provenance import VolumeProvenance


class IntensityScale(Enum):
    """Intensity calibration classification of a Volume.

    - HU:            values are calibrated Hounsfield Units.
    - UNCALIBRATED:  values are valid but not HU. Typical for CBCT,
                     where voxel values are arbitrary but consistent
                     within the volume.
    - UNKNOWN:       calibration cannot be established (e.g., mixed
                     series, corrupted metadata).
    """

    HU = "hu"
    UNCALIBRATED = "uncalibrated"
    UNKNOWN = "unknown"


class VolumeError(ValueError):
    """Raised when a Volume is constructed or used inconsistently."""


@dataclass
class Volume:
    """A 3D medical image with explicit geometry, metadata, and provenance.

    The voxel buffer is the canonical in-memory representation.
    Adapters (VTK, ITK) must retain a reference to this buffer and
    must not free it independently.

    The Volume is mutable at the buffer level (NumPy arrays are
    mutable), but the domain does not expose a public mutation API.
    All mutations must go through Commands (ADR-0007).
    """

    #: The voxel buffer, shape (nz, ny, nx), dtype must be one of
    #: int16, uint16, int32, uint32, float32.
    data: np.ndarray

    #: Spatial geometry.
    geometry: VolumeGeometry

    #: DICOM-derived metadata.
    metadata: ImageMetadata

    #: Intensity calibration classification.
    intensity_scale: IntensityScale

    #: Traceability record.
    provenance: VolumeProvenance

    #: Unique identifier within the project (used by DomainObjectStore).
    volume_id: str

    def __post_init__(self) -> None:
        # Data must be a NumPy array.
        if not isinstance(self.data, np.ndarray):
            raise VolumeError(
                f"Volume.data must be a numpy.ndarray, got {type(self.data).__name__}"
            )

        # Data must be 3D.
        if self.data.ndim != 3:
            raise VolumeError(f"Volume.data must be 3D, got {self.data.ndim}D")

        # Data shape must match geometry.
        expected_zyx = self.geometry.shape_zyx
        if self.data.shape != expected_zyx:
            raise VolumeError(
                f"Volume.data shape {self.data.shape} does not match "
                f"geometry.shape_zyx {expected_zyx}"
            )

        # Data dtype must be supported.
        supported_dtypes = (
            np.dtype(np.int16),
            np.dtype(np.uint16),
            np.dtype(np.int32),
            np.dtype(np.uint32),
            np.dtype(np.float32),
        )
        if self.data.dtype not in supported_dtypes:
            raise VolumeError(
                f"Volume.data dtype {self.data.dtype} is not supported. "
                f"Expected one of {[str(d) for d in supported_dtypes]}"
            )

        # volume_id must be non-empty.
        if not self.volume_id:
            raise VolumeError("Volume.volume_id must not be empty")

    # ----- Convenience accessors ------------------------------------

    @property
    def dimensions(self) -> tuple[int, int, int]:
        """Return dimensions in (nx, ny, nz) order."""
        return self.geometry.dimensions

    @property
    def spacing(self) -> tuple[float, float, float]:
        return self.geometry.spacing

    @property
    def origin(self) -> tuple[float, float, float]:
        return self.geometry.origin

    @property
    def is_hu_calibrated(self) -> bool:
        """Return True if the volume is calibrated to Hounsfield Units."""
        return self.intensity_scale is IntensityScale.HU

    @property
    def scalar_range(self) -> tuple[float, float]:
        """Return the (min, max) scalar range of the voxel buffer."""
        return (float(self.data.min()), float(self.data.max()))

    # ----- Sampling -------------------------------------------------

    def sample_world(
        self,
        world: tuple[float, float, float],
    ) -> float | None:
        """Return the voxel value at a physical coordinate (RAS).

        Returns None if the coordinate is outside the volume.
        Uses nearest-neighbor sampling (no interpolation).

        See Medical Imaging Infrastructure §11.6.
        """
        if not self.geometry.contains_world(world):
            return None

        index_float = self.geometry.world_to_index(world)
        i, j, k = (round(v) for v in index_float)

        # Defensive bounds check after rounding.
        nx, ny, nz = self.geometry.dimensions
        if not (0 <= i < nx and 0 <= j < ny and 0 <= k < nz):
            return None

        # Data is (nz, ny, nx).
        return float(self.data[k, j, i])

    # ----- Representation -------------------------------------------

    def __repr__(self) -> str:
        return (
            f"Volume(volume_id={self.volume_id!r}, "
            f"dimensions={self.dimensions}, "
            f"intensity_scale={self.intensity_scale.value}, "
            f"shape={self.data.shape}, dtype={self.data.dtype})"
        )
