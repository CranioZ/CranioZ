"""WorkspaceSpec — predefined ModuleUISpec values.

Provides the spec used when a project is opened without an active
Flow (Bloco 9 not implemented yet). The Central Area hosts the
TomographyEditor (axial, coronal, sagittal, 3D Views). The lateral
Areas are declared but hidden by default; the user toggles them
from the Top Bar. When Bloco 9 delivers the Flow Catalog, the
Workspace will receive the Flow's ModuleUISpec instead.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QWidget

from cranioz.infrastructure.i18n import tr
from cranioz.ui.editors.base_editor import Editor
from cranioz.ui.editors.editor_context import EditorContext
from cranioz.ui.workspace.areas.placement import Placement
from cranioz.ui.workspace.specs.area_spec import AreaSpec
from cranioz.ui.workspace.specs.editor_layout_spec import EditorLayoutSpec
from cranioz.ui.workspace.specs.module_ui_spec import ModuleUISpec


class _PlaceholderEditor(Editor):
    """A minimal Editor used only by WorkspaceSpec.DEFAULT for the
    lateral and bottom Areas (Left, Right, Bottom).

    Renders a centered QLabel explaining that the Area is a
    placeholder until a Flow or a real Editor claims it. It does not
    declare any Toolbar and it does not know what a Flow is.

    The LayoutBuilder creates Editors by calling
    ``registry.create(editor_id, editor_id=..., title=...)``. This
    subclass accepts those keyword arguments to satisfy the builder's
    calling convention and ignores them: the placeholder uses its own
    fixed ``editor_id`` and ``title`` so that the message is stable
    regardless of how the builder names the instance.
    """

    def __init__(
        self,
        editor_id: str | None = None,
        title: str | None = None,
        **kwargs: object,
    ) -> None:
        del editor_id, title, kwargs  # intentionally ignored
        super().__init__(
            editor_id="editor.placeholder.no_flow",
            title="Placeholder",
        )
        self._label: QLabel | None = None
        self._context: EditorContext | None = None

    def initialize(self, context: EditorContext) -> None:
        self._context = context

    def _tr(self, key: str, source: str) -> str:
        ctx = self._context
        if ctx is not None and ctx.translation_service is not None:
            return ctx.translation_service.tr(key, source)
        return tr(key, source)

    def content_widget(self) -> QWidget:
        if self._label is None:
            self._label = QLabel(
                self._tr(
                    "workspace.placeholder.no_flow",
                    "No editor loaded — select a module from the Top Bar.",
                )
            )
            self._label.setObjectName("workspace.placeholder.label")
            self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._label.setStyleSheet(
                "QLabel#workspace\\_placeholder\\_label {"
                "  color: #888;"
                "  font-size: 16px;"
                "  padding: 24px;"
                "}"
            )
        return self._label


PLACEHOLDER_EDITOR_ID = "editor.placeholder.no_flow"
PLACEHOLDER_EDITOR_CLASS = _PlaceholderEditor


DEFAULT: ModuleUISpec = ModuleUISpec(
    areas=(
        AreaSpec(
            area_id="area.left",
            title="Left",
            placement=Placement.LEFT,
            editor_layout=EditorLayoutSpec.leaf(PLACEHOLDER_EDITOR_ID),
        ),
        AreaSpec(
            area_id="area.central",
            title="Tomography",
            placement=Placement.CENTRAL,
            editor_layout=EditorLayoutSpec.leaf("editor.tomography"),
        ),
        AreaSpec(
            area_id="area.right",
            title="Right",
            placement=Placement.RIGHT,
            editor_layout=EditorLayoutSpec.leaf(PLACEHOLDER_EDITOR_ID),
        ),
        AreaSpec(
            area_id="area.bottom",
            title="Bottom",
            placement=Placement.BOTTOM,
            editor_layout=EditorLayoutSpec.leaf(PLACEHOLDER_EDITOR_ID),
        ),
    ),
)


DEBUG_MESH: ModuleUISpec = ModuleUISpec(
    areas=(
        AreaSpec(
            area_id="area.central",
            title="Mesh Debug",
            placement=Placement.CENTRAL,
            editor_layout=EditorLayoutSpec.leaf("editor.mesh_debug"),
        ),
    ),
)
