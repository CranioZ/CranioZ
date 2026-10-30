"""ToolbarSpec.

Declarative description of a Toolbar inside an Editor.

A Toolbar is internal to an Editor; the Workspace never hosts one.
The same Tool may be referenced by multiple Toolbars across Editors.

Two concepts are separated here:

- ToolbarSpec describes *what* a Toolbar is: identity, orientation,
  position, tools, and its presentation policy.
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


class ToolbarPosition(Enum):
    """Position of a Toolbar inside an Editor (ADR-0013 §2.6).

    The position determines where the Toolbar is rendered relative
    to the Editor's View Layout Tree. A Toolbar with position LEFT
    is rendered on the left side of the Views; a Toolbar with
    position RIGHT is rendered on the right side, and so on.

    Orientation and position are orthogonal:

    - A VERTICAL Toolbar is typically LEFT or RIGHT.
    - A HORIZONTAL Toolbar is typically TOP or BOTTOM.

    The LayoutRenderer materializes the Toolbar at the requested
    position. If the position is incompatible with the orientation
    (e.g., a HORIZONTAL Toolbar on the LEFT), the renderer may
    still render it, but the result is visually awkward.
    """

    TOP = "top"
    BOTTOM = "bottom"
    LEFT = "left"
    RIGHT = "right"


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
    position: ToolbarPosition = ToolbarPosition.TOP
    tool_ids: tuple[str, ...] = field(default_factory=tuple)
    visibility_mode: ToolbarVisibilityMode = ToolbarVisibilityMode.ALWAYS

    def __post_init__(self) -> None:
        if not self.toolbar_id:
            raise ToolbarSpecError("toolbar_id must not be empty")
        if not self.title:
            raise ToolbarSpecError("title must not be empty")

        # Consistency check: a VERTICAL Toolbar should not be TOP or
        # BOTTOM (it would be visually awkward). We do not raise an
        # error to preserve backward compatibility, but we document
        # the expected pairing in the enum docstring.
        #
        # If strict enforcement is desired in the future, uncomment:
        #
        # if self.orientation is ToolbarOrientation.VERTICAL and self.position in (
        #     ToolbarPosition.TOP, ToolbarPosition.BOTTOM
        # ):
        #     raise ToolbarSpecError(
        #         "a VERTICAL Toolbar must be positioned LEFT or RIGHT"
        #     )
        # if self.orientation is ToolbarOrientation.HORIZONTAL and self.position in (
        #     ToolbarPosition.LEFT, ToolbarPosition.RIGHT
        # ):
        #     raise ToolbarSpecError(
        #         "a HORIZONTAL Toolbar must be positioned TOP or BOTTOM"
        #     )
