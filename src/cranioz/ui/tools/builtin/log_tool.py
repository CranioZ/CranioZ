"""LogTool.

Minimal Tool used for tests and early integration.
It logs a message when triggered. It does not modify the Scene.
"""

from __future__ import annotations

import logging

from cranioz.ui.tools.registry.tool_definition import ToolContext

_logger = logging.getLogger(__name__)


class LogTool:
    """A Tool that logs a message."""

    identifier = "tool.log"
    label = "Log"
    description = "Logs a message"
    icon: str | None = "log"
    category: str | None = None

    def __init__(self, message: str = "tool triggered") -> None:
        self.message = message

    def is_available(self, context: ToolContext) -> bool:
        return bool(context.extras.get("available", True))

    def is_enabled(self, context: ToolContext) -> bool:
        return bool(context.extras.get("enabled", True))

    def execute(self, context: ToolContext) -> None:
        _logger.info("%s: %s", self.identifier, self.message)
