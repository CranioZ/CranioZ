"""CranioZ application entry point.

Boot sequence:
1. Load configuration.
2. Configure logging.
3. Configure QSurfaceFormat (VTK needs depth/stencil).
4. Create the QApplication.
5. Initialize application paths.
6. Initialize shared services (EventBus, CommandBus, CommandStack,
   CommandExecutor, TaskManager, TelemetrySink, ModuleRegistry).
7. Initialize the project subsystem.
8. Initialize the UI registries (editors, tools) and the theme service.
9. Create and show the MainWindow.
10. Start the Qt event loop.
"""

from __future__ import annotations

import getpass
import logging
import logging.config
from pathlib import Path

import yaml

# ----- VTK / OpenGL configuration ------------------------------------
# These MUST run before the first QApplication is created. Qt reads
# the global QSurfaceFormat and the AA_ShareOpenGLContexts attribute
# exactly once, at application startup. If they are set after the
# QApplication, they are silently ignored and QVTKRenderWindowInteractor
# fails with "wglMakeCurrent failed" on some Intel drivers.
#
# The cranioz.* imports are deliberately deferred to main() so that
# they cannot create a QApplication before this block runs. Some
# VTK/PySide6 modules create a QApplication as a side effect of being
# imported.
from PySide6.QtCore import Qt
from PySide6.QtGui import QSurfaceFormat
from PySide6.QtWidgets import QApplication, QMessageBox

QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)

_fmt = QSurfaceFormat()
_fmt.setDepthBufferSize(24)
_fmt.setStencilBufferSize(8)
_fmt.setVersion(3, 2)
_fmt.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)
QSurfaceFormat.setDefaultFormat(_fmt)

_logger = logging.getLogger(__name__)

_DEFAULT_LOGGING_CONFIG = Path(__file__).parent / "config" / "defaults" / "logging.yaml"


def _configure_logging(config: "Config") -> None:
    if _DEFAULT_LOGGING_CONFIG.exists():
        with _DEFAULT_LOGGING_CONFIG.open("r", encoding="utf-8") as fh:
            logging.config.dictConfig(yaml.safe_load(fh))
    logging.getLogger().setLevel(config.logging.level)


def _resolve_actor() -> str:
    try:
        return getpass.getuser()
    except Exception:
        return "local-user"


