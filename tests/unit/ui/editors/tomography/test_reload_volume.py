"""Unit test: TomographyEditor.reload_volume() re-applies a new VolumeData."""

from __future__ import annotations

import pytest

pytest.importorskip("pydicom")
pytest.importorskip("vtk")
pytest.importorskip("vtkmodules.qt")

import vtk

from cranioz.application.scene.scene_query import InMemorySceneQuery
from cranioz.domain.scene.domain_object_store import DomainObjectStore
from cranioz.domain.scene.volume_data import VolumeData
from cranioz.ui.editors.editor_context import EditorContext
from cranioz.ui.editors.tomography.editor import TomographyEditor


def _make_volume_data() -> VolumeData:

    image = vtk.vtkImageData()
    image.SetDimensions(4, 4, 4)
    image.SetSpacing(1.0, 1.0, 1.0)
    image.AllocateScalars(vtk.VTK_SHORT, 1)
    return VolumeData(
        vtk_image_data=image,
        series_uid="1.2.3",
        spacing=(1.0, 1.0, 1.0),
        origin=(0.0, 0.0, 0.0),
        dimensions=(4, 4, 4),
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

    # Add a VolumeData to the store and to the Scene.
    volume = _make_volume_data()
    store.add("volume-1", volume)
    scene_query._add("volume-1", object())

    # Reload → the Views must pick up the volume.
    editor.reload_volume()

    for view in editor.views():
        if hasattr(view, "has_volume"):
            assert view.has_volume, f"{view.view_id} has no volume"
