"""MainWindow — the application shell.

MainWindow is the top-level application window. It hosts the Home
Page and the Workspace, and it is the sole orchestrator of navigation
between them (ADR-0006).

Responsibilities:

- Host the HomePage and the Workspace in a QStackedWidget.
- Listen to HomePage.project_open_requested; call ProjectManager,
  create the Workspace with the resulting ProjectContext, inject the
  three Top Bar segments (Home, Modules, Extras) into the TopOverlay,
  and switch to the Workspace.
- Register the DICOM import handler in the CommandBus when the
  project opens (Application Startup §3.4, §4.1: the handler pulls
  pydicom/numpy, which must not be loaded during the boot critical
  path).
- Listen to the Top Bar's close_workspace_requested and close_project
  requests; call ProjectManager.close_project, unregister the DICOM
  import handler, destroy the Workspace, and switch back to the
  HomePage.
- Listen to the Top Bar's import_files_requested (and the legacy
  "Import DICOM" path); open a folder picker, dispatch
  ImportDicomSeriesCommand (which reads the series, assembles a
  Volume, registers it in the DomainObjectStore and the Scene), and
  reload the Workspace's volume.
- Listen to the Top Bar's import_stl_debug_requested; load an STL
  and render it in the first Viewport3DView. Temporary validation
  tool; will be removed when the ImportMeshCommand lands.
- Toggle the visibility of Area Left, Area Right and Area Bottom in
  response to the Top Bar signals. The Workspace owns the runtime
  state; the MainWindow only relays the intent.
- Forward other HomePage signals to MessageBox placeholders for
  pieces that are not yet implemented (Bloco 8 / Bloco 9 / 7.6d).
- Forward shared application services (TaskManager, TelemetrySink,
  SceneProvider, DomainObjectStore) to the Workspace (ADR-0011,
  ADR-0012).
- Populate the HomePage's FlowList from the FlowCatalog (A5).
- Inject the TranslationService into the HomePage so that the
  FlowList can resolve flow labels via the active catalog.

Non-responsibilities (see main_window.md §9 and ADR-0006):

- MainWindow does not implement project lifecycle rules.
- MainWindow does not implement workflow rules.
- MainWindow does not manage long-running operations.
- MainWindow does not persist state.
- MainWindow does not read DICOM or assemble volumes; that is the
  ImportDicomSeriesHandler's responsibility.
"""

from __future__ import annotations

import logging
import os
import uuid
from typing import TYPE_CHECKING

from PySide6.QtWidgets import (
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QStackedWidget,
    QWidget,
)

from cranioz.application.commands.base import CommandDispatchError
from cranioz.application.flows.catalog import FlowCatalog
from cranioz.application.project.project_catalog import ProjectCatalog
from cranioz.application.project.project_context import ProjectContext
from cranioz.application.project.project_errors import ProjectError
from cranioz.application.project.project_manager import ProjectManager
from cranioz.application.scene.commands.scene_commands import (
    ImportDicomSeriesCommand,
)
from cranioz.application.scene.handlers.scene_handlers import (
    ImportDicomSeriesHandler,
)
from cranioz.domain.project.project_id import ProjectId
from cranioz.infrastructure.i18n.translation_service import TranslationService
from cranioz.infrastructure.scene.scene_query_adapter import SceneQueryAdapter
from cranioz.ui.editors.editor_registry import EditorRegistry
from cranioz.ui.editors.viewport_3d.mesh_debug_editor import (
    MESH_DEBUG_EDITOR_ID,
    MeshDebugEditor,
)
from cranioz.ui.home.home_page import HomePage
from cranioz.ui.theme.service import ThemeService
from cranioz.ui.tools.registry.tool_registry import ToolRegistry
from cranioz.ui.workspace.areas.placement import Placement
from cranioz.ui.workspace.structure import (
    ExtrasSegment,
    HomeSegment,
    ModulesSegment,
)
from cranioz.ui.workspace.workspace import Workspace
from cranioz.ui.workspace.workspace_spec import (
    DEBUG_MESH as WORKSPACE_SPEC_DEBUG_MESH,
)
from cranioz.ui.workspace.workspace_spec import (
    DEFAULT as WORKSPACE_SPEC_DEFAULT,
)
from cranioz.ui.workspace.workspace_spec import (
    PLACEHOLDER_EDITOR_CLASS,
    PLACEHOLDER_EDITOR_ID,
)

