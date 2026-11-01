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

See ADR-0008, scene.md.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import numpy as np
from vtkmodules.util.numpy_support import numpy_to_vtk

from cranioz.domain.scene.volume_data import VolumeData

_logger = logging.getLogger(__name__)

# i18n-ready error keys (wired to tr() in Phase 8).
_ERR_FILE_NOT_FOUND = (
    "imaging.dicom.file_not_found",
    "DICOM path not found: {path}",
)
_ERR_NO_FILES = (
    "imaging.dicom.empty",
    "No DICOM files found in: {path}",
)
_ERR_INVALID_DICOM = (
    "imaging.dicom.invalid",
    "Invalid DICOM file: {path}: {reason}",
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


def load_dicom_series(path: Path) -> VolumeData:
    """Load a DICOM series from ``path`` and return a ``VolumeData``.

    ``path`` may be a folder containing ``.dcm`` files or a single
    ``.dcm`` file. The series is loaded into a ``vtkImageData``.

    Raises:
        DicomLoadError: if the path does not exist, contains no
            DICOM files, or the DICOM files are inconsistent.
    """
    # pydicom and vtk are optional dependencies (imported lazily so the
    # rest of the application can boot without them). vtkmodules is a
    # hard import at the top of the file because numpy_to_vtk is used
    # unconditionally by _build_volume_data; if vtkmodules is missing,
    # the import fails at module load, which is the correct behavior
    # (the loader cannot function without it).
    try:
        import pydicom  # noqa: PLC0415
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise DicomLoadError(_log_error(_ERR_PYDICOM_MISSING)) from exc

    try:
        import vtk  # noqa: PLC0415
    except ImportError as exc:
        raise DicomLoadError(_log_error(_ERR_VTK_MISSING)) from exc

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
    return _build_volume_data(vtk, pydicom, slices)


# ----- Internals -----------------------------------------------------


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


def _build_volume_data(vtk: Any, pydicom: Any, slices: list[Any]) -> VolumeData:
    """Build a ``vtkImageData`` from the slices and wrap it."""
    slices.sort(key=lambda s: float(getattr(s, "ImagePositionPatient", [0, 0, 0])[2]))

    first = slices[0]
    rows = int(first.Rows)
    cols = int(first.Columns)
    num_slices = len(slices)

    pixel_spacing = getattr(first, "PixelSpacing", [1.0, 1.0])
    spacing_xy = (float(pixel_spacing[0]), float(pixel_spacing[1]))
    if num_slices > 1:
        z0 = float(getattr(slices[0], "ImagePositionPatient", [0, 0, 0])[2])
        z1 = float(getattr(slices[1], "ImagePositionPatient", [0, 0, 0])[2])
        spacing_z = abs(z1 - z0) or 1.0
    else:
        spacing_z = float(getattr(first, "SliceThickness", 1.0)) or 1.0

    origin = tuple(float(v) for v in getattr(first, "ImagePositionPatient", [0, 0, 0]))

    volume_array = np.zeros((num_slices, rows, cols), dtype=np.int16)
    for index, ds in enumerate(slices):
        volume_array[index, :, :] = ds.pixel_array

    image_data = vtk.vtkImageData()
    image_data.SetDimensions(cols, rows, num_slices)
    image_data.SetSpacing(spacing_xy[0], spacing_xy[1], spacing_z)
    image_data.SetOrigin(origin[0], origin[1], origin[2])

    # numpy_to_vtk espera o array no layout Fortran (column-major),
    # compatível com a ordem de memória do VTK. deep=1 copia o buffer.
    # O call é untyped (vtkmodules não tem type hints); o type: ignore
    # é necessário para o mypy em modo strict.
    flat = volume_array.ravel(order="F")
    vtk_array = numpy_to_vtk(  # type: ignore[no-untyped-call]
        flat,
        deep=1,
        array_type=vtk.VTK_SHORT,
    )
    image_data.GetPointData().SetScalars(vtk_array)

    series_uid = str(getattr(first, "SeriesInstanceUID", ""))
    return VolumeData(
        vtk_image_data=image_data,
        series_uid=series_uid,
        spacing=(spacing_xy[0], spacing_xy[1], spacing_z),
        origin=(origin[0], origin[1], origin[2]),
        dimensions=(cols, rows, num_slices),
    )
