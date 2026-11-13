"""View — a visual representation of an aspect of the Scene.

A View is hosted by an Editor. It is not an Editor itself. The
Editor coordinates its Views, manages its Toolbars, and handles
the user's interaction with the underlying data.

A View may declare its own Toolbars and Control Panels (ADR-0013
§2.6). Those are materialized around the View's content widget by
the ViewLayoutRenderer, and are typically visible only when the
View is active (ToolbarVisibilityMode.ACTIVE_ONLY).

See ADR-0013 §2.3, §2.6.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget

    from cranioz.ui.toolbars.specification import ToolbarSpec


class View(ABC):
    """A visual representation of an aspect of the Scene."""

    view_id: str
    view_type: str  # "axial", "coronal", "sagittal", "3d", "curved_mpr", ...

    def __init__(self, view_id: str, view_type: str) -> None:
        if not view_id:
            raise ValueError("view_id must not be empty")
        if not view_type:
            raise ValueError("view_type must not be empty")
        self.view_id = view_id
        self.view_type = view_type

    # ----- Content --------------------------------------------------

    @abstractmethod
    def content_widget(self) -> QWidget:
        """Return the widget that represents this View's content."""
        ...

    # ----- Toolbars (ADR-0013 §2.6) --------------------------------

    def toolbar_specs(self) -> list[ToolbarSpec]:
        """Return the Toolbars declared by this View.

        Empty by default. Views that own interaction tools override
        this method to declare them (typically with
        ``ToolbarVisibilityMode.ACTIVE_ONLY`` so that only the active
        View shows its tools).

        The declarations are materialized by the ViewLayoutRenderer
        around ``content_widget()``; the View does not create the
        Toolbar widgets itself.
        """
        return []

    def control_panel_specs(self) -> list[ToolbarSpec]:
        """Return the display Control Panels declared by this View.

        A Control Panel is a specialized Toolbar (same ToolbarSpec
        contract) used for display settings (window/level, LUT,
        visibility, ...). Empty by default.

        Semantically distinct from ``toolbar_specs()`` even though
        both use the same data type: the distinction is a UI
        convention, not an architectural one.
        """
        return []

    # ----- Activation ----------------------------------------------

    def activation_widget(self) -> QWidget:
        """Return the widget that receives activation events.

        The ViewLayoutRenderer installs an event filter on this
        widget to detect ``MouseButtonPress`` and ``FocusIn`` and
        forward them to ``Editor.set_active_view``. The default is
        ``content_widget()``, which is correct for Views whose
        content widget is the interactive surface.

        Views backed by a native ``QVTKRenderWindowInteractor`` MUST
        override this method to return the interactor. Qt delivers
        input events to the leaf widget under the cursor, so an
        event filter installed on the container would never fire
        for a click inside the VTK viewport.
        """
        return self.content_widget()

    # ----- Lifecycle ------------------------------------------------

    def dispose(self) -> None:
        """Release the View's resources. Idempotent."""
        return None