if TYPE_CHECKING:
    from cranioz.application.commands.bus import CommandBus
    from cranioz.application.commands.dispatcher import CommandDispatcher
    from cranioz.application.scene.scene_provider import SceneProvider
    from cranioz.application.tasks.base import TaskManager
    from cranioz.application.telemetry.base import TelemetrySink
    from cranioz.domain.scene.domain_object_store import DomainObjectStore

_logger = logging.getLogger(__name__)


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
        translation_service: TranslationService | None = None,
        task_manager: TaskManager | None = None,
        telemetry: TelemetrySink | None = None,
        command_dispatcher: CommandDispatcher | None = None,
        command_bus: CommandBus | None = None,
        flow_catalog: FlowCatalog | None = None,
        scene_provider: SceneProvider | None = None,
        domain_object_store: DomainObjectStore | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._catalog = catalog
        self._manager = manager
        self._actor = actor
        self._editor_registry = editor_registry
        self._tool_registry = tool_registry
        self._theme_service = theme_service
        self._translation_service = translation_service
        self._task_manager = task_manager
        self._telemetry = telemetry
        self._command_dispatcher = command_dispatcher
        self._command_bus = command_bus
        self._flow_catalog = flow_catalog
        self._scene_provider = scene_provider
        self._domain_object_store = domain_object_store

        self._current_project_id: ProjectId | None = None
        self._workspace: Workspace | None = None

        # Debug flag: when CRANIOZ_DEBUG_MESH=1, the workspace uses a
        # MeshDebugEditor spec so that the STL debug import has a
        # Viewport3DView to render into. Not used in production.
        self._debug_mesh = os.environ.get("CRANIOZ_DEBUG_MESH") == "1"

        self._editor_registry.register(PLACEHOLDER_EDITOR_ID, PLACEHOLDER_EDITOR_CLASS)
        if self._debug_mesh:
            self._editor_registry.register(MESH_DEBUG_EDITOR_ID, MeshDebugEditor)

        self._home = HomePage(
            catalog=self._catalog,
            parent=self,
            translation_service=self._translation_service,
        )
        self._stack = QStackedWidget(self)
        self._stack.addWidget(self._home)
        self.setCentralWidget(self._stack)

        self._connect_home_signals()
        self._populate_flow_list()

        self.setWindowTitle(self._tr("core.app.name", "CranioZ"))
        self.resize(1000, 650)

    # ----- HomePage signal wiring ------------------------------------

    def _connect_home_signals(self) -> None:
        """Connect HomePage signals to their handlers.

        The import actions belong to the Top Bar's HomeSegment, not to
        the HomePage; they are wired in ``_wire_top_bar_segments`` when
        the Workspace is created.
        """
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
            QMessageBox.critical(
                self,
                self._tr("workspace.dialog.cannot_open_project", "Cannot open project"),
                str(exc),
            )
            return

        workspace = self._create_workspace(context)
        self._stack.addWidget(workspace)
        self._stack.setCurrentWidget(workspace)
        self._workspace = workspace
        self._current_project_id = project_id

        # Register the DICOM import handler now, when the project is
        # open and the Scene/DomainObjectStore exist. The handler
        # imports pydicom/numpy, which must not be loaded during the
        # boot critical path (Application Startup §3.4, §4.1).
        self._register_dicom_import_handler()

    def _create_workspace(self, context: ProjectContext) -> Workspace:
        # Build the SceneQueryAdapter from the provider's Scene, if any.
        # The adapter is recreated per Workspace, but the underlying
        # Scene is owned by the provider (single source of truth).
        # See ADR-0008, scene.md, editors.md §15.
        scene_query = None
        if self._scene_provider is not None:
            scene = self._scene_provider.get_scene()
            scene_query = SceneQueryAdapter(scene)

        # Ensure the built-in tools required by the default editor
        # specs are registered. The TomographyEditor declares toolbars
        # that reference "tool.log" and "tool.toggle"; without them,
        # AreaWidget._build_toolbars raises KeyError. Registration is
        # idempotent: re-registering the same factory is a no-op.
        self._ensure_builtin_tools()

        workspace = Workspace(
            editor_registry=self._editor_registry,
            tool_registry=self._tool_registry,
            theme_service=self._theme_service,
            project_context=context,
            task_manager=self._task_manager,
            telemetry=self._telemetry,
            command_dispatcher=self._command_dispatcher,
            scene_query=scene_query,
            domain_object_store=self._domain_object_store,
            translation_service=self._translation_service,
        )

        # TopOverlay: three segments, one per zone.
        home_segment = HomeSegment()
        modules_segment = ModulesSegment()
        extras_segment = ExtrasSegment()

        # Placeholder module list until Phase 5 delivers WorkflowEngine.
        modules_segment.set_modules((("tomography", "Tomografia"),))

        # The project is open at this point: context-dependent actions
        # in the Home menu ("Fechar projeto", "Importar arquivos") are
        # enabled.
        home_segment.set_project_open(True)

        self._wire_top_bar_segments(workspace, home_segment, modules_segment, extras_segment)

        workspace.top_overlay().set_left_content(home_segment)
        workspace.top_overlay().set_center_content(modules_segment)
        workspace.top_overlay().set_right_content(extras_segment)

        spec = WORKSPACE_SPEC_DEBUG_MESH if self._debug_mesh else WORKSPACE_SPEC_DEFAULT
        workspace.load_spec(spec)
        return workspace

    def _ensure_builtin_tools(self) -> None:
        """Register the built-in tools that the default editor specs require.

        The TomographyEditor declares toolbars that reference
        "tool.log" and "tool.toggle". Without them registered,
        AreaWidget._build_toolbars raises KeyError when the Workspace
        is created. Registration is idempotent: if a tool is already
        registered, this method does not replace it.
        """
        # Local import to keep the boot path free of UI widget imports
        # that are not needed until a project is opened.
        from cranioz.ui.tools.builtin.log_tool import LogTool  # noqa: PLC0415
        from cranioz.ui.tools.builtin.toggle_tool import ToggleTool  # noqa: PLC0415

        builtin = (
            ("tool.log", LogTool),
            ("tool.toggle", ToggleTool),
        )
        for tool_id, factory in builtin:
            if not self._tool_registry.contains(tool_id):
                self._tool_registry.register(tool_id, factory)

    def _wire_top_bar_segments(
        self,
        workspace: Workspace,
        home: HomeSegment,
        modules: ModulesSegment,
        extras: ExtrasSegment,
    ) -> None:
        """Wire the Top Bar segment signals to their handlers.

        The segments are presentation widgets: they emit signals and
        know nothing about the application. The MainWindow decides
        what each signal means.
        """
        # Home zone
        home.toggle_area_left_requested.connect(
            lambda: self._toggle_area(workspace, Placement.LEFT)
        )
        home.close_workspace_requested.connect(self._on_home_clicked)
        home.new_project_requested.connect(self._on_new_project_requested)
        home.open_project_requested.connect(self._on_manage_projects_requested)
        home.close_project_requested.connect(self._on_home_clicked)
        home.import_files_requested.connect(self._on_import_dicom_clicked)
        home.import_stl_debug_requested.connect(self._on_import_stl_debug_clicked)

        # Modules zone
        modules.add_module_requested.connect(self._on_manage_flows_requested)

        # Extras zone
        extras.settings_requested.connect(self._on_settings_requested)
        extras.themes_requested.connect(self._on_settings_requested)  # placeholder
        extras.help_requested.connect(self._on_help_requested)
        extras.updates_requested.connect(self._on_help_requested)  # placeholder
        extras.about_requested.connect(self._on_help_requested)  # placeholder
        extras.toggle_area_bottom_requested.connect(
            lambda: self._toggle_area(workspace, Placement.BOTTOM)
        )
        extras.toggle_area_right_requested.connect(
            lambda: self._toggle_area(workspace, Placement.RIGHT)
        )

    def _toggle_area(self, workspace: Workspace, placement: Placement) -> None:
        """Toggle an Area's visibility and reflect the new state.

        The Workspace owns the runtime visibility state; the MainWindow
        only relays the intent.
        """
        current = workspace.layout_state().is_visible(placement)
        workspace.set_area_visible(placement, not current)

    def _on_home_clicked(self) -> None:
        if self._current_project_id is None or self._workspace is None:
            return

        self._manager.close_project(self._actor, self._current_project_id)
        self._unregister_dicom_import_handler()
        self._stack.removeWidget(self._workspace)
        self._workspace.setParent(None)
        self._workspace.deleteLater()
        self._workspace = None
        self._current_project_id = None

        self._stack.setCurrentWidget(self._home)
        self._home.refresh()

    # ----- DICOM import handler lifecycle ----------------------------

    def _register_dicom_import_handler(self) -> None:
        """Register the DICOM import handler in the CommandBus.

        The handler imports DicomSeriesReader (and, transitively,
        pydicom and numpy). Registering it here — inside the
        project-opening flow — keeps the application boot free of
        clinical dependencies (Application Startup §3.1, §3.4, §4.1).

        The handler is unregistered in ``_on_home_clicked`` when the
        project is closed, because it references the project's
        Scene and DomainObjectStore.
        """
        if self._command_bus is None:
            return
        if self._scene_provider is None or self._domain_object_store is None:
            return

        # Local import: the handler pulls pydicom/numpy, which must
        # not be loaded during the boot critical path.
        from cranioz.application.scene.handlers.scene_handlers import (  # noqa: PLC0415
            ImportDicomSeriesHandler,
        )

        handler = ImportDicomSeriesHandler(
            scene=self._scene_provider.get_scene(),
            object_store=self._domain_object_store,
        )
        self._command_bus.register(ImportDicomSeriesCommand, handler)

    def _unregister_dicom_import_handler(self) -> None:
        """Unregister the DICOM import handler when the project closes.

        The handler references the project's Scene and
        DomainObjectStore, which become invalid after the project is
        closed. Leaving it registered would keep those references
        alive and allow stale dispatches.
        """
        if self._command_bus is None:
            return
        self._command_bus.unregister(ImportDicomSeriesCommand)

    # ----- DICOM import ----------------------------------------------

    def _on_import_dicom_clicked(self) -> None:
        """Open a folder picker, dispatch ImportDicomSeriesCommand,
        and reload the Workspace.
        """
        if self._workspace is None:
            return

        if self._command_dispatcher is None:
            QMessageBox.critical(
                self,
                self._tr("workspace.dialog.dicom_import_failed", "Failed to import DICOM"),
                self._tr(
                    "workspace.dialog.command_dispatcher_unavailable",
                    "The command dispatcher is not available.",
                ),
            )
            return

        if not self._ensure_dicom_import_handler():
            return

        path = QFileDialog.getExistingDirectory(
            self,
            self._tr("workspace.dialog.select_dicom_folder", "Select folder with DICOM"),
            "",
            QFileDialog.Option.ShowDirsOnly,
        )
        if not path:
            return

        scene = self._scene_provider.get_scene() if self._scene_provider else None
        if scene is None:
            QMessageBox.critical(
                self,
                self._tr("workspace.dialog.dicom_import_failed", "Failed to import DICOM"),
                self._tr(
                    "workspace.dialog.scene_provider_unavailable",
                    "The Scene provider is not available.",
                ),
            )
            return

        object_id = f"volume-{uuid.uuid4().hex[:8]}"
        command = ImportDicomSeriesCommand.new(
            scene_id=scene.scene_id,
            path=path,
            object_id=object_id,
        )

        try:
            self._command_dispatcher.dispatch(command)
        except Exception as exc:
            if isinstance(exc, CommandDispatchError):
                _logger.exception("DICOM import failed for %s", path)
                QMessageBox.critical(
                    self,
                    self._tr("workspace.dialog.dicom_import_failed", "Failed to import DICOM"),
                    str(exc),
                )
            else:
                _logger.exception("unexpected error importing DICOM from %s", path)
                QMessageBox.critical(
                    self,
                    self._tr("workspace.dialog.dicom_import_failed", "Failed to import DICOM"),
                    self._tr(
                        "workspace.dialog.unexpected_error",
                        "Unexpected error: {detail}",
                        detail=exc,
                    ),
                )
            return

        self._workspace.reload_volume()
        _logger.info("Imported DICOM series from %s as %s", path, object_id)

    def _on_import_stl_debug_clicked(self) -> None:
        """Load an STL and render it in the first Viewport3DView.

        Temporary validation tool: it bypasses the (not yet
        implemented) ImportMeshCommand and writes the Mesh directly
        into the Viewport3DView. The item is marked TODO(phase-4) in
        the HomeSegment and will be removed when the import dialog
        and the ImportMeshCommand land.
        """
        # Local import: the geometry I/O pulls VTK, which must not be
        # loaded during the boot critical path.
        from cranioz.domain.geometry.coordinate_frame import (  # noqa: PLC0415
            CoordinateFrame,
        )
        from cranioz.infrastructure.geometry.io.stl import (  # noqa: PLC0415
            StlReadError,
            read_stl,
        )

        workspace = self._workspace
        if workspace is None:
            return

        viewport = workspace.find_viewport_3d()
        if viewport is None:
            QMessageBox.warning(
                self,
                self._tr("workspace.dialog.stl_import_failed", "Failed to import STL"),
                self._tr(
                    "workspace.dialog.no_viewport_3d",
                    "No 3D viewport in the scene. Run the application with "
                    "CRANIOZ_DEBUG_MESH=1 to enable the mesh debug editor, "
                    "or open a project with the TomographyEditor.",
                ),
            )
            return

        path, _ = QFileDialog.getOpenFileName(
            self,
            self._tr("workspace.dialog.select_stl_file", "Select STL file"),
            "",
            self._tr("workspace.dialog.stl_filter", "STL (*.stl);;;All files (*)"),
        )
        if not path:
            return

        try:
            mesh = read_stl(
                path,
                unit_scale=1.0,
                coordinate_frame=CoordinateFrame.identity(),
            )
        except StlReadError as exc:
            QMessageBox.critical(
                self,
                self._tr("workspace.dialog.stl_import_failed", "Failed to import STL"),
                str(exc),
            )
            return

        viewport.set_mesh(mesh)
        _logger.info(
            "Loaded debug STL %s as Mesh(vertices=%d, faces=%d)",
            path,
            mesh.vertex_count,
            mesh.face_count,
        )

    def _ensure_dicom_import_handler(self) -> bool:
        """Ensure the DICOM import handler is registered in the CommandBus.

        Returns True if the handler is registered (or was successfully
        registered now), False if registration is not possible.
        """
        if self._command_bus is None:
            return False

        if self._command_bus.can_dispatch(ImportDicomSeriesCommand):
            return True

        if self._scene_provider is None or self._domain_object_store is None:
            QMessageBox.critical(
                self,
                self._tr("workspace.dialog.dicom_import_failed", "Failed to import DICOM"),
                self._tr(
                    "workspace.dialog.scene_unavailable",
                    "The Scene or the DomainObjectStore is not available. "
                    "Open a project before importing DICOM.",
                ),
            )
            return False

        handler = ImportDicomSeriesHandler(
            scene=self._scene_provider.get_scene(),
            object_store=self._domain_object_store,
        )
        self._command_bus.register(ImportDicomSeriesCommand, handler)
        return True

    # ----- HomePage action handlers (placeholders) -------------------

    def _on_new_project_requested(self) -> None:
        self._show_future_feature(
            "workspace.placeholder.new_project",
            "New project",
            "Bloco 8 (Patient Module)",
        )

    def _on_manage_projects_requested(self) -> None:
        self._show_future_feature(
            "workspace.placeholder.manage_projects",
            "Manage projects",
            "Bloco 8 (Patient Module)",
        )

    def _on_manage_flows_requested(self) -> None:
        self._show_future_feature(
            "workspace.placeholder.manage_flows",
            "Manage flows",
            "Bloco 9 (Flow Catalog)",
        )

    def _on_settings_requested(self) -> None:
        self._show_future_feature(
            "workspace.placeholder.settings",
            "Settings",
            "piece 7.6d (Settings)",
        )

    def _on_help_requested(self) -> None:
        self._show_future_feature(
            "workspace.placeholder.help",
            "Help",
            "piece 7.6d (Documentation)",
        )

    def _on_community_requested(self) -> None:
        self._show_future_feature(
            "workspace.placeholder.community",
            "Community",
            "a future piece",
        )

    def _on_library_requested(self) -> None:
        self._show_future_feature(
            "workspace.placeholder.library",
            "Object library",
            "a future piece",
        )

    def _on_news_requested(self) -> None:
        self._show_future_feature(
            "workspace.placeholder.news",
            "News",
            "a future piece",
        )

    def _on_feedback_requested(self) -> None:
        self._show_future_feature(
            "workspace.placeholder.feedback",
            "Suggest improvements",
            "a future piece",
        )

    def _on_contribute_requested(self) -> None:
        self._show_future_feature(
            "workspace.placeholder.contribute",
            "Contribute",
            "a future piece",
        )

    # ----- i18n ------------------------------------------------------

    def _tr(self, key: str, source: str, **params: object) -> str:
        if self._translation_service is None:
            return source
        return self._translation_service.tr(key, source, **params)

    def _show_future_feature(
        self,
        title_key: str,
        title_source: str,
        piece: str,
    ) -> None:
        QMessageBox.information(
            self,
            self._tr(title_key, title_source),
            self._tr(
                "workspace.placeholder.available_after_piece",
                "Available after {piece}.",
                piece=piece,
            ),
        )

    # ----- Convenience for tests -------------------------------------

    def home(self) -> HomePage:
        return self._home

    def current_workspace(self) -> Workspace | None:
        return self._workspace

    def current_project_id(self) -> ProjectId | None:
        return self._current_project_id
