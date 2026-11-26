"""Unit tests for the Professional Editor profile flow."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from pytestqt.qtbot import QtBot

from cranioz.application.commands.executor import CommandExecutor
from cranioz.application.commands.in_memory_bus import InMemoryCommandBus
from cranioz.application.commands.stack import InMemoryCommandStack
from cranioz.application.commands.transaction import InMemoryTransactionManager
from cranioz.application.event_bus import EventBus
from cranioz.application.professional import (
    InMemoryProfessionalRepository,
    ProfessionalService,
    UpdateProfessionalProfileCommand,
    UpdateProfessionalProfileHandler,
)
from cranioz.domain.professional import (
    Address,
    ProfessionalProfile,
)
from cranioz.editors.builtin.professional import (
    PROFESSIONAL_QUERIES_EXTRA,
    PROFESSIONAL_SETTINGS_EXTRA,
    ProfessionalEditor,
)
from cranioz.editors.core.editor.editor_context import EditorContext
from cranioz.infrastructure.settings.in_memory_settings_service import (
    InMemorySettingsService,
)
from cranioz.infrastructure.settings.keys import PROFESSIONAL_UI_LAST_SECTION
from cranioz.ui.widgets.forms import FormField


@pytest.fixture
def professional_services() -> tuple[
    InMemoryProfessionalRepository,
    ProfessionalService,
    CommandExecutor,
    InMemorySettingsService,
]:
    repository = InMemoryProfessionalRepository()
    service = ProfessionalService(repository)
    command_bus = InMemoryCommandBus()
    command_bus.register(
        UpdateProfessionalProfileCommand,
        UpdateProfessionalProfileHandler(service),
    )
    dispatcher = CommandExecutor(
        command_bus=command_bus,
        command_stack=InMemoryCommandStack(),
        event_bus=EventBus(),
        transaction_manager=InMemoryTransactionManager(),
    )
    return repository, service, dispatcher, InMemorySettingsService()


@pytest.fixture
def editor(
    qtbot: QtBot,
    professional_services: tuple[
        InMemoryProfessionalRepository,
        ProfessionalService,
        CommandExecutor,
        InMemorySettingsService,
    ],
) -> Iterator[tuple[ProfessionalEditor, ProfessionalService, InMemorySettingsService]]:
    _, service, dispatcher, settings = professional_services
    editor = ProfessionalEditor()
    editor.initialize(
        EditorContext(
            editor_id=editor.editor_id,
            command_dispatcher=dispatcher,
            extras={
                PROFESSIONAL_QUERIES_EXTRA: service,
                PROFESSIONAL_SETTINGS_EXTRA: settings,
            },
        )
    )
    content = editor.content_widget()
    qtbot.addWidget(content)
    yield editor, service, settings


def test_editor_loads_existing_profile_into_form(
    editor: tuple[ProfessionalEditor, ProfessionalService, InMemorySettingsService],
) -> None:
    editor_widget, service, _ = editor
    service.update_profile(
        ProfessionalProfile(
            full_name="Dra. Ana Silva",
            salutation="Dra.",
            email="ana@example.com",
            address=Address(city="Sao Paulo", state="SP", country="BR"),
        )
    )
    editor_widget.cancel_changes()

    content = editor_widget.content_widget()
    full_name = content.findChild(FormField, "professional.profile.full_name")
    email = content.findChild(FormField, "professional.profile.email")

    assert full_name is not None
    assert email is not None
    assert full_name.text == "Dra. Ana Silva"
    assert email.text == "ana@example.com"
    assert "Dra. Ana Silva" in editor_widget.preview_text


def test_save_dispatches_profile_command_and_updates_service(
    editor: tuple[ProfessionalEditor, ProfessionalService, InMemorySettingsService],
) -> None:
    editor_widget, service, _ = editor
    content = editor_widget.content_widget()
    full_name = content.findChild(FormField, "professional.profile.full_name")
    authority = content.findChild(FormField, "professional.profile.authority")
    number = content.findChild(FormField, "professional.profile.registration_number")
    state = content.findChild(FormField, "professional.profile.state")

    assert full_name is not None
    assert authority is not None
    assert number is not None
    assert state is not None
    full_name.text = "Dr. Bruno Souza"
    authority.text = "CRM"
    number.text = "123456"
    state.text = "SP"

    saved = editor_widget.save_profile()

    assert saved is not None
    assert saved.registrations[0].region_code == "BR-SP"
    assert service.get_profile() == saved
    assert editor_widget.loaded_profile == saved


def test_cancel_restores_last_persisted_values(
    editor: tuple[ProfessionalEditor, ProfessionalService, InMemorySettingsService],
) -> None:
    editor_widget, service, _ = editor
    saved = ProfessionalProfile(full_name="Dra. Ana Silva")
    service.update_profile(saved)
    editor_widget.cancel_changes()
    content = editor_widget.content_widget()
    full_name = content.findChild(FormField, "professional.profile.full_name")
    assert full_name is not None

    full_name.text = "Unsaved name"
    editor_widget.cancel_changes()

    assert full_name.text == "Dra. Ana Silva"
    assert service.get_profile() == saved


def test_activate_integrates_professional_settings_namespace(
    editor: tuple[ProfessionalEditor, ProfessionalService, InMemorySettingsService],
) -> None:
    editor_widget, _, settings = editor

    editor_widget.activate()

    assert settings.get(PROFESSIONAL_UI_LAST_SECTION, "") == "professional"


def test_blank_full_name_reports_validation_error(
    qtbot: QtBot,
    editor: tuple[ProfessionalEditor, ProfessionalService, InMemorySettingsService],
) -> None:
    editor_widget, service, _ = editor

    with qtbot.waitSignal(editor_widget.save_failed) as blocker:
        result = editor_widget.save_profile()

    assert result is None
    assert "required" in blocker.args[0].lower()
    assert service.get_profile() is None
