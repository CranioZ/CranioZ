"""Viewport3DView — a 3D view of the Scene.

Two independent rendering paths share the same ``vtkRenderer``:

- ``set_volume``: volume rendering via ``vtkSmartVolumeMapper``, with
  presets (Bone, Soft Tissue, Skin, CT Angio, CBCT).
- ``set_mesh``: polygonal rendering via ``mesh_to_polydata``, used to
  validate the VTK pipeline independently of the DICOM volume path.

The two can coexist: a volume and one or more meshes can be shown in
the same viewport. ``set_volume`` and ``set_mesh`` are additive; each
replaces only its own actor (the volume actor or the last mesh actor).

The View does not know about the Scene. The Editor resolves the
``Volume`` (via ``set_volume``) or the ``Mesh`` (via ``set_mesh``).

See ADR-0013 §2.3, scene.md §24, scene.md §27 (presentation state).
"""

from __future__ import annotations

import contextlib
from typing import Any

import numpy as np
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QLayout, QVBoxLayout, QWidget
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

from cranioz.domain.geometry.mesh import Mesh
from cranioz.domain.imaging.volume import Volume
from cranioz.infrastructure.geometry.adapters.vtk.polydata import (
    mesh_to_polydata,
)
from cranioz.infrastructure.visualization.vtk_image_adapter import VtkImageAdapter
from cranioz.ui.editors.view import View
from cranioz.ui.editors.viewport_3d.presets import (
    VolumePreset,
    get_preset,
)
from cranioz.ui.toolbars.specification import (
    ToolbarOrientation,
    ToolbarPosition,
    ToolbarSpec,
    ToolbarVisibilityMode,
)

