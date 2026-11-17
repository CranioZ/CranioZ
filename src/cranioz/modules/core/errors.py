"""Module error hierarchy (see modules.md v10 §13)."""

from __future__ import annotations


class ModuleError(Exception):
    """Base of all Module subsystem errors."""


class ModuleNotFound(ModuleError):
    """The module_id is not registered."""


class ModuleAlreadyRegistered(ModuleError):
    """A different manifest is already registered under the same module_id."""


class ModuleStillLoaded(ModuleError):
    """unregister() was called on a module that is not registered/unloaded."""


class ModuleValidationError(ModuleError):
    """The manifest is structurally invalid."""


class ModuleDependencyUnresolved(ModuleError):
    """A dependency is missing, version-incompatible, or in failed state."""


class ModuleDependencyCycle(ModuleError):
    """The dependency graph reachable from the requested module has a cycle."""


class ModuleRegistrationError(ModuleError):
    """A component cannot be registered or unregistered."""


class ModuleInUse(ModuleError):
    """unload() was called while the module is active or has loaded dependents."""


class ModuleLoadFailed(ModuleError):
    """The entry_point cannot be imported or instantiated."""
