"""AreaWidget.

Qt widget that materializes a single Area.

The Area is a pure domain model (no Qt). The AreaWidget is the
presentation layer for one Area: it renders the Editor's Toolbars,
the Editor's content widget, tabs (when there are multiple Editors),
and a placeholder (when the Area is empty).

Responsibilities:

- Reflect the Area model. The Area is the source of truth. The
  AreaWidget never modifies the Area.
- Emit signals when the user requests a change (close an Editor,
  add an Editor, change the active Editor). The signals have no
  consumers in this piece; they will be connected by the Workspace
  in a future piece.
- Consume ToolRegistry and ThemeService to materialize Toolbars.

Non-responsibilities:

- The AreaWidget does not create Editors. The Editors come from the
  LayoutBuilder (Piece 4), already initialized.
- The AreaWidget does not mutate the Area. All mutations are
  performed by higher-level components in response to signals.
- The AreaWidget does not know about the LayoutTree, the
  LayoutRenderer, or the Workspace.

Structure of the produced widget:

- Empty Area:    a centered QLabel with "{title} (empty)".
- 1 Editor:      a QVBoxLayout with the Editor's Toolbars and the
                 Editor's content_widget().
- >= 2 Editors:  a QTabWidget (tabs at the bottom) with one tab per
                 Editor. Each tab contains the Editor's Toolbars and
                 its content_widget(). Tabs are closable. A '+' corner
                 button is present for future use.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QLabel,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from cranioz.ui.editors.base_editor import Editor
from cranioz.ui.theme.service import ThemeService
from cranioz.ui.toolbars.base import Toolbar
from cranioz.ui.tools.registry.tool_definition import ToolContext
from cranioz.ui.tools.registry.tool_registry import ToolRegistry
from cranioz.ui.workspace.areas.area import Area


class AreaWidget(QWidget):
    """Qt widget that materializes a single Area.

    The widget reflects the Area model. It never modifies the Area.
    User actions that would change the Area are emitted as signals.
    """

    active_editor_changed = Signal(str, str)  # area_id, editor_id
    editor_close_requested = Signal(str, str)  # area_id, editor_id
    editor_add_requested = Signal(str)  # area_id

    def __init__(
        self,
        area: Area,
        tool_registry: ToolRegistry,
        theme_service: ThemeService,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._area = area
        self._tool_registry = tool_registry
        self._theme_service = theme_service

        self.setObjectName(f"area_widget.{area.area_id}")

        # The root layout is replaced on every refresh(). This keeps
        # the widget in sync with the Area without tracking which
        # sub-widgets exist.
        self._root_layout = QVBoxLayout(self)
        self._root_layout.setContentsMargins(0, 0, 0, 0)
        self._root_layout.setSpacing(0)

        self.refresh()

    # ----- Public API -----------------------------------------------

    @property
    def area_id(self) -> str:
        """The area_id of the Area this widget reflects."""
        return self._area.area_id

    def refresh(self) -> None:
        """Re-render the widget from the Area model.

        Called when the Area's Editors or active Editor change.
        The method is idempotent: calling it twice with the same
        Area produces the same widget structure.
        """
        self._clear_layout()

        if self._area.is_empty():
            self._root_layout.addWidget(self._build_empty_placeholder())
            return

        editors = self._area.editors()
        if len(editors) == 1:
            self._root_layout.addWidget(self._build_editor_content(editors[0]))
            return

        self._root_layout.addWidget(self._build_tabs(editors))

    # ----- Internals ------------------------------------------------

    def _clear_layout(self) -> None:
        """Remove all widgets from the root layout and dispose them.

        Uses deleteLater() so that Qt can clean up after the current
        event loop iteration. This is safe even during refresh(),
        which may be triggered from a signal handler.
        """
        while self._root_layout.count():
            item = self._root_layout.takeAt(0)
            widget = item.widget() if item is not None else None
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()

    def _build_empty_placeholder(self) -> QWidget:
        """Build the placeholder for an empty Area.

        A centered QLabel with "{title} (empty)". The placeholder is
        intentionally minimal for this piece; a '+' button to add an
        Editor will be added in a future piece.
        """
        label = QLabel(f"{self._area.title} (empty)")
        label.setObjectName(f"area_widget.{self._area.area_id}.placeholder")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return label

    def _build_editor_content(self, editor: Editor) -> QWidget:
        """Build the content container for a single Editor.

        The container holds the Editor's Toolbars (in declared order)
        followed by the Editor's content_widget().
        """
        container = QWidget()
        container.setObjectName(f"area_widget.{self._area.area_id}.editor.{editor.editor_id}")

        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        for toolbar_widget in self._build_toolbars(editor):
            layout.addWidget(toolbar_widget)

        layout.addWidget(editor.content_widget(), stretch=1)
        return container

    def _build_toolbars(self, editor: Editor) -> list[Toolbar]:
        """Materialize the Editor's Toolbars from its ToolbarSpecs.

        Each ToolbarSpec is resolved against the ToolRegistry and the
        ThemeService. The ToolContext is taken from the Editor: the
        Editor is the owner of the ToolContext, not the AreaWidget.
        """
        context = self._editor_tool_context(editor)
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

    @staticmethod
    def _editor_tool_context(editor: Editor) -> ToolContext:
        """Return the ToolContext for an Editor.

        For now, this is an empty context. When Editors expose their
        own ToolContext (via EditorContext or a dedicated accessor),
        this method will read from the Editor instead of constructing
        an empty one.
        """
        return ToolContext()

    def _build_tabs(self, editors: tuple[Editor, ...]) -> QTabWidget:
        """Build the tabbed container for multiple Editors.

        Tabs are placed at the bottom (South). Each tab contains the
        Editor's Toolbars and its content_widget(). Tabs are closable.
        The active tab corresponds to the Area's active_editor_id.
        """
        tabs = QTabWidget()
        tabs.setObjectName(f"area_widget.{self._area.area_id}.tabs")
        tabs.setTabPosition(QTabWidget.TabPosition.South)
        tabs.setTabsClosable(True)
        tabs.setDocumentMode(True)

        # Map editor_id -> index for restoring the active tab.
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

    # ----- Signal handlers ------------------------------------------

    def _on_tab_close_requested(self, index: int) -> None:
        """Forward a tab close request as a signal.

        The AreaWidget does not remove the Editor. It only emits the
        intent. A higher-level component (the Workspace) will decide
        what to do, likely by dispatching a Command.
        """
        tabs = self._current_tabs()
        if tabs is None:
            return
        editor_id = self._editor_id_for_tab_index(tabs, index)
        if editor_id is None:
            return
        self.editor_close_requested.emit(self._area.area_id, editor_id)

    def _on_current_tab_changed(self, index: int) -> None:
        """Forward a tab change as a signal.

        Emits (area_id, editor_id) so that a higher-level component
        can record the new active Editor. The AreaWidget does not
        mutate the Area.
        """
        tabs = self._current_tabs()
        if tabs is None:
            return
        editor_id = self._editor_id_for_tab_index(tabs, index)
        if editor_id is None:
            return
        self.active_editor_changed.emit(self._area.area_id, editor_id)

    # ----- Helpers --------------------------------------------------

    def _current_tabs(self) -> QTabWidget | None:
        """Return the QTabWidget currently hosted by this widget, if any."""
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
        """Return the editor_id associated with a given tab index.

        The mapping is done by consulting the Area: the Editors are in
        the same order as the tabs, since both derive from
        Area.editors().
        """
        editors = self._area.editors()
        if index < 0 or index >= len(editors):
            return None
        return editors[index].editor_id
