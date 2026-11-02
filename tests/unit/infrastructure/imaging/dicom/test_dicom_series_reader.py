"""Tests for DicomSeriesReader.

These tests require pydicom. They create a folder with synthetic
DICOM files that include the required geometry attributes
(ImagePositionPatient, ImageOrientationPatient, PixelSpacing) so
the reader can assemble a valid Volume.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("pydicom")

from pydicom.dataset import Dataset, FileMetaDataset  # noqa: E402
from pydicom.uid import (  # noqa: E402
    ExplicitVRLittleEndian,
    generate_uid,
)

from cranioz.domain.imaging.volume import IntensityScale  # noqa: E402
from cranioz.infrastructure.imaging.dicom.dicom_series_reader import (  # noqa: E402
    DicomSeriesReader,
    DicomSeriesReaderError,
)


def _write_axial_dcm(
    path: Path,
    series_uid: str,
    instance_number: int,
    z_position: float,
    *,
    rows: int = 4,
    cols: int = 4,
    modality: str = "CT",
    rescale_slope: float = 1.0,
    rescale_intercept: float = -1024.0,
) -> None:
    """Write a single synthetic axial DICOM slice with full geometry."""
    file_meta = FileMetaDataset()
    file_meta.MediaStorageSOPClassUID = generate_uid()
    file_meta.MediaStorageSOPInstanceUID = generate_uid()
    file_meta.TransferSyntaxUID = ExplicitVRLittleEndian
    file_meta.ImplementationClassUID = generate_uid()

    ds = Dataset()
    ds.file_meta = file_meta
    ds.Modality = modality
    ds.Rows = rows
    ds.Columns = cols
    ds.BitsAllocated = 16
    ds.BitsStored = 16
    ds.HighBit = 15
    ds.PixelRepresentation = 1
    ds.SamplesPerPixel = 1
    ds.PhotometricInterpretation = "MONOCHROME2"

    # Geometry attributes required by the DicomSorter.
    ds.PixelSpacing = [0.5, 0.5]
    ds.SliceThickness = 0.5
    ds.ImagePositionPatient = [0.0, 0.0, z_position]
    ds.ImageOrientationPatient = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0]

    # Rescale attributes for the DicomCalibrator.
    ds.RescaleSlope = rescale_slope
    ds.RescaleIntercept = rescale_intercept

    # Identifiers.
    ds.SeriesInstanceUID = series_uid
    ds.StudyInstanceUID = "1.2.3.4"
    ds.SOPInstanceUID = file_meta.MediaStorageSOPInstanceUID
    ds.SOPClassUID = file_meta.MediaStorageSOPClassUID
    ds.InstanceNumber = instance_number

    # Pixel data.
    pixel_data = np.full((rows, cols), instance_number, dtype=np.int16)
    ds.PixelData = pixel_data.tobytes()
    ds.save_as(str(path), enforce_file_format=True)


@pytest.fixture
def axial_series(tmp_path: Path) -> Path:
    series_uid = "1.2.3.4.5"
    for i in range(4):
        _write_axial_dcm(
            tmp_path / f"slice_{i:03d}.dcm",
            series_uid,
            i,
            float(i) * 0.5,
        )
    return tmp_path


# ----- Successful assembly -----------------------------------------


def test_reader_returns_volume_and_report(axial_series: Path) -> None:
    reader = DicomSeriesReader()
    volume, report = reader.read(axial_series)
    assert volume is not None
    assert report.success is True
    assert report.instances_loaded == 4
    assert report.files_detected == 4
    assert volume.dimensions == (4, 4, 4)


def test_reader_sets_intensity_scale(axial_series: Path) -> None:
    reader = DicomSeriesReader()
    volume, _ = reader.read(axial_series)
    assert volume.intensity_scale is IntensityScale.HU


def test_reader_infers_correct_spacing(axial_series: Path) -> None:
    reader = DicomSeriesReader()
    volume, _ = reader.read(axial_series)
    sx, sy, sz = volume.spacing
    assert sx == pytest.approx(0.5, abs=1e-6)
    assert sy == pytest.approx(0.5, abs=1e-6)
    assert sz == pytest.approx(0.5, abs=1e-6)


def test_reader_infers_correct_origin(axial_series: Path) -> None:
    reader = DicomSeriesReader()
    volume, _ = reader.read(axial_series)
    assert volume.origin == (0.0, 0.0, 0.0)


def test_reader_volume_data_is_hu(axial_series: Path) -> None:
    reader = DicomSeriesReader()
    volume, _ = reader.read(axial_series)
    assert float(volume.data.min()) == pytest.approx(-1024.0, abs=1.0)
    assert float(volume.data.max()) == pytest.approx(-1021.0, abs=1.0)


# ----- Error handling ----------------------------------------------


def test_reader_rejects_missing_folder(tmp_path: Path) -> None:
    reader = DicomSeriesReader()
    with pytest.raises(DicomSeriesReaderError, match="not a directory"):
        reader.read(tmp_path / "does-not-exist")


def test_reader_rejects_empty_folder(tmp_path: Path) -> None:
    reader = DicomSeriesReader()
    with pytest.raises(DicomSeriesReaderError, match="no files"):
        reader.read(tmp_path)
