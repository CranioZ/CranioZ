"""Viewport3DView — a 3D view of the Scene.

This is a View, not an Editor. It is hosted by an Editor (e.g.,
TomographyEditor) that coordinates it with other Views (Axial,
Coronal, Sagittal).
"""

from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import QWidget

from cranioz.ui.editors.view import View


class Viewport3DView(View):
    """A 3D view of the Scene."""

    def __init__(self, view_id: str = "view.viewport_3d") -> None:
        super().__init__(view_id=view_id, view_type="3d")
        self._content: QWidget | None = None
        self._renderer: Any = None

    def content_widget(self) -> QWidget:
        if self._content is None:
            try:
                from vtkmodules.qt.QVTKRenderWindowInteractor import (  # noqa: PLC0415
                    QVTKRenderWindowInteractor,
                )
            except ImportError as exc:
                raise RuntimeError(
                    "VTK Qt integration is not installed. Install it with 'pip install vtk'."
                ) from exc
            self._content = QVTKRenderWindowInteractor()  # type: ignore[no-untyped-call]
            self._content.setObjectName(f"viewport_3d.view.{self.view_id}")
            from cranioz.infrastructure.rendering.vtk_scene_renderer import (  # noqa: PLC0415
                VTKSceneRenderer,
            )

            self._renderer = VTKSceneRenderer()
            self._content.GetRenderWindow().AddRenderer(  # type: ignore[no-untyped-call]
                self._renderer.renderer
            )
        return self._content

    def dispose(self) -> None:
        if self._renderer is not None:
            self._renderer.detach_scene()
            self._renderer = None
        if self._content is not None:
            self._content.setParent(None)
            self._content.deleteLater()
            self._content = None
