"""ToolbarItem types.

Declarative description of the individual elements that compose a
Toolbar. Items are data; the Toolbar widget materializes them.

Distinct from ToolbarSpec, which describes the Toolbar as a whole
(identity, orientation, tools, visibility policy). ToolbarItem
describes a single element inside the Toolbar.

Rules:
- An item must have a unique identity within its Toolbar.
- The types are frozen; item data does not change at runtime.
- The widget state (enabled, visible) is not part of the item; it
  belongs to the Toolbar widget and to the Tool's availability.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ToolbarItemKind(Enum):
    """Kind of Toolbar item."""

    ACTION = "action"
    TOGGLE = "toggle"
    SEPARATOR = "separator"


@dataclass(frozen=True)
class ActionItem:
    """A Toolbar item that triggers a single action.

    The action is identified by `tool_id`, resolved by the Toolbar
    widget against the ToolRegistry at materialization time.
    """

    tool_id: str
    label: str
    icon: str | None = None

    @property
    def kind(self) -> ToolbarItemKind:
        return ToolbarItemKind.ACTION

    def __post_init__(self) -> None:
        if not self.tool_id:
            raise ValueError("ActionItem requires a tool_id")
        if not self.label:
            raise ValueError("ActionItem requires a label")


@dataclass(frozen=True)
class ToggleItem:
    """A Toolbar item whose state is on/off.

    The initial state is `checked`. The Toolbar widget manages the
    current state; the item declares the initial value.
    """

    tool_id: str
    label: str
    icon: str | None = None
    checked: bool = False

    @property
    def kind(self) -> ToolbarItemKind:
        return ToolbarItemKind.TOGGLE

    def __post_init__(self) -> None:
        if not self.tool_id:
            raise ValueError("ToggleItem requires a tool_id")
        if not self.label:
            raise ValueError("ToggleItem requires a label")


@dataclass(frozen=True)
class Separator:
    """A visual separator between groups of items.

    Separators carry no identity and no action.
    """

    @property
    def kind(self) -> ToolbarItemKind:
        return ToolbarItemKind.SEPARATOR
