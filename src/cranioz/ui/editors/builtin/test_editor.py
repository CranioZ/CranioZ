"""DummyEditor.

A concrete Editor used for tests and early integration. It is not a
clinical Editor. Its purpose is to exercise the Editor contract, the
ToolbarSpec contract, and the EditorRegistry.

The Editor:
- declares a unique editor_id;
- returns a QLabel as its content widget;
- declares a ToolbarSpec with LogTool and ToggleTool;
- supports persistent_state / restore_state trivially.

This Editor does not touch the Scene, does not issue Commands, and
does not depend on any Module. It exists only to validate the UI
composition machinery.
"""

from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import QLabel, QWidget

from cranioz.ui.editors.base_editor import Editor
from cranioz.ui.editors.editor_context import EditorContext
from cranioz.ui.toolbars.specification import (
    ToolbarOrientation,
    ToolbarSpec,
)
from cranioz.ui.tools.registry.tool_definition import ToolContext


class DummyEditor(Editor):
    """A minimal concrete Editor for tests."""

    def __init__(
        self,
        editor_id: str = "editor.test",
        title: str = "Test Editor",
        toolbar_orientation: ToolbarOrientation = ToolbarOrientation.HORIZONTAL,
    ) -> None:
        super().__init__(editor_id=editor_id, title=title)
        self._toolbar_orientation = toolbar_orientation
        self._label: QLabel | None = None
        self._context: EditorContext | None = None
        self._tool_context = ToolContext()

    # ----- Lifecycle --------------------------------------------------

    def initialize(self, context: EditorContext) -> None:
        self._context = context

    # ----- Content ----------------------------------------------------

    def content_widget(self) -> QWidget:
        if self._label is None:
            self._label = QLabel(self.editor_id)
            self._label.setObjectName(f"dummy_editor.content.{self.editor_id}")
        return self._label

    def toolbar_specs(self) -> list[ToolbarSpec]:
        return [
            ToolbarSpec(
                toolbar_id=f"toolbar.{self.editor_id}",
                title=f"{self.title} Toolbar",
                orientation=self._toolbar_orientation,
                tool_ids=("tool.log", "tool.toggle"),
            )
        ]

    # ----- Persistence ------------------------------------------------

    def persistent_state(self) -> dict[str, Any]:
        if self._context is None:
            return {}
        return {
            "editor_id": self.editor_id,
            "extras": dict(self._context.extras),
        }

    def restore_state(self, state: dict[str, Any]) -> None:
        # DummyEditor does not keep mutable state to restore.
        return None

    # ----- Convenience for tests -------------------------------------

    def tool_context(self) -> ToolContext:
        return self._tool_context
