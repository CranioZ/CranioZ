"""Integration test: TomographyEditor applies a Volume to its Views.

The TomographyEditor resolves the first ``Volume`` from the
``DomainObjectStore`` via ``SceneQuery`` and passes it to each View.
Each View converts the ``Volume`` to ``vtkImageData`` via
``VtkImageAdapter`` internally. This test exercises the full pipeline:

    DomainObjectStore + InMemorySceneQuery
        -> EditorContext
        -> TomographyEditor.initialize()
        -> TomographyEditor.content_widget()
        -> MPRView.set_volume() (x3) + Viewport3DView.set_volume()
        -> has_volume == True on all four Views

VTK is a hard requirement; the test skips when VTK is missing.
"""

from __future__ import annotations

from datetime import UTC, datetime

import numpy as np
import pytest

pytest.importorskip("vtk")
pytest.importorskip("vtkmodules.qt")

from tests.conftest import make_icon_provider, make_theme_service

from cranioz.application.scene.scene_query import InMemorySceneQuery
from cranioz.domain.imaging.image_metadata import (
    ImageMetadata,
    ImageModality,
)
from cranioz.domain.imaging.volume import IntensityScale, Volume
from cranioz.domain.imaging.volume_geometry import VolumeGeometry
from cranioz.domain.imaging.volume_provenance import VolumeProvenance
from cranioz.domain.scene.domain_object_store import DomainObjectStore
from cranioz.ui.editors.editor_context import EditorContext
from cranioz.ui.editors.mpr_viewer.view import MPRView
from cranioz.ui.editors.tomography.editor import TomographyEditor
from cranioz.ui.editors.viewport_3d.presets import get_preset
from cranioz.ui.editors.viewport_3d.view import Viewport3DView
from cranioz.ui.theme.tokens import ThemeMode
from cranioz.ui.tools.builtin.log_tool import LogTool
from cranioz.ui.tools.builtin.toggle_tool import ToggleTool
from cranioz.ui.tools.registry.tool_registry import ToolRegistry


def _make_volume() -> Volume:
    """Build a synthetic ``Volume`` (4x4x4, int16).

    The volume is intentionally non-HU (``IntensityScale.UNKNOWN``)
    so the Viewport3DView exercises the ``cbct`` branch.
    """
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


def _make_hu_volume() -> Volume:
    """Build a synthetic HU-calibrated ``Volume`` (4x4x4, int16).

    Values are chosen inside a plausible HU range (air = -1000,
    bone = 1500) so the Viewport3DView exercises the ``bone`` branch.
    """
    data = np.full((4, 4, 4), -1000, dtype=np.int16)
    data[1:3, 1:3, 1:3] = 1500
    geometry = VolumeGeometry.identity(
        dimensions=(4, 4, 4),
        spacing=(1.0, 1.0, 1.0),
        origin=(0.0, 0.0, 0.0),
    )
    return Volume(
        data=data,
        geometry=geometry,
        metadata=ImageMetadata(modality=ImageModality.CT),
        intensity_scale=IntensityScale.HU,
        provenance=VolumeProvenance(
            import_timestamp=datetime(2026, 1, 1, 12, 0, tzinfo=UTC),
        ),
        volume_id="volume-test-hu",
    )


def _make_context(
    store: DomainObjectStore,
    scene_query: InMemorySceneQuery,
) -> EditorContext:
    """Build an EditorContext complete enough for the TomographyEditor.

    Per ADR-0013 §2.6, the Editor needs tool_registry, theme_service
    and icon_provider to materialize its Views' Toolbars (via the
    ViewLayoutRenderer). The store and scene_query provide the Volume
    that the Editor resolves for its Views.
    """
    registry = ToolRegistry()
    registry.register("tool.log", LogTool)
    registry.register("tool.toggle", ToggleTool)

    theme_service = make_theme_service(ThemeMode.DARK)
    icon_provider = make_icon_provider(theme_service)

    return EditorContext(
        editor_id="editor.tomography",
        scene_query=scene_query,
        domain_object_store=store,
        tool_registry=registry,
        theme_service=theme_service,
        icon_provider=icon_provider,
    )


@pytest.mark.qt
@pytest.mark.integration
def test_tomography_editor_applies_volume_to_all_views(qtbot) -> None:
    """The Editor resolves the first Volume and passes it to all 4 Views."""
    volume = _make_volume()

    store = DomainObjectStore()
    store.add("volume-1", volume)

    scene_query = InMemorySceneQuery()
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
def test_tomography_editor_resolves_only_volume(qtbot) -> None:
    """Objects that are not Volume are ignored."""
    volume = _make_volume()

    store = DomainObjectStore()
    store.add("not-a-volume", object())  # <- should be skipped
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
    volume = _make_volume()
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
    """The Viewport3DView starts with the cbct preset for a non-HU volume."""
    volume = _make_volume()  # IntensityScale.UNKNOWN
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
    assert viewport.volume_actor is not None
    # Non-HU volume -> cbct preset, by design.
    assert viewport.preset is get_preset("cbct")


@pytest.mark.qt
@pytest.mark.integration
def test_tomography_editor_viewport3d_uses_bone_for_hu_volume(qtbot) -> None:
    """The Viewport3DView starts with the bone preset for an HU volume."""
    volume = _make_hu_volume()  # IntensityScale.HU
    store = DomainObjectStore()
    store.add("volume-test-hu", volume)
    scene_query = InMemorySceneQuery()
    scene_query._add("volume-test-hu", object())

    editor = TomographyEditor()
    editor.initialize(_make_context(store, scene_query))
    qtbot.addWidget(editor.content_widget())

    viewport = editor.views()[-1]
    assert isinstance(viewport, Viewport3DView)
    assert viewport.preset is get_preset("bone")
