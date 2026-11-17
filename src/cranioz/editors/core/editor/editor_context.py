"""EditorContext.

The EditorContext is the controlled set of dependencies an Editor
receives at insertion time. It is provided once per Editor and remains
stable throughout the Editor's lifetime (ADR-0002 §2.1).

Per ADR-0011 and ADR-0012, the context also carries the TaskManager
(for off-thread work) and the TelemetrySink (for events and
measurements), plus a ``correlation_id`` that identifies the
operation currently in progress.

The context also carries the TranslationService, so that Editors and
their Toolbars can resolve user-facing strings without importing the
global i18n instance (Sprint B).

The context is deliberately narrow. It is not a service locator:
every field is a specific, named dependency.

The context also carries the ThemeService and the IconProvider, so
that Editors and their Toolbars can resolve theme tokens and icons
without importing the global instances (Sprint C).
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
    from cranioz.infrastructure.i18n.translation_service import TranslationService
    from cranioz.ui.icons.provider import IconProvider
    from cranioz.ui.theme.service import ThemeService
    from cranioz.ui.tools.registry.tool_registry import ToolRegistry


@dataclass(frozen=True)
class EditorContext:
    """Dependencies an Editor receives at insertion time."""

    # Required fields (no default).
    editor_id: str

    # Optional fields (with default).
    # --- Application Layer (Commands, Events, and Tasks) ---
    command_dispatcher: CommandDispatcher | None = None
    task_manager: TaskManager | None = None
    event_subscription: EventSubscription | None = None
    tool_registry: ToolRegistry | None = None

    # --- Domain Layer ---
    domain_object_store: DomainObjectStore | None = None
    scene_query: SceneQuery | None = None

    # --- User Interface & Services (Themes, Icons, and Translation) ---
    translation_service: TranslationService | None = None
    theme_service: ThemeService | None = None
    icon_provider: IconProvider | None = None

    # --- Metadata & General ---
    correlation_id: str | None = None
    extras: dict[str, Any] = field(default_factory=dict)
    telemetry: TelemetrySink | None = None
