"""Integration tests: TomographyEditor end-to-end with 2x2 grid (Block 5).

Covers:
- The 2x2 grid materializes 4 Views and both Editor-level Toolbars.
- Clicking each View activates it (editor.active_view_id).
- View-level ACTIVE_ONLY Toolbars respond to the activation.
- Editor-level ALWAYS/COLLAPSIBLE Toolbars are unaffected.
- dispose() clears Editor-level Toolbars and Views.
"""

from __future__ import annotations

from datetime import UTC, datetime

import numpy as np
import pytest
from PySide6.QtCore import QEvent, QPointF, Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QApplication, QWidget

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
from cranioz.ui.editors.mpr_viewer.view import MPRView
from cranioz.ui.editors.tomography.editor import TomographyEditor
from cranioz.ui.editors.viewport_3d.view import Viewport3DView
from cranioz.ui.theme.tokens import ThemeMode
from cranioz.ui.toolbars.base import Toolbar
from cranioz.ui.tools.builtin.log_tool import LogTool
from cranioz.ui.tools.builtin.toggle_tool import ToggleTool
from cranioz.ui.tools.registry.tool_registry import ToolRegistry


def _make_volume() -> Volume:
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


def _make_editor_with_context() -> TomographyEditor:
    store = DomainObjectStore()
    store.add("volume-1", _make_volume())
    scene_query = InMemorySceneQuery()
    scene_query._add("volume-1", object())

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
    return editor


def _click(widget: QWidget) -> None:
    """Send a MouseButtonPress through the application event pipeline.

    ``QApplication.sendEvent`` invokes the installed event filters
    (unlike ``widget.event()``, which bypasses them). This is how
    the ViewLayoutRenderer's activation filter receives the click.
    """
    event = QMouseEvent(
        QEvent.Type.MouseButtonPress,
        QPointF(5, 5),
        QPointF(5, 5),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    QApplication.sendEvent(widget, event)


@pytest.mark.qt
@pytest.mark.integration
def test_editor_materializes_four_views_and_two_editor_toolbars(qtbot) -> None:
    """The 2x2 grid has 4 Views and the Editor declares 2 Editor Toolbars."""
    editor = _make_editor_with_context()
    content = editor.content_widget()
    qtbot.addWidget(content)

    views = editor.views()
    assert len(views) == 4
    for view in views:
        assert isinstance(view, (MPRView, Viewport3DView))

    editor_toolbars = content.findChildren(Toolbar)
    editor_toolbar_ids = {tb.spec.toolbar_id for tb in editor_toolbars}
    assert "toolbar.tomography.left" in editor_toolbar_ids
    assert "toolbar.tomography.right" in editor_toolbar_ids

    editor.dispose()


@pytest.mark.qt
@pytest.mark.integration
def test_clicking_each_view_activates_it(qtbot) -> None:
    """Clicking a View's activation widget sets editor.active_view_id."""
    editor = _make_editor_with_context()
    content = editor.content_widget()
    qtbot.addWidget(content)

    for view in editor.views():
        _click(view.activation_widget())
        assert editor.active_view_id == view.view_id

    editor.dispose()


@pytest.mark.qt
@pytest.mark.integration
def test_initial_state_no_active_view(qtbot) -> None:
    """After render, no View is active."""
    editor = _make_editor_with_context()
    content = editor.content_widget()
    qtbot.addWidget(content)

    assert editor.active_view_id is None

    editor.dispose()


@pytest.mark.qt
@pytest.mark.integration
def test_activating_view_emphasizes_its_view_level_toolbars(qtbot) -> None:
    """ACTIVE_ONLY View Toolbars are emphasized only for the active View."""
    editor = _make_editor_with_context()
    content = editor.content_widget()
    qtbot.addWidget(content)

    all_toolbars = content.findChildren(Toolbar)
    by_id = {tb.spec.toolbar_id: tb for tb in all_toolbars}

    axial_tools = by_id["toolbar.view.axial.tools"]
    coronal_tools = by_id["toolbar.view.coronal.tools"]

    # Initial state: every View-level ACTIVE_ONLY Toolbar is inactive.
    assert axial_tools.is_active() is False
    assert coronal_tools.is_active() is False

    # Activate axial (views()[0] is axial by TomographyEditor.views()).
    _click(editor.views()[0].activation_widget())
    assert axial_tools.is_active() is True
    assert coronal_tools.is_active() is False

    editor.dispose()


@pytest.mark.qt
@pytest.mark.integration
def test_editor_level_always_toolbar_unaffected(qtbot) -> None:
    """Editor-level ALWAYS Toolbar is never toggled by View activation."""
    editor = _make_editor_with_context()
    content = editor.content_widget()
    qtbot.addWidget(content)

    all_toolbars = content.findChildren(Toolbar)
    by_id = {tb.spec.toolbar_id: tb for tb in all_toolbars}
    left_toolbar = by_id["toolbar.tomography.left"]

    _click(editor.views()[0].activation_widget())
    assert left_toolbar.is_active() is True

    editor.set_active_view(None)
    assert left_toolbar.is_active() is True

    editor.dispose()


@pytest.mark.qt
@pytest.mark.integration
def test_editor_level_collapsible_toolbar_unaffected(qtbot) -> None:
    """Editor-level COLLAPSIBLE Toolbar ignores View activation."""
    editor = _make_editor_with_context()
    content = editor.content_widget()
    qtbot.addWidget(content)

    all_toolbars = content.findChildren(Toolbar)
    by_id = {tb.spec.toolbar_id: tb for tb in all_toolbars}
    right_toolbar = by_id["toolbar.tomography.right"]

    _click(editor.views()[0].activation_widget())
    assert right_toolbar.is_active() is True

    editor.dispose()


@pytest.mark.qt
@pytest.mark.integration
def test_dispose_clears_editor_toolbars_and_views(qtbot) -> None:
    """dispose() clears _editor_toolbars and the content widget."""
    editor = _make_editor_with_context()
    content = editor.content_widget()
    qtbot.addWidget(content)

    assert len(editor._editor_toolbars) == 2  # noqa: SLF001

    editor.dispose()

    assert editor._content is None  # noqa: SLF001
    assert editor._editor_toolbars == []  # noqa: SLF001
    assert editor._view_layout_renderer is None  # noqa: SLF001