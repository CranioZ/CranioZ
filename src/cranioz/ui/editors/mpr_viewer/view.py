"""MPRView — a 2D MPR view (axial, coronal, or sagittal).

This is a View, not an Editor. It is hosted by an Editor (e.g.,
TomographyEditor) that coordinates it with other Views.

The View renders a ``vtkImageData`` via ``vtkImageReslice`` and a
``vtkImageActor``. This is a manual MPR implementation that is more
robust than ``vtkResliceImageViewer``, especially in environments
with limited OpenGL support.

The display plane is locked: the user cannot pan, zoom, or rotate
the image with the mouse. Navigation between slices is done via the
slider at the bottom of the widget. The slider value is kept in sync
with the current slice index.

See ADR-0013 §2.3, scene.md §24.
"""

from __future__ import annotations

import logging

import numpy as np
from PySide6.QtCore import QObject, Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLayout,
    QSlider,
    QVBoxLayout,
    QWidget,
)
from vtkmodules.qt.QVTKRenderWindowInteractor import (
    QVTKRenderWindowInteractor,
)
from vtkmodules.vtkImagingColor import vtkImageMapToWindowLevelColors
from vtkmodules.vtkImagingCore import vtkImageReslice
from vtkmodules.vtkRenderingCore import (
    vtkImageActor,
    vtkRenderer,
)

from cranioz.domain.imaging.volume import Volume
from cranioz.infrastructure.visualization.vtk_image_adapter import VtkImageAdapter
from cranioz.ui.editors.view import View

_logger = logging.getLogger(__name__)

# Orientation indices for the reslice axes.
_AXIAL = 2
_CORONAL = 1
_SAGITTAL = 0

_ORIENTATION_BY_TYPE = {
    "axial": _AXIAL,
    "coronal": _CORONAL,
    "sagittal": _SAGITTAL,
}

_ORIENTATION_LABEL = {
    "axial": "Axial",
    "coronal": "Coronal",
    "sagittal": "Sagittal",
}


class _MPRSignals(QObject):
    """QObject that hosts the MPRView's signals.

    The MPRView itself inherits from View (which uses ABCMeta) and
    cannot also inherit from QObject (metaclass conflict). This tiny
    QObject is composed into MPRView and exposes the signals.
    """

    slice_changed = Signal(int)


