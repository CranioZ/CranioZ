"""Visual debug harness for the Professional Editor (Tela 2).

Run with::

    .venv\\Scripts\\python.exe scripts\\debug\\ui\\professional\\debug_professional_editor.py

The harness materializes the Professional ModuleUISpec through the real
Workspace and ProfessionalEditor. It uses an in-memory profile repository
and a real command executor, so Save exercises the same command path as
production without writing the developer's Professional database.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime

from PySide6.QtWidgets import QApplication, QMainWindow

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
from cranioz.infrastructure.i18n.translation_service import IdentityTranslationService
from cranioz.infrastructure.settings.in_memory_settings_service import (
    InMemorySettingsService,
)
from cranioz.ui.icons.unicode import UnicodeIconProvider
from cranioz.ui.theme.service import ThemeService
from cranioz.ui.theme.tokens import ThemeMode
from cranioz.ui.tools.builtin.log_tool import LogTool
from cranioz.ui.tools.builtin.toggle_tool import ToggleTool
from cranioz.ui.tools.registry.tool_registry import ToolRegistry
from cranioz.ui.workspace.specs.professional import PROFESSIONAL_UI_SPEC
from cranioz.ui.workspace.workspace import Workspace


def _project_context() -> ProjectContext:
    project_id = ProjectId("professional-debug")
    timestamp = datetime(2026, 1, 1, tzinfo=UTC)
    return ProjectContext(
        project_id=project_id,
        metadata=ProjectMetadata(
            project_id=project_id,
            project_name="Professional Debug",
            patient_id="patient-debug",
            patient_display_name="Debug Patient",
            clinical_procedure="professional",
            status=ProjectStatus.ACTIVE,
            created_at=timestamp,
            updated_at=timestamp,
            last_opened_at=None,
            schema_version=1,
        ),
        patient_summary=PatientSummary(
            patient_id=PatientId("patient-debug"),
            display_name="Debug Patient",
            birth_date=None,
            sex=PatientSex.OTHER,
        ),
    )


def main() -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyle("Fusion")

    settings = InMemorySettingsService()
    theme = ThemeService(settings=settings, default_mode=ThemeMode.DARK)
    theme.compiler().apply(theme.compiled())

    command_bus = InMemoryCommandBus()
    service = ProfessionalService(InMemoryProfessionalRepository())
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

    editor_registry = EditorRegistry()
    editor_registry.register(PROFESSIONAL_EDITOR_ID, ProfessionalEditor)
    tool_registry = ToolRegistry()
    tool_registry.register("tool.log", LogTool)
    tool_registry.register("tool.toggle", ToggleTool)

    workspace = Workspace(
        editor_registry=editor_registry,
        tool_registry=tool_registry,
        theme_service=theme,
        icon_provider=UnicodeIconProvider(theme),
        project_context=_project_context(),
        command_dispatcher=dispatcher,
        translation_service=IdentityTranslationService(),
        editor_context_extras={
            PROFESSIONAL_QUERIES_EXTRA: service,
            PROFESSIONAL_SETTINGS_EXTRA: settings,
        },
    )
    workspace.load_spec(PROFESSIONAL_UI_SPEC)

    window = QMainWindow()
    window.setWindowTitle("CranioZ - Professional Editor (L.1)")
    window.setCentralWidget(workspace)
    window.resize(1280, 800)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
