"""CranioZ application entry point.

Boot sequence:
1. Load configuration.
2. Configure logging.
3. Configure QSurfaceFormat (VTK needs compatibility profile).
4. Create the QApplication.
5. Initialize application paths.
6. Initialize shared services (EventBus, CommandBus, CommandStack,
   CommandExecutor, TaskManager, TelemetrySink, ModuleRegistry).
7. Initialize the project subsystem.
8. Initialize user settings (readable/writable, distinct from config).
9. Initialize the UI registries (editors, tools) and the theme service.
10. Compile and apply the theme (QSS) before the first window.
11. Create and show the MainWindow.
12. Start the Qt event loop.
"""

from __future__ import annotations

# Standard Library
import getpass
import logging
import logging.config
import os
from pathlib import Path

# Third-Party Libraries
import vtk
import yaml
from PySide6.QtCore import Qt
from PySide6.QtGui import QSurfaceFormat
from PySide6.QtWidgets import QApplication, QMessageBox

# ----- VTK / OpenGL configuration (CRITICAL: Must run before QApplication) -----
# VTK 9 + PySide6 on Windows requires OpenGL 2.1 Compatibility Profile to avoid
# white screens or crashes. Do not move below QApplication creation.

vtk.vtkObject.GlobalWarningDisplayOff()
os.environ.setdefault("VTK_DEFAULT_OPENGL_WINDOW", "vtkWin32OpenGLRenderWindow")

QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)

_fmt = QSurfaceFormat()
_fmt.setDepthBufferSize(24)
_fmt.setStencilBufferSize(8)
_fmt.setVersion(2, 1)
_fmt.setProfile(QSurfaceFormat.OpenGLContextProfile.CompatibilityProfile)
QSurfaceFormat.setDefaultFormat(_fmt)

# =====================================================================
# Local Imports (cranioz.*)
# =====================================================================

# --- Application Layer (Commands, Events, Flows, and Projects) ---
from cranioz import __version__  # noqa: E402
from cranioz.application.commands.executor import CommandExecutor  # noqa: E402
from cranioz.application.commands.in_memory_bus import InMemoryCommandBus  # noqa: E402
from cranioz.application.commands.stack import InMemoryCommandStack  # noqa: E402
from cranioz.application.commands.transaction import (  # noqa: E402
    InMemoryTransactionManager,
)
from cranioz.application.event_bus import EventBus  # noqa: E402
from cranioz.application.events import EventBusAdapter  # noqa: E402
from cranioz.application.flows.catalog import FlowCatalog  # noqa: E402
from cranioz.application.project.project_access_policy import (  # noqa: E402
    AllowAllProjectAccessPolicy,
)
from cranioz.application.project.project_catalog import ProjectCatalog  # noqa: E402
from cranioz.application.project.project_manager import ProjectManager  # noqa: E402
from cranioz.application.scene.scene_provider import (  # noqa: E402
    InMemorySceneProvider,
)
from cranioz.config.loader import ConfigurationLoader  # noqa: E402
from cranioz.config.schema import Config  # noqa: E402

# --- Domain Layer ---
from cranioz.domain.scene.domain_object_store import DomainObjectStore  # noqa: E402

# --- Infrastructure: Application paths, settings, flows, i18n ---
from cranioz.infrastructure.app.app_path_resolver import (  # noqa: E402
    AppPathInaccessible,
    AppPathResolver,
)
from cranioz.infrastructure.flows.filesystem_flow_repository import (  # noqa: E402
    FilesystemFlowRepository,
)
from cranioz.infrastructure.i18n.catalog_loader import CatalogLoader  # noqa: E402
from cranioz.infrastructure.i18n.catalog_registry import (  # noqa: E402
    TranslationCatalogRegistry,
)
from cranioz.infrastructure.i18n.instance import (  # noqa: E402
    configure as configure_translation,
)
from cranioz.infrastructure.i18n.translation_service import (  # noqa: E402
    CatalogTranslationService,
)
from cranioz.infrastructure.project.filesystem_project_repository import (  # noqa: E402
    FilesystemProjectRepository,
)
from cranioz.infrastructure.settings.filesystem_settings_service import (  # noqa: E402
    FilesystemSettingsService,
)
from cranioz.infrastructure.settings.protocol import (  # noqa: E402
    SettingsService,
)
from cranioz.infrastructure.tasks.qt_task_manager import QtTaskManager  # noqa: E402
from cranioz.infrastructure.telemetry.logging_sink import (  # noqa: E402
    LoggingTelemetrySink,
)

