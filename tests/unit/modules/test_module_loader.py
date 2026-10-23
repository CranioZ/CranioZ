"""Contract tests for ModuleLoader, exercised against InMemoryModuleLoader."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from cranioz.application.commands.base import Command
from cranioz.application.commands.in_memory_bus import InMemoryCommandBus
from cranioz.application.telemetry.noop_sink import NoOpTelemetrySink
from cranioz.modules.base.module import Module, ModuleBase
from cranioz.modules.base.module_context import ModuleContext
from cranioz.modules.base.module_manifest import (
    ModuleDependency,
    ModuleManifest,
)
from cranioz.modules.base.module_state import ModuleState
from cranioz.modules.errors import (
    ModuleInUse,
    ModuleLoadFailed,
    ModuleNotFound,
)
from cranioz.modules.loader.module_loader import (
    InMemoryModuleLoader,
    ModuleLoader,
)
from cranioz.modules.registry.module_registry import InMemoryModuleRegistry


@dataclass(frozen=True)
class CreatePatientCommand(Command):
    pass


class CreatePatientHandler:
    def handle(self, command: CreatePatientCommand) -> str:
        return "ok"


def _manifest(
    module_id: str,
    dependencies: tuple[ModuleDependency, ...] = (),
) -> ModuleManifest:
    return ModuleManifest(
        module_id=module_id,
        version="1.0.0",
        label_key=f"modules.{module_id}.label",
        description_key=f"modules.{module_id}.description",
        entry_point=f"cranioz.modules.builtin.{module_id}.module:Module",
        dependencies=dependencies,
    )


class PatientModule(ModuleBase):
    manifest = _manifest("patient")

    def commands(self) -> tuple[type[Command], ...]:
        return (CreatePatientCommand,)


class TomographyModule(ModuleBase):
    manifest = _manifest("tomography")


class BrokenModule(ModuleBase):
    manifest = _manifest("broken")

    def commands(self) -> tuple[type[Command], ...]:
        return (CreatePatientCommand,)


def _set_handler(command_type: type, handler: object) -> None:
    # The InMemoryModuleLoader's placeholder handler resolution reads
    # ``_handler`` from the Command class. Tests set it explicitly.
    command_type._handler = handler  # type: ignore[attr-defined]


@pytest.fixture
def registry() -> InMemoryModuleRegistry:
    return InMemoryModuleRegistry()


@pytest.fixture
def command_bus() -> InMemoryCommandBus:
    return InMemoryCommandBus()


@pytest.fixture
def telemetry() -> NoOpTelemetrySink:
    return NoOpTelemetrySink()


@pytest.fixture
def instances() -> dict[str, Module]:
    return {
        "patient": PatientModule(),
        "tomography": TomographyModule(),
        "broken": BrokenModule(),
    }


@pytest.fixture
def loader(
    registry: InMemoryModuleRegistry,
    instances: dict[str, Module],
    command_bus: InMemoryCommandBus,
    telemetry: NoOpTelemetrySink,
) -> InMemoryModuleLoader:
    for module_id in instances:
        registry.register(_manifest(module_id))
    _set_handler(CreatePatientCommand, CreatePatientHandler())
    return InMemoryModuleLoader(
        registry=registry,
        instances=instances,
        command_bus=command_bus,
        telemetry=telemetry,
    )


# ----- Protocol -----------------------------------------------------


def test_loader_satisfies_protocol(loader: InMemoryModuleLoader) -> None:
    assert isinstance(loader, ModuleLoader)


# ----- Load ---------------------------------------------------------


def test_load_returns_instance(loader: InMemoryModuleLoader) -> None:
    module = loader.load("patient")
    assert module.manifest.module_id == "patient"


def test_load_updates_state_to_loaded(
    loader: InMemoryModuleLoader,
    registry: InMemoryModuleRegistry,
) -> None:
    loader.load("patient")
    assert registry.state("patient") is ModuleState.LOADED


def test_load_registers_commands(
    loader: InMemoryModuleLoader,
    command_bus: InMemoryCommandBus,
) -> None:
    loader.load("patient")
    assert command_bus.can_dispatch(CreatePatientCommand)


def test_load_is_idempotent(loader: InMemoryModuleLoader) -> None:
    a = loader.load("patient")
    b = loader.load("patient")
    assert a is b


def test_load_unknown_raises(loader: InMemoryModuleLoader) -> None:
    with pytest.raises(ModuleNotFound):
        loader.load("unknown")


def test_load_no_instance_raises(registry: InMemoryModuleRegistry) -> None:
    registry.register(_manifest("ghost"))
    loader = InMemoryModuleLoader(
        registry=registry,
        instances={},
        command_bus=InMemoryCommandBus(),
        telemetry=NoOpTelemetrySink(),
    )
    with pytest.raises(ModuleLoadFailed):
        loader.load("ghost")


# ----- Unload -------------------------------------------------------


def test_unload_returns_to_registered(
    loader: InMemoryModuleLoader,
    registry: InMemoryModuleRegistry,
) -> None:
    loader.load("patient")
    loader.unload("patient")
    assert registry.state("patient") is ModuleState.REGISTERED


def test_unload_unknown_raises(loader: InMemoryModuleLoader) -> None:
    with pytest.raises(ModuleNotFound):
        loader.unload("unknown")


def test_unload_refuses_active(
    loader: InMemoryModuleLoader,
    registry: InMemoryModuleRegistry,
) -> None:
    loader.load("patient")
    registry.set_state("patient", ModuleState.ACTIVE)
    with pytest.raises(ModuleInUse):
        loader.unload("patient")


def test_unload_refuses_if_dependent_is_loaded(
    registry: InMemoryModuleRegistry,
    instances: dict[str, Module],
) -> None:
    # Register a dependent.
    registry.register(_manifest("orthognathic_guide", dependencies=(
        ModuleDependency("osteotomies", ">=1.0.0"),
    )))
    registry.register(_manifest("osteotomies"))

    guide = ModuleBase()
    guide.manifest = _manifest("orthognathic_guide", dependencies=(
        ModuleDependency("osteotomies", ">=1.0.0"),
    ))
    instances["orthognathic_guide"] = guide
    instances["osteotomies"] = ModuleBase()
    instances["osteotomies"].manifest = _manifest("osteotomies")

    loader = InMemoryModuleLoader(
        registry=registry,
        instances=instances,
        command_bus=InMemoryCommandBus(),
        telemetry=NoOpTelemetrySink(),
    )

    loader.load("osteotomies")
    loader.load("orthognathic_guide")
    with pytest.raises(ModuleInUse):
        loader.unload("osteotomies")


# ----- Rollback -----------------------------------------------------


def test_load_rolls_back_on_failure(
    registry: InMemoryModuleRegistry,
    instances: dict[str, Module],
    command_bus: InMemoryCommandBus,
) -> None:
    registry.register(_manifest("broken"))

    class FailingModule(ModuleBase):
        manifest = _manifest("broken")

        def commands(self) -> tuple[type[Command], ...]:
            return (CreatePatientCommand,)

        def on_load(self, context: ModuleContext) -> None:
            raise RuntimeError("boom")

    instances["broken"] = FailingModule()
    _set_handler(CreatePatientCommand, CreatePatientHandler())

    loader = InMemoryModuleLoader(
        registry=registry,
        instances=instances,
        command_bus=command_bus,
        telemetry=NoOpTelemetrySink(),
    )

    with pytest.raises(ModuleLoadFailed):
        loader.load("broken")

    assert registry.state("broken") is ModuleState.REGISTERED
    assert not command_bus.can_dispatch(CreatePatientCommand)
