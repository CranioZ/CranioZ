"""TomographyEditor — hosts the Axial, Coronal, Sagittal, and 3D Views.

This Editor coordinates the four Views of a tomography study in a
2x2 grid: Axial (top-left), Coronal (top-right), Sagittal
(bottom-left), and 3D (bottom-right). It also declares two Toolbars:
one on the left (image tools) and one on the right (visibility).

Per ADR-0013, the Views are internal to the Editor. The Editor
organizes them in a View Layout Tree, and the ViewLayoutRenderer
materializes it as nested QSplitters.

The TomographyEditor does not own the Scene. It reads the Scene
through SceneQuery (read-only) and dispatches Commands through
CommandDispatcher. Both will be provided via EditorContext in a
future piece.
"""

from __future__ import annotations

from PySide6.QtWidgets import QWidget

from cranioz.ui.editors.base_editor import Editor
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

    # ----- Views (ADR-0013) -----------------------------------------

    def views(self) -> tuple[View, ...]:
        """Return the four Views hosted by this Editor."""
        return (self._axial, self._coronal, self._sagittal, self._viewport)

    def view_layout(self) -> ViewLayoutSpec:
        """Return the 2x2 grid layout of the Views.

        Conventional 2x2 grid:
            ┌───────────────┬───────────────┐
            │               │               │
            │     Axial     │    Coronal    │
            │               │               │
            ├───────────────┼───────────────┤
            │               │               │
            │   Sagittal    │      3D       │
            │               │               │
            └───────────────┴───────────────┘
        """
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
        """Return the container that materializes the 4 Views as a 2x2 grid.

        The ViewLayoutRenderer materializes the View Layout Tree as
        nested QSplitters. Each Leaf becomes the View's content widget.
        """
        if self._content is None:
            views_by_id: dict[str, View] = {v.view_id: v for v in self.views()}
            self._content = self._view_layout_renderer.render(
                self.view_layout(),
                views_by_id,
            )
        return self._content

    # ----- Toolbars (ADR-0013) --------------------------------------

    def toolbar_specs(self) -> list[ToolbarSpec]:
        """Declare the two Toolbars of the TomographyEditor. (...)"""
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

    # ----- Lifecycle ------------------------------------------------

    def dispose(self) -> None:
        if self._content is None:
            return  # idempotent
        super().dispose()  # disposes each View
        self._view_layout_renderer.clear_cache()
        self._content.setParent(None)
        self._content.deleteLater()
        self._content = None
