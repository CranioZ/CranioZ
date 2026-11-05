"""WorkspaceSpec — predefined ModuleUISpec values.

Provides the spec used when a project is opened without an active
Flow (Bloco 9 not implemented yet). The Workspace materializes a
minimal composition: the four Areas the prototype declares (Left,
Central, Right, Bottom), each hosting the placeholder Editor. Left,
Right and Bottom start hidden (see ``Workspace.load_spec``); the
user toggles them from the Top Bar.

When Bloco 9 delivers the Flow Catalog, the Workspace will receive
the Flow's ModuleUISpec instead. WorkspaceSpec.DEFAULT is the
fallback for the current phase.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QWidget

from cranioz.ui.editors.base_editor import Editor
from cranioz.ui.workspace.areas.placement import Placement
from cranioz.ui.workspace.specs.area_spec import AreaSpec
from cranioz.ui.workspace.specs.editor_layout_spec import EditorLayoutSpec
from cranioz.ui.workspace.specs.module_ui_spec import ModuleUISpec


class _PlaceholderEditor(Editor):
    """A minimal Editor used only by WorkspaceSpec.DEFAULT.

    Renders a centered QLabel explaining that no flow is loaded.
    It does not declare any Toolbar and it does not know what a Flow
    is.

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
            title="No flow loaded",
        )
        self._label: QLabel | None = None

    def content_widget(self) -> QWidget:
        if self._label is None:
            self._label = QLabel("No flow loaded — select a flow on the Home Page and click Start.")
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
            title="Central",
            placement=Placement.CENTRAL,
            editor_layout=EditorLayoutSpec.leaf(PLACEHOLDER_EDITOR_ID),
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

#: Debug-only spec: a single Central Area hosting the MeshDebugEditor.
#:
#: Used when ``CRANIOZ_DEBUG_MESH=1`` is set. It bypasses the default
#: placeholder Editor so that ``Workspace.find_viewport_3d`` finds a
#: ``Viewport3DView`` for STL validation. Not used in production.
#:
#: The MeshDebugEditor is registered in the EditorRegistry by the
#: MainWindow when the environment variable is set.
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
