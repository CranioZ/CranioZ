"""Re-export EditorLayoutSpec from the canonical location."""

from cranioz.ui.workspace.areas.editor_layout_spec import (
    EditorLayoutSpec,
    EditorLayoutSpecError,
    EditorStackOrientation,
    LayoutType,
    SplitDirection,
)

__all__ = [
    "EditorLayoutSpec",
    "EditorLayoutSpecError",
    "EditorStackOrientation",
    "LayoutType",
    "SplitDirection",
]
