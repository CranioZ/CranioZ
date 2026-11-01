"""Tests for the DICOM loader."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

pydicom = pytest.importorskip("pydicom")
pytest.importorskip("vtk")

from pydicom.dataset import Dataset, FileMetaDataset  # noqa: E402
from pydicom.uid import ExplicitVRLittleEndian, generate_uid  # noqa: E402

from cranioz.domain.scene.volume_data import VolumeData  # noqa: E402
from cranioz.infrastructure.imaging.dicom_loader import (  # noqa: E402
    DicomLoadError,
    load_dicom_series,
)


def _write_synthetic_dcm(  # noqa: PLR0917
    path: Path,
    series_uid: str,
    instance_number: int,
    z_position: float,
    rows: int = 4,
    cols: int = 4,
) -> None:

    file_meta = FileMetaDataset()
    file_meta.MediaStorageSOPClassUID = generate_uid()
    file_meta.MediaStorageSOPInstanceUID = generate_uid()
    file_meta.TransferSyntaxUID = ExplicitVRLittleEndian
    file_meta.ImplementationClassUID = generate_uid()

    ds = Dataset()
    ds.file_meta = file_meta
    ds.Rows = rows
    ds.Columns = cols
    ds.BitsAllocated = 16
    ds.BitsStored = 16
    ds.HighBit = 15
    ds.PixelRepresentation = 1
    ds.SamplesPerPixel = 1
    ds.PhotometricInterpretation = "MONOCHROME2"
    ds.PixelSpacing = [0.5, 0.5]
    ds.SliceThickness = 1.0
    ds.ImagePositionPatient = [0.0, 0.0, z_position]
    ds.SeriesInstanceUID = series_uid
    ds.InstanceNumber = instance_number
    ds.SOPInstanceUID = file_meta.MediaStorageSOPInstanceUID
    ds.SOPClassUID = file_meta.MediaStorageSOPClassUID

    pixel_data = np.zeros((rows, cols), dtype=np.int16) + instance_number
    ds.PixelData = pixel_data.tobytes()
    ds.save_as(str(path), enforce_file_format=True)


def test_load_dicom_series_single_folder(tmp_path: Path) -> None:
    series_uid = "1.2.3.4.5"
    for i in range(3):
        _write_synthetic_dcm(tmp_path / f"slice_{i:03d}.dcm", series_uid, i, float(i))

    volume = load_dicom_series(tmp_path)

    assert isinstance(volume, VolumeData)
    assert volume.series_uid == series_uid
    assert volume.dimensions == (4, 4, 3)
    assert volume.spacing == (0.5, 0.5, 1.0)


def test_load_dicom_series_missing_path(tmp_path: Path) -> None:
    with pytest.raises(DicomLoadError, match="not found"):
        load_dicom_series(tmp_path / "does-not-exist")


def test_load_dicom_series_empty_folder(tmp_path: Path) -> None:
    with pytest.raises(DicomLoadError, match="No DICOM"):
        load_dicom_series(tmp_path)


def test_load_dicom_series_inconsistent_series(tmp_path: Path) -> None:
    _write_synthetic_dcm(tmp_path / "a.dcm", "1.2.3", 1, 0.0)
    _write_synthetic_dcm(tmp_path / "b.dcm", "9.8.7", 2, 1.0)
    with pytest.raises(DicomLoadError, match="inconsistent"):
        load_dicom_series(tmp_path)
