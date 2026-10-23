"""CranioZ application entry point.

Boot sequence:
1. Load configuration.
2. Configure logging.
3. Create the QApplication.
4. Initialize application paths.
5. Initialize shared services (EventBus, CommandBus, TaskManager,
   TelemetrySink, ModuleRegistry).
6. Initialize the project subsystem.
7. Initialize the UI registries (editors, tools) and the theme service.
8. Create and show the MainWindow.
9. Start the Qt event loop.
"""

from __future__ import annotations

import getpass
import logging
import logging.config
from pathlib import Path

import yaml
from PySide6.QtWidgets import QApplication, QMessageBox

from cranioz import __version__
from cranioz.application.commands.in_memory_bus import InMemoryCommandBus
from cranioz.application.event_bus import EventBus
from cranioz.application.events import EventBusAdapter
from cranioz.application.flows.catalog import FlowCatalog
from cranioz.application.project.project_access_policy import (
    AllowAllProjectAccessPolicy,
)
from cranioz.application.project.project_catalog import ProjectCatalog
from cranioz.application.project.project_manager import ProjectManager
from cranioz.application.tasks.noop_task_manager import NoOpTaskManager
from cranioz.application.telemetry.noop_sink import NoOpTelemetrySink
from cranioz.config.loader import ConfigurationLoader
from cranioz.config.schema import Config
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
from cranioz.modules.builtin import BUILTIN_MANIFESTS
from cranioz.modules.registry.module_registry import InMemoryModuleRegistry
from cranioz.ui.editors.editor_registry import EditorRegistry
from cranioz.ui.main_window import MainWindow
from cranioz.ui.theme.service import ThemeName, ThemeService
from cranioz.ui.tools.builtin.log_tool import LogTool
from cranioz.ui.tools.builtin.toggle_tool import ToggleTool
from cranioz.ui.tools.registry.tool_registry import ToolRegistry

_logger = logging.getLogger(__name__)

_DEFAULT_LOGGING_CONFIG = Path(__file__).parent / "config" / "defaults" / "logging.yaml"


def _configure_logging(config: Config) -> None:
    if _DEFAULT_LOGGING_CONFIG.exists():
        with _DEFAULT_LOGGING_CONFIG.open("r", encoding="utf-8") as fh:
            logging.config.dictConfig(yaml.safe_load(fh))
    logging.getLogger().setLevel(config.logging.level)


def _resolve_actor() -> str:
    try:
        return getpass.getuser()
    except Exception:
        return "local-user"


def _build_tool_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register("tool.log", LogTool)
    registry.register("tool.toggle", ToggleTool)
    return registry


def _build_theme_service(config: Config) -> ThemeService:
    try:
        theme_name = ThemeName(config.app.theme.lower())
    except ValueError:
        theme_name = ThemeName.DARK
        _logger.warning(
            "unknown theme %r; falling back to %s",
            config.app.theme,
            theme_name.value,
        )
    return ThemeService(theme=theme_name)


def main() -> int:
    config = ConfigurationLoader().load()
    _configure_logging(config)
    _logger.info("CranioZ %s starting", __version__)

    app = QApplication.instance() or QApplication([])

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

    task_manager = NoOpTaskManager()
    telemetry = NoOpTelemetrySink()
    _logger.debug("TaskManager and TelemetrySink initialized (no-op)")

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

    # ----- UI services ------------------------------------------------
    editor_registry = EditorRegistry()
    tool_registry = _build_tool_registry()
    theme_service = _build_theme_service(config)
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
    )
    window.show()

    _logger.info("Boot complete; MainWindow shown (actor=%r)", actor)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
