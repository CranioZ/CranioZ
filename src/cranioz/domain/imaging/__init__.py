"""Medical imaging domain — internal volume representation.

This package defines the core imaging concepts independently of
file formats (DICOM), visualization frameworks (VTK), or imaging
libraries (ITK, pydicom). It may use NumPy for numerical buffer
representation, but must not depend on anything else.

The domain model follows the Medical Imaging Infrastructure
specification (§4):

- Volume:              the 3D image itself.
- VolumeGeometry:      spatial geometry (origin, spacing, direction).
- ImageMetadata:       DICOM-derived metadata (modality, rescale, ...).
- VolumeProvenance:    traceability (source, validation, processing).
- IntensityScale:      calibration classification (HU, UNCALIBRATED, UNKNOWN).

Public API:

- Volume              — aggregate root of the imaging domain.
- VolumeGeometry      — spatial geometry with index-to-world mapping.
- ImageMetadata       — image metadata (frozen).
- VolumeProvenance    — provenance record (frozen).
- IntensityScale      — enum: HU, UNCALIBRATED, UNKNOWN.
- ImageModality       — enum: CT, CBCT, MRI, UNKNOWN.
- CoordinateSystem    — enum: RAS, LPS, IJK.

See `docs/architecture/imaging/medical_imaging_infrastructure.md`.
"""

from cranioz.domain.imaging.coordinate_system import CoordinateSystem
from cranioz.domain.imaging.image_metadata import (
    ImageMetadata,
    ImageModality,
)

# IntensityScale lives in volume.py but is re-exported here for
# convenience.
from cranioz.domain.imaging.volume import IntensityScale, Volume
from cranioz.domain.imaging.volume_geometry import VolumeGeometry
from cranioz.domain.imaging.volume_provenance import VolumeProvenance

__all__ = [
    "CoordinateSystem",
    "ImageMetadata",
    "ImageModality",
    "IntensityScale",
    "Volume",
    "VolumeGeometry",
    "VolumeProvenance",
]
