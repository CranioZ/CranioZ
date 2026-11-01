"""Tests for Viewport3DView (volume rendering)."""

from __future__ import annotations

import pytest

pytest.importorskip("vtk")
pytest.importorskip("vtkmodules.qt")

import vtk  # noqa: E402

from cranioz.ui.editors.viewport_3d.presets import (  # noqa: E402
    get_preset,
)
from cranioz.ui.editors.viewport_3d.view import Viewport3DView  # noqa: E402


def _make_image() -> object:
    """Build a tiny synthetic ``vtkImageData`` (4x4x4, int16)."""
    image = vtk.vtkImageData()
    image.SetDimensions(4, 4, 4)
    image.SetSpacing(1.0, 1.0, 1.0)
    image.SetOrigin(0.0, 0.0, 0.0)
    image.AllocateScalars(vtk.VTK_SHORT, 1)
    return image


@pytest.mark.qt
def test_viewport_3d_default_preset_is_bone(qtbot) -> None:
    view = Viewport3DView(view_id="view.3d")
    qtbot.addWidget(view.content_widget())
    assert view.preset is get_preset("bone")


@pytest.mark.qt
def test_viewport_3d_rejects_unknown_preset(qtbot) -> None:
    with pytest.raises(KeyError, match="unknown volume preset"):
        Viewport3DView(view_id="view.3d", preset="unknown")


@pytest.mark.qt
def test_viewport_3d_content_widget_returns_container(qtbot) -> None:
    view = Viewport3DView(view_id="view.3d")
    widget = view.content_widget()
    qtbot.addWidget(widget)
    assert widget is not None
    assert not view.has_volume
    assert view.renderer is None


@pytest.mark.qt
def test_viewport_3d_set_volume_marks_has_volume(qtbot) -> None:
    image = _make_image()
    view = Viewport3DView(view_id="view.3d")
    qtbot.addWidget(view.content_widget())

    view.set_volume(image)

    assert view.has_volume is True
    assert view.renderer is not None
    assert view.volume is not None


@pytest.mark.qt
def test_viewport_3d_set_preset_changes_state(qtbot) -> None:
    image = _make_image()
    view = Viewport3DView(view_id="view.3d")
    qtbot.addWidget(view.content_widget())
    view.set_volume(image)
    assert view.preset is get_preset("bone")

    view.set_preset("soft_tissue")
    assert view.preset is get_preset("soft_tissue")
    assert view.window == get_preset("soft_tissue").default_window
    assert view.level == get_preset("soft_tissue").default_level


@pytest.mark.qt
def test_viewport_3d_set_window_level_updates_state(qtbot) -> None:
    image = _make_image()
    view = Viewport3DView(view_id="view.3d")
    qtbot.addWidget(view.content_widget())
    view.set_volume(image)

    view.set_window_level(1000.0, 200.0)
    assert view.window == 1000.0
    assert view.level == 200.0


@pytest.mark.qt
def test_viewport_3d_set_window_level_rejects_non_positive(qtbot) -> None:
    image = _make_image()
    view = Viewport3DView(view_id="view.3d")
    qtbot.addWidget(view.content_widget())
    view.set_volume(image)

    with pytest.raises(ValueError, match="window must be positive"):
        view.set_window_level(0.0, 200.0)
    with pytest.raises(ValueError, match="window must be positive"):
        view.set_window_level(-100.0, 200.0)


@pytest.mark.qt
def test_viewport_3d_dispose_clears_state(qtbot) -> None:
    image = _make_image()
    view = Viewport3DView(view_id="view.3d")
    qtbot.addWidget(view.content_widget())
    view.set_volume(image)
    assert view.has_volume

    view.dispose()

    assert view.has_volume is False
    assert view.renderer is None
    assert view.volume is None
