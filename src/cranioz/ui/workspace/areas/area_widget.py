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

See ADR-0013 (Editor Layout Tree), ADR-0002 (Toolbars inside Editors).
"""

from __future__ import annotations

import logging

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import (
    QLabel,
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
        #    The Editor owns the content_widget() and reuses it across
        #    refreshes (e.g. DummyEditor caches its QLabel, the
        #    TomographyEditor caches its QSplitter). If we let Qt delete
        #    the content_widget() together with its parent container, the
        #    Editor's cached reference becomes a dangling pointer and the
        #    next content_widget() call returns an already-deleted object.
        #    Detaching (setParent(None)) is enough: the container is
        #    destroyed, the Editor's content survives.
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
        return label
