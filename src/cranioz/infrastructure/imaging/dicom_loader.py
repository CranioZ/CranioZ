"""DICOM series loader — pydicom + vtkImageData.

Loads a folder (or a single ``.dcm`` file) and returns a
``VolumeData`` wrapping a ``vtkImageData``.

Scope (Passo 8a):

- Single axial series.
- ``pydicom`` for file reading.
- ``vtkImageData`` for the volume.
- No obliquity, no multi-frame, no DICOMDIR, no JPEG2000.

Limitations are documented as errors (``DicomLoadError``) when
encountered, so the caller can react. Expanding support is Phase 4+.

NOTE: This module is **temporary**. It will be replaced by the
Medical Imaging Infrastructure (`infrastructure/imaging/dicom/`)
in Sprint 3. The `# type: ignore` comments below are pragmatic
fixes to keep `mypy` green until the replacement is ready.

See ADR-0008, scene.md, medical_imaging_infrastructure.md.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import numpy as np
from vtkmodules.util.numpy_support import numpy_to_vtk

from cranioz.domain.scene.volume_data import VolumeData

_logger = logging.getLogger(__name__)

# ----- i18n-ready error keys (wired to tr() in Phase 8) --------------

_ERR_FILE_NOT_FOUND = (
    "imaging.dicom.file_not_found",
    "DICOM path not found: {path}",
)
_ERR_NO_FILES = (
    "imaging.dicom.empty",
    "No DICOM files found in: {path}",
)
_ERR_INCONSISTENT = (
    "imaging.dicom.inconsistent",
    "DICOM series is inconsistent: {reason}",
)
_ERR_VTK_MISSING = (
    "imaging.dicom.vtk_missing",
    "VTK is not installed. Install it with 'pip install vtk'.",
)
_ERR_PYDICOM_MISSING = (
    "imaging.dicom.pydicom_missing",
    "pydicom is required but not installed. Install it with 'pip install pydicom'.",
)


class DicomLoadError(Exception):
    """Raised when a DICOM series cannot be loaded."""


def _log_error(entry: tuple[str, str], **params: object) -> str:
    """Format an i18n-ready error message and log it."""
    key, source = entry
    message = source.format(**params)
    _logger.error("%s: %s", key, message)
    return message


# ----- Public API ----------------------------------------------------


def load_dicom_series(path: Path) -> VolumeData:
    """Load a DICOM series from ``path`` and return a ``VolumeData``.

    ``path`` may be a folder containing ``.dcm`` files or a single
    ``.dcm`` file. The series is loaded into a ``vtkImageData``.

    Raises:
        DicomLoadError: if the path does not exist, contains no
            DICOM files, or the DICOM files are inconsistent.
    """
    pydicom = _import_pydicom()
    vtk = _import_vtk()

    path = Path(path).expanduser()
    if not path.exists():
        raise DicomLoadError(_log_error(_ERR_FILE_NOT_FOUND, path=str(path)))

    files = _collect_dicom_files(path)
    if not files:
        raise DicomLoadError(_log_error(_ERR_NO_FILES, path=str(path)))

    slices = _read_slices(pydicom, files)
    if not slices:
        raise DicomLoadError(_log_error(_ERR_NO_FILES, path=str(path)))

    _validate_series(slices)
    return _build_volume_data(vtk, slices)


# ----- Imports (lazy, optional dependencies) -------------------------


def _import_pydicom() -> Any:
    try:
        import pydicom  # noqa: PLC0415
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise DicomLoadError(_log_error(_ERR_PYDICOM_MISSING)) from exc
    return pydicom


def _import_vtk() -> Any:
    try:
        import vtk  # noqa: PLC0415
    except ImportError as exc:
        raise DicomLoadError(_log_error(_ERR_VTK_MISSING)) from exc
    return vtk


# ----- File discovery ------------------------------------------------


def _collect_dicom_files(path: Path) -> list[Path]:
    """Return the DICOM files under ``path``.

    If ``path`` is a file, returns ``[path]``. If it is a directory,
    returns every file (any extension) — pydicom will validate them.
    """
    if path.is_file():
        return [path]
    return sorted(p for p in path.iterdir() if p.is_file())


def _read_slices(pydicom: Any, files: list[Path]) -> list[Any]:
    """Read every DICOM file that has pixel data. Skip non-DICOM files."""
    slices: list[Any] = []
    for file_path in files:
        try:
            ds = pydicom.dcmread(str(file_path), force=False)
        except Exception as exc:
            # Non-DICOM files are common in a folder (README, thumbnails).
            # Skip them silently; the caller only cares about the series.
            _logger.debug("skipping non-DICOM file %s: %s", file_path, exc)
            continue
        if not hasattr(ds, "PixelData"):
            continue
        slices.append(ds)
    return slices


# ----- Validation ----------------------------------------------------


def _validate_series(slices: list[Any]) -> None:
    """Ensure all slices belong to the same series and geometry."""
    series_uids = {str(getattr(s, "SeriesInstanceUID", "")) for s in slices}
    if len(series_uids) != 1:
        raise DicomLoadError(
            _log_error(
                _ERR_INCONSISTENT,
                reason=f"multiple SeriesInstanceUID found: {sorted(series_uids)!r}",
            )
        )

    rows = {int(getattr(s, "Rows", 0)) for s in slices}
    cols = {int(getattr(s, "Columns", 0)) for s in slices}
    if len(rows) != 1 or len(cols) != 1:
        raise DicomLoadError(
            _log_error(
                _ERR_INCONSISTENT,
                reason=(
                    f"inconsistent slice dimensions: rows={sorted(rows)!r}, cols={sorted(cols)!r}"
                ),
            )
        )


# ----- Ordering ------------------------------------------------------


def _sort_slices(slices: list[Any]) -> None:
    """Sort slices in ASCENDING Z order.

    The ``vtkImageData`` expects slices ordered from the smallest Z
    to the largest Z (the first slice defines the origin). DICOM
    series are often stored in descending order (InstanceNumber 1
    is the topmost slice), so we must sort ascending before building
    the volume.

    Strategy:
    1. If ``ImagePositionPatient`` is present and has distinct Z
       values, sort by it (ascending).
    2. Otherwise, fall back to ``InstanceNumber`` (ascending).
    """
    positions: list[float] = []
    for ds in slices:
        ipp = getattr(ds, "ImagePositionPatient", None)
        if ipp is None or len(ipp) < 3:
            positions = []
            break
        positions.append(float(ipp[2]))

    if positions and len(set(positions)) == len(positions):
        # ImagePositionPatient is present and unique: sort ascending.
        slices.sort(key=lambda ds: float(ds.ImagePositionPatient[2]))
        return

    # Fallback: use InstanceNumber (ascending).
    slices.sort(key=lambda ds: int(getattr(ds, "InstanceNumber", 0)))


# ----- Volume construction -------------------------------------------


def _build_volume_data(vtk: Any, slices: list[Any]) -> VolumeData:
    """Build a ``vtkImageData`` from the slices and wrap it."""
    _sort_slices(slices)

    first = slices[0]
    rows = int(first.Rows)
    cols = int(first.Columns)
    num_slices = len(slices)

    spacing_xy = _spacing_xy(first)
    spacing_z = _spacing_z(slices)
    origin = _origin(first)

    volume_array = _stack_slices(slices, rows, cols, num_slices)

    image_data = vtk.vtkImageData()
    image_data.SetDimensions(cols, rows, num_slices)
    image_data.SetSpacing(spacing_xy[0], spacing_xy[1], spacing_z)
    image_data.SetOrigin(origin[0], origin[1], origin[2])

    flat = volume_array.ravel(order="F")
    vtk_array = numpy_to_vtk(  # type: ignore[no-untyped-call]
        flat,
        deep=1,
        array_type=vtk.VTK_SHORT,
    )
    image_data.GetPointData().SetScalars(vtk_array)

    # --- SMOOTHING (CBCT denoising) ---
    # Apply a Gaussian filter to reduce CBCT noise.
    # This is a pragmatic fallback until the Medical Imaging
    # Infrastructure provides explicit calibration and filtering.
    smooth_filter = vtk.vtkImageGaussianSmooth()
    smooth_filter.SetInputData(image_data)
    smooth_filter.SetStandardDeviations(1.0, 1.0, 1.0)
    smooth_filter.SetRadiusFactors(1.0, 1.0, 1.0)
    smooth_filter.Update()
    image_data = smooth_filter.GetOutput()

    series_uid = str(getattr(first, "SeriesInstanceUID", ""))
    return VolumeData(
        vtk_image_data=image_data,
        series_uid=series_uid,
        spacing=(spacing_xy[0], spacing_xy[1], spacing_z),
        origin=(origin[0], origin[1], origin[2]),
        dimensions=(cols, rows, num_slices),
    )


def _spacing_xy(first: Any) -> tuple[float, float]:
    """Return (sx, sy) in millimetres from ``PixelSpacing``."""
    pixel_spacing = getattr(first, "PixelSpacing", [1.0, 1.0])
    return (float(pixel_spacing[0]), float(pixel_spacing[1]))


def _spacing_z(slices: list[Any]) -> float:
    """Return the Z spacing in millimetres.

    Uses the difference between the first two slices. Falls back to
    ``SliceThickness`` if there is only one slice or if the positions
    are missing.
    """
    if len(slices) > 1:
        z0 = _position_z(slices[0])
        z1 = _position_z(slices[1])
        spacing = abs(z1 - z0)
        if spacing > 0:
            return spacing
    thickness = float(getattr(slices[0], "SliceThickness", 1.0))
    return thickness if thickness > 0 else 1.0


def _origin(first: Any) -> tuple[float, float, float]:
    """Return the origin in millimetres from ``ImagePositionPatient``."""
    ipp = getattr(first, "ImagePositionPatient", [0.0, 0.0, 0.0])
    return (float(ipp[0]), float(ipp[1]), float(ipp[2]))


def _position_z(ds: Any) -> float:
    """Return the Z coordinate of a slice, or 0 if missing."""
    ipp = getattr(ds, "ImagePositionPatient", None)
    if ipp is not None and len(ipp) >= 3:
        return float(ipp[2])
    return 0.0


def _stack_slices(
    slices: list[Any],
    rows: int,
    cols: int,
    num_slices: int,
) -> np.ndarray:
    """Stack the pixel arrays into a (num_slices, rows, cols) int16 array.

    For CBCT data, the raw pixel values are not calibrated HU. We read
    the raw pixel data directly from the DICOM dataset (ignoring
    pydicom's automatic rescale) and normalize it to a viewable range
    (0-4095).

    This is a pragmatic approach: it guarantees the volume is viewable.
    A future piece (Medical Imaging Infrastructure) will handle proper
    CBCT-specific calibration.
    """
    # First, stack the raw data to find the global min/max.
    raw_volume = np.zeros((num_slices, rows, cols), dtype=np.float32)
    for index, ds in enumerate(slices):
        # Read the raw pixel data from PixelData, ignoring RescaleSlope/Intercept.
        # pydicom's `pixel_array` applies the rescale, which can corrupt CBCT data.
        # We use `np.frombuffer` to read the raw bytes.
        try:
            # Get the raw pixel bytes.
            raw_bytes = ds.PixelData
            # Determine the numpy dtype based on DICOM attributes.
            bits_allocated = int(getattr(ds, "BitsAllocated", 16))
            pixel_representation = int(getattr(ds, "PixelRepresentation", 0))

            if bits_allocated == 16:
                if pixel_representation == 1:  # signed
                    dtype = np.int16
                else:  # unsigned
                    dtype = np.uint16  # type: ignore[assignment]
            elif bits_allocated == 8:
                if pixel_representation == 1:
                    dtype = np.int8  # type: ignore[assignment]
                else:
                    dtype = np.uint8  # type: ignore[assignment]
            else:
                raise DicomLoadError(
                    _log_error(
                        _ERR_INCONSISTENT,
                        reason=f"unsupported BitsAllocated: {bits_allocated}",
                    )
                )

            # Read the raw bytes into a numpy array.
            raw_pixels = np.frombuffer(raw_bytes, dtype=dtype)

            # Reshape to (rows, cols).
            raw_pixels = raw_pixels.reshape(rows, cols)  # type: ignore[assignment]

            # Store in the raw volume.
            raw_volume[index, :, :] = raw_pixels.astype(np.float32)

        except Exception as exc:
            raise DicomLoadError(
                _log_error(
                    _ERR_INCONSISTENT,
                    reason=f"cannot read raw pixel data for slice {index}: {exc}",
                )
            ) from exc

    # Find the global min and max.
    raw_min = np.min(raw_volume)
    raw_max = np.max(raw_volume)

    # Avoid division by zero if the volume is flat.
    if raw_max == raw_min:
        raw_max = raw_min + 1.0

    # Normalize to [0, 1] and then scale to a viewable range.
    normalized = (raw_volume - raw_min) / (raw_max - raw_min)
    scaled = normalized * 4095.0
    volume_array = scaled.astype(np.int16)

    return volume_array
