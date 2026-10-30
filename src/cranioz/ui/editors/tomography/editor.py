"""TomographyEditor — hosts the Axial, Coronal, Sagittal, and 3D Views.

This Editor coordinates the four Views of a tomography study in a
2x2 grid: Axial (top-left), Coronal (top-right), Sagittal
(bottom-left), and 3D (bottom-right). It also declares two Toolbars:
one on the left (image tools) and one on the right (visibility).

Per ADR-0013, the Views are internal to the Editor. The Editor
organizes them in a View Layout Tree, and the LayoutRenderer
materializes it as nested QSplitters.

The TomographyEditor does not own the Scene. It reads the Scene
through SceneQuery (read-only) and dispatches Commands through
CommandDispatcher. Both will be provided via EditorContext in a
future piece.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from cranioz.ui.editors.base_editor import Editor
from cranioz.ui.editors.mpr_viewer.view import MPRView
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

        self._content: QWidget | None = None

    # ----- Views (ADR-0013) -----------------------------------------

    def views(self) -> tuple[MPRView | Viewport3DView, ...]:
        """Return the four Views hosted by this Editor."""
        return (self._axial, self._coronal, self._sagittal, self._viewport)

    def view_layout(self) -> ViewLayoutSpec:
        """Return the 2x2 grid layout of the Views."""
        return ViewLayoutSpec.split(
            SplitDirection.HORIZONTAL,
            (
                ViewLayoutSpec.leaf("view.axial"),
                ViewLayoutSpec.split(
                    SplitDirection.VERTICAL,
                    (
                        ViewLayoutSpec.leaf("view.coronal"),
                        ViewLayoutSpec.split(
                            SplitDirection.HORIZONTAL,
                            (
                                ViewLayoutSpec.leaf("view.sagittal"),
                                ViewLayoutSpec.leaf("view.3d"),
                            ),
                        ),
                    ),
                ),
            ),
        )

    # ----- Content --------------------------------------------------

    def content_widget(self) -> QWidget:
        """Return the container that arranges the Views. (...)"""
        if self._content is None:
            self._content = QWidget()
            layout = QVBoxLayout(self._content)
            layout.setContentsMargins(8, 8, 8, 8)

            label = QLabel(
                f"TomographyEditor\n\n"
                f"Views:\n"
                f"  - {self._axial.view_id} ({self._axial.view_type})\n"
                f"  - {self._coronal.view_id} ({self._coronal.view_type})\n"
                f"  - {self._sagittal.view_id} ({self._sagittal.view_type})\n"
                f"  - {self._viewport.view_id} ({self._viewport.view_type})\n\n"
                f"(2x2 grid will be materialized by the LayoutRenderer)"
            )
            label.setObjectName(f"tomography.editor.{self.editor_id}.placeholder")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet(
                "QLabel { background-color: #2a2a2a; color: #eee; font-size: 14px; padding: 24px; }"
            )
            layout.addWidget(label)
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
        """Dispose the Views and the content widget."""
        super().dispose()
        if self._content is not None:
            self._content.setParent(None)
            self._content.deleteLater()
            self._content = None
