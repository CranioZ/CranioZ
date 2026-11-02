"""DicomSeriesReader — assemble a Volume from a DICOM series.

This is the orchestrator. It:

1. Discovers DICOM files in a folder.
2. Reads them with pydicom.
3. Validates the series.
4. Sorts slices and computes the direction matrix.
5. Applies intensity calibration and classifies the scale.
6. Builds a `Volume` with `VolumeGeometry`, `ImageMetadata`, and
   `VolumeProvenance`.
7. Produces an `ImportReport`.

It does NOT depend on VTK. Conversion to `vtkImageData` happens
later, in `infrastructure/visualization/vtk_image_adapter.py`.

See Medical Imaging Infrastructure §5.
"""

from __future__ import annotations

import hashlib
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np

from cranioz.application.imaging.import_report import (
    ImportIssue,
    ImportReport,
    IssueSeverity,
)
from cranioz.domain.imaging.image_metadata import (
    ImageMetadata,
    ImageModality,
)
from cranioz.domain.imaging.volume import IntensityScale, Volume
from cranioz.domain.imaging.volume_geometry import VolumeGeometry
from cranioz.domain.imaging.volume_provenance import VolumeProvenance
from cranioz.infrastructure.imaging.dicom.dicom_calibrator import (
    DicomCalibrator,
)
from cranioz.infrastructure.imaging.dicom.dicom_sorter import (
    DicomSorter,
    DicomSorterError,
)
from cranioz.infrastructure.imaging.dicom.dicom_validator import (
    DicomValidator,
    ValidationResult,
)

_logger = logging.getLogger(__name__)


class DicomSeriesReaderError(Exception):
    """Raised when a DICOM series cannot be assembled."""


