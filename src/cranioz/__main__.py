"""CranioZ application entry point.

Boot sequence:
1. Load configuration.
2. Configure logging.
3. Initialize the project path resolver.
4. Initialize the event bus.
5. Start the Qt application loop.

The main window is not created in this phase.
"""

from __future__ import annotations

import logging
import logging.config
from pathlib import Path

import yaml
from PySide6.QtWidgets import QApplication

from cranioz import __version__
from cranioz.application.event_bus import EventBus
from cranioz.config.loader import ConfigurationLoader
from cranioz.config.schema import Config
from cranioz.infrastructure.project_path_resolver import ProjectPathResolver

_logger = logging.getLogger(__name__)

_DEFAULT_LOGGING_CONFIG = (
    Path(__file__).parent / "config" / "defaults" / "logging.yaml"
)


def _configure_logging(config: Config) -> None:
    """Configure logging from the packaged YAML, then apply config overrides."""
    if _DEFAULT_LOGGING_CONFIG.exists():
        with _DEFAULT_LOGGING_CONFIG.open("r", encoding="utf-8") as fh:
            logging.config.dictConfig(yaml.safe_load(fh))
    logging.getLogger().setLevel(config.logging.level)


def main() -> int:
    """Run the CranioZ application."""
    config = ConfigurationLoader().load()
    _configure_logging(config)
    _logger.info("CranioZ %s starting", __version__)

    resolver = ProjectPathResolver()
    resolver.initialize(config.paths.project_root)
    _logger.info("Project root: %s", resolver.project_root)

    event_bus = EventBus()
    _logger.debug("Event bus initialized: %r", event_bus)

    app = QApplication.instance() or QApplication([])
    _logger.info("Boot complete")
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())