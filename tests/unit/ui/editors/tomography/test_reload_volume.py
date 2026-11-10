"""Unit test: TomographyEditor.reload_volume() re-applies a new Volume."""

from __future__ import annotations

from datetime import UTC, datetime

import numpy as np
import pytest

pytest.importorskip("pydicom")
pytest.importorskip("vtk")
pytest.importorskip("vtkmodules.qt")

from tests.conftest import make_icon_provider, make_theme_service

from cranioz.application.scene.scene_query import InMemorySceneQuery
from cranioz.domain.imaging.image_metadata import ImageMetadata
from cranioz.domain.imaging.volume import IntensityScale, Volume
from cranioz.domain.imaging.volume_geometry import VolumeGeometry
from cranioz.domain.imaging.volume_provenance import VolumeProvenance
from cranioz.domain.scene.domain_object_store import DomainObjectStore
from cranioz.ui.editors.editor_context import EditorContext
from cranioz.ui.editors.tomography.editor import TomographyEditor
from cranioz.ui.theme.tokens import ThemeMode
from cranioz.ui.tools.builtin.log_tool import LogTool
from cranioz.ui.tools.builtin.toggle_tool import ToggleTool
from cranioz.ui.tools.registry.tool_registry import ToolRegistry


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

    # ADR-0013 §2.6: the TomographyEditor needs tool_registry,
    # theme_service and icon_provider to materialize its Views'
    # Toolbars (via the ViewLayoutRenderer).
    registry = ToolRegistry()
    registry.register("tool.log", LogTool)
    registry.register("tool.toggle", ToggleTool)
    theme_service = make_theme_service(ThemeMode.DARK)
    icon_provider = make_icon_provider(theme_service)

    editor = TomographyEditor()
    editor.initialize(
        EditorContext(
            editor_id="editor.tomography",
            scene_query=scene_query,
            domain_object_store=store,
            tool_registry=registry,
            theme_service=theme_service,
            icon_provider=icon_provider,
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
