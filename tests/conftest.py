"""Shared pytest fixtures for CranioZ tests."""

from __future__ import annotations

import logging
import os
from collections.abc import Callable

import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QSurfaceFormat
from PySide6.QtWidgets import QApplication
from pytestqt.qtbot import QtBot

# VTK 9 reports every failed wglMakeCurrent as an error. During tests,
# VTK render windows are created and destroyed rapidly, which triggers
# these spurious reports. They do not affect test outcomes; silence them.
# Keep the variable settable from the shell for debugging.
os.environ.setdefault("VTK_REPORT_OPENGL_ERRORS", "0")

try:
    from vtkmodules.qt.QVTKRenderWindowInteractor import (
        QVTKRenderWindowInteractor,
    )

    _HAS_VTK = True
except ImportError:  # pragma: no cover - VTK is optional
    QVTKRenderWindowInteractor = None  # type: ignore[assignment,misc]
    _HAS_VTK = False

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
from cranioz.application.scene.scene_provider import InMemorySceneProvider
from cranioz.domain.patient.value_objects.patient_id import PatientId
from cranioz.domain.project.project_id import ProjectId
from cranioz.domain.scene.domain_object_store import DomainObjectStore
from cranioz.ui.editors.builtin.test_editor import DummyEditor
from cranioz.ui.editors.editor_registry import EditorRegistry
from cranioz.ui.editors.tomography.editor import TomographyEditor
from cranioz.ui.main_window import MainWindow
from cranioz.ui.theme.service import ThemeName, ThemeService
from cranioz.ui.toolbars.specification import (
    ToolbarOrientation,
    ToolbarSpec,
    ToolbarVisibilityMode,
)
from cranioz.ui.tools.builtin.log_tool import LogTool
from cranioz.ui.tools.builtin.toggle_tool import ToggleTool
from cranioz.ui.tools.registry.tool_registry import ToolRegistry
from cranioz.ui.workspace.workspace_spec import (
    PLACEHOLDER_EDITOR_CLASS,
    PLACEHOLDER_EDITOR_ID,
)

_logger = logging.getLogger(__name__)

# ----- Qt ------------------------------------------------------------


@pytest.fixture(scope="session")
def qapp() -> QApplication:
    """Session-scoped QApplication with a VTK-friendly surface format.

    The surface format and the shared-context attribute are applied
    *before* the QApplication is instantiated. Applying them after is a
    no-op (Qt freezes the format at construction time), which is what
    produced the ``code 2004`` (unsupported operation) reports.
    """
    app = QApplication.instance()
    if isinstance(app, QApplication):
        return app

    QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
    fmt = QSurfaceFormat()
    fmt.setDepthBufferSize(24)
    fmt.setStencilBufferSize(8)
    fmt.setVersion(3, 2)
    fmt.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)
    QSurfaceFormat.setDefaultFormat(fmt)

    return QApplication([])


# ----- VTK cleanup ---------------------------------------------------


@pytest.fixture(autouse=True)
def _finalize_vtk_interactors() -> None:
    """Finalize every live QVTKRenderWindowInteractor after each test.

    Without this, the VTK render window is destroyed by Qt after the
    OpenGL context is already gone, producing a flood of
    ``wglMakeCurrent failed ... code 6`` messages. Finalizing before
    Qt's teardown releases the context cleanly.
    """
    yield
    if not _HAS_VTK:
        return

    for widget in QApplication.allWidgets():
        if isinstance(widget, QVTKRenderWindowInteractor):
            try:
                widget.Finalize()
            except Exception:
                # Finalize can raise if the widget was already torn down
                # by Qt. That is expected during teardown; log at debug
                # so failures remain diagnosable without polluting output.
                _logger.debug(
                    "VTK Finalize failed for %r",
                    widget,
                    exc_info=True,
                )


# ----- Theme ---------------------------------------------------------


@pytest.fixture
def theme_service() -> ThemeService:
    """Default ThemeService (dark theme)."""
    return ThemeService(theme=ThemeName.DARK)


# ----- Tools and Registry --------------------------------------------


@pytest.fixture
def tool_registry() -> ToolRegistry:
    """Registry with LogTool and ToggleTool registered."""
    registry = ToolRegistry()
    registry.register("tool.log", LogTool)
    registry.register("tool.toggle", ToggleTool)
    return registry


@pytest.fixture
def make_test_editor() -> Callable[..., DummyEditor]:
    """Factory to build TestEditor instances with a given editor_id."""

    def _factory(
        editor_id: str = "editor.test",
        title: str = "Test Editor",
    ) -> DummyEditor:
        return DummyEditor(editor_id=editor_id, title=title)

    return _factory


# ----- Toolbar spec factory ------------------------------------------


@pytest.fixture
def make_toolbar_spec() -> Callable[..., ToolbarSpec]:
    """Factory to build ToolbarSpec with sensible defaults."""

    def _factory(
        toolbar_id: str = "tb.test",
        title: str = "Test Toolbar",
        orientation: ToolbarOrientation = ToolbarOrientation.HORIZONTAL,
        tool_ids: tuple[str, ...] = (),
        visibility_mode: ToolbarVisibilityMode = ToolbarVisibilityMode.ALWAYS,
    ) -> ToolbarSpec:
        return ToolbarSpec(
            toolbar_id=toolbar_id,
            title=title,
            orientation=orientation,
            tool_ids=tool_ids,
            visibility_mode=visibility_mode,
        )

    return _factory


# ----- MainWindow with an open project ------------------------------


@pytest.fixture
def main_window_with_open_project(qtbot: QtBot) -> MainWindow:
    """Build a MainWindow with an open project.

    The fixture creates an in-memory ProjectRepository with one
    project, opens it through the same path the HomePage uses, and
    yields the MainWindow. The project is closed at teardown.

    See tests/conftest.py for the rationale behind the shared fixture:
    more than one integration test file needs a MainWindow with a
    Workspace whose Top Bar segments are populated.
    """
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

    window = MainWindow(
        catalog=catalog,
        manager=manager,
        actor="test-actor",
        editor_registry=editor_registry,
        tool_registry=tool_registry,
        theme_service=ThemeService(theme=ThemeName.DARK),
        command_dispatcher=command_dispatcher,
        command_bus=command_bus,
        scene_provider=scene_provider,
        domain_object_store=domain_object_store,
    )
    qtbot.addWidget(window)

    window.home().refresh()
    window.home().project_open_requested.emit(project_id, "orthognathic")
    qtbot.wait(50)

    yield window

    if window.current_workspace() is not None:
        window._on_home_clicked()  # noqa: SLF001
