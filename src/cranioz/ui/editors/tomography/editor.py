"""TomographyEditor — hosts the Axial, Coronal, Sagittal, and 3D Views.

The Editor coordinates the four Views of a tomography study in a 2x2
grid: Axial (top-left), Coronal (top-right), Sagittal (bottom-left),
and 3D (bottom-right). It also declares two Toolbars: one on the left
(image tools) and one on the right (visibility).

The Editor receives an ``EditorContext`` at ``initialize``. When a
``VolumeData`` is available in the ``DomainObjectStore`` (via
``context.domain_object_store``), the Editor resolves the first
``vtk_image_data`` and passes it to each View via ``set_volume``.

The "first" object is a placeholder: when the ``CommandExecutor``
publishes ``SceneObjectAdded`` events (ADR-0007), the Editor will
subscribe and react to specific volumes. Until then, the Editor
resolves on ``activate`` and ``content_widget``.

See ADR-0013, scene.md.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from PySide6.QtWidgets import QWidget

from cranioz.ui.editors.base_editor import Editor
from cranioz.ui.editors.editor_context import EditorContext
from cranioz.ui.editors.mpr_viewer.view import MPRView
from cranioz.ui.editors.view import View
from cranioz.ui.editors.view_layout_renderer import ViewLayoutRenderer
from cranioz.ui.editors.view_layout_spec import (
    SplitDirection,
    ViewLayoutSpec,
)
from cranioz.ui.editors.viewport_3d.view import Viewport3DView
from cranioz.ui.toolbars.specification import (
    ToolbarOrientation,
    ToolbarPosition,
    ToolbarSpec,
    ToolbarVisibilityMode,
)

if TYPE_CHECKING:
    from cranioz.domain.scene.domain_object_store import DomainObjectStore
    from cranioz.domain.scene.volume_data import VolumeData

_logger = logging.getLogger(__name__)


class TomographyEditor(Editor):
    """Hosts the 2x2 grid of MPR + 3D Views for tomography."""

    def __init__(
        self,
        editor_id: str = "editor.tomography",
        title: str = "Tomography",
    ) -> None:
        super().__init__(editor_id=editor_id, title=title)

        self._axial = MPRView(view_id="view.axial", view_type="axial")
        self._coronal = MPRView(view_id="view.coronal", view_type="coronal")
        self._sagittal = MPRView(view_id="view.sagittal", view_type="sagittal")
        self._viewport = Viewport3DView(view_id="view.3d")

        self._view_layout_renderer = ViewLayoutRenderer()
        self._content: QWidget | None = None
        self._context: EditorContext | None = None
        self._volume_applied = False

    # ----- Lifecycle -------------------------------------------------

    def initialize(self, context: EditorContext) -> None:
        self._context = context

    def activate(self) -> None:
        self._try_apply_volume()

    # ----- Views (ADR-0013) -----------------------------------------

    def views(self) -> tuple[View, ...]:
        return (self._axial, self._coronal, self._sagittal, self._viewport)

    def view_layout(self) -> ViewLayoutSpec:
        return ViewLayoutSpec.split(
            SplitDirection.VERTICAL,
            (
                ViewLayoutSpec.split(
                    SplitDirection.HORIZONTAL,
                    (
                        ViewLayoutSpec.leaf("view.axial"),
                        ViewLayoutSpec.leaf("view.coronal"),
                    ),
                ),
                ViewLayoutSpec.split(
                    SplitDirection.HORIZONTAL,
                    (
                        ViewLayoutSpec.leaf("view.sagittal"),
                        ViewLayoutSpec.leaf("view.3d"),
                    ),
                ),
            ),
        )

    # ----- Content --------------------------------------------------

    def content_widget(self) -> QWidget:
        if self._content is None:
            self._try_apply_volume()
            views_by_id: dict[str, View] = {v.view_id: v for v in self.views()}
            self._content = self._view_layout_renderer.render(
                self.view_layout(),
                views_by_id,
            )
        return self._content

    # ----- Toolbars --------------------------------------------------

    def toolbar_specs(self) -> list[ToolbarSpec]:
        return [
            ToolbarSpec(
                toolbar_id="toolbar.tomography.left",
                title="Image Tools",
                orientation=ToolbarOrientation.VERTICAL,
                position=ToolbarPosition.LEFT,
                tool_ids=("tool.log",),
                visibility_mode=ToolbarVisibilityMode.ALWAYS,
            ),
            ToolbarSpec(
                toolbar_id="toolbar.tomography.right",
                title="Visibility",
                orientation=ToolbarOrientation.VERTICAL,
                position=ToolbarPosition.RIGHT,
                tool_ids=("tool.toggle",),
                visibility_mode=ToolbarVisibilityMode.COLLAPSIBLE,
            ),
        ]

    # ----- Volume resolution ----------------------------------------

    def _try_apply_volume(self) -> None:
        """Resolve the first VolumeData from the DomainObjectStore and
        pass it to the Views. Idempotent.

        This is a placeholder for the real mechanism: when the
        CommandExecutor publishes ``SceneObjectAdded`` events
        (ADR-0007), the Editor will subscribe and react to specific
        volumes. Until then, the Editor resolves on first use.
        """
        if self._volume_applied:
            return
        context = self._context
        if context is None:
            return
        store = context.domain_object_store
        scene_query = context.scene_query
        if store is None or scene_query is None:
            return

        volume_data = self._resolve_first_volume(store, scene_query)
        if volume_data is None:
            return

        try:
            self._axial.set_volume(volume_data.vtk_image_data)
            self._coronal.set_volume(volume_data.vtk_image_data)
            self._sagittal.set_volume(volume_data.vtk_image_data)
            self._viewport.set_volume(volume_data.vtk_image_data)
        except RuntimeError:
            # VTK is not installed (e.g., in a CI test environment).
            # Leave the Views as empty containers.
            _logger.warning(
                "VTK is not available; MPRView and Viewport3DView will remain empty (view_id=%s)",
                self.editor_id,
            )
            return
        self._volume_applied = True

    @staticmethod
    def _resolve_first_volume(
        store: DomainObjectStore,
        scene_query: Any,
    ) -> VolumeData | None:
        """Resolve the first VolumeData from the DomainObjectStore."""
        from cranioz.domain.scene.volume_data import VolumeData  # noqa: PLC0415

        for object_id in scene_query.list_objects():
            if not store.contains(object_id):
                continue
            candidate = store.get(object_id)
            if isinstance(candidate, VolumeData):
                return candidate
        return None

    # ----- Volume preset ---------------------------------------------

    def set_volume_preset(self, name: str) -> None:
        """Change the 3D volume rendering preset."""
        self._viewport.set_preset(name)

    def reload_volume(self) -> None:
        """Re-resolve the first VolumeData and pass it to the Views.

        Called by ``Workspace.reload_volume()`` after a successful
        DICOM import (Passo 8e). Idempotent: if the volume is
        already applied and the store has not changed, it is a no-op
        (the ``_volume_applied`` flag is reset, but
        ``_try_apply_volume`` will only mark it True again if a
        VolumeData is found).
        """
        self._volume_applied = False
        self._try_apply_volume()

    # ----- Lifecycle (dispose) --------------------------------------

    def dispose(self) -> None:
        if self._content is None:
            return
        super().dispose()  # disposes each View
        self._view_layout_renderer.clear_cache()
        self._content.setParent(None)
        self._content.deleteLater()
        self._content = None
        self._context = None
        self._volume_applied = False
