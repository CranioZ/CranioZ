"""TopOverlay.

The TopOverlay is the first concrete Overlay in CranioZ. It materializes
the "Painel Superior" (Top Bar) as a structural component of the Workspace,
positioned by the OverlayManager over the Central Region.

Geometric behavior:
- Anchored to the top of the target Region.
- Fixed height.
- Fixed lateral and top margins.
- Width spans the Region minus the lateral margins (dynamic).
- Minimum width = the sum of the three segments' sizeHints (dynamic).
  This prevents the Top Bar from being squeezed below the point where
  its segments overlap.

Structural behavior:
- Contains three segments: Left, Center, Right.
- Each segment has a QHBoxLayout, ready to receive content.
- The Center segment is always horizontally centered within the Top Bar.
- The Left and Right segments are anchored to their respective edges.
- Content is injected by the MainWindow via set_left_content /
  set_center_content / set_right_content. The TopOverlay does not
  know what the injected widgets do (ADR-0006).

Design rules:
- The TopOverlay computes its own geometry from the Region Bounds
  it receives in ``reposition()``. It does not receive a
  pre-computed position.
- The overlay_id and target_region are class-level constants.
- The widget is a plain QFrame. Styling (colors, borders, translucency)
  is NOT applied here. The ThemeService (future) will be responsible
  for the visual presentation.
- The TopOverlay never destroys its widget. It can be hidden and
  shown again; the widget instance remains the same.

Block 5.5: minimum_width() is dynamic. The Workspace queries it
before applying splitter sizes so the Central Area cannot be
squeezed below the Top Bar's real minimum. The minimum changes as
the ModulesSegment gains or loses modules.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
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
    """Concrete Overlay implementing the Top Bar geometry and structure."""

    # ----- Class-level constants ------------------------------------

    OVERLAY_ID: str = "overlay.top_bar"
    TARGET_REGION: Placement = Placement.CENTRAL

    DEFAULT_HEIGHT: int = 40
    DEFAULT_MARGIN_X: int = 8
    DEFAULT_MARGIN_Y: int = 8

    #: Internal margins and spacing of the segment layout (used by
    #: minimum_width()). Kept as class constants so the calculation
    #: stays in sync with __init__.
    _LAYOUT_MARGIN: int = 4
    _LAYOUT_SPACING: int = 4

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

        # The root layout contains the three segments.
        # The Center segment is centered by inserting stretches
        # before and after it.
        self._layout = QHBoxLayout(self._widget)
        self._layout.setContentsMargins(
            self._LAYOUT_MARGIN,
            self._LAYOUT_MARGIN,
            self._LAYOUT_MARGIN,
            self._LAYOUT_MARGIN,
        )
        self._layout.setSpacing(self._LAYOUT_SPACING)
        self._layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self._left_segment = QWidget()
        self._left_segment.setObjectName("top_overlay.left_segment")
        self._left_layout = QHBoxLayout(self._left_segment)
        self._left_layout.setContentsMargins(0, 0, 0, 0)
        self._left_layout.setSpacing(4)

        self._center_segment = QWidget()
        self._center_segment.setObjectName("top_overlay.center_segment")
        self._center_layout = QHBoxLayout(self._center_segment)
        self._center_layout.setContentsMargins(0, 0, 0, 0)
        self._center_layout.setSpacing(4)

        self._right_segment = QWidget()
        self._right_segment.setObjectName("top_overlay.right_segment")
        self._right_layout = QHBoxLayout(self._right_segment)
        self._right_layout.setContentsMargins(0, 0, 0, 0)
        self._right_layout.setSpacing(4)

        # The center segment is guaranteed to be centered by
        # inserting equal stretches on both sides.
        self._layout.addWidget(
            self._left_segment, alignment=Qt.AlignmentFlag.AlignLeft
        )
        self._layout.addStretch(1)
        self._layout.addWidget(
            self._center_segment, alignment=Qt.AlignmentFlag.AlignCenter
        )
        self._layout.addStretch(1)
        self._layout.addWidget(
            self._right_segment, alignment=Qt.AlignmentFlag.AlignRight
        )

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
        minus twice the lateral margin, but never less than
        ``minimum_width()``. If the Region is narrower than the
        Top Bar's minimum, the Top Bar overflows the Region (the
        Workspace is responsible for preventing that by keeping the
        Central Area wide enough; see ``Workspace._apply_default_splitter_sizes``).
        """
        min_width = self.minimum_width()
        x = bounds.x + self._margin_x
        y = bounds.y + self._margin_y
        width = max(0, bounds.width - 2 * self._margin_x)
        width = max(width, min_width)
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

    # ----- Minimum width (Block 5.5) --------------------------------

    def minimum_width(self) -> int:
        """Return the minimum width required by the three segments.

        Home and Extras have fixed, predictable widths (3 buttons
        each). Modules has variable width depending on the active
        workflow (number of modules). This method sums the three
        segments' sizeHints plus the TopOverlay's internal layout
        margins and spacings.

        Called by the Workspace before applying splitter sizes, so
        the Central Area cannot be squeezed below the Top Bar's
        real minimum. The value changes when the ModulesSegment
        gains or loses modules.
        """
        return (
            self._LAYOUT_MARGIN * 2
            + self._LAYOUT_SPACING * 2
            + self._left_segment.sizeHint().width()
            + self._center_segment.sizeHint().width()
            + self._right_segment.sizeHint().width()
        )

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

    # ----- Segment accessors ----------------------------------------

    def left_segment(self) -> QWidget:
        """Return the container for the Left segment."""
        return self._left_segment

    def center_segment(self) -> QWidget:
        """Return the container for the Center segment."""
        return self._center_segment

    def right_segment(self) -> QWidget:
        """Return the container for the Right segment."""
        return self._right_segment

    # ----- Content injection ----------------------------------------

    def set_left_content(self, widget: QWidget | None) -> None:
        """Inject content into the Left segment."""
        _replace_content(self._left_layout, widget)

    def set_center_content(self, widget: QWidget | None) -> None:
        """Inject content into the Center segment."""
        _replace_content(self._center_layout, widget)

    def set_right_content(self, widget: QWidget | None) -> None:
        """Inject content into the Right segment."""
        _replace_content(self._right_layout, widget)

    # ----- Content layout -------------------------------------------

    def content_layout(self) -> QLayout:
        """Return the QLayout that arranges the three segments."""
        return self._layout


# ----- Internals ----------------------------------------------------


def _replace_content(layout: QHBoxLayout, widget: QWidget | None) -> None:
    """Remove any existing children from the layout and add the widget."""
    while layout.count():
        item = layout.takeAt(0)
        existing = item.widget() if item is not None else None
        if existing is not None:
            existing.setParent(None)
            existing.deleteLater()
    if widget is not None:
        layout.addWidget(widget)