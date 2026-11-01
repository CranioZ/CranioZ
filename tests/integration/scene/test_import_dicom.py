"""End-to-end test: DICOM → VolumeData → DomainObjectStore → Scene."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("pydicom")
pytest.importorskip("vtk")

from tests.unit.infrastructure.imaging.test_dicom_loader import (
    _write_synthetic_dcm,
)

from cranioz.application.commands.in_memory_bus import InMemoryCommandBus
from cranioz.application.scene.commands.scene_commands import (
    ImportDicomSeriesCommand,
)
from cranioz.application.scene.handlers.scene_handlers import (
    ImportDicomSeriesHandler,
)
from cranioz.domain.scene.domain_object_store import DomainObjectStore
from cranioz.domain.scene.scene import Scene


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
    assert volume.series_uid == series_uid