class MPRView(View):
    """A 2D MPR view backed by ``vtkImageReslice`` and ``vtkImageActor``.

    The display plane is locked. The user navigates between slices via
    the slider at the bottom of the widget.
    """

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

        # Signals (composed QObject; see _MPRSignals).
        self._signals = _MPRSignals()

        # VTK pipeline.
        self._reslice: vtkImageReslice | None = None
        self._actor: vtkImageActor | None = None
        self._window_level: vtkImageMapToWindowLevelColors | None = None
        self._renderer: vtkRenderer | None = None
        self._interactor: QVTKRenderWindowInteractor | None = None

        # Qt widgets.
        self._container: QWidget | None = None
        self._vtk_container: QWidget | None = None
        self._slider: QSlider | None = None
        self._slice_label: QLabel | None = None

        # State.
        self._volume_set = False
        self._adapter = VtkImageAdapter()
        self._volume: Volume | None = None
        self._slice_index = 0
        self._max_slice = 0

    # ----- Signals -----------------------------------------------------

    @property
    def slice_changed(self) -> Signal:
        """Signal emitted when the current slice changes.

        Delegates to the internal ``_MPRSignals`` QObject. Consumers
        connect with ``view.slice_changed.connect(handler)`` as usual.
        """
        return self._signals.slice_changed

    # ----- Public API --------------------------------------------------

    def set_volume(self, volume: Volume) -> None:
        """Attach a ``Volume`` to this view."""
        if volume is None:
            raise ValueError("MPRView.set_volume requires a non-None Volume")

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
        ):
            raise RuntimeError("MPRView pipeline was not initialized correctly")

        vtk_image_data = self._adapter.to_vtk(volume)
        self._volume = volume
        reslice.SetInputData(vtk_image_data)

        # 1. Conexões do pipeline VTK
        window_level.SetInputConnection(reslice.GetOutputPort())
        actor.GetMapper().SetInputConnection(window_level.GetOutputPort())

        # 2. Cálculo das dimensões da fatia
        dims = vtk_image_data.GetDimensions()
        orientation = _ORIENTATION_BY_TYPE[self.view_type]
        if orientation == _AXIAL:
            self._max_slice = dims[2] - 1
        elif orientation == _CORONAL:
            self._max_slice = dims[1] - 1
        else:
            self._max_slice = dims[0] - 1

        self._slice_index = self._max_slice // 2
        self._update_slider_range()
        self._update_window_level_from_slice()
        self._update_slice()

        # 3. Inicialização segura do interactor e agendamento do render
        interactor.Initialize()

        _logger.debug("MPRView: scheduling initial render via QTimer")
        QTimer.singleShot(0, self._initial_render)

        self._volume_set = True

    def _initial_render(self) -> None:
        """Configure the camera and render the first frame.

        Called via QTimer.singleShot(0) after set_volume, to ensure the
        widget is shown and the OpenGL context is valid.
        """
        renderer = self._renderer
        actor = self._actor
        interactor = self._interactor
        if renderer is None or actor is None:
            return

        self._configure_camera_for_actor()

        if interactor is not None:
            interactor.SetInteractorStyle(None)
            interactor.GetRenderWindow().Render()
        _logger.debug("MPRView: initial render completed successfully")

    def _configure_camera_for_actor(self) -> None:
        """Configure the camera for a 2D MPR view of the current actor."""
        renderer = self._renderer
        actor = self._actor
        if renderer is None or actor is None:
            return

        bounds = actor.GetBounds()
        cx = (bounds[0] + bounds[1]) / 2.0
        cy = (bounds[2] + bounds[3]) / 2.0
        cz = (bounds[4] + bounds[5]) / 2.0
        camera = renderer.GetActiveCamera()
        camera.SetPosition(cx, cy, cz + 100.0)
        camera.SetFocalPoint(cx, cy, cz)
        camera.SetViewUp(0, 1, 0)
        camera.SetClippingRange(1.0, 1000.0)
        camera.SetParallelProjection(True)
        width = bounds[1] - bounds[0]
        height = bounds[3] - bounds[2]
        camera.SetParallelScale(max(width, height) * 0.6)
        renderer.ResetCameraClippingRange()

    @property
    def has_volume(self) -> bool:
        return self._volume_set

    @property
    def slice_index(self) -> int:
        return self._slice_index

    @property
    def max_slice(self) -> int:
        return self._max_slice

    def set_slice(self, index: int) -> None:
        if not self._volume_set:
            return
        new_index = max(0, min(index, self._max_slice))
        if new_index == self._slice_index:
            return
        self._slice_index = new_index
        self._update_window_level_from_slice()
        self._update_slice()
        self._sync_slider()
        self._sync_label()
        self._signals.slice_changed.emit(new_index)

    def get_slice(self) -> int:
        return self._slice_index

    def get_max_slice(self) -> int:
        return self._max_slice

    # ----- View API ----------------------------------------------------

    def content_widget(self) -> QWidget:
        self._ensure_container()
        container = self._container
        if container is None:  # pragma: no cover - defensive
            raise RuntimeError("MPRView container was not initialized correctly")
        return container

    def dispose(self) -> None:
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
        self._volume = None
        self._volume_set = False
        self._slider = None
        self._slice_label = None
        self._vtk_container = None

    # ----- Internal helpers -------------------------------------------

    def _ensure_pipeline(self) -> None:
        if self._reslice is not None:
            return

        interactor = QVTKRenderWindowInteractor()  # type: ignore[no-untyped-call]
        renderer = vtkRenderer()
        interactor.GetRenderWindow().AddRenderer(renderer)  # type: ignore[no-untyped-call]
        renderer.SetBackground(0.0, 0.0, 0.0)

        reslice = vtkImageReslice()
        reslice.SetOutputDimensionality(2)
        reslice.SetInterpolationModeToLinear()
        reslice.SetBackgroundLevel(0.0)

        window_level = vtkImageMapToWindowLevelColors()
        window_level.SetWindow(1.0)
        window_level.SetLevel(0.0)

        actor = vtkImageActor()
        actor.GetMapper().SetInputConnection(window_level.GetOutputPort())
        actor.PickableOff()
        renderer.AddActor(actor)

        self._interactor = interactor
        self._renderer = renderer
        self._reslice = reslice
        self._window_level = window_level
        self._actor = actor

    def _configure_reslice_axes_from_volume(self, volume: Volume) -> None:
        reslice = self._reslice
        if reslice is None:
            return

        d = np.array(volume.geometry.direction, dtype=np.float64)
        col = [d[:, 0], d[:, 1], d[:, 2]]

        orientation = _ORIENTATION_BY_TYPE[self.view_type]
        if orientation == _AXIAL:
            x_axis, y_axis, normal = col[0], col[1], col[2]
        elif orientation == _CORONAL:
            x_axis, y_axis, normal = col[0], col[2], col[1]
        else:  # SAGITTAL
            x_axis, y_axis, normal = col[1], col[2], col[0]

        reslice.SetResliceAxesDirectionCosines(
            float(x_axis[0]), float(x_axis[1]), float(x_axis[2]),
            float(y_axis[0]), float(y_axis[1]), float(y_axis[2]),
            float(normal[0]), float(normal[1]), float(normal[2]),
        )

    def _update_window_level_from_slice(self) -> None:
        """Update the W/L from the current slice's scalar range.

        Uses percentiles (1% and 99%) with fallback to prevent whiteouts
        on uniform or sparse slices.
        """
        window_level = self._window_level
        volume = self._volume
        if window_level is None or volume is None:
            return

        orientation = _ORIENTATION_BY_TYPE[self.view_type]
        if orientation == _AXIAL:
            slice_data = volume.data[self._slice_index, :, :]
        elif orientation == _CORONAL:
            slice_data = volume.data[:, self._slice_index, :]
        else:  # SAGITTAL
            slice_data = volume.data[:, :, self._slice_index]

        p1, p99 = np.percentile(slice_data, [1, 99])
        window = float(p99 - p1)

        # Proteção contra fatias uniformes/vazias para evitar tela totalmente branca
        if window < 1.0:
            global_min, global_max = float(np.min(volume.data)), float(np.max(volume.data))
            window = max(global_max - global_min, 1.0)
            level = float((global_min + global_max) / 2.0)
        else:
            level = float((p1 + p99) / 2.0)

        window_level.SetWindow(window)
        window_level.SetLevel(level)
        _logger.debug(
            "MPRView: slice %d W/L updated -> p1=%.2f, p99=%.2f, Window=%.2f, Level=%.2f",
            self._slice_index, p1, p99, window, level
        )

    def _update_slice(self) -> None:
        reslice = self._reslice
        if reslice is None:
            return
        volume = self._volume
        if volume is None:
            return

        self._configure_reslice_axes_from_volume(volume)

        d = np.array(volume.geometry.direction, dtype=np.float64)
        spacing = np.array(volume.geometry.spacing, dtype=np.float64)
        origin = np.array(volume.geometry.origin, dtype=np.float64)

        orientation = _ORIENTATION_BY_TYPE[self.view_type]
        if orientation == _AXIAL:
            offset = d @ np.array([0.0, 0.0, self._slice_index * spacing[2]])
        elif orientation == _CORONAL:
            offset = d @ np.array([0.0, self._slice_index * spacing[1], 0.0])
        else:
            offset = d @ np.array([self._slice_index * spacing[0], 0.0, 0.0])

        world = origin + offset
        reslice.SetResliceAxesOrigin(
            float(world[0]), float(world[1]), float(world[2])
        )
        reslice.Update()

        self._configure_camera_for_actor()

        interactor = self._interactor
        if interactor is not None:
            interactor.GetRenderWindow().Render()

    def _update_slider_range(self) -> None:
        slider = self._slider
        if slider is None:
            return
        slider.blockSignals(True)
        slider.setMinimum(0)
        slider.setMaximum(self._max_slice)
        slider.setValue(self._slice_index)
        slider.blockSignals(False)
        self._sync_label()

    def _sync_slider(self) -> None:
        slider = self._slider
        if slider is None:
            return
        slider.blockSignals(True)
        slider.setValue(self._slice_index)
        slider.blockSignals(False)

    def _sync_label(self) -> None:
        label = self._slice_label
        if label is None:
            return
        label.setText(f"{self._slice_index + 1} / {self._max_slice + 1}")

    def _on_slider_value_changed(self, value: int) -> None:
        if not self._volume_set:
            return
        self._slice_index = value
        self._update_window_level_from_slice()
        self._update_slice()
        self._sync_label()
        self._signals.slice_changed.emit(value)

    def _ensure_container(self) -> None:
        if self._container is not None:
            return

        container = QWidget()
        container.setObjectName(f"mpr.view.{self.view_id}")
        container.setMinimumSize(1, 1)

        outer_layout = QVBoxLayout(container)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        vtk_container = QWidget()
        vtk_container.setObjectName(f"mpr.view.{self.view_id}.vtk")
        vtk_layout = QVBoxLayout(vtk_container)
        vtk_layout.setContentsMargins(0, 0, 0, 0)
        vtk_layout.setSpacing(0)

        slider_row = QWidget()
        slider_row.setObjectName(f"mpr.view.{self.view_id}.slider_row")
        slider_row.setFixedHeight(28)
        slider_layout = QHBoxLayout(slider_row)
        slider_layout.setContentsMargins(8, 2, 8, 2)
        slider_layout.setSpacing(8)

        slice_label = QLabel("0 / 0")
        slice_label.setObjectName(f"mpr.view.{self.view_id}.slice_label")
        slice_label.setMinimumWidth(60)
        slice_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )

        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setObjectName(f"mpr.view.{self.view_id}.slider")
        slider.setMinimum(0)
        slider.setMaximum(0)
        slider.setValue(0)
        slider.setSingleStep(1)
        slider.setPageStep(10)
        slider.valueChanged.connect(self._on_slider_value_changed)

        slider_layout.addWidget(slice_label)
        slider_layout.addWidget(slider, stretch=1)

        outer_layout.addWidget(vtk_container, stretch=1)
        outer_layout.addWidget(slider_row, stretch=0)

        self._container = container
        self._vtk_container = vtk_container
        self._slice_label = slice_label
        self._slider = slider

    def _ensure_interactor_in_layout(self) -> None:
        vtk_container = self._vtk_container
        interactor = self._interactor
        if vtk_container is None or interactor is None:  # pragma: no cover - defensive
            return

        vtk_layout: QLayout | None = vtk_container.layout()
        if vtk_layout is None:  # pragma: no cover - defensive
            return

        if vtk_layout.indexOf(interactor) == -1:
            vtk_layout.addWidget(interactor)