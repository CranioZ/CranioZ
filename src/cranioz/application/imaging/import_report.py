"""ImportReport — structured report for a DICOM import operation.

Every import operation produces a report. The report is user-facing:
it summarizes what was imported, what was rejected, and what
assumptions were made.

The report does not contain patient-identifying information beyond
what is necessary for identity verification (when applicable). The
reader must minimize PHI exposure.

See Medical Imaging Infrastructure §6.1, §5.8.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class IssueSeverity(Enum):
    """Severity of a validation issue.

    - ERROR:   the data cannot be safely imported.
    - WARNING: the data may be usable but requires review.
    - INFO:    relevant diagnostic information.
    """

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass(frozen=True)
class ImportIssue:
    """A single issue found during import."""

    severity: IssueSeverity
    code: str
    message: str

    def __post_init__(self) -> None:
        if not self.code:
            raise ValueError("ImportIssue.code must not be empty")
        if not self.message:
            raise ValueError("ImportIssue.message must not be empty")


@dataclass(frozen=True)
class ImportReport:
    """Structured report for a DICOM import operation."""

    #: Whether the import succeeded (no ERROR severity issues).
    success: bool

    #: Number of DICOM files detected.
    files_detected: int

    #: Number of valid image instances.
    instances_loaded: int

    #: Number of instances skipped (non-image, corrupted, etc.).
    instances_skipped: int

    #: Modality detected (e.g., "CT", "CBCT").
    modality: str

    #: Transfer syntax UID.
    transfer_syntax: str | None

    #: Volume dimensions (nx, ny, nz).
    dimensions: tuple[int, int, int] | None

    #: Voxel spacing (sx, sy, sz) in millimetres.
    spacing: tuple[float, float, float] | None

    #: Intensity scale classification ("hu", "uncalibrated", "unknown").
    intensity_scale: str | None

    #: List of issues (errors, warnings, info).
    issues: tuple[ImportIssue, ...] = field(default_factory=tuple)

    #: Assumptions made during import (e.g., assumed geometry).
    assumptions: tuple[str, ...] = field(default_factory=tuple)

    @property
    def has_errors(self) -> bool:
        return any(i.severity is IssueSeverity.ERROR for i in self.issues)

    @property
    def has_warnings(self) -> bool:
        return any(i.severity is IssueSeverity.WARNING for i in self.issues)

    def issues_by_severity(self, severity: IssueSeverity) -> tuple[ImportIssue, ...]:
        return tuple(i for i in self.issues if i.severity is severity)

    def summary(self) -> str:
        """Return a concise one-line summary for logging."""
        parts = [
            f"files={self.files_detected}",
            f"loaded={self.instances_loaded}",
            f"skipped={self.instances_skipped}",
            f"modality={self.modality}",
        ]
        if self.dimensions is not None:
            parts.append(f"dims={self.dimensions}")
        if self.spacing is not None:
            parts.append(f"spacing={self.spacing}")
        if self.intensity_scale is not None:
            parts.append(f"scale={self.intensity_scale}")
        parts.append(f"issues={len(self.issues)}")
        return " ".join(parts)
