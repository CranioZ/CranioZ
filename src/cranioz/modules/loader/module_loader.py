"""ModuleLoader — reference implementation (modules.md v10 §11).

The loader resolves dependencies (in the real implementation) or
receives instances (in this in-memory reference), registers their
contributions, calls the lifecycle hooks, and tracks their state.

This file provides:

- ``ModuleLoader`` — the Protocol.
- ``InMemoryModuleLoader`` — a reference implementation that receives
  pre-instantiated Modules and simulates the lifecycle. It does not
  import anything; it does not load manifests from disk. It is used by
  tests and by the early bootstrap.
"""

from __future__ import annotations

import contextlib
import logging
from typing import Any, Protocol, cast, runtime_checkable

from cranioz.application.commands.base import Command, CommandHandler
from cranioz.application.commands.bus import CommandBus
from cranioz.application.event_bus import EventBus
from cranioz.application.events import EventBusAdapter
from cranioz.application.events.base import (
    EventPublisher,
    EventSubscription,
)
from cranioz.application.services import EmptyServiceContainer
from cranioz.application.tasks.base import TaskManager
from cranioz.application.telemetry.base import TelemetrySink
from cranioz.modules.base.module import Module
from cranioz.modules.base.module_context import ModuleContext
from cranioz.modules.base.module_state import ModuleState
from cranioz.modules.errors import (
    ModuleInUse,
    ModuleLoadFailed,
    ModuleNotFound,
)
from cranioz.modules.loader._null_task_manager import _NULL_TASK_MANAGER
from cranioz.modules.registry.module_registry import ModuleRegistry

_logger = logging.getLogger(__name__)


@runtime_checkable
class ModuleLoader(Protocol):
    """Loads and unloads Modules.

    The loader does **not** activate Modules. Activation (materializing
    a ModuleUISpec in the Workspace) is the Application layer's
    responsibility (``modules.md`` v10 §11.5).
    """

    def load(self, module_id: str) -> Module: ...

    def unload(self, module_id: str) -> None: ...

    def get_instance(self, module_id: str) -> Module | None: ...


class InMemoryModuleLoader:
    """Reference implementation of ``ModuleLoader``.

    Receives pre-instantiated Modules (``instances``) and a
    ``ModuleRegistry``. It registers contributions in the platform
    registries (CommandBus and TelemetrySink are the only ones
    available in this piece; the rest are registered once their
    registries exist).

    Rollback: if a registration raises, the loader restores the
    registry state to ``REGISTERED`` and discards the instance. The
    next ``load`` call creates no new instance (the instance is
    supplied by the caller and reused if present).

    This loader does not import ``entry_point``. It expects
    ``instances`` to be pre-built. The real loader (which imports
    ``entry_point`` and constructs the Module) is delivered later.
    """

    def __init__(
        self,
        *,
        registry: ModuleRegistry,
        instances: dict[str, Module],
        command_bus: CommandBus,
        telemetry: TelemetrySink,
    ) -> None:
        self._registry = registry
        self._instances = instances
        self._command_bus = command_bus
        self._telemetry = telemetry

    # ----- Load -----------------------------------------------------

    def load(self, module_id: str) -> Module:
        manifest = self._registry.get(module_id)
        if manifest is None:
            raise ModuleNotFound(f"module not registered: {module_id!r}")

        state = self._registry.state(module_id)
        if state is ModuleState.LOADED:
            instance = self._instances.get(module_id)
            if instance is None:
                raise ModuleLoadFailed(
                    f"registry says {module_id!r} is loaded but no instance "
                    f"is held"
                )
            return instance
        if state is ModuleState.ACTIVE:
            instance = self._instances.get(module_id)
            if instance is None:
                raise ModuleLoadFailed(
                    f"registry says {module_id!r} is active but no instance "
                    f"is held"
                )
            return instance

        instance = self._instances.get(module_id)
        if instance is None:
            raise ModuleLoadFailed(
                f"no instance supplied for module {module_id!r}"
            )

        registered_handlers: list[type[Command]] = []
        try:
            for command_type in instance.commands():
                handler = self._resolve_handler(command_type)
                self._command_bus.register(command_type, handler)
                registered_handlers.append(command_type)

            context = self._build_context(module_id)
            instance.on_load(context)
        except Exception as exc:
            for command_type in reversed(registered_handlers):
                with contextlib.suppress(Exception):
                    self._command_bus.unregister(command_type)
            self._registry.set_state(module_id, ModuleState.REGISTERED)
            raise ModuleLoadFailed(
                f"failed to load module {module_id!r}: {exc}"
            ) from exc

        self._registry.set_state(module_id, ModuleState.LOADED)
        return instance

    # ----- Unload ---------------------------------------------------

    def unload(self, module_id: str) -> None:
        manifest = self._registry.get(module_id)
        if manifest is None:
            raise ModuleNotFound(f"module not registered: {module_id!r}")

        state = self._registry.state(module_id)
        if state is ModuleState.REGISTERED:
            return
        if state is ModuleState.ACTIVE:
            raise ModuleInUse(
                f"cannot unload {module_id!r}: state is 'active'"
            )

        for other in self._registry.list():
            if other.module_id == module_id:
                continue
            for dep in other.dependencies:
                if dep.module_id == module_id:
                    other_state = self._registry.state(other.module_id)
                    if other_state in (
                        ModuleState.LOADED,
                        ModuleState.ACTIVE,
                        ModuleState.DEACTIVATED,
                    ):
                        raise ModuleInUse(
                            f"cannot unload {module_id!r}: "
                            f"{other.module_id!r} depends on it"
                        )

        instance = self._instances.get(module_id)
        if instance is None:
            raise ModuleLoadFailed(
                f"registry says {module_id!r} is loaded but no instance is held"
            )

        for command_type in reversed(instance.commands()):
            with contextlib.suppress(Exception):
                self._command_bus.unregister(command_type)

        try:
            instance.on_unload()
        except Exception:
            _logger.exception("on_unload raised for %r", module_id)

        self._registry.set_state(module_id, ModuleState.REGISTERED)

    # ----- Lookup ---------------------------------------------------

    def get_instance(self, module_id: str) -> Module | None:
        return self._instances.get(module_id)

    # ----- Internals -------------------------------------------------

    def _resolve_handler(
        self, command_type: type[Command]
    ) -> CommandHandler[Any, Any]:
        handler = getattr(command_type, "_handler", None)
        if handler is None:
            raise ModuleLoadFailed(
                f"no handler is available for {command_type.__name__}"
            )
        return cast(CommandHandler[Any, Any], handler)

    def _build_context(self, module_id: str) -> ModuleContext:
        event_bus = EventBus()
        adapter = EventBusAdapter(event_bus)
        subscription = cast(
            EventSubscription, adapter.create_subscription()
        )
        publisher = cast(EventPublisher, adapter.create_publisher())

        return ModuleContext(
            module_id=module_id,
            correlation_id=None,
            event_subscription=subscription,
            event_publisher=publisher,
            command_bus=self._command_bus,
            task_manager=cast(TaskManager, _NULL_TASK_MANAGER),
            project_provider=lambda: None,
            services=EmptyServiceContainer(),
            telemetry=self._telemetry,
        )
