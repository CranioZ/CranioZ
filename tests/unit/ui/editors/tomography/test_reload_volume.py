"""Unit test: TomographyEditor.reload_volume() re-applies a new Volume."""

from __future__ import annotations

from datetime import UTC, datetime

import numpy as np
import pytest

pytest.importorskip("pydicom")
pytest.importorskip("vtk")
pytest.importorskip("vtkmodules.qt")

from cranioz.application.scene.scene_query import InMemorySceneQuery
from cranioz.domain.imaging.image_metadata import ImageMetadata
from cranioz.domain.imaging.volume import IntensityScale, Volume
from cranioz.domain.imaging.volume_geometry import VolumeGeometry
from cranioz.domain.imaging.volume_provenance import VolumeProvenance
from cranioz.domain.scene.domain_object_store import DomainObjectStore
from cranioz.ui.editors.editor_context import EditorContext
from cranioz.ui.editors.tomography.editor import TomographyEditor


def _make_volume() -> Volume:
    """Build a tiny synthetic ``Volume`` (4x4x4, int16)."""
    data = np.zeros((4, 4, 4), dtype=np.int16)
    geometry = VolumeGeometry.identity(
        dimensions=(4, 4, 4),
        spacing=(1.0, 1.0, 1.0),
        origin=(0.0, 0.0, 0.0),
    )
    return Volume(
        data=data,
        geometry=geometry,
        metadata=ImageMetadata(),
        intensity_scale=IntensityScale.UNKNOWN,
        provenance=VolumeProvenance(
            import_timestamp=datetime(2026, 1, 1, 12, 0, tzinfo=UTC),
        ),
        volume_id="volume-test",
    )


@pytest.mark.qt
def test_reload_volume_picks_up_new_volume(qtbot) -> None:
    store = DomainObjectStore()
    scene_query = InMemorySceneQuery()

    editor = TomographyEditor()
    editor.initialize(
        EditorContext(
            editor_id="editor.tomography",
            scene_query=scene_query,
            domain_object_store=store,
        )
    )
    qtbot.addWidget(editor.content_widget())

    # Initially, no volume in the store → no View has a volume.
    for view in editor.views():
        if hasattr(view, "has_volume"):
            assert not view.has_volume

    # Add a Volume to the store and to the Scene.
    volume = _make_volume()
    store.add("volume-1", volume)
    scene_query._add("volume-1", object())

    # Reload → the Views must pick up the volume.
    editor.reload_volume()

    for view in editor.views():
        if hasattr(view, "has_volume"):
            assert view.has_volume, f"{view.view_id} has no volume"
