"""ToolbarSpec.

Declarative description of a Toolbar inside an Editor.

A Toolbar is internal to an Editor; the Workspace never hosts one.
The same Tool may be referenced by multiple Toolbars across Editors.

Two concepts are separated here:

- ToolbarSpec describes *what* a Toolbar is: identity, orientation,
  tools, and its presentation policy.
- ToolbarState (see state.py) describes *whether* a Toolbar is
  currently visible. It is runtime state, not declarative.

Presentation policy is declarative and does not change at runtime.
Runtime visibility is state and does change at runtime.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ToolbarOrientation(Enum):
    """Orientation of a Toolbar."""

    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"


class ToolbarVisibilityMode(Enum):
    """Presentation policy for a Toolbar.

    ALWAYS
        Always visible. The user cannot hide it.

    COLLAPSIBLE
        Visible by default. The user may collapse or expand it
        manually. The preference is persisted across sessions.

    AUTO_HIDE
        Hidden by default. The Editor reveals it when the mouse
        approaches its edge zone (hover-reveal). It hides again
        when the mouse leaves the zone. The user does not toggle
        it manually.

    HIDDEN
        Not visible by default. It can only be revealed by an
        explicit action (a menu, a shortcut, a command).
    """

    ALWAYS = "always"
    COLLAPSIBLE = "collapsible"
    AUTO_HIDE = "auto_hide"
    HIDDEN = "hidden"


class ToolbarSpecError(ValueError):
    """Raised when a ToolbarSpec violates structural rules."""


@dataclass(frozen=True)
class ToolbarSpec:
    """Declarative description of a Toolbar."""

    toolbar_id: str
    title: str
    orientation: ToolbarOrientation = ToolbarOrientation.HORIZONTAL
    tool_ids: tuple[str, ...] = field(default_factory=tuple)
    visibility_mode: ToolbarVisibilityMode = ToolbarVisibilityMode.ALWAYS

    def __post_init__(self) -> None:
        if not self.toolbar_id:
            raise ToolbarSpecError("toolbar_id must not be empty")
        if not self.title:
            raise ToolbarSpecError("title must not be empty")