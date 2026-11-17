"""Debug script: launch the Workspace with mock Editors on all four Areas.

This script isolates the layout behavior from the real Editor content.
If the layout is correct here but wrong in the real application, the
problem is the real Editors' minimumSizeHint (TomographyEditor,
_PlaceholderEditor). If the layout is wrong here too, the problem is
in the Workspace's splitter sizing logic.

Run with:

    .venv\\Scripts\\python.exe scripts\\debug\\ui\\workspace\\debug_workspace_with_mocks.py
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime

# VTK / OpenGL configuration
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QSurfaceFormat
from PySide6.QtWidgets import QApplication, QMainWindow

QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
_fmt = QSurfaceFormat()
_fmt.setDepthBufferSize(24)
_fmt.setStencilBufferSize(8)
_fmt.setVersion(3, 2)
_fmt.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)
QSurfaceFormat.setDefaultFormat(_fmt)

# CranioZ imports
from cranioz.domain.patient.enums.patient_sex import PatientSex
from cranioz.domain.patient.patient_summary import PatientSummary
from cranioz.domain.patient.value_objects.patient_id import PatientId

from cranioz.application.project.context import ProjectContext
from cranioz.application.scene.scene_query import InMemorySceneQuery
from cranioz.domain.project.project_id import ProjectId
from cranioz.domain.project.project_metadata import ProjectMetadata
from cranioz.domain.project.project_status import ProjectStatus
from cranioz.domain.scene.domain_object_store import DomainObjectStore
from cranioz.infrastructure.settings.in_memory_settings_service import (
    InMemorySettingsService,
)
from cranioz.ui.editors.editor_registry import EditorRegistry
from cranioz.ui.editors.tomography.editor import TomographyEditor
from cranioz.ui.icons.unicode import UnicodeIconProvider
from cranioz.ui.theme.service import ThemeService
from cranioz.ui.theme.tokens import ThemeMode
from cranioz.ui.tools.builtin.log_tool import LogTool
from cranioz.ui.tools.builtin.toggle_tool import ToggleTool
from cranioz.ui.tools.registry.tool_registry import ToolRegistry
from cranioz.ui.workspace.areas.placement import Placement
from cranioz.ui.workspace.specs.area_spec import AreaSpec
from cranioz.ui.workspace.specs.editor_layout_spec import EditorLayoutSpec
from cranioz.ui.workspace.specs.module_ui_spec import ModuleUISpec
from cranioz.ui.workspace.workspace import Workspace

# Mock Editors

from src.cranioz.ui.editors.mock import (
    MockConsoleEditor,
    MockObjetosEditor,
    MockPosicaoEditor,
)


def build_project_context() -> ProjectContext:
    pid = ProjectId("p-debug")
    now = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
    return ProjectContext(
        project_id=pid,
        metadata=ProjectMetadata(
            project_id=pid,
            project_name="Debug Case",
            patient_id="pat-debug",
            patient_display_name="Debug Patient",
            clinical_procedure="orthognathic",
            status=ProjectStatus.ACTIVE,
            created_at=now,
            updated_at=now,
            last_opened_at=None,
            schema_version=1,
        ),
    )


def build_editor_registry() -> EditorRegistry:
    registry = EditorRegistry()
    registry.register("editor.tomography", TomographyEditor)
    registry.register("editor.mock.console", MockConsoleEditor)
    registry.register("editor.mock.objetos", MockObjetosEditor)
    registry.register("editor.mock.posicao", MockPosicaoEditor)
    return registry

def build_project_context() -> ProjectContext:
    pid = ProjectId("p-debug")
    now = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
    return ProjectContext(
        project_id=pid,
        metadata=ProjectMetadata(
            project_id=pid,
            project_name="Debug Case",
            patient_id="pat-debug",
            patient_display_name="Debug Patient",
            clinical_procedure="orthognathic",
            status=ProjectStatus.ACTIVE,
            created_at=now,
            updated_at=now,
            last_opened_at=None,
            schema_version=1,
        ),
        patient_summary=PatientSummary(
            patient_id=PatientId("pat-debug"),
            display_name="Debug Patient",
            birth_date=None,
            sex=PatientSex.MALE,
        ),
    )


def build_tool_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register("tool.log", LogTool)
    registry.register("tool.toggle", ToggleTool)
    return registry


def build_spec() -> ModuleUISpec:
    """Build a ModuleUISpec with all four Areas and mock Editors."""
    return ModuleUISpec(
        areas=(
            AreaSpec(
                area_id="area.left",
                title="Posição",
                placement=Placement.LEFT,
                editor_layout=EditorLayoutSpec.leaf("editor.mock.posicao"),
            ),
            AreaSpec(
                area_id="area.central",
                title="Tomography",
                placement=Placement.CENTRAL,
                editor_layout=EditorLayoutSpec.leaf("editor.tomography"),
            ),
            AreaSpec(
                area_id="area.right",
                title="Objetos",
                placement=Placement.RIGHT,
                editor_layout=EditorLayoutSpec.leaf("editor.mock.objetos"),
            ),
            AreaSpec(
                area_id="area.bottom",
                title="Console",
                placement=Placement.BOTTOM,
                editor_layout=EditorLayoutSpec.leaf("editor.mock.console"),
            ),
        ),
    )


def main() -> int:
    app = QApplication.instance() or QApplication([])
    app.setStyle("Fusion")

    theme_service = ThemeService(
        settings=InMemorySettingsService(),
        default_mode=ThemeMode.DARK,
    )
    theme_service.compiler().apply(theme_service.compiled())

    icon_provider = UnicodeIconProvider(theme_service)

    workspace = Workspace(
        editor_registry=build_editor_registry(),
        tool_registry=build_tool_registry(),
        theme_service=theme_service,
        icon_provider=icon_provider,
        project_context=build_project_context(),
        domain_object_store=DomainObjectStore(),
        scene_query=InMemorySceneQuery(),
    )
    workspace.load_spec(build_spec())

    # --- Top Bar fake (apenas para o debug) ---
    from PySide6.QtWidgets import QHBoxLayout, QPushButton, QVBoxLayout, QWidget

    fake_top_bar = QWidget()
    fake_top_bar.setObjectName("debug_top_bar")
    fake_top_bar.setStyleSheet(
        "QWidget#debug_top_bar {"
        "  background-color: #2b2b2b;"
        "  border-bottom: 1px solid #444;"
        "  padding: 4px;"
        "}"
    )
    fake_top_bar_layout = QHBoxLayout(fake_top_bar)
    fake_top_bar_layout.setContentsMargins(8, 4, 8, 4)

    # Botão para toggle Left
    btn_left = QPushButton("Toggle Left")
    btn_left.clicked.connect(
        lambda: workspace.set_area_visible(
            Placement.LEFT,
            not workspace.layout_state().is_visible(Placement.LEFT),
        )
    )
    fake_top_bar_layout.addWidget(btn_left)

    # Botão para toggle Right
    btn_right = QPushButton("Toggle Right")
    btn_right.clicked.connect(
        lambda: workspace.set_area_visible(
            Placement.RIGHT,
            not workspace.layout_state().is_visible(Placement.RIGHT),
        )
    )
    fake_top_bar_layout.addWidget(btn_right)

    # Botão para toggle Bottom
    btn_bottom = QPushButton("Toggle Bottom")
    btn_bottom.clicked.connect(
        lambda: workspace.set_area_visible(
            Placement.BOTTOM,
            not workspace.layout_state().is_visible(Placement.BOTTOM),
        )
    )
    fake_top_bar_layout.addWidget(btn_bottom)

    fake_top_bar_layout.addStretch(1)

    # Container vertical com a fake Top Bar + Workspace
    main_container = QWidget()
    main_layout = QVBoxLayout(main_container)
    main_layout.setContentsMargins(0, 0, 0, 0)
    main_layout.setSpacing(0)
    main_layout.addWidget(fake_top_bar)
    main_layout.addWidget(workspace, stretch=1)

    window = QMainWindow()
    window.setWindowTitle("CranioZ — Workspace with mock Editors + fake Top Bar")
    window.setCentralWidget(main_container)
    window.resize(1280, 800)
    window.show()

    # Mostra as laterais e o bottom por padrão para inspecionar o layout
    QTimer.singleShot(100, lambda: workspace.set_area_visible(Placement.LEFT, True))
    QTimer.singleShot(150, lambda: workspace.set_area_visible(Placement.RIGHT, True))
    QTimer.singleShot(200, lambda: workspace.set_area_visible(Placement.BOTTOM, True))

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())