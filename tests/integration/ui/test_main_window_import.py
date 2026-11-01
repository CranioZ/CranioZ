"""Integration test: import DICOM via MainWindow (Passo 8e)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

pytest.importorskip("pydicom")
pytest.importorskip("vtk")
pytest.importorskip("vtkmodules.qt")

from tests.unit.infrastructure.imaging.test_dicom_loader import (
    _write_synthetic_dcm,
)

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
from cranioz.ui.editors.tomography.editor import TomographyEditor
from cranioz.ui.main_window import MainWindow
from cranioz.ui.theme.service import ThemeName, ThemeService
from cranioz.ui.tools.builtin.log_tool import LogTool
from cranioz.ui.tools.builtin.toggle_tool import ToggleTool
from cranioz.ui.tools.registry.tool_registry import ToolRegistry
from cranioz.ui.workspace.workspace_spec import (
    PLACEHOLDER_EDITOR_CLASS,
    PLACEHOLDER_EDITOR_ID,
)


@pytest.fixture
def window(qtbot) -> MainWindow:
    """Fresh MainWindow with in-memory repositories and a SceneProvider."""
    repository = InMemoryProjectRepository()
    event_bus = EventBus()
    catalog = ProjectCatalog(repository=repository)
    manager = ProjectManager(
        repository=repository,
        event_bus=event_bus,
        access_policy=AllowAllProjectAccessPolicy(),
    )
    # Seed a project so that `project_open_requested` works.
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
    editor_registry.register("editor.tomography", TomographyEditor)

    tool_registry = ToolRegistry()
    tool_registry.register("tool.log", LogTool)
    tool_registry.register("tool.toggle", ToggleTool)

    window = MainWindow(
        catalog=catalog,
        manager=manager,
        actor="test-actor",
        editor_registry=editor_registry,
        tool_registry=tool_registry,
        theme_service=ThemeService(theme=ThemeName.DARK),
        scene_provider=scene_provider,
        domain_object_store=domain_object_store,
    )
    qtbot.addWidget(window)
    return window


@pytest.mark.qt
@pytest.mark.integration
def test_import_dicom_adds_volume_to_scene(
    qtbot,
    window: MainWindow,
    tmp_path: Path,
) -> None:
    """Clicking 'Importar DICOM' loads a series and adds it to the Scene."""
    # Arrange: open a project (the Workspace exists)
    window.home().refresh()
    window.home().project_open_requested.emit(ProjectId("p-001"), "orthognathic")
    qtbot.wait(50)
    workspace = window.current_workspace()
    assert workspace is not None

    # Create a synthetic DICOM folder
    series_uid = "1.2.3.4.5"
    for i in range(3):
        _write_synthetic_dcm(tmp_path / f"slice_{i:03d}.dcm", series_uid, i, float(i))

    # Mock QFileDialog to return the temp folder
    with patch(
        "cranioz.ui.main_window.QFileDialog.getExistingDirectory",
        return_value=str(tmp_path),
    ):
        window._on_import_dicom_clicked()

    # Assert: the Scene now contains a volume
    scene = window._scene_provider.get_scene()
    ids = scene.list_objects()
    assert len(ids) == 1
    object_id = ids[0]
    assert object_id.startswith("volume-")

    # Assert: the DomainObjectStore has the volume
    assert window._domain_object_store is not None
    assert window._domain_object_store.contains(object_id)
    stored = window._domain_object_store.get(object_id)
    assert stored.series_uid == series_uid
