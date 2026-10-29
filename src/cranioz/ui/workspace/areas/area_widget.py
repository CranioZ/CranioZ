"""AreaWidget.

Qt widget that materializes a single Area.

The Area is a pure domain model (no Qt). The AreaWidget is the
presentation layer for one Area: it renders the Editor's Toolbars,
the Editor's content widget, tabs (when there are multiple Editors),
and a placeholder (when the Area is empty).
"""

from __future__ import annotations

import logging

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import (
    QLabel,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from cranioz.ui.editors.base_editor import Editor
from cranioz.ui.theme.service import ThemeService
from cranioz.ui.toolbars.base import Toolbar
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
        # Cache of content widgets, keyed by editor_id.
        # The AreaWidget owns the *container*; the Editor owns the
        # content_widget(). We cache the content widget here so that
        # we can re-parent it safely across refresh() calls.
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
        self._clear_layout()

        if self._area.is_empty():
            self._root_layout.addWidget(self._build_empty_placeholder())
            return

        if getattr(self, "_debug_colors", False):
            debug_label = QLabel(f"[{self._area.area_id}]")
            debug_label.setStyleSheet(
                "QLabel { background: rgba(255,255,255,200); font-weight: bold; padding: 2px; }"
            )
            self._root_layout.addWidget(debug_label)

        editors = self._area.editors()
        if len(editors) == 1:
            self._root_layout.addWidget(self._build_editor_content(editors[0]))
            return

        self._root_layout.addWidget(self._build_tabs(editors))

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
        """Remove widgets from the layout without destroying Editor content.

        For each Editor, we detach its content_widget() from any
        container that is about to be destroyed. The content_widget()
        is owned by the Editor and must survive refresh().

        The containers themselves (the QWidget that holds the toolbars
        and the content_widget) are deleted via deleteLater(). They
        are recreated on the next refresh().
        """
        # 1. Detach every Editor's content_widget() from its container.
        #    This must happen BEFORE the container is deleted, otherwise
        #    the QLabel would be destroyed along with the container.
        for editor in self._area.editors():
            content = self._content_widgets.pop(editor.editor_id, None)
            if content is None:
                continue
            try:
                # A widget that was already deleted by Qt would raise
                # RuntimeError here. We catch and log it to keep refresh()
                # idempotent even after a partial teardown.
                content.setParent(None)
            except RuntimeError:
                _logger.exception(
                    "content_widget for %r was already deleted; skipping detach",
                    editor.editor_id,
                )

        # 2. Now it's safe to delete the containers.
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

    def _build_editor_content(self, editor: Editor) -> QWidget:
        """Build the container for a single Editor.

        The container is owned by AreaWidget. The content_widget() is
        owned by the Editor and is cached in `_content_widgets` so it
        can be safely detached and re-attached across refresh() calls.
        """
        container = QWidget()
        container.setObjectName(f"area_widget.{self._area.area_id}.editor.{editor.editor_id}")

        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        for toolbar_widget in self._build_toolbars(editor):
            layout.addWidget(toolbar_widget)

        # Get (or create) the content_widget() and cache it.
        content = editor.content_widget()
        self._content_widgets[editor.editor_id] = content

        # Ensure it's parented to the new container.
        content.setParent(container)
        layout.addWidget(content, stretch=1)

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

    def _build_tabs(self, editors: tuple[Editor, ...]) -> QTabWidget:
        tabs = QTabWidget()
        tabs.setObjectName(f"area_widget.{self._area.area_id}.tabs")
        tabs.setTabPosition(QTabWidget.TabPosition.South)
        tabs.setTabsClosable(True)
        tabs.setDocumentMode(True)

        tabs.tabBar().setStyleSheet("QTabBar { alignment: center; }")

        index_by_editor_id: dict[str, int] = {}
        for editor in editors:
            content = self._build_editor_content(editor)
            index = tabs.addTab(content, editor.title)
            index_by_editor_id[editor.editor_id] = index

        tabs.tabCloseRequested.connect(self._on_tab_close_requested)
        tabs.currentChanged.connect(self._on_current_tab_changed)

        active_editor_id = self._area.active_editor_id
        if active_editor_id is not None and active_editor_id in index_by_editor_id:
            tabs.setCurrentIndex(index_by_editor_id[active_editor_id])

        return tabs

    def _on_tab_close_requested(self, index: int) -> None:
        tabs = self._current_tabs()
        if tabs is None:
            return
        editor_id = self._editor_id_for_tab_index(tabs, index)
        if editor_id is None:
            return
        self.editor_close_requested.emit(self._area.area_id, editor_id)

    def _on_current_tab_changed(self, index: int) -> None:
        tabs = self._current_tabs()
        if tabs is None:
            return
        editor_id = self._editor_id_for_tab_index(tabs, index)
        if editor_id is None:
            return
        self.active_editor_changed.emit(self._area.area_id, editor_id)

    def _current_tabs(self) -> QTabWidget | None:
        for i in range(self._root_layout.count()):
            item = self._root_layout.itemAt(i)
            widget = item.widget() if item is not None else None
            if isinstance(widget, QTabWidget):
                return widget
        return None

    def _editor_id_for_tab_index(
        self,
        tabs: QTabWidget,
        index: int,
    ) -> str | None:
        editors = self._area.editors()
        if index < 0 or index >= len(editors):
            return None
        return editors[index].editor_id
