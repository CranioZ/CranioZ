"""HomeSegment — the left zone of the Workspace Top Bar.

Three buttons, left to right:

- ``☰`` (panel-with-sidebar glyph): toggle Area Left.
- ``⋮`` (three dots): a ``QMenu`` with project actions
  (Novo projeto, Abrir projeto, Fechar projeto, Importar arquivos).
- ``⌂`` (house glyph): close the current Workspace and return to
  the Home Page.

The glyphs are textual placeholders. A future piece will replace them
with ``ThemeService.icon_name(...)`` when the icon loader exists.

The segment is a pure presentation widget: it does not know the
Workspace, the ProjectManager or the ProjectContext. Each user
intention emits a signal; the MainWindow decides what to do.

"Fechar projeto" and "Importar arquivos" are context-dependent: they
only make sense while a project is open. ``set_project_open(bool)``
toggles their enabled state. The segment does not know what a project
is; it only reflects the boolean it is given.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMenu,
    QPushButton,
    QWidget,
)


class HomeSegment(QWidget):
    """Left zone of the Workspace Top Bar."""

    toggle_area_left_requested = Signal()
    new_project_requested = Signal()
    open_project_requested = Signal()
    close_project_requested = Signal()
    import_files_requested = Signal()
    close_workspace_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("workspace.top_bar.home_segment")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self._toggle_left_button = self._make_button(
            "☰", "workspace.top_bar.home_segment.toggle_left", "Toggle Area Left"
        )
        self._toggle_left_button.clicked.connect(self.toggle_area_left_requested)

        self._menu_button = self._make_button(
            "⋮", "workspace.top_bar.home_segment.menu", "Project actions"
        )
        self._build_menu()
        self._menu_button.clicked.connect(self._on_menu_button_clicked)

        self._close_workspace_button = self._make_button(
            "⌂", "workspace.top_bar.home_segment.close_workspace", "Close workspace"
        )
        self._close_workspace_button.clicked.connect(self.close_workspace_requested)

        layout.addWidget(self._toggle_left_button)
        layout.addWidget(self._menu_button)
        layout.addWidget(self._close_workspace_button)

        # Context-dependent actions start disabled: no project is open
        # until the MainWindow says otherwise.
        self._project_open = False
        self._sync_context_actions()

    # ----- Public API -----------------------------------------------

    def set_project_open(self, open: bool) -> None:
        """Reflect the project-open state on context-dependent actions.

        "Fechar projeto" and "Importar arquivos" are only enabled when
        a project is open. The segment does not inspect the application
        state; it trusts the boolean.
        """
        self._project_open = open
        self._sync_context_actions()

    def is_project_open(self) -> bool:
        return self._project_open

    # ----- Internals ------------------------------------------------

    def _make_button(self, glyph: str, object_name: str, tooltip: str) -> QPushButton:
        button = QPushButton(glyph, self)
        button.setObjectName(object_name)
        button.setFlat(True)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setToolTip(tooltip)
        button.setFixedWidth(28)
        return button

    def _build_menu(self) -> None:
        self._menu = QMenu(self)
        self._menu.setObjectName("workspace.top_bar.home_segment.menu.popup")

        self._action_new_project = self._menu.addAction("Novo projeto")
        self._action_new_project.triggered.connect(self.new_project_requested)

        self._action_open_project = self._menu.addAction("Abrir projeto")
        self._action_open_project.triggered.connect(self.open_project_requested)

        self._menu.addSeparator()

        self._action_close_project = self._menu.addAction("Fechar projeto")
        self._action_close_project.triggered.connect(self.close_project_requested)

        self._action_import_files = self._menu.addAction("Importar arquivos")
        self._action_import_files.triggered.connect(self.import_files_requested)

    def _on_menu_button_clicked(self) -> None:
        # Anchor the menu below the button, not at the cursor.
        bottom_left = self._menu_button.rect().bottomLeft()
        global_pos = self._menu_button.mapToGlobal(bottom_left)
        self._menu.exec(global_pos)

    def _sync_context_actions(self) -> None:
        self._action_close_project.setEnabled(self._project_open)
        self._action_import_files.setEnabled(self._project_open)
