"""MPRView — a 2D MPR view (axial, coronal, or sagittal).

This is a View, not an Editor. It is hosted by an Editor (e.g.,
TomographyEditor) that coordinates it with other Views.

The View renders a ``vtkImageData`` via ``vtkImageReslice`` and a
``vtkImageActor``. This is a manual MPR implementation that is more
robust than ``vtkResliceImageViewer``, especially in environments
with limited OpenGL support.

See ADR-0013 §2.3, scene.md §24.
"""

from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import QLayout, QVBoxLayout, QWidget
from vtkmodules.qt.QVTKRenderWindowInteractor import (
    QVTKRenderWindowInteractor,
)
from vtkmodules.vtkImagingColor import vtkImageMapToWindowLevelColors
from vtkmodules.vtkImagingCore import vtkImageReslice
from vtkmodules.vtkRenderingCore import (
    vtkImageActor,
    vtkRenderer,
)

from cranioz.ui.editors.view import View

# Orientation indices for the reslice axes.
_AXIAL = 2
_CORONAL = 1
_SAGITTAL = 0

_ORIENTATION_BY_TYPE = {
    "axial": _AXIAL,
    "coronal": _CORONAL,
    "sagittal": _SAGITTAL,
}

# Default Window/Level for CBCT (Soft Tissue preset).
# The data is normalized to 0-4095 by the DICOM loader.
_CBCT_WINDOW = 800.0
_CBCT_LEVEL = 1500.0


