"""Editor ABC.

An Editor is a functional unit hosted by an Area. It provides a specific
interaction experience. It does not know where it is placed; the Area
hosts it.

An Editor may host one or more Views (Axial, Coronal, Sagittal, 3D, ...).
Views are internal to the Editor and are organized in a View Layout Tree
(ADR-0013). The Editor coordinates its Views, manages its Toolbars, and
handles the user's interaction with the underlying data.

This module defines the contract only. Concrete Editors may use Qt for
materialization, but the contract itself has no Qt dependency.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from cranioz.ui.tools.registry.tool_definition import ToolContext

if TYPE_CHECKING:
    from cranioz.ui.editors.editor_context import EditorContext
    from cranioz.ui.editors.view import View
    from cranioz.ui.editors.view_layout_spec import ViewLayoutSpec
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
        """Called when the Editor is removed and its resources released.

        Disposes every View hosted by this Editor, then the Editor's
        own resources. Concrete Editors that override this method must
        call ``super().dispose()`` to ensure the Views are disposed.
        """
        for view in self.views():
            view.dispose()

    # Content -------------------------------------------------------

    @abstractmethod
    def content_widget(self) -> Any:
        """Return the widget that represents the Editor's content.

        When the Editor hosts Views, the content widget is the
        container that arranges the Views according to
        ``view_layout()``. When the Editor has no Views, the content
        widget is the Editor's own widget (e.g., a Properties panel,
        a Console, etc.).
        """
        raise NotImplementedError

    # Views (ADR-0013) ----------------------------------------------

    def views(self) -> tuple[View, ...]:
        """Return the Views hosted by this Editor.

        Empty by default. Editors that host Views (e.g., the
        TomographyEditor) override this method to return them in the
        order they appear in the layout.

        The Editor owns the Views. It is responsible for disposing
        them (see ``dispose()``).
        """
        return ()

    def view_layout(self) -> ViewLayoutSpec | None:
        """Return the layout of the Views, or None for a single View.

        The layout is a ``ViewLayoutSpec`` (nested split tree), the
        same N-ary model used for the Area Layout Tree and the
        Editor Layout Tree. The LayoutRenderer materializes it.

        Editors with zero or one View return None; the single View
        (if any) occupies the whole content area.
        """
        return None

    # Toolbars ------------------------------------------------------

    def toolbar_specs(self) -> list[ToolbarSpec]:
        """Declare the Editor's internal Toolbars. Empty by default.

        Each ToolbarSpec declares its orientation (HORIZONTAL or
        VERTICAL) and its position (LEFT, RIGHT, TOP, BOTTOM) inside
        the Editor. See ADR-0013 §2.6.
        """
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
