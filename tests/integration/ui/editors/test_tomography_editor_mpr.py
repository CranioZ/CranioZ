"""Integration test: TomographyEditor applies a VolumeData to its Views.

The TomographyEditor resolves the first ``VolumeData`` from the
``DomainObjectStore`` via ``SceneQuery`` and passes the
``vtk_image_data`` to each View. This test exercises the full
pipeline:

    DomainObjectStore + InMemorySceneQuery
        → EditorContext
        → TomographyEditor.initialize()
        → TomographyEditor.content_widget()
        → MPRView.set_volume() (x3) + Viewport3DView.set_volume()
        → has_volume == True on all four Views

VTK is a hard requirement; the test skips when VTK is missing.
"""

from __future__ import annotations

import pytest

pytest.importorskip("vtk")
pytest.importorskip("vtkmodules.qt")

import vtk  # noqa: E402

from cranioz.application.scene.scene_query import InMemorySceneQuery
from cranioz.domain.scene.domain_object_store import DomainObjectStore
from cranioz.domain.scene.volume_data import VolumeData
from cranioz.ui.editors.editor_context import EditorContext
from cranioz.ui.editors.mpr_viewer.view import MPRView
from cranioz.ui.editors.tomography.editor import TomographyEditor
from cranioz.ui.editors.viewport_3d.presets import get_preset
from cranioz.ui.editors.viewport_3d.view import Viewport3DView


def _make_volume_data() -> VolumeData:
    """Build a synthetic ``VolumeData`` (4x4x4, int16)."""

    image = vtk.vtkImageData()
    image.SetDimensions(4, 4, 4)
    image.SetSpacing(1.0, 1.0, 1.0)
    image.SetOrigin(0.0, 0.0, 0.0)
    image.AllocateScalars(vtk.VTK_SHORT, 1)

    return VolumeData(
        vtk_image_data=image,
        series_uid="1.2.3.4.5",
        spacing=(1.0, 1.0, 1.0),
        origin=(0.0, 0.0, 0.0),
        dimensions=(4, 4, 4),
    )


def _make_context(
    store: DomainObjectStore,
    scene_query: InMemorySceneQuery,
) -> EditorContext:
    return EditorContext(
        editor_id="editor.tomography",
        scene_query=scene_query,
        domain_object_store=store,
    )


@pytest.mark.qt
@pytest.mark.integration
def test_tomography_editor_applies_volume_to_all_views(qtbot) -> None:
    """The Editor resolves the first VolumeData and passes it to all 4 Views."""
    volume = _make_volume_data()

    store = DomainObjectStore()
    store.add("volume-1", volume)

    scene_query = InMemorySceneQuery()
    # _add is the test-only helper on InMemorySceneQuery (see
    # application/scene/scene_query.py). It registers the object so
    # that list_objects() returns its id.
    scene_query._add("volume-1", object())

    editor = TomographyEditor()
    editor.initialize(_make_context(store, scene_query))
    qtbot.addWidget(editor.content_widget())

    for view in editor.views():
        assert isinstance(view, (MPRView, Viewport3DView))
        assert view.has_volume, f"{view.view_id} has no volume"


@pytest.mark.qt
@pytest.mark.integration
def test_tomography_editor_handles_empty_store(qtbot) -> None:
    """When the store is empty, the Views remain without a volume."""
    store = DomainObjectStore()
    scene_query = InMemorySceneQuery()

    editor = TomographyEditor()
    editor.initialize(_make_context(store, scene_query))
    qtbot.addWidget(editor.content_widget())

    for view in editor.views():
        if isinstance(view, (MPRView, Viewport3DView)):
            assert not view.has_volume, f"{view.view_id} should be empty"


@pytest.mark.qt
@pytest.mark.integration
def test_tomography_editor_resolves_only_volume_data(qtbot) -> None:
    """Objects that are not VolumeData are ignored."""
    volume = _make_volume_data()

    store = DomainObjectStore()
    store.add("not-a-volume", object())  # ← should be skipped
    store.add("volume-1", volume)

    scene_query = InMemorySceneQuery()
    scene_query._add("not-a-volume", object())
    scene_query._add("volume-1", object())

    editor = TomographyEditor()
    editor.initialize(_make_context(store, scene_query))
    qtbot.addWidget(editor.content_widget())

    for view in editor.views():
        if isinstance(view, (MPRView, Viewport3DView)):
            assert view.has_volume, f"{view.view_id} should have a volume"


@pytest.mark.qt
@pytest.mark.integration
def test_tomography_editor_dispose_clears_volume_flag(qtbot) -> None:
    volume = _make_volume_data()
    store = DomainObjectStore()
    store.add("volume-1", volume)
    scene_query = InMemorySceneQuery()
    scene_query._add("volume-1", object())

    editor = TomographyEditor()
    editor.initialize(_make_context(store, scene_query))
    qtbot.addWidget(editor.content_widget())
    assert all(v.has_volume for v in editor.views() if isinstance(v, (MPRView, Viewport3DView)))

    editor.dispose()

    # The Views were disposed; the Editor must reset its internal flag.
    assert editor._volume_applied is False  # noqa: SLF001


@pytest.mark.qt
@pytest.mark.integration
def test_tomography_editor_viewport3d_has_volume_rendering(qtbot) -> None:
    """The Viewport3DView is created with volume rendering (not outline)."""
    volume = _make_volume_data()
    store = DomainObjectStore()
    store.add("volume-1", volume)
    scene_query = InMemorySceneQuery()
    scene_query._add("volume-1", object())

    editor = TomographyEditor()
    editor.initialize(_make_context(store, scene_query))
    qtbot.addWidget(editor.content_widget())

    viewport = editor.views()[-1]  # the 4th view is the 3D
    assert isinstance(viewport, Viewport3DView)
    assert viewport.has_volume is True
    assert viewport.volume is not None
    assert viewport.preset is get_preset("bone")
