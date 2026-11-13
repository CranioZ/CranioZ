"""Tests for Viewport3DView (volume rendering)."""

from __future__ import annotations

from datetime import UTC, datetime

import numpy as np
import pytest

pytest.importorskip("vtk")
pytest.importorskip("vtkmodules.qt")

from cranioz.domain.imaging.image_metadata import (
    ImageMetadata,
    ImageModality,
)
from cranioz.domain.imaging.volume import IntensityScale, Volume
from cranioz.domain.imaging.volume_geometry import VolumeGeometry
from cranioz.domain.imaging.volume_provenance import VolumeProvenance
from cranioz.ui.editors.viewport_3d.presets import (
    get_preset,
)
from cranioz.ui.editors.viewport_3d.view import Viewport3DView


def _make_volume() -> Volume:
    """Build a tiny synthetic ``Volume`` (4x4x4, int16).

    The volume is intentionally non-HU (``IntensityScale.UNKNOWN``)
    so it exercises the ``cbct`` branch of ``Viewport3DView.set_volume()``.
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
    """Build a tiny HU-calibrated synthetic Volume (4x4x4, int16).

    Values are chosen inside a plausible HU range (air = -1000,
    bone = 1500) so the ``DicomCalibrator`` classification would
    agree with ``IntensityScale.HU``. This exercises the "HU volume"
    branch of ``Viewport3DView.set_volume()``.
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


@pytest.mark.qt
def test_viewport_3d_initial_preset_before_volume_is_bone(qtbot) -> None:
    """The default preset before any volume is 'bone'.

    This is the *initial* state only: after ``set_volume()``, the preset
    is selected from the volume's ``IntensityScale`` (HU -> bone,
    otherwise -> cbct).
    """
    view = Viewport3DView(view_id="view.3d")
    qtbot.addWidget(view.content_widget())
    assert view.preset is get_preset("bone")


@pytest.mark.qt
def test_viewport_3d_rejects_unknown_preset(qtbot) -> None:
    with pytest.raises(KeyError, match="unknown volume preset"):
        Viewport3DView(view_id="view.3d", preset="unknown")


@pytest.mark.qt
def test_viewport_3d_content_widget_returns_container(qtbot) -> None:
    """content_widget() must eagerly create the VTK pipeline.

    Block 4: ``content_widget()`` calls ``_ensure_pipeline()`` so that
    the ``QVTKRenderWindowInteractor`` exists before
    ``ViewLayoutRenderer`` installs its activation filter on it. The
    renderer is therefore non-None immediately after the first
    ``content_widget()`` call, even before any volume is attached.
    """
    view = Viewport3DView(view_id="view.3d")
    widget = view.content_widget()
    qtbot.addWidget(widget)
    assert widget is not None
    # The pipeline exists (interactor + renderer), but no volume is
    # attached yet.
    assert view.has_volume is False
    assert view.renderer is not None


@pytest.mark.qt
def test_viewport_3d_set_volume_marks_has_volume(qtbot) -> None:
    volume = _make_volume()
    view = Viewport3DView(view_id="view.3d")
    qtbot.addWidget(view.content_widget())

    view.set_volume(volume)

    assert view.has_volume is True
    assert view.renderer is not None
    assert view.volume_actor is not None


@pytest.mark.qt
def test_viewport_3d_retains_volume_reference(qtbot) -> None:
    """The View must retain a strong reference to the Volume (§8.1)."""
    volume = _make_volume()
    view = Viewport3DView(view_id="view.3d")
    qtbot.addWidget(view.content_widget())

    view.set_volume(volume)
    assert view._volume is volume  # noqa: SLF001

    view.dispose()
    assert view._volume is None  # noqa: SLF001


@pytest.mark.qt
def test_viewport_3d_set_preset_changes_state(qtbot) -> None:
    """A non-HU volume starts at 'cbct'; set_preset() overrides it."""
    volume = _make_volume()  # IntensityScale.UNKNOWN
    view = Viewport3DView(view_id="view.3d")
    qtbot.addWidget(view.content_widget())
    view.set_volume(volume)

    # Non-HU volume -> cbct preset, by design.
    assert view.preset is get_preset("cbct")

    view.set_preset("soft_tissue")
    assert view.preset is get_preset("soft_tissue")
    assert view.window == get_preset("soft_tissue").default_window
    assert view.level == get_preset("soft_tissue").default_level


@pytest.mark.qt
def test_viewport_3d_uses_bone_preset_for_hu_volume(qtbot) -> None:
    """An HU-calibrated volume starts at 'bone'."""
    volume = _make_hu_volume()
    view = Viewport3DView(view_id="view.3d")
    qtbot.addWidget(view.content_widget())
    view.set_volume(volume)

    assert view.preset is get_preset("bone")


@pytest.mark.qt
def test_viewport_3d_set_window_level_updates_state(qtbot) -> None:
    volume = _make_volume()
    view = Viewport3DView(view_id="view.3d")
    qtbot.addWidget(view.content_widget())
    view.set_volume(volume)

    view.set_window_level(1000.0, 200.0)
    assert view.window == 1000.0
    assert view.level == 200.0


@pytest.mark.qt
def test_viewport_3d_set_window_level_rejects_non_positive(qtbot) -> None:
    volume = _make_volume()
    view = Viewport3DView(view_id="view.3d")
    qtbot.addWidget(view.content_widget())
    view.set_volume(volume)

    with pytest.raises(ValueError, match="window must be positive"):
        view.set_window_level(0.0, 200.0)
    with pytest.raises(ValueError, match="window must be positive"):
        view.set_window_level(-100.0, 200.0)


@pytest.mark.qt
def test_viewport_3d_dispose_clears_state(qtbot) -> None:
    volume = _make_volume()
    view = Viewport3DView(view_id="view.3d")
    qtbot.addWidget(view.content_widget())
    view.set_volume(volume)
    assert view.has_volume

    view.dispose()

    assert view.has_volume is False
    assert view.renderer is None
    assert view.volume_actor is None
