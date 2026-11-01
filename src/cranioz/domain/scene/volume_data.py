"""VolumeData — payload of a DICOM volume in the Scene.

The ``Scene`` and the ``DomainObjectStore`` deal with opaque object
payloads (``Any``). ``VolumeData`` is the first concrete payload
type we introduce, wrapping the ``vtkImageData`` produced by the
DICOM loader.

This is deliberately minimal. It carries only what the loader can
guarantee and what a future MPR view will need:

- ``vtk_image_data`` — the actual volume (in-memory, not serialized).
- ``series_uid``      — DICOM SeriesInstanceUID, for provenance.
- ``spacing``         — (sx, sy, sz) in millimetres.
- ``origin``          — (ox, oy, oz) in millimetres.
- ``dimensions``      — (nx, ny, nz) voxels.

Serialization (``scene.json``) is out of scope for Phase 4 and is
deferred to a later piece. ``VolumeData`` is in-memory only.

See ADR-0008, scene.md.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class VolumeData:
    """Immutable payload of a DICOM volume."""

    vtk_image_data: Any  # vtkImageData; kept as Any to avoid a hard VTK import
    series_uid: str
    spacing: tuple[float, float, float]
    origin: tuple[float, float, float]
    dimensions: tuple[int, int, int]

    def __post_init__(self) -> None:
        if not self.series_uid:
            raise ValueError("VolumeData.series_uid must not be empty")
        if len(self.spacing) != 3:
            raise ValueError("VolumeData.spacing must have 3 components")
        if len(self.origin) != 3:
            raise ValueError("VolumeData.origin must have 3 components")
        if len(self.dimensions) != 3:
            raise ValueError("VolumeData.dimensions must have 3 components")
        if any(s <= 0 for s in self.spacing):
            raise ValueError("VolumeData.spacing components must be positive")
        if any(d <= 0 for d in self.dimensions):
            raise ValueError("VolumeData.dimensions components must be positive")

    def __repr__(self) -> str:
        return (
            f"VolumeData(series_uid={self.series_uid!r}, "
            f"dimensions={self.dimensions!r}, "
            f"spacing={self.spacing!r})"
        )
