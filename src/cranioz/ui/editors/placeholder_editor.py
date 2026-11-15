"""PlaceholderEditor.

A minimal Editor used when no real Editor is available for an Area.
Renders a centered QLabel explaining that the Area is a placeholder.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QWidget

from cranioz.infrastructure.i18n import tr
from cranioz.ui.editors.base_editor import Editor
from cranioz.ui.editors.editor_context import EditorContext


class PlaceholderEditor(Editor):
    """A minimal Editor used by WorkspaceSpec.DEFAULT for the
    lateral and bottom Areas (Left, Right, Bottom).
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
