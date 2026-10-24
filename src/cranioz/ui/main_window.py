"""MainWindow — the application shell.

MainWindow is the top-level application window. It hosts the Home
Page and the Workspace, and it is the sole orchestrator of navigation
between them (ADR-0006).

Responsibilities:

- Host the HomePage and the Workspace in a QStackedWidget.
- Listen to HomePage.project_open_requested; call ProjectManager,
  create the Workspace with the resulting ProjectContext, inject
  the "Home" button into the TopOverlay, and switch to the Workspace.
- Listen to the "Home" button's clicked; call ProjectManager.close_project,
  destroy the Workspace, and switch back to the HomePage.
- Forward other HomePage signals to MessageBox placeholders for
  pieces that are not yet implemented (Bloco 8 / Bloco 9 / 7.6d).
- Forward shared application services (TaskManager, TelemetrySink)
  to the Workspace (ADR-0011, ADR-0012).
- Populate the HomePage's FlowList from the FlowCatalog (A5).
- Translate flow labels for the HomePage via a temporary humanizer
  until the TranslationService is wired.

Non-responsibilities (see main_window.md §9 and ADR-0006):

- MainWindow does not implement project lifecycle rules.
- MainWindow does not implement workflow rules.
- MainWindow does not manage long-running operations.
- MainWindow does not persist state.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PySide6.QtWidgets import (
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QWidget,
)

from cranioz.application.flows.catalog import FlowCatalog
from cranioz.application.project.project_catalog import ProjectCatalog
from cranioz.application.project.project_context import ProjectContext
from cranioz.application.project.project_errors import ProjectError
from cranioz.application.project.project_manager import ProjectManager
from cranioz.domain.project.project_id import ProjectId
from cranioz.ui.editors.editor_registry import EditorRegistry
from cranioz.ui.home.home_page import HomePage
from cranioz.ui.theme.service import ThemeService
from cranioz.ui.tools.registry.tool_registry import ToolRegistry
from cranioz.ui.workspace.workspace import Workspace
from cranioz.ui.workspace.workspace_spec import (
    DEFAULT as WORKSPACE_SPEC_DEFAULT,
)
from cranioz.ui.workspace.workspace_spec import (
    PLACEHOLDER_EDITOR_CLASS,
    PLACEHOLDER_EDITOR_ID,
)

if TYPE_CHECKING:
    from cranioz.application.tasks.base import TaskManager
    from cranioz.application.telemetry.base import TelemetrySink

_logger = logging.getLogger(__name__)


def _humanize_translation_key(key: str) -> str:
    """Fallback translator: turns a translation key into a readable label.

    This is a temporary bridge until the TranslationService is wired.
    When i18n is active, replace this with ``translation_service.tr``.

    Examples:
        "flows.orthognathic_basic.name"             -> "Orthognathic Basic"
        "flows.orthognathic_basic.steps.patient"    -> "Patient"
        "flows.orthognathic_basic.steps.organize_data" -> "Organize Data"

    The function is deliberately simple: it splits on "." and humanizes
    the last non-structural segment. It does not attempt to translate;
    it only makes the key readable.
    """
    structural = {"flows", "steps", "name"}
    parts = [p for p in key.split(".") if p and p not in structural]
    if not parts:
        return key
    last = parts[-1]
    return last.replace("_", " ").title()


class MainWindow(QMainWindow):
    """Application shell: hosts HomePage and Workspace."""

    def __init__(
        self,
        *,
        catalog: ProjectCatalog,
        manager: ProjectManager,
        actor: str,
        editor_registry: EditorRegistry,
        tool_registry: ToolRegistry,
        theme_service: ThemeService,
        task_manager: TaskManager | None = None,
        telemetry: TelemetrySink | None = None,
        flow_catalog: FlowCatalog | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._catalog = catalog
        self._manager = manager
        self._actor = actor
        self._editor_registry = editor_registry
        self._tool_registry = tool_registry
        self._theme_service = theme_service
        self._task_manager = task_manager
        self._telemetry = telemetry
        self._flow_catalog = flow_catalog

        self._current_project_id: ProjectId | None = None
        self._workspace: Workspace | None = None

        self._editor_registry.register(PLACEHOLDER_EDITOR_ID, PLACEHOLDER_EDITOR_CLASS)

        self._home = HomePage(
            catalog=self._catalog,
            parent=self,
            flow_list_translate=_humanize_translation_key,
        )
        self._stack = QStackedWidget(self)
        self._stack.addWidget(self._home)
        self.setCentralWidget(self._stack)

        self._connect_home_signals()
        self._populate_flow_list()

        self.setWindowTitle("CranioZ")
        self.resize(1000, 650)

    # ----- HomePage signal wiring ------------------------------------

    def _connect_home_signals(self) -> None:
        home = self._home
        home.project_open_requested.connect(self._on_project_open_requested)
        home.new_project_requested.connect(self._on_new_project_requested)
        home.manage_projects_requested.connect(self._on_manage_projects_requested)
        home.manage_flows_requested.connect(self._on_manage_flows_requested)
        home.settings_requested.connect(self._on_settings_requested)
        home.help_requested.connect(self._on_help_requested)
        home.community_requested.connect(self._on_community_requested)
        home.library_requested.connect(self._on_library_requested)
        home.news_requested.connect(self._on_news_requested)
        home.feedback_requested.connect(self._on_feedback_requested)
        home.contribute_requested.connect(self._on_contribute_requested)

    # ----- Flow population -------------------------------------------

    def _populate_flow_list(self) -> None:
        """Load flows from the catalog (if any) into the HomePage.

        The catalog is optional: if it is ``None``, the HomePage keeps
        the placeholder "Nenhum fluxo disponível". Any catalog failure
        is logged and does not prevent the HomePage from showing.
        """
        if self._flow_catalog is None:
            return
        try:
            definitions = self._flow_catalog.list_definitions()
        except Exception:
            _logger.exception("cannot load flows into the Home Page")
            return
        self._home._flow_list_widget().set_flows(definitions)

    # ----- Project navigation ----------------------------------------

    def _on_project_open_requested(
        self,
        project_id: ProjectId,
        flow_id: str,
    ) -> None:
        try:
            context = self._manager.open_project(
                self._actor,
                project_id,
                workflow_id=flow_id,
                workflow_config={},
            )
        except ProjectError as exc:
            QMessageBox.critical(self, "Cannot open project", str(exc))
            return

        workspace = self._create_workspace(context)
        self._stack.addWidget(workspace)
        self._stack.setCurrentWidget(workspace)
        self._workspace = workspace
        self._current_project_id = project_id

    def _create_workspace(self, context: ProjectContext) -> Workspace:
        workspace = Workspace(
            editor_registry=self._editor_registry,
            tool_registry=self._tool_registry,
            theme_service=self._theme_service,
            project_context=context,
            task_manager=self._task_manager,
            telemetry=self._telemetry,
        )

        home_button = QPushButton("Home")
        home_button.setObjectName("workspace.home_button")
        home_button.clicked.connect(self._on_home_clicked)
        workspace.top_overlay().set_left_content(home_button)

        workspace.load_spec(WORKSPACE_SPEC_DEFAULT)
        return workspace

    def _on_home_clicked(self) -> None:
        if self._current_project_id is None or self._workspace is None:
            return

        self._manager.close_project(self._actor, self._current_project_id)
        self._stack.removeWidget(self._workspace)
        self._workspace.setParent(None)
        self._workspace.deleteLater()
        self._workspace = None
        self._current_project_id = None

        self._stack.setCurrentWidget(self._home)
        self._home.refresh()

    # ----- HomePage action handlers (placeholders) ------------------

    def _on_new_project_requested(self) -> None:
        QMessageBox.information(self, "New project", "Available after Bloco 8 (Patient Module).")

    def _on_manage_projects_requested(self) -> None:
        QMessageBox.information(
            self,
            "Manage projects",
            "Available after Bloco 8 (Patient Module).",
        )

    def _on_manage_flows_requested(self) -> None:
        QMessageBox.information(self, "Manage flows", "Available after Bloco 9 (Flow Catalog).")

    def _on_settings_requested(self) -> None:
        QMessageBox.information(self, "Settings", "Available after piece 7.6d (Settings).")

    def _on_help_requested(self) -> None:
        QMessageBox.information(self, "Help", "Available after piece 7.6d (Documentation).")

    def _on_community_requested(self) -> None:
        QMessageBox.information(self, "Community", "Available in a future piece.")

    def _on_library_requested(self) -> None:
        QMessageBox.information(self, "Object library", "Available in a future piece.")

    def _on_news_requested(self) -> None:
        QMessageBox.information(self, "News", "Available in a future piece.")

    def _on_feedback_requested(self) -> None:
        QMessageBox.information(self, "Suggest improvements", "Available in a future piece.")

    def _on_contribute_requested(self) -> None:
        QMessageBox.information(self, "Contribute", "Available in a future piece.")

    # ----- Convenience for tests ------------------------------------

    def home(self) -> HomePage:
        return self._home

    def current_workspace(self) -> Workspace | None:
        return self._workspace

    def current_project_id(self) -> ProjectId | None:
        return self._current_project_id