def main() -> int:
    # Import cranioz.* only after the QSurfaceFormat is configured.
    # Importing them at module level would run before the QSurfaceFormat
    # block, and some of them may create a QApplication as a side effect.
    from cranioz import __version__
    from cranioz.application.commands.executor import CommandExecutor
    from cranioz.application.commands.in_memory_bus import InMemoryCommandBus
    from cranioz.application.commands.stack import InMemoryCommandStack
    from cranioz.application.commands.transaction import (
        InMemoryTransactionManager,
    )
    from cranioz.application.event_bus import EventBus
    from cranioz.application.events import EventBusAdapter
    from cranioz.application.flows.catalog import FlowCatalog
    from cranioz.application.project.project_access_policy import (
        AllowAllProjectAccessPolicy,
    )
    from cranioz.application.project.project_catalog import ProjectCatalog
    from cranioz.application.project.project_manager import ProjectManager
    from cranioz.application.scene.scene_provider import InMemorySceneProvider
    from cranioz.config.loader import ConfigurationLoader
    from cranioz.config.schema import Config
    from cranioz.domain.scene.domain_object_store import DomainObjectStore
    from cranioz.infrastructure.app.app_path_resolver import (
        AppPathInaccessible,
        AppPathResolver,
    )
    from cranioz.infrastructure.flows.filesystem_flow_repository import (
        FilesystemFlowRepository,
    )
    from cranioz.infrastructure.project.filesystem_project_repository import (
        FilesystemProjectRepository,
    )
    from cranioz.infrastructure.tasks.qt_task_manager import QtTaskManager
    from cranioz.infrastructure.telemetry.logging_sink import (
        LoggingTelemetrySink,
    )
    from cranioz.modules.builtin import BUILTIN_MANIFESTS
    from cranioz.modules.registry.module_registry import (
        InMemoryModuleRegistry,
    )
    from cranioz.ui.editors.editor_registry import EditorRegistry
    from cranioz.ui.editors.tomography.editor import TomographyEditor
    from cranioz.ui.main_window import MainWindow
    from cranioz.ui.theme.service import ThemeName, ThemeService
    from cranioz.ui.tools.builtin.log_tool import LogTool
    from cranioz.ui.tools.builtin.toggle_tool import ToggleTool
    from cranioz.ui.tools.registry.tool_registry import ToolRegistry

    config = ConfigurationLoader().load()
    _configure_logging(config)
    _logger.info("CranioZ %s starting", __version__)

    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    else:
        _logger.warning(
            "QApplication already exists; QSurfaceFormat and "
            "AA_ShareOpenGLContexts were not applied. VTK may fail "
            "to create an OpenGL context."
        )

    # ----- Application paths -----------------------------------------
    app_paths = AppPathResolver()
    try:
        app_paths.initialize(config.paths)
    except AppPathInaccessible as exc:
        _logger.exception("cannot initialize application paths")
        QMessageBox.critical(
            None,
            "CranioZ cannot start",
            f"The application paths could not be initialized:\n\n{exc}",
        )
        return 1
    _logger.info("Projects root: %s", app_paths.projects_root)

    # ----- Shared services -------------------------------------------
    event_bus = EventBus()
    _logger.debug("Event bus initialized: %r", event_bus)

    command_bus = InMemoryCommandBus()
    _logger.debug("Command bus initialized: %r", command_bus)

    command_stack = InMemoryCommandStack()
    transaction_manager = InMemoryTransactionManager()
    command_dispatcher = CommandExecutor(
        command_bus=command_bus,
        command_stack=command_stack,
        event_bus=event_bus,
        transaction_manager=transaction_manager,
    )
    _logger.debug("CommandDispatcher initialized: %r", command_dispatcher)

    task_manager = QtTaskManager()
    telemetry = LoggingTelemetrySink()
    _logger.debug(
        "TaskManager initialized (QtTaskManager); "
        "TelemetrySink initialized (LoggingTelemetrySink)"
    )

    event_bus_adapter = EventBusAdapter(event_bus)
    _logger.debug("EventBusAdapter initialized: %r", event_bus_adapter)

    module_registry = InMemoryModuleRegistry()
    for manifest in BUILTIN_MANIFESTS:
        module_registry.register(manifest)
    _logger.debug("ModuleRegistry initialized: %r", module_registry)

    # ----- Project subsystem -----------------------------------------
    repository = FilesystemProjectRepository(
        projects_root=app_paths.projects_root,
    )
    catalog = ProjectCatalog(repository=repository)
    manager = ProjectManager(
        repository=repository,
        event_bus=event_bus,
        access_policy=AllowAllProjectAccessPolicy(),
    )

    # ----- Scene -----------------------------------------------------
    scene_provider = InMemorySceneProvider()
    domain_object_store = DomainObjectStore()
    _logger.debug("SceneProvider initialized: %r", scene_provider)
    _logger.debug("DomainObjectStore initialized: %r", domain_object_store)

    # ----- UI services ------------------------------------------------
    editor_registry = EditorRegistry()
    editor_registry.register("editor.tomography", TomographyEditor)
    tool_registry = ToolRegistry()
    tool_registry.register("tool.log", LogTool)
    tool_registry.register("tool.toggle", ToggleTool)

    try:
        theme_name = ThemeName(config.app.theme.lower())
    except ValueError:
        theme_name = ThemeName.DARK
        _logger.warning(
            "unknown theme %r; falling back to %s",
            config.app.theme,
            theme_name.value,
        )
    theme_service = ThemeService(theme=theme_name)
    actor = _resolve_actor()

    # ----- Flows -------------------------------------------------------
    flow_repository = FilesystemFlowRepository(
        flows_root=app_paths.flows_root,
    )
    flow_catalog = FlowCatalog(repository=flow_repository)
    _logger.debug("FlowCatalog initialized: %r", flow_catalog)

    # ----- Main window ------------------------------------------------
    window = MainWindow(
        catalog=catalog,
        manager=manager,
        actor=actor,
        editor_registry=editor_registry,
        tool_registry=tool_registry,
        theme_service=theme_service,
        task_manager=task_manager,
        telemetry=telemetry,
        flow_catalog=flow_catalog,
        command_dispatcher=command_dispatcher,
        scene_provider=scene_provider,
        domain_object_store=domain_object_store,
    )
    window.show()

    _logger.info("Boot complete; MainWindow shown (actor=%r)", actor)
    exit_code = app.exec()
    _logger.info("Qt event loop exited; shutting down TaskManager")
    task_manager.shutdown()
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())