"""TopOverlay.

The TopOverlay is the first concrete Overlay in CranioZ. It
materializes the "Painel Superior" (Top Bar) shown across the UI
prototype: a horizontal bar anchored to the top of the Central
Region, with a fixed height and small lateral margins.

Geometric behavior (this piece):

- Anchored to the top of the target Region.
- Fixed height.
- Fixed lateral and top margins.
- Width spans the Region minus the lateral margins.

Content behavior (future pieces):

- The three segments (left, center, right) described in the
  prototype are not built here. This piece provides a container
  widget with an accessible content layout so that the Workspace
  (or a dedicated TopBar composition) can populate it later
  without changing the TopOverlay contract.

Design rules:

- The TopOverlay computes its own geometry from the Region Bounds
  it receives in ``reposition()``. It does not receive a
  pre-computed position.
- The overlay_id and target_region are class-level constants. Every
  TopOverlay instance targets the Central Region and has the same
  identity.
- The widget is a plain QFrame. Styling (colors, borders) will be
  applied later through the ThemeService, via Qt stylesheets keyed
  by the object name.
- The TopOverlay never destroys its widget. It can be hidden and
  shown again; the widget instance remains the same.
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLayout,
    QWidget,
)

from cranioz.ui.workspace.areas.placement import Placement
from cranioz.ui.workspace.overlays.overlay import Overlay
from cranioz.ui.workspace.overlays.region import Bounds


class TopOverlayError(ValueError):
    """Raised when a TopOverlay is constructed with invalid parameters."""


class TopOverlay(Overlay):
    """Concrete Overlay implementing the Top Bar geometry.

    The TopOverlay is anchored to the top of the Central Region. Its
    height is fixed; its width follows the Region's width minus the
    configured lateral margins.
    """

    # ----- Class-level constants ------------------------------------

    OVERLAY_ID: str = "overlay.top_bar"
    TARGET_REGION: Placement = Placement.CENTRAL

    DEFAULT_HEIGHT: int = 40
    DEFAULT_MARGIN_X: int = 8
    DEFAULT_MARGIN_Y: int = 8

    # ----- Construction ---------------------------------------------

    def __init__(
        self,
        height: int = DEFAULT_HEIGHT,
        margin_x: int = DEFAULT_MARGIN_X,
        margin_y: int = DEFAULT_MARGIN_Y,
        parent: QWidget | None = None,
    ) -> None:
        if height <= 0:
            raise TopOverlayError(f"height must be positive, got {height}")
        if margin_x < 0:
            raise TopOverlayError(f"margin_x must be non-negative, got {margin_x}")
        if margin_y < 0:
            raise TopOverlayError(f"margin_y must be non-negative, got {margin_y}")

        self._height = height
        self._margin_x = margin_x
        self._margin_y = margin_y
        self._visible = True

        self._widget = QFrame(parent)
        self._widget.setObjectName("top_overlay")
        self._widget.setFixedHeight(height)

        # A horizontal layout is the natural container for the three
        # segments. The segments themselves are added by a future
        # piece; the layout is exposed via content_layout().
        self._layout = QHBoxLayout(self._widget)
        self._layout.setContentsMargins(4, 4, 4, 4)
        self._layout.setSpacing(4)

    # ----- Overlay API ----------------------------------------------

    @property
    def overlay_id(self) -> str:
        return self.OVERLAY_ID

    @property
    def target_region(self) -> Placement:
        return self.TARGET_REGION

    def widget(self) -> QWidget:
        return self._widget

    def reposition(self, bounds: Bounds) -> None:
        """Position the Top Bar over the given Region Bounds.

        The Top Bar is anchored to the top-left of the Region with
        the configured margins. Its width is the Region's width
        minus twice the lateral margin. If the resulting width
        would be negative (extremely narrow Region), it is clamped
        to zero so that Qt receives a valid geometry.
        """
        x = bounds.x + self._margin_x
        y = bounds.y + self._margin_y
        width = max(0, bounds.width - 2 * self._margin_x)
        height = self._height

        self._widget.setGeometry(
            round(x),
            round(y),
            round(width),
            round(height),
        )

    def set_visible(self, visible: bool) -> None:
        self._visible = visible
        self._widget.setVisible(visible)

    def is_visible(self) -> bool:
        return self._visible

    # ----- Convenience accessors ------------------------------------

    @property
    def height(self) -> int:
        """Return the fixed height of the Top Bar in pixels."""
        return self._height

    @property
    def margin_x(self) -> int:
        """Return the horizontal margin applied to the Top Bar."""
        return self._margin_x

    @property
    def margin_y(self) -> int:
        """Return the vertical margin applied to the Top Bar."""
        return self._margin_y

    def content_layout(self) -> QLayout:
        """Return the layout that will hold the Top Bar's content.

        Future pieces (the Workspace or a dedicated TopBar
        composition) add the left, center, and right segments to
        this layout. The TopOverlay itself does not create those
        segments: it only provides the container and its geometry.
        """
        return self._layout
