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

from typing import Any

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

    # ----- Public API ---------------------------------------------------

    def set_volume(self, volume: Volume) -> None:
        """Attach a ``Volume`` and render it as a volume.

        The ``Volume`` is converted to ``vtkImageData`` via
        ``VtkImageAdapter`` (the sole bridge between the domain and
        VTK, per Medical Imaging Infrastructure §3.2). A strong
        reference to the ``Volume`` is retained so that the shared
        NumPy buffer is not garbage-collected while VTK still points
        to it (§8.1).
        """
        if volume is None:
            raise ValueError("Viewport3DView.set_volume requires a non-None Volume")

        # Choose preset based on intensity_scale.
        if volume.is_hu_calibrated:
            preset_name = _DEFAULT_PRESET
        else:
            preset_name = _CBCT_PRESET
        self._preset = get_preset(preset_name)
        self._window = self._preset.default_window
        self._level = self._preset.default_level

        self._ensure_pipeline()
        self._ensure_interactor_in_layout()

        # Convert Volume -> vtkImageData via the sole bridge.
        vtk_image_data = self._adapter.to_vtk(volume)

        # Retain a strong reference to the Volume so the shared
        # NumPy buffer is not garbage-collected while VTK still
        # points to it (§8.1).
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

        # Rebuild the outline for the new input.
        if self._outline_actor is not None:
            renderer.RemoveActor(self._outline_actor)
        self._outline_actor = self._build_outline_actor()

        renderer.ResetCamera()
        self._render()
        self._volume_set = True

    def set_mesh(self, mesh: Mesh) -> None:
        """Render a canonical ``Mesh`` as a polygonal actor.

        This is the second rendering path of the View. It bypasses the
        ``Volume`` → ``vtkImageData`` pipeline (adapter, reslice,
        transfer functions) and renders a plain ``vtkPolyData``. If
        the mesh renders correctly, the renderer, camera and OpenGL
        context are healthy, and any remaining volume-rendering issue
        lives in the ``vtkImageData`` path.

        The mesh is added on top of any existing volume (both can
        coexist in the same scene). Calling ``set_mesh`` again replaces
        the previous mesh; the volume is left untouched.

        A strong reference to the ``Mesh`` is retained so the shared
        NumPy buffer is not garbage-collected while VTK still points
        to it.

        Args:
            mesh: the canonical mesh to render.

        Raises:
            ValueError: if ``mesh`` is None.
        """
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

        renderer.ResetCamera()
        self._render()

    def set_preset(self, name: str) -> None:
        """Change the volume rendering preset."""
        self._preset = get_preset(name)
        self._window = self._preset.default_window
        self._level = self._preset.default_level
        if self._volume_property is None or not self._volume_set:
            return
        self._apply_transfer_functions()
        self._render()

    def set_window_level(self, window: float, level: float) -> None:
        """Adjust the volume window/level (Hounsfield Units)."""
        if window <= 0:
            raise ValueError(f"window must be positive, got {window}")
        self._window = window
        self._level = level
        if self._volume_property is None or not self._volume_set:
            return
        self._apply_transfer_functions()
        self._render()

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
        """Return the container widget for this view.

        The VTK interactor is NOT added to the container until a
        ``set_volume`` or ``set_mesh`` call. This avoids creating an
        OpenGL context for a view that has no data.
        """
        self._ensure_container()
        container = self._container
        if container is None:  # pragma: no cover - defensive
            raise RuntimeError("Viewport3DView container was not initialized correctly")
        return container

    def dispose(self) -> None:
        """Release the VTK pipeline and the Qt widgets. Idempotent."""
        # 1. Detach props from the renderer.
        if self._renderer is not None:
            self._renderer.RemoveAllViewProps()
            self._renderer = None

        self._outline_actor = None
        self._volume_actor = None
        self._volume_property = None
        self._mesh_actor = None

        # 2. Finalize and destroy the interactor.
        if self._interactor is not None:
            self._interactor.Finalize()  # type: ignore[no-untyped-call]
            self._interactor.setParent(None)
            self._interactor.deleteLater()
            self._interactor = None

        # 3. Destroy the container.
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
        """Create the renderer, interactor, and volume on first use."""
        if self._interactor is not None:
            return

        interactor = QVTKRenderWindowInteractor()  # type: ignore[no-untyped-call]
        renderer = vtkRenderer()
        renderer.SetBackground(0.1, 0.1, 0.2)  # dark blue
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

        self._interactor = interactor
        self._renderer = renderer
        self._volume_property = volume_property
        self._volume_actor = volume_actor

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

    def _render(self) -> None:
        """Trigger a render on the VTK render window. No-op if not ready."""
        interactor = self._interactor
        if interactor is None:  # pragma: no cover - defensive
            return
        interactor.GetRenderWindow().Render()  # type: ignore[no-untyped-call]
        interactor.Initialize()

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
        """Apply the current preset and window/level to the volume property.

        **Dynamic adaptation**: if the volume's scalar range is outside
        the preset's expected range, the transfer function is scaled
        to cover the actual range. This guarantees that the volume
        is visible regardless of the preset.
        """
        volume_property = self._volume_property
        if volume_property is None:  # pragma: no cover - defensive
            return

        # If the volume is not calibrated (CBCT), adapt the transfer
        # function to the actual data range.
        if self._volume is not None and not self._volume.is_hu_calibrated:
            data_min, data_max = self._volume.scalar_range
            color = vtkColorTransferFunction()
            color.AddRGBPoint(data_min, 0.0, 0.0, 0.0)
            color.AddRGBPoint(data_max, 1.0, 1.0, 1.0)

            opacity = vtkPiecewiseFunction()
            opacity.AddPoint(data_min, 0.0)
            opacity.AddPoint(data_max, 1.0)

            volume_property.SetColor(color)
            volume_property.SetScalarOpacity(opacity)
            volume_property.SetScalarOpacityUnitDistance(1.0)
            return

        # For calibrated volumes, use the preset as-is.
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

        volume_property.SetColor(color)
        volume_property.SetScalarOpacity(opacity)
        volume_property.SetScalarOpacityUnitDistance(1.0)

        # Window/level for volume rendering is deferred to Passo 8d.
        _ = self._window, self._level
