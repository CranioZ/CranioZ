"""Tests for ModuleRegistry and InMemoryModuleRegistry."""

from __future__ import annotations

import pytest

from cranioz.modules.base.module_manifest import (
    ModuleManifest,
)
from cranioz.modules.base.module_state import ModuleState
from cranioz.modules.errors import (
    ModuleAlreadyRegistered,
    ModuleNotFound,
    ModuleStillLoaded,
)
from cranioz.modules.registry.module_registry import (
    InMemoryModuleRegistry,
    ModuleRegistry,
)


def _manifest(module_id: str = "patient") -> ModuleManifest:
    return ModuleManifest(
        module_id=module_id,
        version="1.0.0",
        label_key=f"modules.{module_id}.label",
        description_key=f"modules.{module_id}.description",
        entry_point=f"cranioz.modules.builtin.{module_id}.module:Module",
        dependencies=(),
    )


@pytest.fixture
def registry() -> InMemoryModuleRegistry:
    return InMemoryModuleRegistry()


def test_registry_satisfies_protocol() -> None:
    assert isinstance(InMemoryModuleRegistry(), ModuleRegistry)


def test_new_registry_is_empty(registry: InMemoryModuleRegistry) -> None:
    assert registry.list() == ()
    assert len(registry) == 0


def test_register_then_get(registry: InMemoryModuleRegistry) -> None:
    manifest = _manifest()
    registry.register(manifest)
    assert registry.get("patient") is manifest
    assert registry.contains("patient")
    assert registry.state("patient") is ModuleState.REGISTERED


def test_register_same_manifest_is_idempotent(
    registry: InMemoryModuleRegistry,
) -> None:
    manifest = _manifest()
    registry.register(manifest)
    registry.register(manifest)
    assert len(registry) == 1


def test_register_different_manifest_raises(
    registry: InMemoryModuleRegistry,
) -> None:
    registry.register(_manifest())
    with pytest.raises(ModuleAlreadyRegistered):
        registry.register(_manifest())


def test_get_unknown_returns_none(registry: InMemoryModuleRegistry) -> None:
    assert registry.get("unknown") is None


def test_require_unknown_raises(registry: InMemoryModuleRegistry) -> None:
    with pytest.raises(ModuleNotFound):
        registry.require("unknown")


def test_unregister_registered_is_ok(
    registry: InMemoryModuleRegistry,
) -> None:
    registry.register(_manifest())
    registry.unregister("patient")
    assert not registry.contains("patient")


def test_unregister_loaded_raises(registry: InMemoryModuleRegistry) -> None:
    registry.register(_manifest())
    registry.set_state("patient", ModuleState.LOADED)
    with pytest.raises(ModuleStillLoaded):
        registry.unregister("patient")


def test_unregister_active_raises(registry: InMemoryModuleRegistry) -> None:
    registry.register(_manifest())
    registry.set_state("patient", ModuleState.ACTIVE)
    with pytest.raises(ModuleStillLoaded):
        registry.unregister("patient")


def test_unregister_unknown_is_noop(
    registry: InMemoryModuleRegistry,
) -> None:
    registry.unregister("unknown")  # must not raise


def test_set_state_unknown_raises(
    registry: InMemoryModuleRegistry,
) -> None:
    with pytest.raises(ModuleNotFound):
        registry.set_state("unknown", ModuleState.LOADED)


def test_state_unknown_returns_none(
    registry: InMemoryModuleRegistry,
) -> None:
    assert registry.state("unknown") is None
