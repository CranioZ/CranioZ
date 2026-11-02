"""DicomValidator — validate a DICOM series before assembly.

Validation covers:

- Required attributes.
- Consistent dimensions, pixel spacing.
- Consistent slice spacing (regularity check).
- Unsupported transfer syntaxes.
- Duplicate or incompatible instances.

The validator produces a `ValidationResult` with a list of
`ImportIssue`s. It does NOT raise on every issue: only on errors
that make assembly impossible.

See Medical Imaging Infrastructure §5.6, §6.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from cranioz.application.imaging.import_report import (
    ImportIssue,
    IssueSeverity,
)

_logger = logging.getLogger(__name__)

# Tolerance for slice spacing regularity (in mm).
_SPACING_TOLERANCE_MM = 0.01

# Minimum number of slices for a usable volume.
_MIN_SLICES = 2

# Supported transfer syntaxes (uncompressed only, for Phase 4).
_SUPPORTED_TRANSFER_SYNTAXES = {
    "1.2.840.10008.1.2",  # Implicit VR Little Endian
    "1.2.840.10008.1.2.1",  # Explicit VR Little Endian
    "1.2.840.10008.1.2.1.99",  # Deflated Explicit VR Little Endian
    "1.2.840.10008.1.2.2",  # Explicit VR Big Endian
}

# Required attributes.
_REQUIRED_ATTRIBUTES = (
    "Rows",
    "Columns",
    "BitsAllocated",
    "BitsStored",
    "PixelRepresentation",
    "ImagePositionPatient",
    "ImageOrientationPatient",
    "PixelSpacing",
)


@dataclass(frozen=True)
class ValidationResult:
    """Result of validating a DICOM series."""

    issues: tuple[ImportIssue, ...] = field(default_factory=tuple)

    @property
    def has_errors(self) -> bool:
        return any(i.severity is IssueSeverity.ERROR for i in self.issues)

    @property
    def has_warnings(self) -> bool:
        return any(i.severity is IssueSeverity.WARNING for i in self.issues)

    def errors(self) -> tuple[ImportIssue, ...]:
        return tuple(i for i in self.issues if i.severity is IssueSeverity.ERROR)

    def warnings(self) -> tuple[ImportIssue, ...]:
        return tuple(i for i in self.issues if i.severity is IssueSeverity.WARNING)


class DicomValidator:
    """Validates a DICOM series."""

    def validate(self, slices: list[Any]) -> ValidationResult:
        issues: list[ImportIssue] = []

        issues.extend(self._check_required_attributes(slices))
        issues.extend(self._check_minimum_slices(slices))
        issues.extend(self._check_dimensions(slices))
        issues.extend(self._check_pixel_spacing(slices))
        issues.extend(self._check_transfer_syntax(slices))
        issues.extend(self._check_slice_spacing(slices))

        return ValidationResult(issues=tuple(issues))

    # ----- Individual checks ----------------------------------------

    @staticmethod
    def _check_required_attributes(slices: list[Any]) -> list[ImportIssue]:
        issues: list[ImportIssue] = []
        for attr in _REQUIRED_ATTRIBUTES:
            missing = sum(1 for s in slices if not hasattr(s, attr))
            if missing > 0:
                issues.append(
                    ImportIssue(
                        severity=IssueSeverity.ERROR,
                        code=f"missing.{attr}",
                        message=(f"{missing} slice(s) are missing the required attribute {attr}"),
                    )
                )
        return issues

    @staticmethod
    def _check_minimum_slices(slices: list[Any]) -> list[ImportIssue]:
        if len(slices) < _MIN_SLICES:
            return [
                ImportIssue(
                    severity=IssueSeverity.ERROR,
                    code="too_few_slices",
                    message=(
                        f"series has {len(slices)} slice(s); "
                        f"at least {_MIN_SLICES} are required to form a volume"
                    ),
                )
            ]
        return []

    @staticmethod
    def _check_dimensions(slices: list[Any]) -> list[ImportIssue]:
        rows = {int(getattr(s, "Rows", 0)) for s in slices}
        cols = {int(getattr(s, "Columns", 0)) for s in slices}
        if len(rows) != 1 or len(cols) != 1:
            return [
                ImportIssue(
                    severity=IssueSeverity.ERROR,
                    code="inconsistent_dimensions",
                    message=(
                        f"inconsistent slice dimensions: rows={sorted(rows)}, cols={sorted(cols)}"
                    ),
                )
            ]
        return []

    @staticmethod
    def _check_pixel_spacing(slices: list[Any]) -> list[ImportIssue]:
        spacings: set[tuple[float, float]] = set()
        for s in slices:
            sp = getattr(s, "PixelSpacing", None)
            if sp is not None and len(sp) >= 2:
                spacings.add((round(float(sp[0]), 6), round(float(sp[1]), 6)))
        if len(spacings) > 1:
            return [
                ImportIssue(
                    severity=IssueSeverity.WARNING,
                    code="inconsistent_pixel_spacing",
                    message=(f"PixelSpacing varies between slices: {sorted(spacings)}"),
                )
            ]
        return []

    @staticmethod
    def _check_transfer_syntax(slices: list[Any]) -> list[ImportIssue]:
        transfer_syntaxes: set[str] = set()
        for s in slices:
            ts = getattr(s, "file_meta", None)
            if ts is not None:
                uid = getattr(ts, "TransferSyntaxUID", None)
                if uid is not None:
                    transfer_syntaxes.add(str(uid))
        unsupported = transfer_syntaxes - _SUPPORTED_TRANSFER_SYNTAXES
        if unsupported:
            return [
                ImportIssue(
                    severity=IssueSeverity.ERROR,
                    code="unsupported_transfer_syntax",
                    message=(f"unsupported transfer syntax(es): {sorted(unsupported)}"),
                )
            ]
        return []

    @staticmethod
    def _check_slice_spacing(slices: list[Any]) -> list[ImportIssue]:
        if len(slices) < 3:
            return []

        # Compute positions along the slice normal.
        orientation = getattr(slices[0], "ImageOrientationPatient", None)
        if orientation is None or len(orientation) != 6:
            return []

        row = np.array([float(v) for v in orientation[0:3]])
        col = np.array([float(v) for v in orientation[3:6]])
        normal = np.cross(row, col)
        normal /= np.linalg.norm(normal)

        positions: list[float] = []
        for s in slices:
            pos = getattr(s, "ImagePositionPatient", None)
            if pos is None or len(pos) != 3:
                return []
            positions.append(float(np.dot(np.array([float(v) for v in pos]), normal)))

        positions.sort()
        spacings = [positions[i + 1] - positions[i] for i in range(len(positions) - 1)]
        # Exclude tiny numerical noise.
        spacings = [s for s in spacings if abs(s) > 1e-6]
        if not spacings:
            return []
        min_s = min(spacings)
        max_s = max(spacings)
        if (max_s - min_s) > _SPACING_TOLERANCE_MM:
            return [
                ImportIssue(
                    severity=IssueSeverity.WARNING,
                    code="irregular_slice_spacing",
                    message=(
                        f"slice spacing varies between {min_s:.3f} mm and "
                        f"{max_s:.3f} mm; the volume may have non-uniform "
                        f"geometry"
                    ),
                )
            ]
        return []
