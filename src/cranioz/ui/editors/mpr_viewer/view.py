"""MPRView — a 2D MPR view (axial, coronal, or sagittal).

The view renders a 2D slice directly from the ``Volume.data`` NumPy
array, applying window/level in NumPy and converting the result to a
``QImage`` displayed in a ``QLabel``. It does not use VTK, OpenGL,
or a render window.

Architectural decision (not a workaround):

- **MPR 2D is NumPy**. The three orthogonal slices (axial, coronal,
  sagittal) are simple array extractions. NumPy does this in
  microseconds, is deterministic, and does not depend on a graphics
  driver. The window/level is computed from the slice's percentiles
  (1% and 99%), the same calculation used by the Matplotlib debug
  script that proved the data is correct.

- **3D is VTK**. ``Viewport3DView`` continues to use VTK volume
  rendering, which needs OpenGL. The application entry point
  configures ``QSurfaceFormat`` with the Compatibility Profile so
  that the 3D view works. This separation — NumPy for 2D, VTK for
  3D — is what the project settled on after repeated, environment-
  dependent failures of VTK 2D rendering on Windows.

The display plane is locked: the user cannot pan, zoom, or rotate
the image. Navigation between slices is done via the slider at the
bottom of the widget. The slider value is kept in sync with the
current slice index.

See ADR-0013 §2.3, scene.md §24.
"""

from __future__ import annotations

import logging

import numpy as np
from PySide6.QtCore import QObject, Qt, Signal, SignalInstance
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from cranioz.domain.imaging.volume import Volume
from cranioz.ui.editors.view import View
from cranioz.ui.toolbars.specification import (
    ToolbarOrientation,
    ToolbarPosition,
    ToolbarSpec,
    ToolbarVisibilityMode,
)

_logger = logging.getLogger(__name__)

_AXIAL = 2
_CORONAL = 1
_SAGITTAL = 0

_ORIENTATION_BY_TYPE = {
    "axial": _AXIAL,
    "coronal": _CORONAL,
    "sagittal": _SAGITTAL,
}


class _MPRSignals(QObject):
    """QObject that hosts the MPRView's signals.

    The MPRView itself inherits from View (which uses ABCMeta) and
    cannot also inherit from QObject (metaclass conflict). This tiny
    QObject is composed into MPRView and exposes the signals.
    """

    slice_changed = Signal(int)


