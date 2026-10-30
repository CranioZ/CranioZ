"""View — a visual representation of an aspect of the Scene.

A View is hosted by an Editor. It is not an Editor itself. The
Editor coordinates its Views, manages its Toolbars, and handles
the user's interaction with the underlying data.

Examples of Views:
- AxialView, CoronalView, SagittalView (2D MPR views)
- Viewport3DView (3D view)
- CurvedMPRView (panoramic reconstruction)

The View does NOT own the Scene. It reads the Scene through
SceneQuery (read-only).

See ADR-0013 §2.3.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget


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

    @abstractmethod
    def content_widget(self) -> QWidget:
        """Return the widget that represents this View's content."""
        ...

    def dispose(self) -> None:
        """Release the View's resources. Idempotent."""
        return None
