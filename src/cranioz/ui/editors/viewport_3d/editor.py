"""Viewport3DEditor — 3D viewport with VTK rendering.

The editor materializes a QVTKRenderWindowInteractor as its content
widget. It uses the VTKSceneRenderer to display the Scene.

The editor does NOT own the Scene. It receives a SceneQuery via
EditorContext and observes changes.

VTK (and its Qt integration) is an optional dependency. The import
is deferred to ``content_widget()`` so that the application can boot
without VTK installed; the error is raised only when the viewport is
actually materialized.

See editors.md §12, scene.md §50.
"""

from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import QWidget

from cranioz.ui.editors.base_editor import Editor
from cranioz.ui.editors.editor_context import EditorContext


class Viewport3DEditor(Editor):
    """3D viewport with VTK rendering."""

    def __init__(
        self,
        editor_id: str = "editor.viewport_3d",
        title: str = "3D Viewport",
    ) -> None:
        super().__init__(editor_id=editor_id, title=title)
        self._content: QWidget | None = None
        self._context: EditorContext | None = None
        self._renderer: Any = None

    def initialize(self, context: EditorContext) -> None:
        self._context = context

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
            self._content.setObjectName(f"viewport_3d.content.{self.editor_id}")
            # Placeholder: initialize a VTK renderer.
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
