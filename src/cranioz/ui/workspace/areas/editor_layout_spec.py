"""EditorLayoutSpec.

Declarative description of how Editors are organized inside a single Area.

The same N-ary split model as the Area Layout Tree.

Sprint H adds an optional `stacked` flag to SPLIT nodes. When True,
the renderer materializes the node as an EditorStack (tabs) instead
of a QSplitter. When False (default), the node is rendered as a
QSplitter. This preserves the existing tree behavior while
introducing the EditorStack capability without forcing a breaking
change on existing specs.

Rules:
- LEAF must have a non-empty (non-whitespace) editor_id and no children.
- SPLIT must have a direction and at least two children, and no editor_id.
- A SPLIT node may declare `stacked=True` to use an EditorStack.
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


class EditorStackOrientation(Enum):
    """Orientation of the EditorStack switcher (where the buttons sit)."""

    TOP = "top"
    BOTTOM = "bottom"
    LEFT = "left"
    RIGHT = "right"


class EditorLayoutSpecError(ValueError):
    """Raised when an EditorLayoutSpec violates structural rules."""


@dataclass(frozen=True)
class EditorLayoutSpec:
    """Declarative description of an Editor Layout Tree node."""

    type: LayoutType
    direction: SplitDirection | None = None
    children: tuple[EditorLayoutSpec, ...] = field(default_factory=tuple)
    editor_id: str | None = None
    # Sprint H: if True, a SPLIT node is rendered as an EditorStack.
    stacked: bool = False
    # Sprint H: Orientation of the stack switcher (only used if stacked=True).
    orientation: EditorStackOrientation | None = None

    def __post_init__(self) -> None:
        # Normalize children to a tuple to prevent mutability leaks.
        # (The annotation says tuple, but callers may pass a list at runtime.)
        object.__setattr__(self, "children", tuple(self.children))

        # Normalize editor_id by stripping whitespace.
        if self.editor_id is not None:
            object.__setattr__(self, "editor_id", self.editor_id.strip())

        self._validate()

    def _validate(self) -> None:
        if self.type is LayoutType.LEAF:
            self._validate_leaf()
        elif self.type is LayoutType.SPLIT:
            self._validate_split()
        else:
            raise EditorLayoutSpecError(f"unknown layout type: {self.type!r}")

    def _validate_leaf(self) -> None:
        if not self.editor_id:
            raise EditorLayoutSpecError("LEAF must declare a non-empty editor_id")
        if self.children:
            raise EditorLayoutSpecError("LEAF must not have children")
        if self.direction is not None:
            raise EditorLayoutSpecError("LEAF must not declare direction")
        if self.stacked:
            raise EditorLayoutSpecError("LEAF must not declare stacked")
        if self.orientation is not None:
            raise EditorLayoutSpecError("LEAF must not declare orientation")

    def _validate_split(self) -> None:
        if self.editor_id is not None:
            raise EditorLayoutSpecError("SPLIT must not declare editor_id")
        if self.direction is None:
            raise EditorLayoutSpecError("SPLIT must declare direction")
        if len(self.children) < 2:
            raise EditorLayoutSpecError("SPLIT must have at least two children")
        if self.stacked and self.orientation is None:
            raise EditorLayoutSpecError(
                "A stacked SPLIT must declare an orientation. "
                "Use EditorLayoutSpec.stack(...) to get a default."
            )
        if not self.stacked and self.orientation is not None:
            raise EditorLayoutSpecError("A non-stacked SPLIT must not declare an orientation.")

    # ----- Constructors ---------------------------------------------

    @classmethod
    def leaf(cls, editor_id: str) -> EditorLayoutSpec:
        """Create a LEAF node for the given editor_id."""
        return cls(type=LayoutType.LEAF, editor_id=editor_id)

    @classmethod
    def split(
        cls,
        direction: SplitDirection,
        children: tuple[EditorLayoutSpec, ...],
    ) -> EditorLayoutSpec:
        """Create a SPLIT node with the given direction and children."""
        return cls(type=LayoutType.SPLIT, direction=direction, children=children)

    @classmethod
    def stack(
        cls,
        children: tuple[EditorLayoutSpec, ...],
        *,
        direction: SplitDirection = SplitDirection.HORIZONTAL,
        orientation: EditorStackOrientation | None = None,
    ) -> EditorLayoutSpec:
        """Create a STACK node (EditorStack) with the given children.

        If `orientation` is not provided, it is inferred from `direction`:
        - HORIZONTAL -> BOTTOM (row of buttons).
        - VERTICAL -> LEFT (column of buttons).
        """
        if orientation is None:
            orientation = (
                EditorStackOrientation.BOTTOM
                if direction is SplitDirection.HORIZONTAL
                else EditorStackOrientation.LEFT
            )
        return cls(
            type=LayoutType.SPLIT,
            direction=direction,
            children=children,
            stacked=True,
            orientation=orientation,
        )
