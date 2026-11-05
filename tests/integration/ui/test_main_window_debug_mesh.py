"""Integration tests for the CRANIOZ_DEBUG_MESH spec (STL validation)."""

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
from cranioz.domain.patient.value_objects.patient_id import PatientId
from cranioz.domain.project.project_id import ProjectId
from cranioz.ui.editors.editor_registry import EditorRegistry
from cranioz.ui.editors.viewport_3d.mesh_debug_editor import (
    MESH_DEBUG_EDITOR_ID,
    MeshDebugEditor,
)
from cranioz.ui.editors.viewport_3d.view import Viewport3DView
from cranioz.ui.main_window import MainWindow
from cranioz.ui.theme.service import ThemeName, ThemeService
from cranioz.ui.tools.registry.tool_registry import ToolRegistry
from cranioz.ui.workspace.workspace_spec import (
    PLACEHOLDER_EDITOR_CLASS,
    PLACEHOLDER_EDITOR_ID,
)


@pytest.fixture
def window_with_debug_mesh(qtbot, monkeypatch) -> MainWindow:
    """Build a MainWindow with CRANIOZ_DEBUG_MESH=1 and an open project."""
    monkeypatch.setenv("CRANIOZ_DEBUG_MESH", "1")

    repository = InMemoryProjectRepository()
    event_bus = EventBus()
    catalog = ProjectCatalog(repository=repository)
    manager = ProjectManager(
        repository=repository,
        event_bus=event_bus,
        access_policy=AllowAllProjectAccessPolicy(),
    )
    project_id = ProjectId("p-001")
    manager.create_project(
        "test-actor",
        project_id=project_id,
        project_name="Case 001",
        patient_id=PatientId("pat-001"),
        patient_display_name="João Silva",
        clinical_procedure="orthognathic",
    )

    editor_registry = EditorRegistry()
    editor_registry.register(PLACEHOLDER_EDITOR_ID, PLACEHOLDER_EDITOR_CLASS)

    window = MainWindow(
        catalog=catalog,
        manager=manager,
        actor="test-actor",
        editor_registry=editor_registry,
        tool_registry=ToolRegistry(),
        theme_service=ThemeService(theme=ThemeName.DARK),
    )
    qtbot.addWidget(window)

    window.home().refresh()
    window.home().project_open_requested.emit(project_id, "orthognathic")
    qtbot.wait(50)

    yield window

    if window.current_workspace() is not None:
        window._on_home_clicked()  # noqa: SLF001


@pytest.mark.qt
@pytest.mark.integration
def test_debug_mesh_editor_is_registered(window_with_debug_mesh: MainWindow) -> None:
    window = window_with_debug_mesh
    assert window._editor_registry.contains(MESH_DEBUG_EDITOR_ID)  # noqa: SLF001


@pytest.mark.qt
@pytest.mark.integration
def test_workspace_loads_mesh_debug_editor(
    window_with_debug_mesh: MainWindow,
) -> None:
    window = window_with_debug_mesh
    workspace = window.current_workspace()
    assert workspace is not None

    areas = workspace.areas()
    assert len(areas) == 1
    assert areas[0].placement.value == "central"
    editors = areas[0].editors()
    assert len(editors) == 1
    assert isinstance(editors[0], MeshDebugEditor)


@pytest.mark.qt
@pytest.mark.integration
def test_find_viewport_3d_returns_viewport(
    window_with_debug_mesh: MainWindow,
) -> None:
    window = window_with_debug_mesh
    workspace = window.current_workspace()
    assert workspace is not None

    viewport = workspace.find_viewport_3d()
    assert viewport is not None
    assert isinstance(viewport, Viewport3DView)


@pytest.mark.qt
@pytest.mark.integration
def test_workspace_default_spec_is_used_without_env_var(qtbot, monkeypatch) -> None:
    """Without CRANIOZ_DEBUG_MESH=1, the default placeholder spec is used."""
    monkeypatch.delenv("CRANIOZ_DEBUG_MESH", raising=False)

    repository = InMemoryProjectRepository()
    catalog = ProjectCatalog(repository=repository)
    manager = ProjectManager(
        repository=repository,
        event_bus=EventBus(),
        access_policy=AllowAllProjectAccessPolicy(),
    )
    project_id = ProjectId("p-001")
    manager.create_project(
        "test-actor",
        project_id=project_id,
        project_name="Case 001",
        patient_id=PatientId("pat-001"),
        patient_display_name="João Silva",
        clinical_procedure="orthognathic",
    )

    editor_registry = EditorRegistry()
    editor_registry.register(PLACEHOLDER_EDITOR_ID, PLACEHOLDER_EDITOR_CLASS)

    window = MainWindow(
        catalog=catalog,
        manager=manager,
        actor="test-actor",
        editor_registry=editor_registry,
        tool_registry=ToolRegistry(),
        theme_service=ThemeService(theme=ThemeName.DARK),
    )
    qtbot.addWidget(window)
    window.home().refresh()
    window.home().project_open_requested.emit(project_id, "orthognathic")
    qtbot.wait(50)

    workspace = window.current_workspace()
    assert workspace is not None
    assert not window._editor_registry.contains(MESH_DEBUG_EDITOR_ID)  # noqa: SLF001
    assert workspace.find_viewport_3d() is None