class DicomSeriesReader:
    """Assemble a Volume from a DICOM series."""

    def __init__(self) -> None:
        self._sorter = DicomSorter()
        self._calibrator = DicomCalibrator()
        self._validator = DicomValidator()

    def read(self, path: Path) -> tuple[Volume, ImportReport]:
        """Read a DICOM series and return (volume, report).

        Args:
            path: folder containing DICOM files.

        Returns:
            (volume, report):
                - volume: assembled Volume with geometry, metadata,
                  provenance, and intensity scale.
                - report: structured import report.

        Raises:
            DicomSeriesReaderError: if the series cannot be assembled.
        """
        pydicom = self._import_pydicom()

        path = Path(path).expanduser()
        if not path.is_dir():
            raise DicomSeriesReaderError(f"path is not a directory: {path}")

        files = self._collect_files(path)
        if not files:
            raise DicomSeriesReaderError(f"no files found in {path}")

        slices = self._read_slices(pydicom, files)
        if not slices:
            raise DicomSeriesReaderError(f"no DICOM image instances found in {path}")

        # Validate.
        validation = self._validator.validate(slices)

        # Sort and compute direction.
        try:
            sorted_slices, direction_ras = self._sorter.sort(slices)
        except DicomSorterError as exc:
            # Add the error to the validation and raise.
            validation = ValidationResult(
                issues=(
                    *validation.issues,
                    ImportIssue(
                        severity=IssueSeverity.ERROR,
                        code="sort_failed",
                        message=str(exc),
                    ),
                )
            )
            report = self._build_failed_report(files, slices, validation)
            raise DicomSeriesReaderError(f"cannot sort slices: {exc}") from exc

        if validation.has_errors:
            report = self._build_failed_report(files, slices, validation)
            raise DicomSeriesReaderError(f"validation failed: {self._summarize_errors(validation)}")

        # Stack raw voxels.
        raw_volume = self._stack_raw_voxels(sorted_slices)

        # Calibrate.
        calibrated, intensity_scale = self._calibrator.calibrate(raw_volume, sorted_slices)

        # Build geometry, metadata, provenance.
        geometry = self._build_geometry(sorted_slices, direction_ras)
        metadata = self._build_metadata(sorted_slices)
        provenance = self._build_provenance(path, sorted_slices, validation, intensity_scale)

        # Build volume_id (deterministic from SeriesInstanceUID).
        series_uid = str(getattr(sorted_slices[0], "SeriesInstanceUID", ""))
        volume_id = f"volume-{hashlib.sha256(series_uid.encode()).hexdigest()[:12]}"

        volume = Volume(
            data=calibrated.astype(np.int16),
            geometry=geometry,
            metadata=metadata,
            intensity_scale=intensity_scale,
            provenance=provenance,
            volume_id=volume_id,
        )

        report = self._build_success_report(files, slices, validation, volume)

        return volume, report

    # ----- File discovery and reading --------------------------------

    @staticmethod
    def _collect_files(path: Path) -> list[Path]:
        return sorted(p for p in path.iterdir() if p.is_file())

    def _read_slices(self, pydicom: Any, files: list[Path]) -> list[Any]:
        slices: list[Any] = []
        for file_path in files:
            try:
                ds = pydicom.dcmread(str(file_path), force=False)
            except Exception as exc:
                _logger.debug("skipping non-DICOM file %s: %s", file_path, exc)
                continue
            if not hasattr(ds, "PixelData"):
                continue
            slices.append(ds)
        return slices

    @staticmethod
    def _import_pydicom() -> Any:
        try:
            import pydicom  # noqa: PLC0415
        except ImportError as exc:
            raise DicomSeriesReaderError("pydicom is required but not installed") from exc
        return pydicom

    # ----- Volume construction --------------------------------------

    @staticmethod
    def _stack_raw_voxels(slices: list[Any]) -> np.ndarray:
        """Stack raw pixel data into an array of shape (nz, ny, nx)."""
        first = slices[0]
        rows = int(first.Rows)
        cols = int(first.Columns)
        nz = len(slices)

        dtype = DicomSeriesReader._dtype_for(first)
        out = np.zeros((nz, rows, cols), dtype=dtype)

        for index, ds in enumerate(slices):
            raw = ds.PixelData
            arr = np.frombuffer(raw, dtype=dtype)
            if arr.size != rows * cols:
                raise DicomSeriesReaderError(
                    f"slice {index} has {arr.size} pixels; expected {rows * cols}"
                )
            out[index] = arr.reshape(rows, cols)

        return out

    @staticmethod
    def _dtype_for(ds: Any) -> type[np.generic]:
        bits = int(getattr(ds, "BitsAllocated", 16))
        signed = int(getattr(ds, "PixelRepresentation", 0)) == 1
        if bits == 8:
            return np.int8 if signed else np.uint8
        if bits == 16:
            return np.int16 if signed else np.uint16
        raise DicomSeriesReaderError(f"unsupported BitsAllocated={bits}")

    @staticmethod
    def _build_geometry(
        slices: list[Any],
        direction_ras: np.ndarray,
    ) -> VolumeGeometry:
        first = slices[0]
        last = slices[-1]

        rows = int(first.Rows)
        cols = int(first.Columns)
        nz = len(slices)

        pixel_spacing = getattr(first, "PixelSpacing", [1.0, 1.0])
        sx = float(pixel_spacing[0])
        sy = float(pixel_spacing[1])

        # Slice spacing = distance between first and last / (nz - 1).
        p0 = np.array([float(v) for v in first.ImagePositionPatient])
        p1 = np.array([float(v) for v in last.ImagePositionPatient])
        if nz > 1:
            sz = float(np.linalg.norm(p1 - p0) / (nz - 1))
        else:
            sz = float(getattr(first, "SliceThickness", 1.0))

        # Origin in RAS (convert from LPS by flipping first two axes).
        origin_lps = p0
        origin_ras = np.array([-origin_lps[0], -origin_lps[1], origin_lps[2]])

        d = direction_ras
        direction = (
            (float(d[0, 0]), float(d[0, 1]), float(d[0, 2])),
            (float(d[1, 0]), float(d[1, 1]), float(d[1, 2])),
            (float(d[2, 0]), float(d[2, 1]), float(d[2, 2])),
        )

        return VolumeGeometry(
            dimensions=(cols, rows, nz),
            origin=(float(origin_ras[0]), float(origin_ras[1]), float(origin_ras[2])),
            spacing=(sx, sy, sz),
            direction=direction,
        )

    @staticmethod
    def _build_metadata(slices: list[Any]) -> ImageMetadata:
        first = slices[0]
        modality = DicomSeriesReader._read_modality(first)
        return ImageMetadata(
            modality=modality,
            study_instance_uid=str(getattr(first, "StudyInstanceUID", "")),
            series_instance_uid=str(getattr(first, "SeriesInstanceUID", "")),
            study_description=getattr(first, "StudyDescription", None),
            series_description=getattr(first, "SeriesDescription", None),
            patient_id=getattr(first, "PatientID", None),
            patient_name=getattr(first, "PatientName", None),
            patient_birth_date=getattr(first, "PatientBirthDate", None),
            patient_sex=getattr(first, "PatientSex", None),
            manufacturer=getattr(first, "Manufacturer", None),
            manufacturer_model_name=getattr(first, "ManufacturerModelName", None),
            kvp=DicomSeriesReader._read_float_attr(first, "KVP"),
            slice_thickness=DicomSeriesReader._read_float_attr(first, "SliceThickness"),
            rescale_slope=DicomSeriesReader._read_float_attr(first, "RescaleSlope"),
            rescale_intercept=DicomSeriesReader._read_float_attr(first, "RescaleIntercept"),
            bits_allocated=int(getattr(first, "BitsAllocated", 0)) or None,
            bits_stored=int(getattr(first, "BitsStored", 0)) or None,
            pixel_representation=int(getattr(first, "PixelRepresentation", 0)) or None,
            photometric_interpretation=getattr(first, "PhotometricInterpretation", None),
        )

    @staticmethod
    def _read_modality(ds: Any) -> ImageModality:
        modality = getattr(ds, "Modality", None)
        if modality == "CT":
            return ImageModality.CT
        if modality in ("CBCT", "CT_CBCT"):
            return ImageModality.CBCT
        if modality in ("MR", "MRI"):
            return ImageModality.MRI
        return ImageModality.UNKNOWN

    @staticmethod
    def _read_float_attr(ds: Any, name: str) -> float | None:
        value = getattr(ds, name, None)
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _build_provenance(
        path: Path,
        slices: list[Any],
        validation: ValidationResult,
        intensity_scale: IntensityScale,
    ) -> VolumeProvenance:
        validation_outcome = tuple(
            (issue.severity.value, issue.code) for issue in validation.issues
        )

        return VolumeProvenance(
            import_timestamp=datetime.now(tz=UTC),
            source_format="DICOM",
            source_reference=str(path),
            validation_outcome=validation_outcome,
        )

    # ----- Reports --------------------------------------------------

    def _build_success_report(
        self,
        files: list[Path],
        slices: list[Any],
        validation: ValidationResult,
        volume: Volume,
    ) -> ImportReport:
        return ImportReport(
            success=True,
            files_detected=len(files),
            instances_loaded=len(slices),
            instances_skipped=len(files) - len(slices),
            modality=volume.metadata.modality.value.upper(),
            transfer_syntax=None,
            dimensions=volume.dimensions,
            spacing=volume.spacing,
            intensity_scale=volume.intensity_scale.value,
            issues=validation.issues,
            assumptions=(),
        )

    def _build_failed_report(
        self,
        files: list[Path],
        slices: list[Any],
        validation: ValidationResult,
    ) -> ImportReport:
        return ImportReport(
            success=False,
            files_detected=len(files),
            instances_loaded=0,
            instances_skipped=len(files) - len(slices),
            modality="UNKNOWN",
            transfer_syntax=None,
            dimensions=None,
            spacing=None,
            intensity_scale=None,
            issues=validation.issues,
            assumptions=(),
        )

    @staticmethod
    def _summarize_errors(validation: ValidationResult) -> str:
        return "; ".join(i.message for i in validation.errors())