# --- Modules ---
from cranioz.modules.builtin import BUILTIN_MANIFESTS  # noqa: E402
from cranioz.modules.registry.module_registry import (  # noqa: E402
    InMemoryModuleRegistry,
)

# --- User Interface: Editors ---
from cranioz.ui.editors.editor_registry import EditorRegistry  # noqa: E402
from cranioz.ui.editors.tomography.editor import TomographyEditor  # noqa: E402

# --- Icons ---
from cranioz.ui.icons import UnicodeIconProvider  # noqa: E402

# --- User Interface: Main Window ---
from cranioz.ui.main_window import MainWindow  # noqa: E402
from cranioz.ui.theme import ThemeMode, ThemeService  # noqa: E402

# --- User Interface: Tools ---
from cranioz.ui.tools.builtin.log_tool import LogTool  # noqa: E402
from cranioz.ui.tools.builtin.toggle_tool import ToggleTool  # noqa: E402
from cranioz.ui.tools.registry.tool_registry import ToolRegistry  # noqa: E402

_logger = logging.getLogger(__name__)

_DEFAULT_LOGGING_CONFIG = Path(__file__).parent / "config" / "defaults" / "logging.yaml"


# ----- Helpers -------------------------------------------------------


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


def _build_shared_services(
    event_bus: EventBus,
) -> tuple[
    InMemoryCommandBus,
    CommandExecutor,
    QtTaskManager,
    LoggingTelemetrySink,
    EventBusAdapter,
    InMemoryModuleRegistry,
]:
    """Build the shared application services (bus, stack, tasks, ...)."""
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
        "TaskManager initialized (QtTaskManager); TelemetrySink initialized (LoggingTelemetrySink)"
    )

    event_bus_adapter = EventBusAdapter(event_bus)
    _logger.debug("EventBusAdapter initialized: %r", event_bus_adapter)

    module_registry = InMemoryModuleRegistry()
    for manifest in BUILTIN_MANIFESTS:
        module_registry.register(manifest)
    _logger.debug("ModuleRegistry initialized: %r", module_registry)

    return (
        command_bus,
        command_dispatcher,
        task_manager,
        telemetry,
        event_bus_adapter,
        module_registry,
    )


def _build_project_subsystem(
    app_paths: AppPathResolver,
    event_bus: EventBus,
) -> tuple[ProjectCatalog, ProjectManager]:
    """Build the project subsystem (repository, catalog, manager)."""
    repository = FilesystemProjectRepository(
        projects_root=app_paths.projects_root,
    )
    catalog = ProjectCatalog(repository=repository)
    manager = ProjectManager(
        repository=repository,
        event_bus=event_bus,
        access_policy=AllowAllProjectAccessPolicy(),
    )
    return catalog, manager


def _build_ui_registries() -> tuple[EditorRegistry, ToolRegistry]:
    """Build the UI registries (editors, tools)."""
    editor_registry = EditorRegistry()
    editor_registry.register("editor.tomography", TomographyEditor)

    tool_registry = ToolRegistry()
    tool_registry.register("tool.log", LogTool)
    tool_registry.register("tool.toggle", ToggleTool)

    return editor_registry, tool_registry


