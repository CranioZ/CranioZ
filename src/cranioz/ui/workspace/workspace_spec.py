"""WorkspaceSpec — predefined ModuleUISpec values.

Provides the spec used when a project is opened without an active
Flow (Bloco 9 not implemented yet). The Workspace still materializes
a minimal composition: a single Central Area with a placeholder
Editor that explains that no flow is loaded.

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
    It does not declare any Toolbar (it is a placeholder, not an
    editor with tools) and it does not know what a Flow is.

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


DEFAULT: ModuleUISpec = ModuleUISpec(
    areas=(
        AreaSpec(
            area_id="area.central",
            title="Workspace",
            placement=Placement.CENTRAL,
            editor_layout=EditorLayoutSpec.leaf("editor.placeholder.no_flow"),
        ),
    ),
)

PLACEHOLDER_EDITOR_ID = "editor.placeholder.no_flow"
PLACEHOLDER_EDITOR_CLASS = _PlaceholderEditor
