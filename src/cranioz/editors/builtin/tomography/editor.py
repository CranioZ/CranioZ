"""TomographyEditor — hosts the Axial, Coronal, Sagittal, and 3D Views.

The Editor coordinates the four Views of a tomography study in a 2x2
grid: Axial (top-left), Coronal (top-right), Sagittal (bottom-left),
and 3D (bottom-right).

The Editor receives an ``EditorContext`` at ``initialize``. When a
``Volume`` is available in the ``DomainObjectStore`` (via
``context.domain_object_store``), the Editor resolves it and passes it
to each View via ``set_volume``. The Views convert the ``Volume`` to
``vtkImageData`` via ``VtkImageAdapter`` internally.

The "first" object is a placeholder: when the ``CommandExecutor``
publishes ``SceneObjectAdded`` events (ADR-0007), the Editor will
subscribe and react to specific volumes. Until then, the Editor
resolves on ``activate`` and ``content_widget``.

Block 5.5 note: Editor-level Toolbars are temporarily disabled to
reduce visual noise in the prototype. ``toolbar_specs()`` returns
an empty list, so ``_wrap_with_editor_toolbars()`` short-circuits
and returns the View grid unchanged. The Toolbar wiring is kept
intact in the codebase; re-enabling them is a one-line change
(return the specs list instead of ``[]``).

See ADR-0013, scene.md, Medical Imaging Infrastructure §3.2.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from PySide6.QtWidgets import QHBoxLayout, QSizePolicy, QWidget

from cranioz.domain.imaging.volume import Volume
from cranioz.editors.core.editor.base_editor import Editor
from cranioz.editors.core.editor.editor_context import EditorContext
from cranioz.editors.core.view.view import View
from cranioz.editors.core.view.view_layout_renderer import ViewLayoutRenderer
from cranioz.editors.core.view.view_layout_spec import (
    SplitDirection,
    ViewLayoutSpec,
)
from cranioz.editors.views.mpr_viewer.view import MPRView
from cranioz.editors.views.viewport_3d.view import Viewport3DView
from cranioz.ui.toolbars.base import Toolbar
from cranioz.ui.toolbars.specification import (
    ToolbarPosition,
    ToolbarSpec,
)

if TYPE_CHECKING:
    from cranioz.domain.scene.domain_object_store import DomainObjectStore

_logger = logging.getLogger(__name__)


class TomographyEditor(Editor):
    """Tomography Editor with a 2x2 grid."""

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

        self._view_layout_renderer: ViewLayoutRenderer | None = None
        self._content: QWidget | None = None
        self._context: EditorContext | None = None
        self._volume_applied = False
        self._editor_toolbars: list[Toolbar] = []

    # ----- Lifecycle -------------------------------------------------

    def initialize(self, context: EditorContext) -> None:
        self._context = context

    def _ensure_renderer(self) -> ViewLayoutRenderer:
        if self._view_layout_renderer is not None:
            return self._view_layout_renderer
        ctx = self._context
        if ctx is None:
            raise RuntimeError(
                "TomographyEditor.initialize() must be called before content_widget()"
            )
        if ctx.tool_registry is None or ctx.theme_service is None or ctx.icon_provider is None:
            raise RuntimeError(
                "TomographyEditor requires tool_registry, theme_service and "
                "icon_provider in its EditorContext (ADR-0013 §2.6)."
            )
        self._view_layout_renderer = ViewLayoutRenderer(
            tool_registry=ctx.tool_registry,
            theme_service=ctx.theme_service,
            icon_provider=ctx.icon_provider,
            editor=self,
        )
        return self._view_layout_renderer

    def _tr(self, key: str, source: str) -> str:
        ctx = self._context
        if ctx is None or ctx.translation_service is None:
            return source
        return ctx.translation_service.tr(key, source)

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
            renderer = self._ensure_renderer()
            views_widget = renderer.render(
                self.view_layout(),
                views_by_id,
            )
            self._content = self._wrap_with_editor_toolbars(views_widget)
        return self._content

    def _wrap_with_editor_toolbars(self, views_widget: QWidget) -> QWidget:
        """Wrap the View grid with the Editor's own Toolbars.

        Block 5.5: short-circuits when ``toolbar_specs()`` returns
        an empty list. This is the current behavior: the Editor's
        Toolbars are disabled to reduce visual noise in the
        prototype.
        """
        specs = self.toolbar_specs()
        if not specs:
            return views_widget

        # Original implementation (kept for future re-enabling):
        ctx = self._context
        if (
            ctx is None
            or ctx.tool_registry is None
            or ctx.theme_service is None
            or ctx.icon_provider is None
        ):
            _logger.warning(
                "TomographyEditor cannot materialize Editor-level Toolbars: "
                "EditorContext is missing tool_registry, theme_service, or "
                "icon_provider (ADR-0013 §2.6)."
            )
            return views_widget

        container = QWidget()
        container.setObjectName(f"editor_container.{self.editor_id}")
        container.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        outer = QHBoxLayout(container)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        by_position: dict[ToolbarPosition, list[Toolbar]] = {
            ToolbarPosition.LEFT: [],
            ToolbarPosition.RIGHT: [],
            ToolbarPosition.TOP: [],
            ToolbarPosition.BOTTOM: [],
        }
        for spec in specs:
            toolbar = Toolbar(
                spec=spec,
                registry=ctx.tool_registry,
                theme=ctx.theme_service,
                icon_provider=ctx.icon_provider,
                parent=container,
            )
            by_position[spec.position].append(toolbar)
            self._editor_toolbars.append(toolbar)

        for toolbar in by_position[ToolbarPosition.LEFT]:
            toolbar.setSizePolicy(
                QSizePolicy.Policy.Preferred,
                QSizePolicy.Policy.Expanding,
            )
            toolbar.setMinimumWidth(0)
            toolbar.setMaximumWidth(96)
            outer.addWidget(toolbar, stretch=0)

        outer.addWidget(views_widget, stretch=1)

        for toolbar in by_position[ToolbarPosition.RIGHT]:
            toolbar.setSizePolicy(
                QSizePolicy.Policy.Preferred,
                QSizePolicy.Policy.Expanding,
            )
            toolbar.setMinimumWidth(0)
            toolbar.setMaximumWidth(96)
            outer.addWidget(toolbar, stretch=0)

        return container

    # ----- Toolbars --------------------------------------------------

    def toolbar_specs(self) -> list[ToolbarSpec]:
        """Return the Editor-level Toolbar specs.

        Block 5.5: temporarily returns an empty list to remove the
        visual noise of the Log and Toggle buttons in the prototype.
        The original specs (image tools + visibility) are kept as a
        comment below so re-enabling them later is a copy-paste
        change.
        """
        return []

        # Original specs (uncomment to re-enable):
        # return [
        #     ToolbarSpec(
        #         toolbar_id="toolbar.tomography.left",
        #         title=self._tr("tomography.toolbar.image_tools", "Image Tools"),
        #         orientation=ToolbarOrientation.VERTICAL,
        #         position=ToolbarPosition.LEFT,
        #         tool_ids=("tool.log",),
        #         visibility_mode=ToolbarVisibilityMode.ALWAYS,
        #     ),
        #     ToolbarSpec(
        #         toolbar_id="toolbar.tomography.right",
        #         title=self._tr("tomography.toolbar.visibility", "Visibility"),
        #         orientation=ToolbarOrientation.VERTICAL,
        #         position=ToolbarPosition.RIGHT,
        #         tool_ids=("tool.toggle",),
        #         visibility_mode=ToolbarVisibilityMode.COLLAPSIBLE,
        #     ),
        # ]

    # ----- Volume resolution ----------------------------------------

    def _try_apply_volume(self) -> None:
        if self._volume_applied:
            return
        context = self._context
        if context is None:
            return
        store = context.domain_object_store
        scene_query = context.scene_query
        if store is None or scene_query is None:
            return

        volume = self._resolve_first_volume(store, scene_query)
        if volume is None:
            return

        try:
            self._axial.set_volume(volume)
            self._coronal.set_volume(volume)
            self._sagittal.set_volume(volume)
            self._viewport.set_volume(volume)
        except RuntimeError:
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
    ) -> Volume | None:
        for object_id in scene_query.list_objects():
            if not store.contains(object_id):
                continue
            candidate = store.get(object_id)
            if isinstance(candidate, Volume):
                return candidate
        return None

    # ----- Volume preset ---------------------------------------------

    def set_volume_preset(self, name: str) -> None:
        self._viewport.set_preset(name)

    def reload_volume(self) -> None:
        self._volume_applied = False
        self._try_apply_volume()

    # ----- Lifecycle (dispose) --------------------------------------

    def dispose(self) -> None:
        if self._content is None:
            return
        super().dispose()
        renderer = self._view_layout_renderer
        if renderer is not None:
            renderer.clear_cache()
        self._editor_toolbars.clear()
        self._content.setParent(None)
        self._content.deleteLater()
        self._content = None
        self._view_layout_renderer = None
        self._context = None
        self._volume_applied = False