class MPRView(View):
    """A 2D MPR view backed by ``vtkImageReslice`` and ``vtkImageActor``."""

    def __init__(
        self,
        view_id: str = "view.mpr_axial",
        view_type: str = "axial",
    ) -> None:
        super().__init__(view_id=view_id, view_type=view_type)
        if view_type not in _ORIENTATION_BY_TYPE:
            raise ValueError(
                f"MPRView.view_type must be one of "
                f"{sorted(_ORIENTATION_BY_TYPE)!r}, got {view_type!r}"
            )
        self._reslice: vtkImageReslice | None = None
        self._actor: vtkImageActor | None = None
        self._window_level: vtkImageMapToWindowLevelColors | None = None
        self._renderer: vtkRenderer | None = None
        self._interactor: QVTKRenderWindowInteractor | None = None
        self._container: QWidget | None = None
        self._volume_set = False
        self._slice_index = 0
        self._max_slice = 0

    # ----- Public API --------------------------------------------------

    def set_volume(self, vtk_image_data: Any) -> None:
        """Attach a ``vtkImageData`` to this view.

        The MPR pipeline is created lazily on the first call.
        The slice is reset to the middle of the new volume.
        """
        if vtk_image_data is None:
            raise ValueError("MPRView.set_volume requires a non-None vtkImageData")

        self._ensure_pipeline()
        self._ensure_container()
        self._ensure_interactor_in_layout()

        reslice = self._reslice
        actor = self._actor
        window_level = self._window_level
        renderer = self._renderer
        interactor = self._interactor
        if (
            reslice is None
            or actor is None
            or window_level is None
            or renderer is None
            or interactor is None
        ):  # pragma: no cover - defensive
            raise RuntimeError("MPRView pipeline was not initialized correctly")

        # Set the input volume.
        reslice.SetInputData(vtk_image_data)

        # Determine the max slice index based on the volume dimensions.
        dims = vtk_image_data.GetDimensions()
        orientation = _ORIENTATION_BY_TYPE[self.view_type]
        if orientation == _AXIAL:
            self._max_slice = dims[2] - 1
        elif orientation == _CORONAL:
            self._max_slice = dims[1] - 1
        else:  # SAGITTAL
            self._max_slice = dims[0] - 1

        # Reset to the middle slice.
        self._slice_index = self._max_slice // 2
        self._update_slice()

        # Set Window/Level.
        window_level.SetWindow(_CBCT_WINDOW)
        window_level.SetLevel(_CBCT_LEVEL)

        # Connect the pipeline:
        # vtkImageReslice -> vtkImageMapToWindowLevelColors -> vtkImageActor
        window_level.SetInputConnection(reslice.GetOutputPort())
        actor.GetMapper().SetInputConnection(window_level.GetOutputPort())

        renderer.ResetCamera()
        renderer.GetRenderWindow().Render()
        interactor.Initialize()
        self._volume_set = True

    @property
    def has_volume(self) -> bool:
        """Return True if a volume has been attached and rendered."""
        return self._volume_set

    def set_slice(self, index: int) -> None:
        """Set the current slice index."""
        if not self._volume_set:
            return
        self._slice_index = max(0, min(index, self._max_slice))
        self._update_slice()

    def get_slice(self) -> int:
        """Return the current slice index."""
        return self._slice_index

    def get_max_slice(self) -> int:
        """Return the maximum slice index."""
        return self._max_slice

    # ----- View API ----------------------------------------------------

    def content_widget(self) -> QWidget:
        """Return the container widget for this view."""
        self._ensure_container()
        container = self._container
        if container is None:  # pragma: no cover - defensive
            raise RuntimeError("MPRView container was not initialized correctly")
        return container

    def dispose(self) -> None:
        """Release the VTK pipeline and the Qt widgets. Idempotent."""
        if self._interactor is not None:
            self._interactor.Finalize()  # type: ignore[no-untyped-call]
            self._interactor.setParent(None)
            self._interactor.deleteLater()
            self._interactor = None

        if self._container is not None:
            self._container.setParent(None)
            self._container.deleteLater()
            self._container = None

        self._reslice = None
        self._actor = None
        self._window_level = None
        self._renderer = None
        self._volume_set = False

    # ----- Internal helpers -------------------------------------------

    def _ensure_pipeline(self) -> None:
        """Create the VTK pipeline (reslice + actor + renderer) once."""
        if self._reslice is not None:
            return

        interactor = QVTKRenderWindowInteractor()  # type: ignore[no-untyped-call]
        renderer = vtkRenderer()
        interactor.GetRenderWindow().AddRenderer(renderer)  # type: ignore[no-untyped-call]
        renderer.SetBackground(0.0, 0.0, 0.0)  # black background

        reslice = vtkImageReslice()
        reslice.SetOutputDimensionality(2)
        reslice.SetInterpolationModeToLinear()
        reslice.SetBackgroundLevel(0.0)

        # Configure the reslice axes for the desired orientation.
        self._configure_reslice_axes(reslice)

        window_level = vtkImageMapToWindowLevelColors()
        window_level.SetWindow(_CBCT_WINDOW)
        window_level.SetLevel(_CBCT_LEVEL)

        actor = vtkImageActor()
        actor.GetMapper().SetInputConnection(window_level.GetOutputPort())
        renderer.AddActor(actor)

        self._interactor = interactor
        self._renderer = renderer
        self._reslice = reslice
        self._window_level = window_level
        self._actor = actor

    def _configure_reslice_axes(self, reslice: vtkImageReslice) -> None:
        """Configure the reslice axes for the desired orientation.

        The reslice axes matrix maps the input volume axes to the
        output plane. For an axial view, the Z axis is the slice
        direction. For coronal, Y is the slice direction. For
        sagittal, X is the slice direction.
        """
        orientation = _ORIENTATION_BY_TYPE[self.view_type]

        if orientation == _AXIAL:
            # Axial: slice along Z. X -> X, Y -> Y, Z -> Z.
            reslice.SetResliceAxesDirectionCosines(
                1,
                0,
                0,
                0,
                1,
                0,
                0,
                0,
                1,
            )
        elif orientation == _CORONAL:
            # Coronal: slice along Y. X -> X, Z -> Y, Y -> Z.
            reslice.SetResliceAxesDirectionCosines(
                1,
                0,
                0,
                0,
                0,
                1,
                0,
                -1,
                0,
            )
        else:  # SAGITTAL
            # Sagittal: slice along X. Y -> X, Z -> Y, X -> Z.
            reslice.SetResliceAxesDirectionCosines(
                0,
                1,
                0,
                0,
                0,
                1,
                1,
                0,
                0,
            )

    def _update_slice(self) -> None:
        """Update the reslice to show the current slice."""
        reslice = self._reslice
        if reslice is None:
            return

        input_data = reslice.GetInput()
        if input_data is None:
            return

        spacing = input_data.GetSpacing()
        origin = input_data.GetOrigin()
        orientation = _ORIENTATION_BY_TYPE[self.view_type]

        # The slice position is the center of the current slice.
        if orientation == _AXIAL:
            # Slice along Z.
            z = origin[2] + self._slice_index * spacing[2]
            reslice.SetResliceAxesOrigin(origin[0], origin[1], z)
        elif orientation == _CORONAL:
            # Slice along Y.
            y = origin[1] + self._slice_index * spacing[1]
            reslice.SetResliceAxesOrigin(origin[0], y, origin[2])
        else:  # SAGITTAL
            # Slice along X.
            x = origin[0] + self._slice_index * spacing[0]
            reslice.SetResliceAxesOrigin(x, origin[1], origin[2])

        reslice.Update()

    def _ensure_container(self) -> None:
        """Create the Qt container widget once. Idempotent."""
        if self._container is not None:
            return

        container = QWidget()
        container.setObjectName(f"mpr.view.{self.view_id}")
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
