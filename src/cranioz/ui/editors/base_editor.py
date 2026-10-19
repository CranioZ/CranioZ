"""Editor ABC.

An Editor is a functional unit hosted by an Area. It provides a specific
interaction experience. It does not know where it is placed; the Area
hosts it.

This module defines the contract only. Concrete Editors may use Qt for
materialization, but the contract itself has no Qt dependency.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from cranioz.ui.tools.registry.tool_definition import ToolContext

if TYPE_CHECKING:
    from cranioz.ui.editors.editor_context import EditorContext
    from cranioz.ui.toolbars.specification import ToolbarSpec


class Editor(ABC):
    """Abstract Editor contract."""

    editor_id: str
    title: str

    def __init__(self, editor_id: str, title: str) -> None:
        self.editor_id = editor_id
        self.title = title

    # Lifecycle -----------------------------------------------------

    def initialize(self, context: EditorContext) -> None:
        """Called once at insertion. Heavy resources are set up here."""
        return None

    def activate(self) -> None:
        """Called when the Editor becomes the active one in its Area."""
        return None

    def deactivate(self) -> None:
        """Called when the Editor stops being active. Must not dispose."""
        return None

    def dispose(self) -> None:
        """Called when the Editor is removed and its resources released."""
        return None

    # Content -------------------------------------------------------

    @abstractmethod
    def content_widget(self) -> Any:
        """Return the widget that represents the Editor's content."""
        raise NotImplementedError

    def toolbar_specs(self) -> list[ToolbarSpec]:
        """Declare the Editor's internal Toolbars. Empty by default."""
        return []

    def tool_context(self) -> ToolContext:
        """Return the ToolContext used to materialize this Editor's Toolbars.

        The Editor owns its ToolContext; the AreaWidget and the Toolbar
        widget only consume it. Editors that need a richer context
        (selection, scene query, command dispatcher) override this method
        and return an instance with the appropriate services.

        The default implementation returns an empty ``ToolContext``,
        which is correct for Editors that declare no Toolbar or whose
        Tools are context-independent.
        """
        return ToolContext()

    # Persistence ---------------------------------------------------

    def persistent_state(self) -> dict[str, Any]:
        """Return the Editor's persistable presentation state."""
        return {}

    def restore_state(self, state: dict[str, Any]) -> None:
        """Restore a previously saved presentation state."""
        return None
