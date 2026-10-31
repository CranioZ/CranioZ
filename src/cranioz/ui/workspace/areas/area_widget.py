"""AreaWidget.

Qt widget that materializes a single Area.

The Area is a pure domain model (no Qt). The AreaWidget is the
presentation layer for one Area: it renders the Editor Layout Tree
as nested QSplitters (ADR-0013), with each Editor's Toolbars inside
the Editor (ADR-0002), and a placeholder when the Area is empty.

Per ADR-0013, the default organization is the split tree, not tabs.
The Editor Layout Tree is rendered as QSplitters: each Split becomes
a QSplitter, each Leaf becomes the Editor widget.
"""

from __future__ import annotations

import logging

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from cranioz.ui.editors.base_editor import Editor
from cranioz.ui.theme.service import ThemeService
from cranioz.ui.toolbars.base import Toolbar
from cranioz.ui.toolbars.specification import ToolbarPosition
from cranioz.ui.tools.registry.tool_registry import ToolRegistry
from cranioz.ui.workspace.areas.area import Area
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
        debug_colors: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._area = area
        self._tool_registry = tool_registry
        self._theme_service = theme_service
        self._debug_colors = debug_colors
        self._content_widgets: dict[str, QWidget] = {}

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

    def refresh(self) -> None:
        # 1. Dispose the Editors' internal resources before rebuilding.
        #    This is critical for Editors that hold Qt widgets internally
        #    (e.g., TomographyEditor with its View Layout Tree). Without
        #    this, the old widgets leak and stack on top of the new ones.
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
        if getattr(self, "_debug_colors", False):
            debug_label = QLabel(f"[{self._area.area_id}]")
            debug_label.setStyleSheet(
                "QLabel { background: rgba(255,255,255,200); font-weight: bold; padding: 2px; }"
            )
            self._root_layout.addWidget(debug_label)

        # 5. Build the Editor Layout Tree.
        editors = self._area.editors()
        if len(editors) == 1:
            # Single editor: render directly, no splitter needed.
            self._root_layout.addWidget(self._build_editor_widget(editors[0]))
            return

        # Multiple editors: build a QSplitter (Editor Layout Tree).
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setObjectName(f"area_widget.{self._area.area_id}.splitter")
        splitter.setChildrenCollapsible(False)
        for editor in editors:
            splitter.addWidget(self._build_editor_widget(editor))
        self._root_layout.addWidget(splitter)

    # ----- Internals ------------------------------------------------

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
        """Remove widgets from the layout without destroying Editor content."""
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
        return label

    def _build_editor_widget(self, editor: Editor) -> QWidget:
        """Build the widget for a single Editor (Toolbars + Content).

        The Editor's content_widget() is self-contained (e.g., the
        TomographyEditor returns a QSplitter with its 4 Views). The
        AreaWidget only wraps it with the Editor's Toolbars, according
        to their declared position (LEFT, RIGHT, TOP, BOTTOM).

        Toolbars are given a fixed size policy so they are not stretched
        or collapsed by the layout. A VERTICAL Toolbar (LEFT/RIGHT) is
        fixed in width; a HORIZONTAL Toolbar (TOP/BOTTOM) is fixed in
        height.
        """
        container = QWidget()
        container.setObjectName(f"area_widget.{self._area.area_id}.editor.{editor.editor_id}")

        # Group Toolbars by position.
        toolbars_by_position: dict[ToolbarPosition, list[Toolbar]] = {
            ToolbarPosition.TOP: [],
            ToolbarPosition.BOTTOM: [],
            ToolbarPosition.LEFT: [],
            ToolbarPosition.RIGHT: [],
        }
        for toolbar in self._build_toolbars(editor):
            toolbars_by_position[toolbar.spec.position].append(toolbar)

        # Outer layout: [LEFT] [inner] [RIGHT]
        outer = QHBoxLayout(container)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        for toolbar in toolbars_by_position[ToolbarPosition.LEFT]:
            # A VERTICAL Toolbar on the LEFT is fixed in width.
            toolbar.setSizePolicy(
                QSizePolicy.Policy.Fixed,
                QSizePolicy.Policy.Expanding,
            )
            outer.addWidget(toolbar, stretch=0)

        # Inner layout: [TOP] [content] [BOTTOM]
        inner = QWidget(container)
        inner_layout = QVBoxLayout(inner)
        inner_layout.setContentsMargins(0, 0, 0, 0)
        inner_layout.setSpacing(0)

        for toolbar in toolbars_by_position[ToolbarPosition.TOP]:
            # A HORIZONTAL Toolbar on the TOP is fixed in height.
            toolbar.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Fixed,
            )
            inner_layout.addWidget(toolbar, stretch=0)

        content = editor.content_widget()
        self._content_widgets[editor.editor_id] = content
        content.setParent(inner)
        inner_layout.addWidget(content, stretch=1)

        for toolbar in toolbars_by_position[ToolbarPosition.BOTTOM]:
            # A HORIZONTAL Toolbar on the BOTTOM is fixed in height.
            toolbar.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Fixed,
            )
            inner_layout.addWidget(toolbar, stretch=0)

        outer.addWidget(inner, stretch=1)

        for toolbar in toolbars_by_position[ToolbarPosition.RIGHT]:
            # A VERTICAL Toolbar on the RIGHT is fixed in width.
            toolbar.setSizePolicy(
                QSizePolicy.Policy.Fixed,
                QSizePolicy.Policy.Expanding,
            )
            outer.addWidget(toolbar, stretch=0)

        return container

    def _build_toolbars(self, editor: Editor) -> list[Toolbar]:
        context = editor.tool_context()
        result: list[Toolbar] = []
        for spec in editor.toolbar_specs():
            toolbar = Toolbar(
                spec=spec,
                registry=self._tool_registry,
                theme=self._theme_service,
                context=context,
            )
            result.append(toolbar)
        return result
