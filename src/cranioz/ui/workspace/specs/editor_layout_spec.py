"""EditorLayoutSpec.

Declarative description of how Editors are organized inside a single Area.

The same N-ary split model as the Area Layout Tree.

Rules:
- LEAF must have an editor_id and no children.
- SPLIT must have a direction and at least two children, and no editor_id.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class LayoutType(Enum):
    """Type of node in an Editor Layout Tree."""

    LEAF = "leaf"
    SPLIT = "split"


class SplitDirection(Enum):
    """Direction of a split node."""

    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"


class EditorLayoutSpecError(ValueError):
    """Raised when an EditorLayoutSpec violates structural rules."""


@dataclass(frozen=True)
class EditorLayoutSpec:
    """Declarative description of an Editor Layout Tree node."""

    type: LayoutType
    direction: SplitDirection | None = None
    children: tuple["EditorLayoutSpec", ...] = field(default_factory=tuple)
    editor_id: str | None = None

    def __post_init__(self) -> None:
        self._validate()

    def _validate(self) -> None:
        if self.type is LayoutType.LEAF:
            if not self.editor_id:
                raise EditorLayoutSpecError("LEAF must declare editor_id")
            if self.children:
                raise EditorLayoutSpecError("LEAF must not have children")
            if self.direction is not None:
                raise EditorLayoutSpecError("LEAF must not declare direction")
        elif self.type is LayoutType.SPLIT:
            if self.editor_id is not None:
                raise EditorLayoutSpecError("SPLIT must not declare editor_id")
            if self.direction is None:
                raise EditorLayoutSpecError("SPLIT must declare direction")
            if len(self.children) < 2:
                raise EditorLayoutSpecError(
                    "SPLIT must have at least two children"
                )
        else:
            raise EditorLayoutSpecError(
                f"unknown layout type: {self.type!r}"
            )

    @classmethod
    def leaf(cls, editor_id: str) -> "EditorLayoutSpec":
        """Create a LEAF node for the given editor_id."""
        return cls(type=LayoutType.LEAF, editor_id=editor_id)

    @classmethod
    def split(
        cls,
        direction: SplitDirection,
        children: tuple["EditorLayoutSpec", ...],
    ) -> "EditorLayoutSpec":
        """Create a SPLIT node with the given direction and children."""
        return cls(type=LayoutType.SPLIT, direction=direction, children=children)