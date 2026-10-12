"""ToggleTool.

Minimal Tool with on/off state, used for tests and early integration.
The state is held by the Tool instance; the toolbar widget reads and
writes it via the Tool's methods.
"""

from __future__ import annotations

from cranioz.ui.tools.registry.tool_definition import ToolContext


class ToggleTool:
    """A Tool with on/off state."""

    identifier = "tool.toggle"
    label = "Toggle"
    description = "Toggles a state"
    icon: str | None = "toggle"
    category: str | None = None

    def __init__(self, checked: bool = False) -> None:
        self._checked = checked

    def is_available(self, context: ToolContext) -> bool:
        return bool(context.extras.get("available", True))

    def is_enabled(self, context: ToolContext) -> bool:
        return bool(context.extras.get("enabled", True))

    @property
    def checked(self) -> bool:
        return self._checked

    def toggle(self) -> bool:
        """Flip the state and return the new value."""
        self._checked = not self._checked
        return self._checked
