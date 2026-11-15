"""AreaWidget.

Qt widget that materializes a single Area.

The Area is a pure domain model (no Qt). The AreaWidget is the
presentation layer for one Area: it renders the Editor Layout Tree
via the AreaLayoutRenderer (intra-Area layout) and a placeholder
when the Area is empty.

The AreaWidget is responsible for:

- The empty placeholder.
- Caching the content widgets so they can be detached before a
  rebuild (``_content_widgets``).
- The optional debug label and background.
- Scheduling the VTK first-frame render.

The AreaLayoutRenderer is responsible for:

- Materializing the Editor containers and their Toolbars.
- Building the QSplitter when there are multiple Editors.

Block 5.5: the AreaWidget exposes a dynamic property
``area_placement`` (values: ``"central"``, ``"left"``, ``"right"``,
``"bottom"``) consumed by the global QSS to paint the Area with the
correct background and rounded corners. The property is set in
``__init__`` before ``refresh()``; ``unpolish/polish`` is called to
force the QSS to match immediately.

Block 5.5: ``refresh()`` returns early when the Area model says it
is hidden. This prevents the placeholder label from appearing in an
Area that the Workspace has just hidden via ``set_area_visible``.

Block 5.5: the widget uses ``QSizePolicy.Expanding`` on both axes.
The parent QSplitter respects the policy when distributing space;
without it, the AreaWidget is limited to its ``sizeHint``, which
leaves the Central Area half-empty.

See ADR-0013 (Editor Layout Tree), ADR-0002 (Toolbars inside Editors).
"""

from __future__ import annotations

