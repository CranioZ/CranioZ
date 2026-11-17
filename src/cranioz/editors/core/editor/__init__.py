"""Editor contracts and registry."""

from cranioz.editors.core.editor.base_editor import Editor
from cranioz.editors.core.editor.editor_context import EditorContext
from cranioz.editors.core.editor.editor_registry import EditorRegistry
from cranioz.editors.core.editor.placeholder_editor import (
    PLACEHOLDER_EDITOR_ID,
    PlaceholderEditor,
)

__all__ = [
    "PLACEHOLDER_EDITOR_ID",
    "Editor",
    "EditorContext",
    "EditorRegistry",
    "PlaceholderEditor",
]
