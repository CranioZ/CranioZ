"""ViewLayoutSpec — declarative layout of Views inside an Editor.

Uses the same N-ary split tree model as the Area Layout Tree and
the Editor Layout Tree.

See ADR-0013 §2.4.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ViewLayoutType(Enum):
    LEAF = "leaf"
    SPLIT = "split"


class SplitDirection(Enum):
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"


class ViewLayoutSpecError(ValueError):
    """Raised when a ViewLayoutSpec violates structural rules."""


@dataclass(frozen=True)
class ViewLayoutSpec:
    """Declarative layout of Views inside an Editor."""

    type: ViewLayoutType
    direction: SplitDirection | None = None
    children: tuple[ViewLayoutSpec, ...] = field(default_factory=tuple)
    view_id: str | None = None

    def __post_init__(self) -> None:
        self._validate()

    def _validate(self) -> None:
        if self.type is ViewLayoutType.LEAF:
            if not self.view_id:
                raise ViewLayoutSpecError("LEAF must declare view_id")
            if self.children:
                raise ViewLayoutSpecError("LEAF must not have children")
            if self.direction is not None:
                raise ViewLayoutSpecError("LEAF must not declare direction")
        elif self.type is ViewLayoutType.SPLIT:
            if self.view_id is not None:
                raise ViewLayoutSpecError("SPLIT must not declare view_id")
            if self.direction is None:
                raise ViewLayoutSpecError("SPLIT must declare direction")
            if len(self.children) < 2:
                raise ViewLayoutSpecError("SPLIT must have at least two children")
        else:
            raise ViewLayoutSpecError(f"unknown layout type: {self.type!r}")

    @classmethod
    def leaf(cls, view_id: str) -> ViewLayoutSpec:
        return cls(type=ViewLayoutType.LEAF, view_id=view_id)

    @classmethod
    def split(
        cls,
        direction: SplitDirection,
        children: tuple[ViewLayoutSpec, ...],
    ) -> ViewLayoutSpec:
        return cls(type=ViewLayoutType.SPLIT, direction=direction, children=children)