_DEFAULT_PRESET = "bone"
_CBCT_PRESET = "cbct"


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
        self._volume_actor: vtkVolume | None = None
        self._volume_property: vtkVolumeProperty | None = None
        self._outline_actor: vtkActor | None = None
        self._mesh_actor: vtkActor | None = None
        self._window: float = self._preset.default_window
        self._level: float = self._preset.default_level
        self._container: QWidget | None = None
        self._vtk_image_data: Any = None
        self._volume_set = False
        self._adapter = VtkImageAdapter()
        self._volume: Volume | None = None
        self._mesh: Mesh | None = None
        self._render_pending = False
        self._initial_render_timer: QTimer | None = None

    # ----- Public API ---------------------------------------------------

    def set_volume(self, volume: Volume) -> None:
        """Attach a ``Volume`` and render it as a volume."""
        if volume is None:
            raise ValueError("Viewport3DView.set_volume requires a non-None Volume")

        if volume.is_hu_calibrated:
            preset_name = _DEFAULT_PRESET
        else:
            preset_name = _CBCT_PRESET
        self._preset = get_preset(preset_name)
        self._window = self._preset.default_window
        self._level = self._preset.default_level

        self._ensure_pipeline()
        self._ensure_interactor_in_layout()

        vtk_image_data = self._adapter.to_vtk(volume)
        self._volume = volume
        self._vtk_image_data = vtk_image_data

        volume_actor = self._volume_actor
        volume_property = self._volume_property
        renderer = self._renderer
        if volume_actor is None or volume_property is None or renderer is None:
            raise RuntimeError("Viewport3DView pipeline was not initialized correctly")

        mapper = vtkSmartVolumeMapper()
        mapper.SetInputData(vtk_image_data)
        mapper.SetBlendModeToComposite()

        volume_actor.SetMapper(mapper)
        self._apply_transfer_functions()
        volume_actor.SetProperty(volume_property)

        if self._outline_actor is not None:
            renderer.RemoveActor(self._outline_actor)
        self._outline_actor = self._build_outline_actor()

        interactor = self._interactor
        if interactor is not None:
            with contextlib.suppress(RuntimeError):
                interactor.Initialize()

        self._volume_set = True
        self._schedule_initial_render()

    def _schedule_initial_render(self) -> None:
        """Schedule the first render, avoiding a double dispatch."""
        if self._render_pending:
            return
        self._render_pending = True

        timer = self._initial_render_timer
        if timer is None:
            return
        timer.start(0)

    def _initial_render(self) -> None:
        """Configure the camera and render the first frame."""
        interactor = self._interactor
        renderer = self._renderer
        if interactor is None or renderer is None:
            self._render_pending = False
            return

        try:
            width_ok = interactor.width() > 0 and interactor.height() > 0
        except RuntimeError:
            self._render_pending = False
            return

        if not width_ok:
            timer = self._initial_render_timer
            if timer is not None:
                timer.start(50)
            return

        self._render_pending = False

        try:
            self._configure_camera_for_volume()
            render_window = interactor.GetRenderWindow()  # type: ignore[no-untyped-call]
            if render_window is not None:
                render_window.Render()
        except RuntimeError:
            return

    def _configure_camera_for_volume(self) -> None:
        """Configure the camera to frame the current volume."""
        renderer = self._renderer
        if renderer is None:
            return

        bounds = self._current_bounds()
        if bounds is None:
            return

        cx = (bounds[0] + bounds[1]) / 2.0
        cy = (bounds[2] + bounds[3]) / 2.0
        cz = (bounds[4] + bounds[5]) / 2.0
        width = bounds[1] - bounds[0]
        height = bounds[3] - bounds[2]
        depth = bounds[5] - bounds[4]

        diagonal = (width**2 + height**2 + depth**2) ** 0.5
        if diagonal <= 0:
            return

        camera = renderer.GetActiveCamera()
        camera.SetPosition(cx, cy - diagonal * 1.5, cz + diagonal * 1.5)
        camera.SetFocalPoint(cx, cy, cz)
        camera.SetViewUp(0, 0, 1)
        camera.SetClippingRange(diagonal * 0.1, diagonal * 5.0)
        camera.SetParallelProjection(True)
        camera.SetParallelScale(max(width, height) * 0.7)
        renderer.ResetCameraClippingRange()

    def _current_bounds(self) -> tuple[float, ...] | None:
        """Return the bounds of the current volume or mesh actor."""
        try:
            if self._volume_actor is not None and self._volume_set:
                return self._volume_actor.GetBounds()
            if self._mesh_actor is not None:
                return self._mesh_actor.GetBounds()
        except RuntimeError:
            return None
        return None

    def set_mesh(self, mesh: Mesh) -> None:
        """Render a canonical ``Mesh`` as a polygonal actor."""
        if mesh is None:
            raise ValueError("Viewport3DView.set_mesh requires a non-None Mesh")

        self._ensure_pipeline()
        self._ensure_interactor_in_layout()

        poly = mesh_to_polydata(mesh)

        mapper = vtkPolyDataMapper()
        mapper.SetInputData(poly)

        actor = vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(0.85, 0.85, 0.85)
        actor.GetProperty().SetEdgeVisibility(False)

        renderer = self._renderer
        if renderer is None:
            raise RuntimeError("Viewport3DView pipeline was not initialized correctly")

        if self._mesh_actor is not None:
            renderer.RemoveActor(self._mesh_actor)
        renderer.AddActor(actor)
        self._mesh_actor = actor
        self._mesh = mesh

        interactor = self._interactor
        if interactor is not None:
            with contextlib.suppress(RuntimeError):
                interactor.Initialize()

        self._schedule_initial_render()

    def set_preset(self, name: str) -> None:
        """Change the volume rendering preset."""
        self._preset = get_preset(name)
        self._window = self._preset.default_window
        self._level = self._preset.default_level
        if self._volume_property is None or not self._volume_set:
            return
        self._apply_transfer_functions()
        self._schedule_initial_render()

    def set_window_level(self, window: float, level: float) -> None:
        """Adjust the volume window/level (Hounsfield Units)."""
        if window <= 0:
            raise ValueError(f"window must be positive, got {window}")
        self._window = window
        self._level = level
        if self._volume_property is None or not self._volume_set:
            return
        self._apply_transfer_functions()
        self._schedule_initial_render()

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
    def has_mesh(self) -> bool:
        return self._mesh_actor is not None

    @property
    def mesh(self) -> Mesh | None:
        return self._mesh

    @property
    def renderer(self) -> vtkRenderer | None:
        return self._renderer

    @property
    def volume_actor(self) -> vtkVolume | None:
        return self._volume_actor

    # ----- View API ----------------------------------------------------

    def content_widget(self) -> QWidget:
        """Return the container widget for this view."""
        self._ensure_container()
        container = self._container
        if container is None:  # pragma: no cover - defensive
            raise RuntimeError("Viewport3DView container was not initialized correctly")
        return container

    def dispose(self) -> None:
        """Release the VTK pipeline and the Qt widgets. Idempotent."""
        if self._initial_render_timer is not None:
            self._initial_render_timer.stop()
            with contextlib.suppress(RuntimeError, TypeError):
                self._initial_render_timer.timeout.disconnect()
            self._initial_render_timer.deleteLater()
            self._initial_render_timer = None
        self._render_pending = False

        if self._renderer is not None:
            self._renderer.RemoveAllViewProps()
            self._renderer = None

        self._outline_actor = None
        self._volume_actor = None
        self._volume_property = None
        self._mesh_actor = None

        if self._interactor is not None:
            with contextlib.suppress(RuntimeError):
                self._interactor.Finalize()  # type: ignore[no-untyped-call]
            self._interactor.setParent(None)
            self._interactor.deleteLater()
            self._interactor = None

        if self._container is not None:
            self._container.setParent(None)
            self._container.deleteLater()
            self._container = None

        self._vtk_image_data = None
        self._volume = None
        self._mesh = None
        self._volume_set = False

    # ----- Internal helpers -------------------------------------------

    def _ensure_pipeline(self) -> None:
        """Create the renderer, interactor, volume, and render timer on first use."""
        if self._interactor is not None:
            return

        interactor = QVTKRenderWindowInteractor()  # type: ignore[no-untyped-call]
        renderer = vtkRenderer()
        renderer.SetBackground(0.1, 0.1, 0.2)
        interactor.GetRenderWindow().AddRenderer(renderer)  # type: ignore[no-untyped-call]

        volume_property = vtkVolumeProperty()
        volume_property.SetInterpolationTypeToLinear()
        volume_property.ShadeOn()
        volume_property.SetAmbient(0.2)
        volume_property.SetDiffuse(0.8)
        volume_property.SetSpecular(0.2)
        volume_property.SetSpecularPower(10.0)

        volume_actor = vtkVolume()
        volume_actor.SetProperty(volume_property)
        renderer.AddVolume(volume_actor)

        # QTimer without a parent. The View is not a QObject, so it
        # cannot be used as the parent. Cleanup is explicit in dispose().
        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(self._initial_render)

        self._interactor = interactor
        self._renderer = renderer
        self._volume_property = volume_property
        self._volume_actor = volume_actor
        self._initial_render_timer = timer

        self._ensure_container()

    def _ensure_container(self) -> None:
        """Create the Qt container widget once. Idempotent."""
        if self._container is not None:
            return

        container = QWidget()
        container.setObjectName(f"viewport_3d.view.{self.view_id}")
        container.setMinimumSize(1, 1)

        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        self._container = container

    def _ensure_interactor_in_layout(self) -> None:
        """Add the interactor to the container's layout, once."""
        container = self._container
        interactor = self._interactor
        if container is None or interactor is None:  # pragma: no cover - defensive
            return

        container_layout: QLayout | None = container.layout()
        if container_layout is None:  # pragma: no cover - defensive
            return

        if container_layout.indexOf(interactor) == -1:
            container_layout.addWidget(interactor)

    def _build_outline_actor(self) -> vtkActor:
        """Build a bounding-box outline for the current volume."""
        outline = vtkOutlineFilter()
        outline.SetInputData(self._vtk_image_data)

        mapper = vtkPolyDataMapper()
        mapper.SetInputConnection(outline.GetOutputPort())

        actor = vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(0.9, 0.9, 0.9)
        actor.GetProperty().SetLineWidth(2.0)
        if self._renderer is not None:
            self._renderer.AddActor(actor)
        return actor

    def _apply_transfer_functions(self) -> None:
        """Apply the current preset and window/level to the volume property."""
        volume_property = self._volume_property
        if volume_property is None:  # pragma: no cover - defensive
            return

        color = vtkColorTransferFunction()
        opacity = vtkPiecewiseFunction()

        if self._volume is not None and not self._volume.is_hu_calibrated:
            p1, p99 = np.percentile(self._volume.data, [1, 99])

            color.AddRGBPoint(p1, 0.0, 0.0, 0.0)
            color.AddRGBPoint(p1 + (p99 - p1) * 0.3, 0.2, 0.2, 0.2)
            color.AddRGBPoint(p1 + (p99 - p1) * 0.7, 0.8, 0.7, 0.6)
            color.AddRGBPoint(p99, 1.0, 1.0, 1.0)

            opacity.AddPoint(p1, 0.0)
            opacity.AddPoint(p1 + (p99 - p1) * 0.2, 0.0)
            opacity.AddPoint(p1 + (p99 - p1) * 0.5, 0.15)
            opacity.AddPoint(p99, 0.9)
        else:
            for color_point in self._preset.color_points:
                color.AddRGBPoint(
                    color_point.scalar,
                    color_point.r,
                    color_point.g,
                    color_point.b,
                )

            for opacity_point in self._preset.opacity_points:
                opacity.AddPoint(opacity_point.scalar, opacity_point.opacity)

        volume_property.SetColor(color)
        volume_property.SetScalarOpacity(opacity)
        volume_property.SetScalarOpacityUnitDistance(1.0)

    def toolbar_specs(self) -> list[ToolbarSpec]:
        """Interaction tools: ROI, cut, paint, annotations."""
        return [
            ToolbarSpec(
                toolbar_id=f"toolbar.{self.view_id}.tools",
                title="3D Tools",
                orientation=ToolbarOrientation.VERTICAL,
                position=ToolbarPosition.LEFT,
                tool_ids=("tool.log",),
                visibility_mode=ToolbarVisibilityMode.ACTIVE_ONLY,
            )
        ]

    def control_panel_specs(self) -> list[ToolbarSpec]:
        """Display controls: preset, orientation, background."""
        return [
            ToolbarSpec(
                toolbar_id=f"toolbar.{self.view_id}.display",
                title="3D Display",
                orientation=ToolbarOrientation.VERTICAL,
                position=ToolbarPosition.RIGHT,
                tool_ids=("tool.toggle",),
                visibility_mode=ToolbarVisibilityMode.ACTIVE_ONLY,
            )
        ]
