"""Integration test: import DICOM via MainWindow.

Covers the full path from the Top Bar's "Importar arquivos" action to
the ``Volume`` being registered in the ``DomainObjectStore`` and the
``Scene``, and the registration/unregistration of the
``ImportDicomSeriesHandler`` in the ``CommandBus`` across the project
lifecycle.

The MainWindow registers the handler when a project is opened (inside
``_on_project_open_requested``) and unregisters it when the project
closes (inside ``_on_home_clicked``, triggered by the Top Bar's
``close_workspace_requested`` signal). This mirrors the production
boot path, where the handler is not loaded during the boot critical
path (Application Startup §3.1, §3.4, §4.1).
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest

pytest.importorskip("pydicom")
pytest.importorskip("vtk")
pytest.importorskip("vtkmodules.qt")

from pydicom.dataset import Dataset, FileMetaDataset
from pydicom.uid import ExplicitVRLittleEndian, generate_uid
from tests.conftest import make_icon_provider, make_theme_service

from cranioz.application.commands.executor import CommandExecutor
from cranioz.application.commands.in_memory_bus import InMemoryCommandBus
from cranioz.application.commands.stack import InMemoryCommandStack
from cranioz.application.commands.transaction import (
    InMemoryTransactionManager,
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
from cranioz.application.scene.commands.scene_commands import (
    ImportDicomSeriesCommand,
)
from cranioz.application.scene.scene_provider import InMemorySceneProvider
from cranioz.domain.imaging.volume import Volume
from cranioz.domain.patient.value_objects.patient_id import PatientId
from cranioz.domain.project.project_id import ProjectId
from cranioz.domain.scene.domain_object_store import DomainObjectStore
from cranioz.ui.editors.editor_registry import EditorRegistry
from cranioz.ui.editors.tomography.editor import TomographyEditor
from cranioz.ui.main_window import MainWindow
from cranioz.ui.theme.tokens import ThemeMode
from cranioz.ui.tools.builtin.log_tool import LogTool
from cranioz.ui.tools.builtin.toggle_tool import ToggleTool
from cranioz.ui.tools.registry.tool_registry import ToolRegistry
from cranioz.ui.workspace.structure import HomeSegment
from cranioz.ui.workspace.workspace_spec import (
    PLACEHOLDER_EDITOR_CLASS,
    PLACEHOLDER_EDITOR_ID,
)


def _write_synthetic_dcm(
    path: Path,
    series_uid: str,
    instance_number: int,
    z_position: float,
    *,
    rows: int = 4,
    cols: int = 4,
) -> None:
    """Write a single synthetic axial DICOM slice with full geometry.

    Includes the geometry attributes required by ``DicomSorter``:
    ``ImagePositionPatient``, ``ImageOrientationPatient``, and
    ``PixelSpacing``. The default orientation is a standard axial
    stack (row = +X, col = +Y), which is enough for the reader to
    assemble a valid volume.
    """
    file_meta = FileMetaDataset()
    file_meta.MediaStorageSOPClassUID = generate_uid()
    file_meta.MediaStorageSOPInstanceUID = generate_uid()
    file_meta.TransferSyntaxUID = ExplicitVRLittleEndian
    file_meta.ImplementationClassUID = generate_uid()

    ds = Dataset()
    ds.file_meta = file_meta
    ds.Modality = "CT"
    ds.Rows = rows
    ds.Columns = cols
    ds.BitsAllocated = 16
    ds.BitsStored = 16
    ds.HighBit = 15
    ds.PixelRepresentation = 1
    ds.SamplesPerPixel = 1
    ds.PhotometricInterpretation = "MONOCHROME2"

    # Geometry attributes (required by DicomSorter).
    ds.PixelSpacing = [0.5, 0.5]
    ds.SliceThickness = 1.0
    ds.ImagePositionPatient = [0.0, 0.0, z_position]
    ds.ImageOrientationPatient = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0]

    # Rescale attributes (used by DicomCalibrator).
    ds.RescaleSlope = 1.0
    ds.RescaleIntercept = -1024.0

    # Identifiers.
    ds.SeriesInstanceUID = series_uid
    ds.StudyInstanceUID = "1.2.3.4"
    ds.SOPInstanceUID = file_meta.MediaStorageSOPInstanceUID
    ds.SOPClassUID = file_meta.MediaStorageSOPClassUID
    ds.InstanceNumber = instance_number

    # Pixel data.
    pixel_data = np.zeros((rows, cols), dtype=np.int16) + instance_number
    ds.PixelData = pixel_data.tobytes()
    ds.save_as(str(path), enforce_file_format=True)


@pytest.fixture
def window(qtbot) -> MainWindow:
    """Fresh MainWindow with in-memory repositories and a SceneProvider.

    The ``CommandBus`` starts empty. The ``ImportDicomSeriesHandler``
    is registered by ``MainWindow._on_project_open_requested``, after
    the Workspace is created. This mirrors the production boot path:
    the handler must not be loaded during the boot critical path.
    """
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
    editor_registry.register("editor.tomography", TomographyEditor)

    tool_registry = ToolRegistry()
    tool_registry.register("tool.log", LogTool)
    tool_registry.register("tool.toggle", ToggleTool)

    command_bus = InMemoryCommandBus()
    command_dispatcher = CommandExecutor(
        command_bus=command_bus,
        command_stack=InMemoryCommandStack(),
        event_bus=event_bus,
        transaction_manager=InMemoryTransactionManager(),
    )

    theme_service = make_theme_service(ThemeMode.DARK)
    icon_provider = make_icon_provider(theme_service)

    window = MainWindow(
        catalog=catalog,
        manager=manager,
        actor="test-actor",
        editor_registry=editor_registry,
        tool_registry=tool_registry,
        theme_service=theme_service,
        icon_provider=icon_provider,
        command_dispatcher=command_dispatcher,
        command_bus=command_bus,
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
    """The 'Importar arquivos' action dispatches the Command, which
    loads a series and adds it to the Scene as a ``Volume``."""
    # Arrange: open a project (the Workspace exists).
    window.home().refresh()
    window.home().project_open_requested.emit(ProjectId("p-001"), "orthognathic")
    qtbot.wait(50)
    workspace = window.current_workspace()
    assert workspace is not None

    # The handler must be registered by _on_project_open_requested.
    assert window._command_bus is not None
    assert window._command_bus.can_dispatch(ImportDicomSeriesCommand)

    # Create a synthetic DICOM folder.
    series_uid = "1.2.3.4.5"
    for i in range(3):
        _write_synthetic_dcm(tmp_path / f"slice_{i:03d}.dcm", series_uid, i, float(i))

    # Mock QFileDialog to return the temp folder.
    with patch(
        "cranioz.ui.main_window.QFileDialog.getExistingDirectory",
        return_value=str(tmp_path),
    ):
        window._on_import_dicom_clicked()

    # Assert: the Scene now contains a volume.
    scene = window._scene_provider.get_scene()
    ids = scene.list_objects()
    assert len(ids) == 1
    object_id = ids[0]
    assert object_id.startswith("volume-")

    # Assert: the DomainObjectStore has the Volume (not VolumeData).
    assert window._domain_object_store is not None
    assert window._domain_object_store.contains(object_id)
    stored = window._domain_object_store.get(object_id)
    assert isinstance(stored, Volume)
    assert stored.metadata.series_instance_uid == series_uid


@pytest.mark.qt
@pytest.mark.integration
def test_dicom_import_handler_unregistered_on_close_workspace(
    qtbot,
    window: MainWindow,
) -> None:
    """Closing the project must unregister the DICOM import handler.

    The handler references the project's Scene and DomainObjectStore,
    which become invalid after the project closes. Leaving it
    registered would keep stale references alive and allow stale
    dispatches.

    The 'close workspace' path is the Top Bar's ``HomeSegment``:
    emitting ``close_workspace_requested`` is the architectural
    equivalent of the old "Home" button click.
    """
    window.home().refresh()
    window.home().project_open_requested.emit(ProjectId("p-001"), "orthognathic")
    qtbot.wait(50)
    assert window._command_bus is not None
    assert window._command_bus.can_dispatch(ImportDicomSeriesCommand)

    workspace = window.current_workspace()
    assert workspace is not None
    home_segment = workspace.top_overlay().left_segment().findChild(HomeSegment)
    assert home_segment is not None

    home_segment.close_workspace_requested.emit()

    assert window.current_workspace() is None
    assert window._command_bus.can_dispatch(ImportDicomSeriesCommand) is False
