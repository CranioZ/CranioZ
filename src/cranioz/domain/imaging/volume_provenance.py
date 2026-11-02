"""VolumeProvenance — traceability of a volume's origin and processing.

Every Volume carries a provenance record. It is the single source of
truth for "where did this data come from, what assumptions were made,
and how was it validated?".

The provenance is deliberately small: it references source files by
hash, not by content. It does NOT duplicate the DICOM data.

See Medical Imaging Infrastructure §4.6, §9.3.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class VolumeProvenance:
    """Traceability record for a Volume.

    All fields are optional except `import_timestamp`. The reader
    populates the fields it can extract.
    """

    #: When the import occurred (UTC).
    import_timestamp: datetime

    #: Source format (e.g., "DICOM", "NIfTI").
    source_format: str = "DICOM"

    #: Source directory or file reference (no PHI).
    source_reference: str | None = None

    #: SHA-256 hashes of source files, keyed by relative path.
    #: Empty for externally referenced sources where hashing was
    #: not performed.
    source_hashes: tuple[tuple[str, str], ...] = ()

    #: Import parameters (e.g., storage mode, path).
    import_parameters: tuple[tuple[str, str], ...] = ()

    #: Assumptions made during import (e.g., "assumed axial
    #: orientation because ImageOrientationPatient was missing").
    geometry_assumptions: tuple[str, ...] = ()

    #: Validation outcome summary (severity, message).
    validation_outcome: tuple[tuple[str, str], ...] = ()

    #: Processing operations applied after import (e.g., Gaussian
    #: smoothing). Empty for raw imported volumes.
    processing_history: tuple[str, ...] = ()

    #: Parent volume reference, when this volume is derived.
    parent_volume_id: str | None = None

    def __post_init__(self) -> None:
        if self.import_timestamp.tzinfo is None:
            raise ValueError("VolumeProvenance.import_timestamp must be timezone-aware")

    def with_processing_step(self, step: str) -> VolumeProvenance:
        """Return a new provenance with an additional processing step."""
        return VolumeProvenance(
            import_timestamp=self.import_timestamp,
            source_format=self.source_format,
            source_reference=self.source_reference,
            source_hashes=self.source_hashes,
            import_parameters=self.import_parameters,
            geometry_assumptions=self.geometry_assumptions,
            validation_outcome=self.validation_outcome,
            processing_history=(*self.processing_history, step),
            parent_volume_id=self.parent_volume_id,
        )