def _build_theme_service(
    config: Config,
    settings: SettingsService,
) -> ThemeService:
    """Build the theme service.

    ``config.app.theme`` is the *initial default* used when
    ``appearance.theme_mode`` is absent from the user settings. Once
    the user chooses a theme, the persisted value wins.
    """
    try:
        default_mode = ThemeMode(config.app.theme.lower())
    except ValueError:
        default_mode = ThemeMode.DARK
        _logger.warning(
            "unknown theme %r in app.json; falling back to %s",
            config.app.theme,
            default_mode.value,
        )
    return ThemeService(
        settings=settings,
        default_mode=default_mode,
    )


def _build_flow_catalog(app_paths: AppPathResolver) -> FlowCatalog:
    """Build the flow catalog from the filesystem."""
    flow_repository = FilesystemFlowRepository(
        flows_root=app_paths.flows_root,
    )
    flow_catalog = FlowCatalog(repository=flow_repository)
    _logger.debug("FlowCatalog initialized: %r", flow_catalog)
    return flow_catalog


def _build_translation_service(config: Config) -> CatalogTranslationService:
    translations_root = Path(__file__).parent / "translations"
    loader = CatalogLoader(translations_root)
    registry = TranslationCatalogRegistry(loader)
    service = CatalogTranslationService(registry, language=config.app.language)
    configure_translation(service)
    return service


# ----- Main ----------------------------------------------------------


def main() -> int:
    config = ConfigurationLoader().load()
    translation_service = _build_translation_service(config)
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
            translation_service.tr(
                "core.errors.startup_failed.title",
                "CranioZ cannot start",
            ),
            translation_service.tr(
                "core.errors.startup_failed.paths",
                "The application paths could not be initialized:\n\n{detail}",
                detail=exc,
            ),
        )
        return 1
    _logger.info("Projects root: %s", app_paths.projects_root)

    # ----- Shared services -------------------------------------------
    event_bus = EventBus()
    _logger.debug("Event bus initialized: %r", event_bus)

    (
        command_bus,
        command_dispatcher,
        task_manager,
        telemetry,
        _event_bus_adapter,
        _module_registry,
    ) = _build_shared_services(event_bus)

    # ----- Project subsystem -----------------------------------------
    catalog, manager = _build_project_subsystem(app_paths, event_bus)

    # ----- Scene -----------------------------------------------------
    scene_provider = InMemorySceneProvider()
    domain_object_store = DomainObjectStore()
    _logger.debug("SceneProvider initialized: %r", scene_provider)
    _logger.debug("DomainObjectStore initialized: %r", domain_object_store)

    # ----- User settings (readable/writable, distinct from config) ---
    settings = FilesystemSettingsService(
        path=app_paths.user_settings_path(),
    )
    _logger.debug("SettingsService initialized: %r", settings)

    # ----- UI services ------------------------------------------------
    editor_registry, tool_registry = _build_ui_registries()
    theme_service = _build_theme_service(config, settings)
    theme_service.compiler().apply(theme_service.compiled())
    icon_provider = UnicodeIconProvider(theme_service)
    _logger.debug("ThemeService initialized and applied: %r", theme_service)
    actor = _resolve_actor()

    # ----- Flows ------------------------------------------------------
    flow_catalog = _build_flow_catalog(app_paths)

    # ----- Main window ------------------------------------------------
    window = MainWindow(
        catalog=catalog,
        manager=manager,
        actor=actor,
        editor_registry=editor_registry,
        tool_registry=tool_registry,
        theme_service=theme_service,
        icon_provider=icon_provider,
        task_manager=task_manager,
        telemetry=telemetry,
        flow_catalog=flow_catalog,
        command_dispatcher=command_dispatcher,
        command_bus=command_bus,
        scene_provider=scene_provider,
        domain_object_store=domain_object_store,
        translation_service=translation_service,
    )
    window.show()

    _logger.info("Boot complete; MainWindow shown (actor=%r)", actor)
    exit_code = app.exec()
    _logger.info("Qt event loop exited; shutting down TaskManager")
    task_manager.shutdown()
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
