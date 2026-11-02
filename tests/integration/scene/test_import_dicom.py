"""End-to-end test: DICOM → VolumeData → DomainObjectStore → Scene."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("pydicom")
pytest.importorskip("vtk")

from pydicom.dataset import Dataset, FileMetaDataset
from pydicom.uid import ExplicitVRLittleEndian, generate_uid

from cranioz.application.commands.in_memory_bus import InMemoryCommandBus
from cranioz.application.scene.commands.scene_commands import (
    ImportDicomSeriesCommand,
)
from cranioz.application.scene.handlers.scene_handlers import (
    ImportDicomSeriesHandler,
)
from cranioz.domain.scene.domain_object_store import DomainObjectStore
from cranioz.domain.scene.scene import Scene


def _write_synthetic_dcm(
    path: Path,
    series_uid: str,
    instance_number: int,
    z_position: float,
    *,
    rows: int = 4,
    cols: int = 4,
) -> None:
    """Write a single synthetic axial DICOM slice with full geometry."""
    file_meta = FileMetaDataset()
    file_meta.MediaStorageSOPClassUID = generate_uid()
    file_meta.MediaStorageSOPInstanceUID = generate_uid()
    file_meta.TransferSyntaxUID = ExplicitVRLittleEndian
    file_meta.ImplementationClassUID = generate_uid()

    ds = Dataset()
    ds.file_meta = file_meta
    ds.Modality = "CT"
    ds.Rows = rows
    ds.Columns = cols
    ds.BitsAllocated = 16
    ds.BitsStored = 16
    ds.HighBit = 15
    ds.PixelRepresentation = 1
    ds.SamplesPerPixel = 1
    ds.PhotometricInterpretation = "MONOCHROME2"

    # Geometry attributes (required by DicomSorter).
    ds.PixelSpacing = [0.5, 0.5]
    ds.SliceThickness = 1.0
    ds.ImagePositionPatient = [0.0, 0.0, z_position]
    ds.ImageOrientationPatient = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0]

    # Rescale attributes (used by DicomCalibrator).
    ds.RescaleSlope = 1.0
    ds.RescaleIntercept = -1024.0

    # Identifiers.
    ds.SeriesInstanceUID = series_uid
    ds.StudyInstanceUID = "1.2.3.4"
    ds.SOPInstanceUID = file_meta.MediaStorageSOPInstanceUID
    ds.SOPClassUID = file_meta.MediaStorageSOPClassUID
    ds.InstanceNumber = instance_number

    # Pixel data.
    pixel_data = np.zeros((rows, cols), dtype=np.int16) + instance_number
    ds.PixelData = pixel_data.tobytes()
    ds.save_as(str(path), enforce_file_format=True)


def test_import_dicom_series_adds_volume_to_scene(tmp_path: Path) -> None:
    series_uid = "1.2.3.4.5"
    for i in range(3):
        _write_synthetic_dcm(tmp_path / f"slice_{i:03d}.dcm", series_uid, i, float(i))

    scene = Scene(scene_id="scene.test")
    store = DomainObjectStore()
    handler = ImportDicomSeriesHandler(scene=scene, object_store=store)
    bus = InMemoryCommandBus()
    bus.register(ImportDicomSeriesCommand, handler)

    command = ImportDicomSeriesCommand.new(
        scene_id=scene.scene_id,
        path=str(tmp_path),
        object_id="volume-1",
    )
    bus.dispatch(command)

    assert scene.contains("volume-1")
    assert scene.list_objects() == ("volume-1",)
    assert store.contains("volume-1")
    volume = store.get("volume-1")
    assert volume.metadata.series_instance_uid == series_uid
