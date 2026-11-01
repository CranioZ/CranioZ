"""MPRView — a 2D MPR view (axial, coronal, or sagittal).

This is a View, not an Editor. It is hosted by an Editor (e.g.,
TomographyEditor) that coordinates it with other Views.

The View renders a ``vtkImageData`` via ``vtkResliceImageViewer``.
It does not know about the Scene, SceneQuery, or DomainObjectStore.
The Editor resolves the VolumeData and passes it via
``set_volume(...)``.

See ADR-0013 §2.3, scene.md §24.
"""

from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import QVBoxLayout, QWidget
from vtkmodules.qt.QVTKRenderWindowInteractor import (
    QVTKRenderWindowInteractor,
)
from vtkmodules.vtkInteractionImage import vtkResliceImageViewer

from cranioz.ui.editors.view import View

# vtkResliceImageViewer orientation constants (re-exported for clarity).
_AXIAL = 2
_CORONAL = 1
_SAGITTAL = 0

_ORIENTATION_BY_TYPE = {
    "axial": _AXIAL,
    "coronal": _CORONAL,
    "sagittal": _SAGITTAL,
}


class MPRView(View):
    """A 2D MPR view backed by ``vtkResliceImageViewer``."""

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
        self._image_viewer: vtkResliceImageViewer | None = None
        self._interactor: QVTKRenderWindowInteractor | None = None
        self._container: QWidget | None = None
        self._volume_set = False

    # ----- Volume ------------------------------------------------------

    def set_volume(self, vtk_image_data: Any) -> None:
        """Attach a ``vtkImageData`` to this view.

        The view is created lazily on first call. Subsequent calls
        replace the volume and reset the slice to the middle.
        """
        # 1. Create the VTK pipeline (interactor + image viewer) once.
        if self._image_viewer is None:
            self._interactor = QVTKRenderWindowInteractor()  # type: ignore[no-untyped-call]
            self._image_viewer = vtkResliceImageViewer()
            self._image_viewer.SetRenderWindow(
                self._interactor.GetRenderWindow()  # type: ignore[no-untyped-call]
            )
            self._image_viewer.SetupInteractor(self._interactor)
            orientation = _ORIENTATION_BY_TYPE[self.view_type]
            self._image_viewer.SetSliceOrientation(orientation)
            # Window/level defaults; Passo 8d will expose controls.
            self._image_viewer.SetColorWindow(2000.0)
            self._image_viewer.SetColorLevel(500.0)
            self._image_viewer.SetResliceModeToAxisAligned()

        # 2. Ensure the container exists. This may already have been
        #    created by content_widget() (which the Editor calls before
        #    set_volume in some paths). Creating it here is idempotent.
        if self._container is None:
            self._container = QWidget()
            self._container.setObjectName(f"mpr.view.{self.view_id}")
            self._container.setMinimumSize(1, 1)
            layout = QVBoxLayout(self._container)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)

        # 3. Ensure the interactor is in the container's layout. This
        #    is the fix for the bug: when content_widget() ran first,
        #    the container existed but the interactor was never added
        #    to its layout. addWidget is idempotent for the same widget.
        assert self._interactor is not None  # noqa: S101
        layout = self._container.layout()
        if layout is not None and layout.indexOf(self._interactor) == -1:
            layout.addWidget(self._interactor)

        # 4. Push the data to VTK and render.
        assert self._image_viewer is not None  # noqa: S101
        self._image_viewer.SetInputData(vtk_image_data)
        self._image_viewer.SetSlice(
            self._image_viewer.GetSliceMin()
            + (self._image_viewer.GetSliceMax() - self._image_viewer.GetSliceMin()) // 2
        )
        self._image_viewer.Render()
        self._interactor.Initialize()
        self._volume_set = True

    @property
    def has_volume(self) -> bool:
        return self._volume_set

    @property
    def image_viewer(self) -> vtkResliceImageViewer | None:
        """Expose the ``vtkResliceImageViewer`` (used for synchronization)."""
        return self._image_viewer

    # ----- View API ----------------------------------------------------

    def content_widget(self) -> QWidget:
        if self._container is None:
            # No volume yet — return an empty widget. The Editor will
            # call set_volume() when a VolumeData becomes available.
            self._container = QWidget()
            self._container.setObjectName(f"mpr.view.{self.view_id}")
            self._container.setMinimumSize(1, 1)
            layout = QVBoxLayout(self._container)
            layout.setContentsMargins(0, 0, 0, 0)
        return self._container

    def dispose(self) -> None:
        if self._image_viewer is not None:
            self._image_viewer.SetInputData(None)
            self._image_viewer = None
        if self._interactor is not None:
            self._interactor.Finalize()  # type: ignore[no-untyped-call]
            self._interactor.setParent(None)
            self._interactor.deleteLater()
            self._interactor = None
        if self._container is not None:
            self._container.setParent(None)
            self._container.deleteLater()
            self._container = None
        self._volume_set = False