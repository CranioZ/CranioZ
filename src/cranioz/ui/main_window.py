"""MainWindow — the main_window shell."""

from __future__ import annotations

import logging
import os
import uuid
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from PySide6.QtCore import QEvent, QObject, QPoint, Qt
from PySide6.QtGui import QCloseEvent, QIcon, QMouseEvent
from PySide6.QtWidgets import (
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from cranioz.application.commands.base import CommandDispatchError
from cranioz.application.flows.catalog import FlowCatalog
from cranioz.application.flows.definition import FlowDefinition
from cranioz.application.project.catalog import ProjectCatalog
from cranioz.application.project.context import ProjectContext
from cranioz.application.project.errors import ProjectError
from cranioz.application.project.manager import ProjectManager
from cranioz.application.scene.commands.scene_commands import (
    ImportDicomSeriesCommand,
)
from cranioz.application.scene.handlers.scene_handlers import (
    ImportDicomSeriesHandler,
)
from cranioz.application.tasks.base import CancelToken
from cranioz.domain.project.project_id import ProjectId
from cranioz.editors.core.editor.editor_registry import EditorRegistry
from cranioz.editors.views.viewport_3d.mesh_debug_editor import (
    MESH_DEBUG_EDITOR_ID,
    MeshDebugEditor,
)
from cranioz.infrastructure.i18n.translation_service import TranslationService
from cranioz.infrastructure.scene.scene_query_adapter import SceneQueryAdapter
from cranioz.ui.home.home_page import HomePage
from cranioz.ui.home.project_management_page import ProjectManagementPage
from cranioz.ui.icons.provider import IconProvider
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

BORDER_WIDTH = 8
CONTAINER_MARGIN = 4


class WindowDragFilter(QObject):
    """Filtro que permite arrastar a janela clicando nos widgets filhos."""

    def __init__(self, window: QMainWindow) -> None:
        super().__init__(window)
        self._window = window
        self._drag_pos: QPoint | None = None

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:  # noqa: N802
        if isinstance(obj, QPushButton):
            return super().eventFilter(obj, event)

        if event.type() == QEvent.Type.MouseButtonPress:
            if event.button() == Qt.MouseButton.LeftButton:  # type: ignore[attr-defined]
                self._drag_pos = (
                    event.globalPosition().toPoint()  # type: ignore[attr-defined]
                    - self._window.frameGeometry().topLeft()
                )
                return False
        elif event.type() == QEvent.Type.MouseMove:
            if self._drag_pos is not None and event.buttons() == Qt.MouseButton.LeftButton:  # type: ignore[attr-defined]
                self._window.move(
                    event.globalPosition().toPoint() - self._drag_pos  # type: ignore[attr-defined]
                )
                return True
        elif event.type() == QEvent.Type.MouseButtonRelease:
            self._drag_pos = None

        return super().eventFilter(obj, event)


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
        icon_provider: IconProvider,
        translation_service: TranslationService | None = None,
        task_manager: TaskManager | None = None,
        telemetry: TelemetrySink | None = None,
        command_dispatcher: CommandDispatcher | None = None,
        command_bus: CommandBus | None = None,
        flow_catalog: FlowCatalog | None = None,
        scene_provider: SceneProvider | None = None,
        domain_object_store: DomainObjectStore | None = None,
        editor_context_extras: dict[str, Any] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._catalog = catalog
        self._manager = manager
        self._actor = actor
        self._editor_registry = editor_registry
        self._tool_registry = tool_registry
        self._theme_service = theme_service
        self._icon_provider = icon_provider
        self._translation_service = translation_service
        self._task_manager = task_manager
        self._telemetry = telemetry
        self._command_dispatcher = command_dispatcher
        self._command_bus = command_bus
        self._flow_catalog = flow_catalog
        self._scene_provider = scene_provider
        self._domain_object_store = domain_object_store
        self._editor_context_extras = dict(editor_context_extras or {})

        self._current_project_id: ProjectId | None = None
        self._workspace: Workspace | None = None
        self._management_return_widget: QWidget | None = None
        self._debug_mesh = os.environ.get("CRANIOZ_DEBUG_MESH") == "1"

        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowMinimizeButtonHint
            | Qt.WindowType.WindowMaximizeButtonHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setMouseTracking(True)

        self._drag_filter = WindowDragFilter(self)

        self._ensure_builtin_tools()
        self._editor_registry.register(PLACEHOLDER_EDITOR_ID, PLACEHOLDER_EDITOR_CLASS)
        if self._debug_mesh:
            self._editor_registry.register(MESH_DEBUG_EDITOR_ID, MeshDebugEditor)

        self._home = HomePage(
            catalog=self._catalog,
            parent=self,
            translation_service=self._translation_service,
            icon_provider=self._icon_provider,
        )
        self._project_management = ProjectManagementPage(
            self._catalog,
            icon_provider=self._icon_provider,
            parent=self,
        )
        self._stack = QStackedWidget(self)
        self._stack.addWidget(self._home)
        self._stack.addWidget(self._project_management)

        self._central_container = QWidget(self)
        container_layout = QVBoxLayout(self._central_container)
        container_layout.setContentsMargins(
            CONTAINER_MARGIN, CONTAINER_MARGIN, CONTAINER_MARGIN, CONTAINER_MARGIN
        )
        container_layout.setSpacing(0)
        container_layout.addWidget(self._stack)

        self.setCentralWidget(self._central_container)

        # Importante: aplica o mouse tracking também no container central
        # para que os eventos de mouse cheguem na MainWindow
        self._central_container.setMouseTracking(True)

        self._home._top_bar_widget().installEventFilter(self._drag_filter)
        if hasattr(self._home._top_bar_widget(), "_title"):
            self._home._top_bar_widget()._title.installEventFilter(self._drag_filter)

        self._connect_home_signals()
        self._connect_project_management_signals()
        self._dispatch_flow_loading()

        self.setWindowTitle(self._tr("core.app.name", "CranioZ"))
        self.resize(1000, 650)
        self._update_window_control_state()

    # ----- Redimensionamento Nativo (Qt 6) ---------------------------
    # (idêntico ao original; omitido aqui por brevidade — NÃO MUDA)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        pos = event.position().toPoint()
        edges = Qt.Edge(0)

        if pos.x() < BORDER_WIDTH:
            edges |= Qt.Edge.LeftEdge
        elif pos.x() > self.width() - BORDER_WIDTH:
            edges |= Qt.Edge.RightEdge

        if pos.y() < BORDER_WIDTH:
            edges |= Qt.Edge.TopEdge
        elif pos.y() > self.height() - BORDER_WIDTH:
            edges |= Qt.Edge.BottomEdge

        if edges:
            self.setCursor(self._cursor_for_edges(edges))
        else:
            self.unsetCursor()

        super().mouseMoveEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position().toPoint()
            edges = Qt.Edge(0)

            if pos.x() < BORDER_WIDTH:
                edges |= Qt.Edge.LeftEdge
            elif pos.x() > self.width() - BORDER_WIDTH:
                edges |= Qt.Edge.RightEdge

            if pos.y() < BORDER_WIDTH:
                edges |= Qt.Edge.TopEdge
            elif pos.y() > self.height() - BORDER_WIDTH:
                edges |= Qt.Edge.BottomEdge

            if edges:
                self.windowHandle().startSystemResize(edges)
                event.accept()
                return

        super().mousePressEvent(event)

    def _cursor_for_edges(self, edges: Qt.Edge) -> Qt.CursorShape:
        has_left = bool(edges & Qt.Edge.LeftEdge)
        has_right = bool(edges & Qt.Edge.RightEdge)
        has_top = bool(edges & Qt.Edge.TopEdge)
        has_bottom = bool(edges & Qt.Edge.BottomEdge)

        if (has_left and has_top) or (has_right and has_bottom):
            return Qt.CursorShape.SizeFDiagCursor
        if (has_right and has_top) or (has_left and has_bottom):
            return Qt.CursorShape.SizeBDiagCursor
        if has_left or has_right:
            return Qt.CursorShape.SizeHorCursor
        if has_top or has_bottom:
            return Qt.CursorShape.SizeVerCursor
        return Qt.CursorShape.ArrowCursor

    # ----- Built-in registration -------------------------------------

    def _ensure_builtin_tools(self) -> None:
        from cranioz.ui.tools.builtin.log_tool import LogTool  # noqa: PLC0415
        from cranioz.ui.tools.builtin.toggle_tool import ToggleTool  # noqa: PLC0415

        builtin_tools = (
            ("tool.log", LogTool),
            ("tool.toggle", ToggleTool),
        )
        for tool_id, factory in builtin_tools:
            if not self._tool_registry.contains(tool_id):
                self._tool_registry.register(tool_id, factory)

        from cranioz.editors.builtin.professional import ProfessionalEditor  # noqa: PLC0415
        from cranioz.editors.builtin.tomography.editor import TomographyEditor  # noqa: PLC0415

        self._editor_registry.register("editor.tomography", TomographyEditor)
        self._editor_registry.register("editor.professional", ProfessionalEditor)
        _logger.debug(
            "MainWindow registered editor.tomography -> %s",
            TomographyEditor.__module__,
        )

    # ----- HomePage signal wiring ------------------------------------

    def _connect_home_signals(self) -> None:
        home = self._home
        home.project_open_requested.connect(self._on_project_open_requested)
        home.new_project_requested.connect(self._on_new_project_requested)
        home.manage_projects_requested.connect(self._on_manage_projects_requested)
        home.manage_flows_requested.connect(self._on_manage_flows_requested)
        home.settings_requested.connect(self._on_settings_requested)
        home.help_requested.connect(self._on_help_requested)
        home.logs_requested.connect(self._on_logs_requested)
        home.community_requested.connect(self._on_community_requested)
        home.library_requested.connect(self._on_library_requested)
        home.news_requested.connect(self._on_news_requested)
        home.feedback_requested.connect(self._on_feedback_requested)
        home.contribute_requested.connect(self._on_contribute_requested)
        home.minimize_requested.connect(self.showMinimized)
        home.maximize_requested.connect(self._on_window_maximize_requested)
        home.close_requested.connect(self.close)

    def _connect_project_management_signals(self) -> None:
        page = self._project_management
        page.back_requested.connect(self._on_project_management_back_requested)
        page.new_project_requested.connect(self._on_new_project_requested)
        page.remove_projects_requested.connect(self._on_remove_projects_requested)
        page.export_projects_requested.connect(self._on_export_projects_requested)
        page.import_projects_requested.connect(self._on_import_projects_requested)
        page.logs_requested.connect(self._on_logs_requested)
        page.help_requested.connect(self._on_help_requested)
        page.settings_requested.connect(self._on_settings_requested)
        page.minimize_requested.connect(self.showMinimized)
        page.maximize_requested.connect(self._on_window_maximize_requested)
        page.close_requested.connect(self.close)

    # ----- Async flow loading (Sprint K) -----------------------------

    def _dispatch_flow_loading(self) -> None:
        flow_catalog = self._flow_catalog
        if flow_catalog is None:
            return

        if self._task_manager is None:
            self._load_flows_sync(flow_catalog)
            return

        self._home.flows_loading_started.emit()
        self._task_manager.dispatch(
            task=_LoadFlowsTask(flow_catalog),
            on_result=self._on_flows_loaded,
            on_error=self._on_flows_failed,
        )

    def _load_flows_sync(self, flow_catalog: FlowCatalog) -> None:
        try:
            definitions = tuple(flow_catalog.list_definitions())
        except Exception:
            _logger.exception("cannot load flows into the Home Page")
            self._home.flows_loading_failed.emit("cannot load flows")
            return
        self._home._flow_list_widget().set_flows(definitions)
        self._home.flows_loading_finished.emit()

    def _on_flows_loaded(self, definitions: tuple[FlowDefinition, ...]) -> None:
        """Task succeeded: install the flows on the GUI thread."""
        self._home._flow_list_widget().set_flows(definitions)
        self._home.flows_loading_finished.emit()

    def _on_flows_failed(self, exc: BaseException) -> None:
        """Task failed: log and notify. The placeholder stays visible."""
        _logger.exception("flow loading failed", exc_info=exc)
        self._home.flows_loading_failed.emit(str(exc))

    # ----- Project navigation ----------------------------------------

    def _on_project_open_requested(
        self,
        project_id: ProjectId,
        flow_id: str,
    ) -> None:
        """Open project with rollback on Workspace creation failure.

        Project opening is synchronous (fast, in-memory index).
        Workspace creation is synchronous on GUI thread (Qt requirement).
        If Workspace creation fails, we roll back by closing the project.
        """
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

        try:
            workspace = self._create_workspace(context)
        except Exception as exc:
            _logger.exception("Workspace creation failed for project %s; rolling back", project_id)
            QMessageBox.critical(
                self,
                self._tr("workspace.dialog.cannot_open_project", "Cannot open project"),
                self._tr(
                    "workspace.dialog.workspace_creation_failed",
                    "Failed to create workspace: {detail}",
                    detail=str(exc),
                ),
            )
            self._manager.close_project(self._actor, project_id)
            return

        self._stack.addWidget(workspace)
        self._stack.setCurrentWidget(workspace)
        self._workspace = workspace
        self._current_project_id = project_id
        self._register_dicom_import_handler()
        self._update_window_control_state()

    def _create_workspace(self, context: ProjectContext) -> Workspace:
        scene_query = None
        if self._scene_provider is not None:
            scene = self._scene_provider.get_scene()
            scene_query = SceneQueryAdapter(scene)

        workspace = Workspace(
            editor_registry=self._editor_registry,
            tool_registry=self._tool_registry,
            theme_service=self._theme_service,
            icon_provider=self._icon_provider,
            project_context=context,
            task_manager=self._task_manager,
            telemetry=self._telemetry,
            command_dispatcher=self._command_dispatcher,
            scene_query=scene_query,
            domain_object_store=self._domain_object_store,
            translation_service=self._translation_service,
            editor_context_extras=self._editor_context_extras,
        )

        home_segment = HomeSegment(self._icon_provider)
        modules_segment = ModulesSegment(self._icon_provider)
        extras_segment = ExtrasSegment(self._icon_provider)

        modules_segment.modules_changed.connect(self._on_top_bar_content_changed)
        modules_segment.set_modules((("tomography", "Tomografia"),))

        home_segment.set_project_open(True)

        self._wire_top_bar_segments(workspace, home_segment, modules_segment, extras_segment)

        workspace.top_overlay().set_left_content(home_segment)
        workspace.top_overlay().set_center_content(modules_segment)
        workspace.top_overlay().set_right_content(extras_segment)

        workspace.top_overlay().widget().installEventFilter(self._drag_filter)

        spec = WORKSPACE_SPEC_DEBUG_MESH if self._debug_mesh else WORKSPACE_SPEC_DEFAULT
        workspace.load_spec(spec)

        return workspace

    def _wire_top_bar_segments(
        self,
        workspace: Workspace,
        home: HomeSegment,
        modules: ModulesSegment,
        extras: ExtrasSegment,
    ) -> None:
        home.toggle_area_left_requested.connect(
            lambda: self._toggle_area(workspace, Placement.LEFT)
        )
        home.close_workspace_requested.connect(self._on_home_clicked)
        home.new_project_requested.connect(self._on_new_project_requested)
        home.open_project_requested.connect(self._on_manage_projects_requested)
        home.close_project_requested.connect(self._on_home_clicked)
        home.import_files_requested.connect(self._on_import_dicom_clicked)
        home.import_stl_debug_requested.connect(self._on_import_stl_debug_clicked)

        modules.add_module_requested.connect(self._on_manage_flows_requested)

        extras.settings_requested.connect(self._on_settings_requested)
        extras.themes_requested.connect(self._on_settings_requested)
        extras.help_requested.connect(self._on_help_requested)
        extras.updates_requested.connect(self._on_help_requested)
        extras.about_requested.connect(self._on_help_requested)
        extras.toggle_area_bottom_requested.connect(
            lambda: self._toggle_area(workspace, Placement.BOTTOM)
        )
        extras.toggle_area_right_requested.connect(
            lambda: self._toggle_area(workspace, Placement.RIGHT)
        )
        extras.minimize_requested.connect(self.showMinimized)
        extras.maximize_requested.connect(self._on_window_maximize_requested)
        extras.close_requested.connect(self.close)

    def _on_window_maximize_requested(self) -> None:
        if self.isFullScreen():
            self.showNormal()
        elif self.isMaximized():
            self.showFullScreen()
        else:
            self.showMaximized()
        self._update_window_control_state()

    def _update_window_control_state(self) -> None:
        if self.isFullScreen():
            icon_name = "window_restore"
            tooltip = self._tr("workspace.window.restore", "Restore")
        elif self.isMaximized():
            icon_name = "window_fullscreen"
            tooltip = self._tr("workspace.window.full_screen", "Full screen")
        else:
            icon_name = "window_maximize"
            tooltip = self._tr("workspace.window.maximize", "Maximize")

        icon = self._icon_provider.icon(icon_name)

        home = getattr(self, "_home", None)
        if home is not None:
            tb = home._top_bar_widget()
            if hasattr(tb, "_maximize_button"):
                self._set_window_control(tb._maximize_button, icon, tooltip)

        management = getattr(self, "_project_management", None)
        if management is not None:
            tb = management.top_bar()
            if hasattr(tb, "_maximize_button"):
                self._set_window_control(tb._maximize_button, icon, tooltip)

        if self._workspace is not None:
            right_segment = self._workspace.top_overlay().right_segment()
            extras = right_segment.findChild(ExtrasSegment)
            if extras and hasattr(extras, "_maximize_button"):
                self._set_window_control(extras._maximize_button, icon, tooltip)

    @staticmethod
    def _set_window_control(button: QPushButton, icon: QIcon, tooltip: str) -> None:
        button.setIcon(icon)
        button.setToolTip(tooltip)
        button.setAccessibleName(tooltip)

    def changeEvent(self, event: QEvent) -> None:  # noqa: N802
        super().changeEvent(event)
        if event.type() == QEvent.Type.WindowStateChange:
            self._update_window_control_state()

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        if self._current_project_id is not None:
            reply = QMessageBox.question(
                self,
                self._tr("workspace.dialog.confirm_close_title", "Close main_window?"),
                self._tr(
                    "workspace.dialog.confirm_close_body",
                    "There is an open project. Any unsaved changes will be lost. "
                    "Do you want to close the main_window?",
                ),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
            self._close_active_project()
        event.accept()

    def _on_top_bar_content_changed(self) -> None:
        if self._workspace is not None:
            self._workspace._schedule_layout_update()

    def _toggle_area(self, workspace: Workspace, placement: Placement) -> None:
        current = workspace.layout_state().is_visible(placement)
        workspace.set_area_visible(placement, not current)

    def _on_home_clicked(self) -> None:
        self._close_active_project()
        self._stack.setCurrentWidget(self._home)
        self._home.refresh()

    def _close_active_project(self) -> None:
        if self._current_project_id is None or self._workspace is None:
            return

        self._manager.close_project(self._actor, self._current_project_id)
        self._unregister_dicom_import_handler()
        self._stack.removeWidget(self._workspace)
        self._workspace.setParent(None)
        self._workspace.deleteLater()
        self._workspace = None
        self._current_project_id = None

    def _register_dicom_import_handler(self) -> None:
        if self._command_bus is None:
            return
        if self._scene_provider is None or self._domain_object_store is None:
            return

        handler = ImportDicomSeriesHandler(
            scene=self._scene_provider.get_scene(),
            object_store=self._domain_object_store,
        )
        self._command_bus.register(ImportDicomSeriesCommand, handler)

    def _unregister_dicom_import_handler(self) -> None:
        if self._command_bus is None:
            return
        self._command_bus.unregister(ImportDicomSeriesCommand)

    def _on_import_dicom_clicked(self) -> None:
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
                    "No 3D viewport in the scene. Run the main_window with "
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
    # (idênticos ao original; omitidos por brevidade — NÃO MUDAM)

    def _on_new_project_requested(self) -> None:
        self._show_future_feature(
            "workspace.placeholder.new_project",
            "New project",
            "Bloco 8 (Patient Module)",
        )

    def _on_manage_projects_requested(self) -> None:
        self._management_return_widget = self._stack.currentWidget()
        self._project_management.refresh()
        self._stack.setCurrentWidget(self._project_management)

    def _on_project_management_back_requested(self) -> None:
        target = self._management_return_widget
        if target is None or target is self._project_management:
            target = self._home
        self._stack.setCurrentWidget(target)
        self._management_return_widget = None

    def _on_remove_projects_requested(self, project_ids: object) -> None:
        if not isinstance(project_ids, tuple) or not project_ids:
            return

        count = len(project_ids)
        reply = QMessageBox.question(
            self,
            self._tr(
                "homepage.project_management.confirm_remove_title",
                "Remove projects?",
            ),
            self._tr(
                "homepage.project_management.confirm_remove_body",
                "Remove {count} selected project(s)? This action cannot be undone.",
                count=count,
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        failures: list[str] = []
        for project_id in project_ids:
            if not isinstance(project_id, ProjectId):
                continue
            try:
                self._manager.delete_project(self._actor, project_id)
            except ProjectError as exc:
                failures.append(f"{project_id.value}: {exc}")

        self._home.refresh()
        self._project_management.refresh()

        if failures:
            QMessageBox.critical(
                self,
                self._tr(
                    "homepage.project_management.remove_failed_title",
                    "Could not remove projects",
                ),
                "\n".join(failures),
            )

    def _on_export_projects_requested(self, _project_ids: object) -> None:
        self._show_future_feature(
            "homepage.project_management.export_projects",
            "Export project",
            "Phase 8",
        )

    def _on_import_projects_requested(self) -> None:
        self._show_future_feature(
            "homepage.project_management.import_projects",
            "Import project",
            "Phase 8",
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

    def _on_logs_requested(self) -> None:
        self._show_future_feature(
            "homepage.top_bar.logs",
            "Logs",
            "monitor_logs.md",
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
            try:
                return source.format(**params) if params else source
            except (KeyError, IndexError, ValueError):
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

    def project_management(self) -> ProjectManagementPage:
        return self._project_management

    def current_workspace(self) -> Workspace | None:
        return self._workspace

    def current_project_id(self) -> ProjectId | None:
        return self._current_project_id


# ----- Task definition (module-level for picklability) --------------


class _LoadFlowsTask:
    def __init__(self, flow_catalog: FlowCatalog) -> None:
        self._flow_catalog = flow_catalog

    def run(
        self,
        progress: Callable[[float], None],
        cancel_token: CancelToken,
    ) -> tuple[FlowDefinition, ...]:
        progress(0.0)
        cancel_token.raise_if_cancelled()
        definitions = tuple(self._flow_catalog.list_definitions())
        cancel_token.raise_if_cancelled()
        progress(1.0)
        return definitions
