"""Module Protocol and ModuleBase (modules.md v10 §6).

A Module is a coherent functional capability. It declares contributions
(Commands, Services, Tools, Editors, Data Types, Flows, ModuleUISpec)
and provides lifecycle hooks. The loader instantiates the Module,
registers its contributions, and calls the hooks.

The Module Protocol is structural: the loader accepts any class whose
instance satisfies it, without requiring inheritance from
``ModuleBase``. ``ModuleBase`` is a convenience base with default
implementations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from cranioz.application.commands.base import Command
    from cranioz.modules.base.module_context import ModuleContext
    from cranioz.modules.base.module_manifest import ModuleManifest
    from cranioz.ui.editors.base_editor import Editor
    from cranioz.ui.tools.registry.tool_definition import Tool
    from cranioz.ui.workspace.specs.module_ui_spec import ModuleUISpec


@runtime_checkable
class Module(Protocol):
    """Coherent functional capability (modules.md v10 §6).

    Contribution methods are declarative: they return classes (or
    immutable definitions), not instances. The loader registers them in
    the respective platform registries.

    Lifecycle hooks (``on_load``, ``on_unload``, ``on_activate``,
    ``on_deactivate``) are called by the loader and by the Application
    layer respectively. See ``modules.md`` v10 §7 for the contract.
    """

    manifest: ModuleManifest

    def commands(self) -> tuple[type[Command], ...]: ...
    def services(self) -> tuple[type, ...]: ...
    def tools(self) -> tuple[type[Tool], ...]: ...
    def editors(self) -> tuple[type[Editor], ...]: ...
    def data_types(self) -> tuple[type, ...]: ...
    def flows(self) -> tuple[type, ...]: ...
    def ui_specs(self) -> tuple[ModuleUISpec, ...]: ...

    def on_load(self, context: ModuleContext) -> None: ...
    def on_unload(self) -> None: ...
    def on_activate(self, spec: ModuleUISpec) -> None: ...
    def on_deactivate(self) -> None: ...


class ModuleBase:
    """Convenience base class with default empty implementations.

    Subclasses override only what they need. ``manifest`` is abstract
    (subclasses must set it) and is not defined here to keep the base
    class free of instance state.

    The default contribution methods return empty tuples; the default
    hooks do nothing. The lifecycle hooks run on the GUI thread and
    must complete quickly (ADR-0011).
    """

    manifest: ModuleManifest

    def commands(self) -> tuple[type[Command], ...]:
        return ()

    def services(self) -> tuple[type, ...]:
        return ()

    def tools(self) -> tuple[type[Tool], ...]:
        return ()

    def editors(self) -> tuple[type[Editor], ...]:
        return ()

    def data_types(self) -> tuple[type, ...]:
        return ()

    def flows(self) -> tuple[type, ...]:
        return ()

    def ui_specs(self) -> tuple[ModuleUISpec, ...]:
        return ()

    def on_load(self, context: ModuleContext) -> None:
        return None

    def on_unload(self) -> None:
        return None

    def on_activate(self, spec: ModuleUISpec) -> None:
        return None

    def on_deactivate(self) -> None:
        return None
