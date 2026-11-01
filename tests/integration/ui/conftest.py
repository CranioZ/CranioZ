"""Shared fixtures for UI integration tests."""

from __future__ import annotations

import pytest

from cranioz.application.event_bus import EventBus
from cranioz.application.project.in_memory_project_repository import (
    InMemoryProjectRepository,
)
from cranioz.application.project.project_access_policy import (
    AllowAllProjectAccessPolicy,
)
from cranioz.application.project.project_catalog import ProjectCatalog
from cranioz.application.project.project_manager import ProjectManager
from cranioz.application.scene.scene_provider import InMemorySceneProvider
from cranioz.domain.patient.value_objects.patient_id import PatientId
from cranioz.domain.project.project_id import ProjectId
from cranioz.domain.scene.domain_object_store import DomainObjectStore
from cranioz.ui.editors.editor_registry import EditorRegistry
from cranioz.ui.main_window import MainWindow
from cranioz.ui.theme.service import ThemeName, ThemeService
from cranioz.ui.tools.registry.tool_registry import ToolRegistry
from cranioz.ui.workspace.workspace_spec import (
    PLACEHOLDER_EDITOR_CLASS,
    PLACEHOLDER_EDITOR_ID,
)


@pytest.fixture
def window(qtbot) -> MainWindow:
    repository = InMemoryProjectRepository()
    event_bus = EventBus()
    catalog = ProjectCatalog(repository=repository)
    manager = ProjectManager(
        repository=repository,
        event_bus=event_bus,
        access_policy=AllowAllProjectAccessPolicy(),
    )
    manager.create_project(
        "test-actor",
        project_id=ProjectId("p-001"),
        project_name="Case 001",
        patient_id=PatientId("pat-001"),
        patient_display_name="João Silva",
        clinical_procedure="orthognathic",
    )

    scene_provider = InMemorySceneProvider()
    domain_object_store = DomainObjectStore()

    editor_registry = EditorRegistry()
    editor_registry.register(PLACEHOLDER_EDITOR_ID, PLACEHOLDER_EDITOR_CLASS)

    window = MainWindow(
        catalog=catalog,
        manager=manager,
        actor="test-actor",
        editor_registry=editor_registry,
        tool_registry=ToolRegistry(),
        theme_service=ThemeService(theme=ThemeName.DARK),
        scene_provider=scene_provider,
        domain_object_store=domain_object_store,
    )
    qtbot.addWidget(window)
    return window
