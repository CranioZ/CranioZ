"""Tests for the Professional profile command/query flow."""

from __future__ import annotations

import pytest

from cranioz.application.commands.executor import CommandExecutor
from cranioz.application.commands.in_memory_bus import InMemoryCommandBus
from cranioz.application.commands.stack import InMemoryCommandStack
from cranioz.application.commands.transaction import InMemoryTransactionManager
from cranioz.application.event_bus import EventBus
from cranioz.application.professional import (
    InMemoryProfessionalRepository,
    ProfessionalQueries,
    ProfessionalService,
    UpdateProfessionalProfileCommand,
    UpdateProfessionalProfileHandler,
)
from cranioz.domain.professional import ProfessionalProfile


@pytest.fixture
def repository() -> InMemoryProfessionalRepository:
    return InMemoryProfessionalRepository()


@pytest.fixture
def service(
    repository: InMemoryProfessionalRepository,
) -> ProfessionalService:
    return ProfessionalService(repository)


def test_service_satisfies_queries_protocol(
    service: ProfessionalService,
) -> None:
    assert isinstance(service, ProfessionalQueries)


def test_service_returns_none_before_profile_exists(
    service: ProfessionalService,
) -> None:
    assert service.get_profile() is None


def test_service_update_persists_profile(
    service: ProfessionalService,
    repository: InMemoryProfessionalRepository,
) -> None:
    profile = ProfessionalProfile(full_name="Dra. Ana Silva")

    result = service.update_profile(profile)

    assert result is profile
    assert service.get_profile() is profile
    assert repository.load_profile() is profile


def test_service_rejects_non_profile_value(
    service: ProfessionalService,
) -> None:
    with pytest.raises(TypeError, match="ProfessionalProfile"):
        service.update_profile("not-a-profile")  # type: ignore[arg-type]


def test_update_command_carries_profile_and_is_irreversible() -> None:
    profile = ProfessionalProfile(full_name="Dra. Ana Silva")

    command = UpdateProfessionalProfileCommand(profile=profile)

    assert command.profile is profile
    assert command.is_reversible is False


def test_update_command_rejects_non_profile_value() -> None:
    with pytest.raises(TypeError, match="ProfessionalProfile"):
        UpdateProfessionalProfileCommand(profile="not-a-profile")  # type: ignore[arg-type]


def test_handler_updates_profile_through_service(
    service: ProfessionalService,
) -> None:
    profile = ProfessionalProfile(full_name="Dra. Ana Silva")
    handler = UpdateProfessionalProfileHandler(service)

    result = handler.handle(UpdateProfessionalProfileCommand(profile=profile))

    assert result is profile
    assert service.get_profile() is profile


def test_command_dispatch_persists_profile(
    service: ProfessionalService,
) -> None:
    command_bus = InMemoryCommandBus()
    command_bus.register(
        UpdateProfessionalProfileCommand,
        UpdateProfessionalProfileHandler(service),
    )
    profile = ProfessionalProfile(full_name="Dra. Ana Silva")

    result = command_bus.dispatch(UpdateProfessionalProfileCommand(profile=profile))

    assert result is profile
    assert service.get_profile() is profile


def test_executor_does_not_push_irreversible_profile_command(
    service: ProfessionalService,
) -> None:
    command_bus = InMemoryCommandBus()
    command_bus.register(
        UpdateProfessionalProfileCommand,
        UpdateProfessionalProfileHandler(service),
    )
    executor = CommandExecutor(
        command_bus=command_bus,
        command_stack=InMemoryCommandStack(),
        event_bus=EventBus(),
        transaction_manager=InMemoryTransactionManager(),
    )

    executor.dispatch(
        UpdateProfessionalProfileCommand(profile=ProfessionalProfile(full_name="Dra. Ana Silva"))
    )

    assert executor.can_undo() is False
