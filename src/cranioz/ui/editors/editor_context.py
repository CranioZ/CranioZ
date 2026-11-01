"""EditorContext.

The EditorContext is the controlled set of dependencies an Editor
receives at insertion time. It is provided once per Editor and remains
stable throughout the Editor's lifetime (ADR-0002 §2.1).

Per ADR-0011 and ADR-0012, the context also carries the TaskManager
(for off-thread work) and the TelemetrySink (for events and
measurements), plus a ``correlation_id`` that identifies the
operation currently in progress.

The context is deliberately narrow. It is not a service locator:
every field is a specific, named dependency.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from cranioz.application.commands.dispatcher import CommandDispatcher
    from cranioz.application.events.base import EventSubscription
    from cranioz.application.scene.scene_query import SceneQuery
    from cranioz.application.tasks.base import TaskManager
    from cranioz.application.telemetry.base import TelemetrySink
    from cranioz.domain.scene.domain_object_store import DomainObjectStore


@dataclass(frozen=True)
class EditorContext:
    """Dependencies an Editor receives at insertion time."""

    # Required fields (no default).
    editor_id: str

    # Optional fields (with default).
    correlation_id: str | None = None
    extras: dict[str, Any] = field(default_factory=dict)
    task_manager: TaskManager | None = None
    telemetry: TelemetrySink | None = None
    command_dispatcher: CommandDispatcher | None = None
    scene_query: SceneQuery | None = None
    domain_object_store: DomainObjectStore | None = None
    event_subscription: EventSubscription | None = None