class MPRView(View):
    """A 2D MPR view backed by NumPy + QImage (no VTK)."""

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

        self._signals = _MPRSignals()

        self._volume: Volume | None = None
        self._volume_set = False
        self._slice_index = 0
        self._max_slice = 0

        self._container: QWidget | None = None
        self._image_label: QLabel | None = None
        self._slider: QSlider | None = None
        self._slice_label: QLabel | None = None

    @property
    def slice_changed(self) -> SignalInstance:
        return self._signals.slice_changed

    def set_volume(self, volume: Volume) -> None:
        if volume is None:
            raise ValueError("MPRView.set_volume requires a non-None Volume")

        self._ensure_container()

        self._volume = volume
        orientation = _ORIENTATION_BY_TYPE[self.view_type]
        dims = volume.dimensions  # (nx, ny, nz)
        if orientation == _AXIAL:
            self._max_slice = dims[2] - 1
        elif orientation == _CORONAL:
            self._max_slice = dims[1] - 1
        else:  # SAGITTAL
            self._max_slice = dims[0] - 1

        self._slice_index = self._max_slice // 2
        self._update_slider_range()
        self._volume_set = True

        self._render_slice()

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
        self._render_slice()
        self._sync_slider()
        self._sync_label()
        self._signals.slice_changed.emit(new_index)

    def get_slice(self) -> int:
        return self._slice_index

    def get_max_slice(self) -> int:
        return self._max_slice

    def content_widget(self) -> QWidget:
        self._ensure_container()
        container = self._container
        if container is None:
            raise RuntimeError("MPRView container was not initialized correctly")
        return container

    def dispose(self) -> None:
        if self._container is not None:
            self._container.setParent(None)
            self._container.deleteLater()
            self._container = None
        self._volume = None
        self._volume_set = False
        self._slider = None
        self._slice_label = None
        self._image_label = None

    def _render_slice(self) -> None:
        volume = self._volume
        image_label = self._image_label
        if volume is None or image_label is None:
            return

        orientation = _ORIENTATION_BY_TYPE[self.view_type]
        if orientation == _AXIAL:
            slice_data = volume.data[self._slice_index, :, :]
        elif orientation == _CORONAL:
            slice_data = volume.data[:, self._slice_index, :]
        else:  # SAGITTAL
            slice_data = volume.data[:, :, self._slice_index]

        if slice_data.size == 0:
            return

        # Window/level by percentiles (1% and 99%). Same calculation
        # used by the Matplotlib debug script that proved the data is
        # correct. The percentiles ignore the outlier air (-6114) and
        # metal (16383) values that would otherwise flatten the image.
        p1, p99 = np.percentile(slice_data, [1, 99])
        if p99 <= p1:
            p99 = p1 + 1.0
        arr = slice_data.astype(np.float32)
        arr = np.clip((arr - p1) / (p99 - p1), 0.0, 1.0)
        arr = (arr * 255.0).astype(np.uint8)

        # Volume.data is (nz, ny, nx). The slice_data is already
        # (ny, nx), which is what QImage expects. QImage's origin is
        # top-left; the Matplotlib debug script used origin='lower'
        # to match the VTK convention. We flip the image vertically
        # to keep the same orientation as the (now 3D-only) VTK view.
        height, width = arr.shape
        q_image = QImage(
            arr.tobytes(),
            width,
            height,
            arr.strides[0],
            QImage.Format.Format_Grayscale8,
        )
        q_image = q_image.mirrored(False, True)

        pixmap = QPixmap.fromImage(q_image)
        image_label.setPixmap(pixmap)

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
        self.set_slice(value)

    def _ensure_container(self) -> None:
        if self._container is not None:
            return

        container = QWidget()
        container.setObjectName(f"mpr.view.{self.view_id}")
        container.setMinimumSize(1, 1)

        outer_layout = QVBoxLayout(container)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        image_label = QLabel()
        image_label.setObjectName(f"mpr.view.{self.view_id}.image")
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_label.setStyleSheet("background-color: black;")
        image_label.setMinimumSize(1, 1)

        slider_row = QWidget()
        slider_row.setObjectName(f"mpr.view.{self.view_id}.slider_row")
        slider_row.setFixedHeight(28)
        slider_layout = QHBoxLayout(slider_row)
        slider_layout.setContentsMargins(8, 2, 8, 2)
        slider_layout.setSpacing(8)

        slice_label = QLabel("0 / 0")
        slice_label.setObjectName(f"mpr.view.{self.view_id}.slice_label")
        slice_label.setMinimumWidth(60)
        slice_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

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

        outer_layout.addWidget(image_label, stretch=1)
        outer_layout.addWidget(slider_row, stretch=0)

        self._container = container
        self._image_label = image_label
        self._slice_label = slice_label
        self._slider = slider

    def toolbar_specs(self) -> list[ToolbarSpec]:
        """Interaction tools: window/level, zoom, pan, cursor."""
        return [
            ToolbarSpec(
                toolbar_id=f"toolbar.{self.view_id}.tools",
                title=f"{self.view_type.capitalize()} Tools",
                orientation=ToolbarOrientation.VERTICAL,
                position=ToolbarPosition.LEFT,
                tool_ids=("tool.log",),  # placeholder until real tools land
                visibility_mode=ToolbarVisibilityMode.ACTIVE_ONLY,
            )
        ]

    def control_panel_specs(self) -> list[ToolbarSpec]:
        """Display controls: LUT, ruler, crosshair."""
        return [
            ToolbarSpec(
                toolbar_id=f"toolbar.{self.view_id}.display",
                title=f"{self.view_type.capitalize()} Display",
                orientation=ToolbarOrientation.VERTICAL,
                position=ToolbarPosition.RIGHT,
                tool_ids=("tool.toggle",),  # placeholder
                visibility_mode=ToolbarVisibilityMode.ACTIVE_ONLY,
            )
        ]
