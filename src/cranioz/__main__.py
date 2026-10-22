"""CranioZ application entry point.

Boot sequence:
1. Load configuration.
2. Configure logging.
3. Create the QApplication.
4. Initialize the application path resolver.
5. Initialize the event bus.
6. Initialize the project subsystem (repository, catalog, manager).
7. Initialize the UI registries (editors, tools) and the theme service.
8. Create and show the MainWindow.
9. Start the Qt application loop.

The main window is the sole top-level window of the application. Without
it, the Qt event loop would idle with no visible window and the process
would appear to hang.
"""

from __future__ import annotations

import getpass
import logging
import logging.config
from pathlib import Path

import yaml
from PySide6.QtWidgets import QApplication, QMessageBox

from cranioz import __version__
from cranioz.application.event_bus import EventBus
from cranioz.application.project.project_access_policy import (
    AllowAllProjectAccessPolicy,
)
from cranioz.application.project.project_catalog import ProjectCatalog
from cranioz.application.project.project_manager import ProjectManager
from cranioz.config.loader import ConfigurationLoader
from cranioz.config.schema import Config
from cranioz.infrastructure.app.app_path_resolver import (
    AppPathInaccessible,
    AppPathResolver,
)
from cranioz.infrastructure.project.filesystem_project_repository import (
    FilesystemProjectRepository,
)
from cranioz.ui.editors.editor_registry import EditorRegistry
from cranioz.ui.main_window import MainWindow
from cranioz.ui.theme.service import ThemeName, ThemeService
from cranioz.ui.tools.builtin.log_tool import LogTool
from cranioz.ui.tools.builtin.toggle_tool import ToggleTool
from cranioz.ui.tools.registry.tool_registry import ToolRegistry

_logger = logging.getLogger(__name__)

_DEFAULT_LOGGING_CONFIG = Path(__file__).parent / "config" / "defaults" / "logging.yaml"


# ----- Internals ----------------------------------------------------


def _configure_logging(config: Config) -> None:
    """Configure logging from the packaged YAML, then apply config overrides."""
    if _DEFAULT_LOGGING_CONFIG.exists():
        with _DEFAULT_LOGGING_CONFIG.open("r", encoding="utf-8") as fh:
            logging.config.dictConfig(yaml.safe_load(fh))
    logging.getLogger().setLevel(config.logging.level)


def _resolve_actor() -> str:
    """Return the current OS username as the actor identifier.

    The actor is injected by the bootstrap; MainWindow does not
    construct one (ADR-0006 §2.6). When the application gains a
    proper user model, this function is replaced by a lookup
    against the authenticated user.
    """
    try:
        return getpass.getuser()
    except Exception:  # noqa: BLE001
        return "local-user"


def _build_tool_registry() -> ToolRegistry:
    """Build the ToolRegistry with the built-in tools.

    Built-in tools are registered at boot. Modules and plugins will
    register their own tools when they are activated.
    """
    registry = ToolRegistry()
    registry.register("tool.log", LogTool)
    registry.register("tool.toggle", ToggleTool)
    return registry


def _build_theme_service(config: Config) -> ThemeService:
    """Build the ThemeService from configuration.

    The configuration's ``theme`` value is resolved to a ``ThemeName``.
    Unknown values fall back to ``DARK`` (the current default), so a
    misconfigured theme does not prevent the application from starting.
    """
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


# ----- Main ---------------------------------------------------------


def main() -> int:
    """Run the CranioZ application."""
    # 1. Configuration.
    config = ConfigurationLoader().load()
    _configure_logging(config)
    _logger.info("CranioZ %s starting", __version__)

    # 2. QApplication. Created early so error dialogs can be shown
    #    before any window exists.
    app = QApplication.instance() or QApplication([])

    # 3. Application paths.
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

    # 4. Application services.
    event_bus = EventBus()
    _logger.debug("Event bus initialized: %r", event_bus)

    repository = FilesystemProjectRepository(
        projects_root=app_paths.projects_root,
    )
    catalog = ProjectCatalog(repository=repository)
    manager = ProjectManager(
        repository=repository,
        event_bus=event_bus,
        access_policy=AllowAllProjectAccessPolicy(),
    )

    editor_registry = EditorRegistry()
    tool_registry = _build_tool_registry()
    theme_service = _build_theme_service(config)
    actor = _resolve_actor()

    # 5. Main window.
    window = MainWindow(
        catalog=catalog,
        manager=manager,
        actor=actor,
        editor_registry=editor_registry,
        tool_registry=tool_registry,
        theme_service=theme_service,
    )
    window.show()

    _logger.info("Boot complete; MainWindow shown (actor=%r)", actor)

    # 6. Qt event loop.
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())