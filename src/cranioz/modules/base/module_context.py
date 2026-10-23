"""ModuleContext — the dependencies a Module receives at load time.

``ModuleContext`` is an immutable snapshot. It carries the platform
services the Module needs: event subscription/publisher, the command
bus, the task manager, the current project provider, the service
container, and the telemetry sink. It does not carry the Scene, the
Project aggregate, or the Workspace.

``project_provider`` is a callable rather than a frozen context, so
that a Module loaded before a project opens can still access the
current project when one becomes available. Modules must not cache the
result across project open/close transitions.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cranioz.application.commands.bus import CommandBus
    from cranioz.application.events.base import (
        EventPublisher,
        EventSubscription,
    )
    from cranioz.application.project.project_context import ProjectContext
    from cranioz.application.services.container import ServiceContainer
    from cranioz.application.tasks.base import TaskManager
    from cranioz.application.telemetry.base import TelemetrySink


@dataclass(frozen=True)
class ModuleContext:
    """Immutable snapshot of the dependencies a Module receives."""

    module_id: str
    correlation_id: str | None
    event_subscription: EventSubscription
    event_publisher: EventPublisher
    command_bus: CommandBus
    task_manager: TaskManager
    project_provider: Callable[[], ProjectContext | None]
    services: ServiceContainer
    telemetry: TelemetrySink

    def __post_init__(self) -> None:
        if not self.module_id:
            raise ValueError("ModuleContext.module_id must not be empty")
        if self.correlation_id is not None and not self.correlation_id:
            raise ValueError(
                "ModuleContext.correlation_id, when set, must not be empty"
            )
