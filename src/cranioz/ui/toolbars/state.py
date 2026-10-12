"""ToolbarState.

Runtime visibility state of a Toolbar.

A ToolbarSpec declares *how* a Toolbar should behave (its visibility
policy). A ToolbarState records *whether* it is currently visible.

State is per-instance, per-session. It may be persisted via
Editor.persistent_state() when the policy is COLLAPSIBLE.
"""

from __future__ import annotations

from dataclasses import dataclass

from cranioz.ui.toolbars.specification import ToolbarVisibilityMode


class ToolbarStateError(ValueError):
    """Raised when a ToolbarState violates structural rules."""


@dataclass
class ToolbarState:
    """Runtime state of a Toolbar instance."""

    toolbar_id: str
    visible: bool = True

    @classmethod
    def initial_for(
        cls,
        toolbar_id: str,
        mode: ToolbarVisibilityMode,
    ) -> ToolbarState:
        """Return the initial state for a given toolbar and visibility mode."""
        if mode is ToolbarVisibilityMode.ALWAYS or mode is ToolbarVisibilityMode.COLLAPSIBLE:
            visible = True
        elif mode is ToolbarVisibilityMode.AUTO_HIDE or mode is ToolbarVisibilityMode.HIDDEN:
            visible = False
        else:
            raise ToolbarStateError(f"unknown visibility mode: {mode!r}")
        return cls(toolbar_id=toolbar_id, visible=visible)