import logging

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import (
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from cranioz.ui.icons.provider import IconProvider
from cranioz.ui.theme.service import ThemeService
from cranioz.ui.tools.registry.tool_registry import ToolRegistry
from cranioz.ui.workspace.areas.area import Area
from cranioz.ui.workspace.areas.area_layout_renderer import AreaLayoutRenderer
from cranioz.ui.workspace.areas.placement import Placement

_logger = logging.getLogger(__name__)


class AreaWidget(QWidget):
    """Qt widget that materializes a single Area."""

    active_editor_changed = Signal(str, str)
    editor_close_requested = Signal(str, str)
    editor_add_requested = Signal(str)

    def __init__(
        self,
        area: Area,
        tool_registry: ToolRegistry,
        theme_service: ThemeService,
        *,
        icon_provider: IconProvider,
        debug_colors: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        # ADR-0013 §2.6: Toolbar materialization moved to the
        # ViewLayoutRenderer (View-level Toolbars) inside each Editor.
        # The AreaLayoutRenderer no longer materializes Toolbars and
        # no longer needs these services. The parameters are kept on
        # the signature for compatibility with LayoutRenderer; they
        # will be removed in Sprint H, when the LayoutRenderer is
        # updated to construct AreaWidget with only ``area`` +
        # ``debug_colors``.
        del tool_registry, theme_service, icon_provider

        self._area = area
        self._debug_colors = debug_colors
        self._content_widgets: dict[str, QWidget] = {}

        self._area_layout_renderer = AreaLayoutRenderer()

        self.setObjectName(f"area_widget.{area.area_id}")

        # Block 5.5: the AreaWidget must expand to fill the space the
        # LayoutRenderer gives it. Without Expanding, the parent
        # QSplitter gives the AreaWidget only its sizeHint, which
        # makes the Central Area half-empty (the grid inside it is
        # then squeezed).
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        # Block 5.5: expose the placement as a dynamic property so
        # the global QSS (QWidget[area_placement="..."]) can paint
        # the Area with the correct background and rounded corners.
        # The property MUST be set before WA_StyledBackground and
        # before refresh() so the QSS matches on the first paint.
        self.setProperty("area_placement", self._area.placement.value)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        # Force the QSS to apply now that the property is set. Without
        # this, the QSS set on the QApplication before this widget was
        # created does not match the property-based selector.
        self.style().unpolish(self)
        self.style().polish(self)

        self._root_layout = QVBoxLayout(self)
        self._root_layout.setContentsMargins(0, 0, 0, 0)
        self._root_layout.setSpacing(0)

        if debug_colors:
            self._apply_debug_background()

        self.refresh()

    # ----- Public API -----------------------------------------------

    @property
    def area_id(self) -> str:
        return self._area.area_id

    def area_placement(self) -> Placement:
        return self._area.placement

    def area(self) -> Area:
        """Return the Area this widget materializes."""
        return self._area

    def refresh(self) -> None:
        # Block 5.5: if the Area model says it is hidden, do not
        # render the placeholder or the content. The Workspace also
        # calls setVisible(False) on the widget, but refresh() may
        # run while the widget is still visible during a transition.
        if not self._area.visible:
            return

        # 1. Dispose the Editors' internal resources before rebuilding.
        for editor in self._area.editors():
            try:
                editor.dispose()
            except Exception:
                _logger.exception("Editor.dispose() failed for %r", editor.editor_id)

        # 2. Clear the layout (detach content widgets, delete containers).
        self._clear_layout()

        # 3. Build the empty placeholder if there are no Editors.
        if self._area.is_empty():
            self._root_layout.addWidget(self._build_empty_placeholder())
            # Re-polish after adding the placeholder, so the QSS
            # applies to the new child.
            self.style().unpolish(self)
            self.style().polish(self)
            return

        # 4. Optional debug label.
        if self._debug_colors:
            debug_label = QLabel(f"[{self._area.area_id}]")
            debug_label.setStyleSheet(
                "QLabel { background: rgba(255,255,255,200); font-weight: bold; padding: 2px; }"
            )
            self._root_layout.addWidget(debug_label)

        # 5. Delegate the intra-Area composition to the renderer.
        content = self._area_layout_renderer.render(self._area, self._content_widgets)
        self._root_layout.addWidget(content)

        # 6. Force VTK to render its first frame.
        QTimer.singleShot(0, self._force_vtk_render)
        QTimer.singleShot(100, self._force_vtk_render)

        # 7. Re-polish after the refresh, so the QSS applies to the
        # newly created children (the container, its labels, etc.).
        self.style().unpolish(self)
        self.style().polish(self)

    # ----- Internals ------------------------------------------------

    def _force_vtk_render(self) -> None:
        """Ask every QVTKRenderWindowInteractor under this Area to render."""
        found = 0
        for child in self.findChildren(QWidget):
            render_window = getattr(child, "GetRenderWindow", None)
            if render_window is None:
                continue
            found += 1
            try:
                rw = render_window()
                if rw is not None:
                    rw.Render()
            except Exception:
                _logger.exception("VTK first-frame render failed for %r", child)

        if found == 0:
            _logger.debug(
                "_force_vtk_render(%r): no QVTKRenderWindowInteractor found",
                self.area_id,
            )
        else:
            _logger.debug(
                "_force_vtk_render(%r): rendered %d interactor(s)",
                self.area_id,
                found,
            )

    def _apply_debug_background(self) -> None:
        palette = {
            Placement.LEFT: "#dbe9f4",
            Placement.CENTRAL: "#dff0d8",
            Placement.RIGHT: "#fcf3cf",
            Placement.BOTTOM: "#e8daef",
        }
        color = palette.get(self._area.placement)
        if color is None:
            return
        qcolor = QColor(color)
        pal = self.palette()
        pal.setColor(QPalette.ColorRole.Window, qcolor)
        self.setPalette(pal)
        self.setAutoFillBackground(True)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(f"QWidget#{self.objectName()} {{ background-color: {color}; }}")

    def _clear_layout(self) -> None:
        # 1. Detach every Editor's content_widget() from its container.
        for editor in self._area.editors():
            content = self._content_widgets.pop(editor.editor_id, None)
            if content is None:
                continue
            try:
                content.setParent(None)
            except RuntimeError:
                _logger.exception(
                    "content_widget for %r was already deleted; skipping detach",
                    editor.editor_id,
                )

        # 2. Clear the root layout.
        while self._root_layout.count():
            item = self._root_layout.takeAt(0)
            widget = item.widget() if item is not None else None
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()

    def _build_empty_placeholder(self) -> QWidget:
        label = QLabel(f"{self._area.title} (empty)")
        label.setObjectName(f"area_widget.{self._area.area_id}.placeholder")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Transparent so the Area background (via QSS) shows through.
        label.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        return label