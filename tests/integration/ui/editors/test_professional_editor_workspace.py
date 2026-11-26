"""Workspace integration for the Professional Editor."""

from __future__ import annotations

from datetime import UTC, datetime

from pytestqt.qtbot import QtBot
from tests.conftest import make_icon_provider, make_theme_service

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
from cranioz.application.project.context import ProjectContext
from cranioz.domain.patient.enums.patient_sex import PatientSex
from cranioz.domain.patient.patient_summary import PatientSummary
from cranioz.domain.patient.value_objects.patient_id import PatientId
from cranioz.domain.project.project_id import ProjectId
from cranioz.domain.project.project_metadata import ProjectMetadata
from cranioz.domain.project.project_status import ProjectStatus
from cranioz.editors.builtin.professional import (
    PROFESSIONAL_EDITOR_ID,
    PROFESSIONAL_QUERIES_EXTRA,
    PROFESSIONAL_SETTINGS_EXTRA,
    ProfessionalEditor,
)
from cranioz.editors.core.editor.editor_registry import EditorRegistry
from cranioz.infrastructure.settings.in_memory_settings_service import (
    InMemorySettingsService,
)
from cranioz.ui.theme.tokens import ThemeMode
from cranioz.ui.tools.builtin.log_tool import LogTool
from cranioz.ui.tools.builtin.toggle_tool import ToggleTool
from cranioz.ui.tools.registry.tool_registry import ToolRegistry
from cranioz.ui.workspace.specs.professional import PROFESSIONAL_UI_SPEC
from cranioz.ui.workspace.workspace import Workspace


def _project_context() -> ProjectContext:
    project_id = ProjectId("professional-test")
    timestamp = datetime(2026, 1, 1, tzinfo=UTC)
    return ProjectContext(
        project_id=project_id,
        metadata=ProjectMetadata(
            project_id=project_id,
            project_name="Professional Test",
            patient_id="patient-test",
            patient_display_name="Test Patient",
            clinical_procedure="professional",
            status=ProjectStatus.ACTIVE,
            created_at=timestamp,
            updated_at=timestamp,
            last_opened_at=None,
            schema_version=1,
        ),
        patient_summary=PatientSummary(
            patient_id=PatientId("patient-test"),
            display_name="Test Patient",
            birth_date=None,
            sex=PatientSex.OTHER,
        ),
    )


def test_professional_module_spec_materializes_editor_with_dependencies(
    qtbot: QtBot,
) -> None:
    service = ProfessionalService(InMemoryProfessionalRepository())
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
    settings = InMemorySettingsService()

    editor_registry = EditorRegistry()
    editor_registry.register(PROFESSIONAL_EDITOR_ID, ProfessionalEditor)
    tool_registry = ToolRegistry()
    tool_registry.register("tool.log", LogTool)
    tool_registry.register("tool.toggle", ToggleTool)
    theme = make_theme_service(ThemeMode.DARK)

    workspace = Workspace(
        editor_registry=editor_registry,
        tool_registry=tool_registry,
        theme_service=theme,
        icon_provider=make_icon_provider(theme),
        project_context=_project_context(),
        command_dispatcher=dispatcher,
        editor_context_extras={
            PROFESSIONAL_QUERIES_EXTRA: service,
            PROFESSIONAL_SETTINGS_EXTRA: settings,
        },
    )
    qtbot.addWidget(workspace)
    workspace.load_spec(PROFESSIONAL_UI_SPEC)
    # AreaWidget schedules VTK first-frame callbacks at 0 and 100 ms.
    # Let them run before pytest-qt tears the widget tree down.
    qtbot.wait(150)

    build_result = workspace._build_result  # noqa: SLF001
    assert build_result is not None
    editors = build_result.editors("area.professional.central")
    assert len(editors) == 1
    assert isinstance(editors[0], ProfessionalEditor)
    context = editors[0]._context  # noqa: SLF001
    assert context is not None
    assert context.extras[PROFESSIONAL_QUERIES_EXTRA] is service
    assert context.extras[PROFESSIONAL_SETTINGS_EXTRA] is settings
