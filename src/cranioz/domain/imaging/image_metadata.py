"""ImageMetadata — DICOM-derived metadata for an imaging volume.

This is a frozen value object that carries the metadata required by
the application: modality, study/series identifiers, intensity
rescaling parameters, transfer syntax, and acquisition info.

DICOM-specific structures (Dataset, DataElement) must NOT leak into
the domain. Only the fields listed here are preserved.

The `metadata_available` field distinguishes between "the attribute
was missing" and "the attribute was present but empty". Missing
information must remain distinguishable from default values.

See Medical Imaging Infrastructure §4.4.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class ImageModality(Enum):
    """Imaging modality of a volume.

    CBCT (Cone Beam CT) is distinct from conventional CT (Fan Beam)
    because their intensity scales, geometric accuracy, and clinical
    reliability differ.
    """

    CT = "ct"
    CBCT = "cbct"
    MRI = "mri"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ImageMetadata:
    """DICOM-derived metadata for a Volume.

    All fields are optional except `modality`, which defaults to
    UNKNOWN. The reader populates the fields it can extract.

    `rescale_slope` and `rescale_intercept` are preserved separately
    from the voxel data. Whether they were applied (and therefore
    whether the voxel values are Hounsfield Units) is expressed by
    `Volume.intensity_scale`, not by this metadata.
    """

    # Identity / source
    modality: ImageModality = ImageModality.UNKNOWN
    study_instance_uid: str | None = None
    series_instance_uid: str | None = None
    study_description: str | None = None
    series_description: str | None = None
    patient_id: str | None = None
    patient_name: str | None = None
    patient_birth_date: str | None = None
    patient_sex: str | None = None

    # Acquisition
    acquisition_date: datetime | None = None
    manufacturer: str | None = None
    manufacturer_model_name: str | None = None
    kvp: float | None = None
    slice_thickness: float | None = None

    # Pixel interpretation (raw DICOM attributes)
    rescale_slope: float | None = None
    rescale_intercept: float | None = None
    bits_allocated: int | None = None
    bits_stored: int | None = None
    pixel_representation: int | None = None
    transfer_syntax_uid: str | None = None
    photometric_interpretation: str | None = None

    # Diagnostics
    metadata_available: dict[str, bool] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.modality is None:
            raise ValueError("ImageMetadata.modality must not be None")
