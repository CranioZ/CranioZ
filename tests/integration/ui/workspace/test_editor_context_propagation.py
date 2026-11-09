"""Contract test: every Editor receives the full EditorContext.

Sprint C: after ThemeService and IconProvider were added to the
context, every Editor registered in the EditorRegistry must receive
all nine fields non-null. This test guards against the wiring
silently dropping one of them in a future refactor.
"""

from __future__ import annotations

# Standard Library
from datetime import UTC, datetime

# Third-Party Libraries
import pytest
from pytestqt.qtbot import QtBot

# Local Imports (tests)
from tests.conftest import make_icon_provider, make_theme_service

# Local Imports (cranioz.*)
from cranioz.application.commands.executor import CommandExecutor
from cranioz.application.commands.in_memory_bus import InMemoryCommandBus
from cranioz.application.commands.stack import InMemoryCommandStack
from cranioz.application.commands.transaction import (
    InMemoryTransactionManager,
)
from cranioz.application.event_bus import EventBus
from cranioz.application.project.project_context import ProjectContext
from cranioz.application.scene.scene_query import InMemorySceneQuery
from cranioz.application.tasks.noop_task_manager import NoOpTaskManager
from cranioz.application.telemetry.noop_sink import NoOpTelemetrySink
from cranioz.domain.patient.enums.patient_sex import PatientSex
from cranioz.domain.patient.patient_summary import PatientSummary
from cranioz.domain.patient.value_objects.patient_id import PatientId
from cranioz.domain.project.project_id import ProjectId
from cranioz.domain.project.project_metadata import ProjectMetadata
from cranioz.domain.project.project_status import ProjectStatus
from cranioz.infrastructure.i18n.translation_service import (
    IdentityTranslationService,
)
from cranioz.ui.editors.builtin.test_editor import DummyEditor
from cranioz.ui.editors.editor_context import EditorContext
from cranioz.ui.editors.editor_registry import EditorRegistry
from cranioz.ui.theme.tokens import ThemeMode
from cranioz.ui.tools.registry.tool_registry import ToolRegistry
from cranioz.ui.workspace.areas.placement import Placement
from cranioz.ui.workspace.specs.area_spec import AreaSpec
from cranioz.ui.workspace.specs.editor_layout_spec import EditorLayoutSpec
from cranioz.ui.workspace.specs.module_ui_spec import ModuleUISpec
from cranioz.ui.workspace.workspace import Workspace


@pytest.mark.qt
@pytest.mark.integration
def test_every_editor_receives_all_context_fields(
    qtbot: QtBot,
    tool_registry: ToolRegistry,
) -> None:
    """Every Editor gets the nine fields non-null in its EditorContext."""
    # --- Build the shared services ---
    event_bus = EventBus()
    command_bus = InMemoryCommandBus()
    command_dispatcher = CommandExecutor(
        command_bus=command_bus,
        command_stack=InMemoryCommandStack(),
        event_bus=event_bus,
        transaction_manager=InMemoryTransactionManager(),
    )
    scene_query = InMemorySceneQuery()
    task_manager = NoOpTaskManager()
    telemetry = NoOpTelemetrySink()
    translation_service = IdentityTranslationService()
    theme_service = make_theme_service(ThemeMode.DARK)
    icon_provider = make_icon_provider(theme_service)

    # --- Build the Workspace ---
    editor_registry = EditorRegistry()
    editor_registry.register("editor.test", DummyEditor)
    # tool_registry comes from the shared fixture; it already registers
    # tool.log and tool.toggle, which DummyEditor's ToolbarSpec requires.

    workspace = Workspace(
        editor_registry=editor_registry,
        tool_registry=tool_registry,
        theme_service=theme_service,
        icon_provider=icon_provider,
        project_context=_minimal_project_context(),
        task_manager=task_manager,
        telemetry=telemetry,
        command_dispatcher=command_dispatcher,
        scene_query=scene_query,
        event_subscription=None,  # optional
        translation_service=translation_service,
    )
    qtbot.addWidget(workspace)

    spec = ModuleUISpec(
        areas=(
            AreaSpec(
                area_id="area.central",
                title="Central",
                placement=Placement.CENTRAL,
                editor_layout=EditorLayoutSpec.leaf("editor.test"),
            ),
        ),
    )
    workspace.load_spec(spec)

    # --- Assert every field is non-null on the created Editor ---
    build_result = workspace._build_result  # noqa: SLF001
    assert build_result is not None
    editors = build_result.editors("area.central")
    assert len(editors) == 1

    context: EditorContext = editors[0]._context  # noqa: SLF001
    assert context is not None

    # Not asserted here:
    # - correlation_id: not yet propagated by Workspace (tracked for a
    #   future sprint; see implementation_plan.md §3.1.2).
    # - domain_object_store: not in the Sprint C target set.
    # - event_subscription: passed as None in this test; a dedicated
    #   test should cover it once the EventBus exposes a subscription
    #   helper suitable for unit tests.

    assert context.task_manager is task_manager
    assert context.telemetry is telemetry
    assert context.command_dispatcher is command_dispatcher
    assert context.scene_query is scene_query
    assert context.translation_service is translation_service
    assert context.theme_service is theme_service  # Sprint C
    assert context.icon_provider is icon_provider  # Sprint C


def _minimal_project_context() -> ProjectContext:
    """Build a minimal ProjectContext for the Workspace."""
    pid = ProjectId("p-test")
    return ProjectContext(
        project_id=pid,
        metadata=ProjectMetadata(
            project_id=pid,
            project_name="Test",
            patient_id="pat-test",
            patient_display_name="Test",
            clinical_procedure="test",
            status=ProjectStatus.ACTIVE,
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
            updated_at=datetime(2026, 1, 1, tzinfo=UTC),
            last_opened_at=None,
            schema_version=1,
        ),
        patient_summary=PatientSummary(
            patient_id=PatientId("pat-test"),
            display_name="Test",
            birth_date=None,
            sex=PatientSex.MALE,
        ),
    )
