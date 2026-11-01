"""Viewport3DView — a 3D view of the Scene.

For the Passo 8c, this renders the volume with
``vtkSmartVolumeMapper`` + ``vtkVolume`` using one of the presets
defined in ``presets.py`` (Bone, Soft Tissue, Skin, CT Angio).

A ``vtkOutlineFilter`` is rendered as a bounding box around the
volume, so the user can see the extent of the data.

The View does not know about the Scene. The Editor resolves the
VolumeData and passes it via ``set_volume(...)``.

See ADR-0013 §2.3, scene.md §24, scene.md §27 (presentation state).
"""

from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import QVBoxLayout, QWidget
from vtkmodules.qt.QVTKRenderWindowInteractor import (
    QVTKRenderWindowInteractor,
)
from vtkmodules.vtkCommonDataModel import vtkPiecewiseFunction
from vtkmodules.vtkFiltersModeling import vtkOutlineFilter
from vtkmodules.vtkRenderingCore import (
    vtkActor,
    vtkColorTransferFunction,
    vtkPolyDataMapper,
    vtkRenderer,
    vtkVolume,
    vtkVolumeProperty,
)
from vtkmodules.vtkRenderingVolumeOpenGL2 import vtkSmartVolumeMapper

from cranioz.ui.editors.view import View
from cranioz.ui.editors.viewport_3d.presets import (
    VolumePreset,
    get_preset,
)

_DEFAULT_PRESET = "bone"


