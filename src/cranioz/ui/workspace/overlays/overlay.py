"""Overlay.

An Overlay is a floating layer managed by the Workspace. It is
positioned over a Region, not over an individual Area. The Overlay
does not participate in the layout tree; it floats above the Areas.

The distinction matters (see workspace_pt.md §7.1):

- An Area is part of the layout tree; it is arranged by the
  LayoutRenderer into QSplitters.
- An Overlay is a separate widget that the Workspace places over a
  Region. It is not hosted by any Area. It can be shown, hidden,
  moved, and resized without touching the layout tree.

The Overlay ABC defines the minimal contract the Workspace needs to
manage a floating layer:

- A stable identity (``overlay_id``).
- A target Region, identified by its ``Placement``.
- Access to the Qt widget that represents the Overlay.
- Ability to reposition the widget when the Region's Bounds change.
- Ability to show / hide the widget.

Concrete Overlays (e.g. the Top Bar, the Steps Panel) live in their
own modules and implement this contract. The Workspace only knows
the ABC.

Qt dependency:

- ``Overlay.widget()`` returns a ``QWidget``, so concrete Overlays
  must import PySide6. That is expected: an Overlay is a visual
  layer. The ABC itself imports ``QWidget`` only for typing; it does
  not instantiate Qt objects.
- The ABC is still safe to import without a QApplication, as long
  as no concrete Overlay is instantiated. Tests that instantiate a
  concrete Overlay use ``qtbot`` and a running QApplication.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from cranioz.ui.workspace.areas.placement import Placement
from cranioz.ui.workspace.overlays.region import Bounds

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget


class OverlayError(ValueError):
    """Raised when an Overlay operation violates a structural rule."""


class Overlay(ABC):
    """Abstract base class for a floating layer managed by the Workspace.

    An Overlay is identified by a stable ``overlay_id`` and targets
    a Region identified by its ``Placement``. The Workspace uses the
    target to decide where to place the Overlay as the layout changes.
    """

    # ----- Identity --------------------------------------------------

    @property
    @abstractmethod
    def overlay_id(self) -> str:
        """Return the stable identifier of this Overlay.

        The identifier must be unique within a Workspace. It is
        used by the OverlayManager to register and retrieve the
        Overlay, and by other components to reference it.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def target_region(self) -> Placement:
        """Return the Placement of the Region this Overlay targets.

        The Workspace positions the Overlay over the Region whose
        ``semantic_role`` matches this Placement. If the Region does
        not exist (e.g. no Area has that Placement), the Overlay is
        not shown.
        """
        raise NotImplementedError

    # ----- Widget ----------------------------------------------------

    @abstractmethod
    def widget(self) -> QWidget:
        """Return the Qt widget that represents this Overlay.

        The Overlay owns the widget. The Workspace does not create,
        destroy, or reparent it. The widget is used as-is by the
        OverlayManager when it positions the Overlay on the screen.

        The method is allowed to return the same instance on every
        call. The Overlay is responsible for managing the widget's
        lifecycle (creation, configuration, disposal).
        """
        raise NotImplementedError

    # ----- Geometry --------------------------------------------------

    @abstractmethod
    def reposition(self, bounds: Bounds) -> None:
        """Reposition the Overlay to the given Bounds.

        The Workspace calls this method whenever the target Region's
        geometry changes (window resize, layout switch, Region
        recomputation). The Overlay applies its own anchoring rules
        within the given Bounds: for example, an Overlay anchored to
        the top of the Region positions itself at ``bounds.y``,
        while an Overlay anchored to the bottom positions itself at
        ``bounds.y + bounds.height - overlay_height``.

        The method must not change the Overlay's identity or target.
        It only adjusts the widget's position and size.
        """
        raise NotImplementedError

    # ----- Visibility ------------------------------------------------

    @abstractmethod
    def set_visible(self, visible: bool) -> None:
        """Show or hide the Overlay.

        Hiding an Overlay does not destroy its widget and does not
        remove it from the OverlayManager. The Overlay remains
        registered; it is simply not shown on screen.
        """
        raise NotImplementedError

    @abstractmethod
    def is_visible(self) -> bool:
        """Return True if the Overlay is currently visible."""
        raise NotImplementedError
