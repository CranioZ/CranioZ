"""ModuleRegistry — declarative manifest registry (modules.md v10 §10).

The registry stores manifests and their lifecycle state. It does not
own Module instances; the ``ModuleLoader`` owns them. It does not
decide which Module to activate; the Application layer does.

The registry is the source of truth for:
- which modules are known (``list``, ``get``, ``contains``);
- the state of each known module (``state``).

It is not the source of truth for the module instances themselves.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from cranioz.modules.base.module_manifest import ModuleManifest
from cranioz.modules.base.module_state import ModuleState
from cranioz.modules.errors import (
    ModuleAlreadyRegistered,
    ModuleNotFound,
    ModuleStillLoaded,
)


@runtime_checkable
class ModuleRegistry(Protocol):
    """Registry of known Modules."""

    def register(self, manifest: ModuleManifest) -> None: ...

    def unregister(self, module_id: str) -> None: ...

    def get(self, module_id: str) -> ModuleManifest | None: ...

    def require(self, module_id: str) -> ModuleManifest: ...

    def list(self) -> tuple[ModuleManifest, ...]: ...

    def state(self, module_id: str) -> ModuleState | None: ...

    def contains(self, module_id: str) -> bool: ...

    def set_state(self, module_id: str, state: ModuleState) -> None: ...


class InMemoryModuleRegistry:
    """Reference implementation of ``ModuleRegistry``."""

    def __init__(self) -> None:
        self._manifests: dict[str, ModuleManifest] = {}
        self._states: dict[str, ModuleState] = {}

    def register(self, manifest: ModuleManifest) -> None:
        existing = self._manifests.get(manifest.module_id)
        if existing is manifest:
            return
        if existing is not None:
            raise ModuleAlreadyRegistered(
                f"a different manifest is already registered under {manifest.module_id!r}"
            )
        self._manifests[manifest.module_id] = manifest
        self._states[manifest.module_id] = ModuleState.REGISTERED

    def unregister(self, module_id: str) -> None:
        if module_id not in self._manifests:
            return
        state = self._states[module_id]
        if state is not ModuleState.REGISTERED:
            raise ModuleStillLoaded(
                f"cannot unregister {module_id!r}: state is {state.value!r}, expected 'registered'"
            )
        del self._manifests[module_id]
        del self._states[module_id]

    def get(self, module_id: str) -> ModuleManifest | None:
        return self._manifests.get(module_id)

    def require(self, module_id: str) -> ModuleManifest:
        manifest = self._manifests.get(module_id)
        if manifest is None:
            raise ModuleNotFound(f"module not registered: {module_id!r}")
        return manifest

    def list(self) -> tuple[ModuleManifest, ...]:
        return tuple(self._manifests.values())

    def state(self, module_id: str) -> ModuleState | None:
        return self._states.get(module_id)

    def contains(self, module_id: str) -> bool:
        return module_id in self._manifests

    def set_state(self, module_id: str, state: ModuleState) -> None:
        if module_id not in self._manifests:
            raise ModuleNotFound(f"module not registered: {module_id!r}")
        self._states[module_id] = state

    def __len__(self) -> int:
        return len(self._manifests)

    def __repr__(self) -> str:
        return f"InMemoryModuleRegistry(modules={list(self._manifests)!r})"