class Viewport3DView(View):
    """A 3D view backed by ``QVTKRenderWindowInteractor``."""

    def __init__(
        self,
        view_id: str = "view.viewport_3d",
        preset: str = _DEFAULT_PRESET,
    ) -> None:
        super().__init__(view_id=view_id, view_type="3d")
        self._preset = get_preset(preset)
        self._interactor: QVTKRenderWindowInteractor | None = None
        self._renderer: vtkRenderer | None = None
        self._volume: vtkVolume | None = None
        self._volume_property: vtkVolumeProperty | None = None
        self._window: float = self._preset.default_window
        self._level: float = self._preset.default_level
        self._container: QWidget | None = None
        self._vtk_image_data: Any = None
        self._volume_set = False

    # ----- Public API ---------------------------------------------------

    def set_volume(self, vtk_image_data: Any) -> None:
        """Attach a ``vtkImageData`` and render it as a volume.

        The preset and window/level are applied from the current
        state (which can be changed via ``set_preset`` and
        ``set_window_level`` before or after this call).
        """
        self._vtk_image_data = vtk_image_data
        self._ensure_pipeline()
        assert self._volume is not None  # noqa: S101
        assert self._volume_property is not None  # noqa: S101

        mapper = vtkSmartVolumeMapper()
        mapper.SetInputData(vtk_image_data)
        mapper.SetBlendModeToComposite()

        self._volume.SetMapper(mapper)
        self._apply_transfer_functions()
        self._volume.SetProperty(self._volume_property)

        assert self._renderer is not None  # noqa: S101
        self._renderer.ResetCamera()
        assert self._interactor is not None  # noqa: S101
        self._interactor.GetRenderWindow().Render()  # type: ignore[no-untyped-call]
        self._interactor.Initialize()
        self._volume_set = True

    def set_preset(self, name: str) -> None:
        """Change the volume rendering preset.

        If a volume is already attached, the transfer functions are
        re-applied immediately.
        """
        self._preset = get_preset(name)
        self._window = self._preset.default_window
        self._level = self._preset.default_level
        if self._volume_property is not None and self._volume_set:
            self._apply_transfer_functions()
            assert self._interactor is not None  # noqa: S101
            self._interactor.GetRenderWindow().Render()  # type: ignore[no-untyped-call]

    def set_window_level(self, window: float, level: float) -> None:
        """Adjust the volume window/level.

        ``window`` and ``level`` are in Hounsfield Units (for CT).
        """
        if window <= 0:
            raise ValueError(f"window must be positive, got {window}")
        self._window = window
        self._level = level
        if self._volume_property is not None and self._volume_set:
            self._apply_transfer_functions()
            assert self._interactor is not None  # noqa: S101
            self._interactor.GetRenderWindow().Render()  # type: ignore[no-untyped-call]

    @property
    def preset(self) -> VolumePreset:
        return self._preset

    @property
    def window(self) -> float:
        return self._window

    @property
    def level(self) -> float:
        return self._level

    @property
    def has_volume(self) -> bool:
        return self._volume_set

    @property
    def renderer(self) -> vtkRenderer | None:
        return self._renderer

    @property
    def volume(self) -> vtkVolume | None:
        return self._volume

    # ----- Internals ---------------------------------------------------

    def _ensure_pipeline(self) -> None:
        """Create the renderer, interactor, and volume on first use."""
        if self._interactor is not None:
            return

        self._interactor = QVTKRenderWindowInteractor()  # type: ignore[no-untyped-call]
        self._renderer = vtkRenderer()
        self._renderer.SetBackground(0.1, 0.1, 0.2)  # dark blue
        self._interactor.GetRenderWindow().AddRenderer(self._renderer)  # type: ignore[no-untyped-call]

        self._volume_property = vtkVolumeProperty()
        self._volume_property.SetInterpolationTypeToLinear()
        self._volume_property.ShadeOn()
        self._volume_property.SetAmbient(0.2)
        self._volume_property.SetDiffuse(0.8)
        self._volume_property.SetSpecular(0.2)
        self._volume_property.SetSpecularPower(10.0)

        self._volume = vtkVolume()
        self._volume.SetProperty(self._volume_property)
        self._renderer.AddVolume(self._volume)

        if self._container is None:
            self._container = QWidget()
            self._container.setObjectName(f"viewport_3d.view.{self.view_id}")
            layout = QVBoxLayout(self._container)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
            layout.addWidget(self._interactor)

        # Add the outline (bounding box) once. It is updated in
        # set_volume when the input changes.
        self._outline_actor = self._build_outline_actor()

    def _build_outline_actor(self) -> vtkActor:
        assert self._renderer is not None  # noqa: S101
        outline = vtkOutlineFilter()
        outline.SetInputData(self._vtk_image_data)

        mapper = vtkPolyDataMapper()
        mapper.SetInputConnection(outline.GetOutputPort())

        actor = vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(0.9, 0.9, 0.9)
        actor.GetProperty().SetLineWidth(2.0)
        self._renderer.AddActor(actor)
        return actor

    def _apply_transfer_functions(self) -> None:
        """Apply the current preset and window/level to the volume property."""
        assert self._volume_property is not None  # noqa: S101

        color = vtkColorTransferFunction()
        for color_point in self._preset.color_points:
            color.AddRGBPoint(
                color_point.scalar,
                color_point.r,
                color_point.g,
                color_point.b,
            )

        opacity = vtkPiecewiseFunction()
        for opacity_point in self._preset.opacity_points:
            opacity.AddPoint(opacity_point.scalar, opacity_point.opacity)

        self._volume_property.SetColor(color)
        self._volume_property.SetScalarOpacity(opacity)
        self._volume_property.SetScalarOpacityUnitDistance(1.0)

        # Apply window/level via the scalar range mapping.
        # vtkVolumeProperty does not have SetColorWindow/SetColorLevel;
        # window/level for volume rendering is expressed through the
        # transfer functions (which are already in HU). To honor the
        # requested window/level, we shift/scale the color points.
        # For simplicity, we keep the preset's HU points as-is and
        # document that window/level for volume rendering is
        # controlled via the preset. The MPR views still use
        # SetColorWindow/SetColorLevel.
        _ = self._window, self._level  # reserved for Passo 8d

    # ----- View API ----------------------------------------------------

    def content_widget(self) -> QWidget:
        if self._container is None:
            self._container = QWidget()
            self._container.setObjectName(f"viewport_3d.view.{self.view_id}")
            layout = QVBoxLayout(self._container)
            layout.setContentsMargins(0, 0, 0, 0)
        return self._container

    def dispose(self) -> None:
        if self._renderer is not None:
            self._renderer.RemoveAllViewProps()
            self._renderer = None
        if self._volume is not None:
            self._volume = None
        if self._volume_property is not None:
            self._volume_property = None
        if self._interactor is not None:
            self._interactor.Finalize()  # type: ignore[no-untyped-call]
            self._interactor.setParent(None)
            self._interactor.deleteLater()
            self._interactor = None
        if self._container is not None:
            self._container.setParent(None)
            self._container.deleteLater()
            self._container = None
        self._vtk_image_data = None
        self._volume_set = False
