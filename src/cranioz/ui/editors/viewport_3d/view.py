"""Viewport3DView — a 3D view of the Scene.

For the Passo 8b, this renders the volume as a 3D outline
(``vtkOutlineFilter``) with a simple camera. Volume rendering and
isosurface extraction are deferred to Passo 8c.

The View does not know about the Scene. The Editor resolves the
VolumeData and passes it via ``set_volume(...)``.

See ADR-0013 §2.3, scene.md §24.
"""

from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import QVBoxLayout, QWidget
from vtkmodules.qt.QVTKRenderWindowInteractor import (
    QVTKRenderWindowInteractor,
)
from vtkmodules.vtkFiltersModeling import vtkOutlineFilter
from vtkmodules.vtkRenderingCore import (
    vtkActor,
    vtkPolyDataMapper,
    vtkRenderer,
)

from cranioz.ui.editors.view import View


class Viewport3DView(View):
    """A 3D view backed by ``QVTKRenderWindowInteractor``."""

    def __init__(self, view_id: str = "view.viewport_3d") -> None:
        super().__init__(view_id=view_id, view_type="3d")
        self._interactor: QVTKRenderWindowInteractor | None = None
        self._renderer: vtkRenderer | None = None
        self._container: QWidget | None = None
        self._volume_set = False

    def set_volume(self, vtk_image_data: Any) -> None:
        """Attach a ``vtkImageData`` and render a 3D outline.

        The outline is a placeholder; Passo 8c will add volume
        rendering and/or isosurface extraction.
        """
        if self._interactor is None:
            self._interactor = QVTKRenderWindowInteractor()  # type: ignore[no-untyped-call]
            self._renderer = vtkRenderer()
            self._renderer.SetBackground(0.1, 0.1, 0.2)  # dark blue
            self._interactor.GetRenderWindow().AddRenderer(  # type: ignore[no-untyped-call]
                self._renderer
            )

            if self._container is None:
                self._container = QWidget()
                self._container.setObjectName(f"viewport_3d.view.{self.view_id}")
                layout = QVBoxLayout(self._container)
                layout.setContentsMargins(0, 0, 0, 0)
                layout.setSpacing(0)
                layout.addWidget(self._interactor)

        # After the block above, both are guaranteed to be set.
        assert self._interactor is not None  # noqa: S101
        assert self._renderer is not None  # noqa: S101

        # Clear previous actors (the input may have changed).
        self._renderer.RemoveAllViewProps()

        outline = vtkOutlineFilter()
        outline.SetInputData(vtk_image_data)
        outline.Update()

        mapper = vtkPolyDataMapper()
        mapper.SetInputConnection(outline.GetOutputPort())

        actor = vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(0.9, 0.9, 0.9)

        self._renderer.AddActor(actor)
        self._renderer.ResetCamera()
        self._interactor.GetRenderWindow().Render()  # type: ignore[no-untyped-call]
        self._interactor.Initialize()
        self._volume_set = True

    @property
    def has_volume(self) -> bool:
        return self._volume_set

    @property
    def renderer(self) -> vtkRenderer | None:
        return self._renderer

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
