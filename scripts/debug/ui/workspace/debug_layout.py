"""Debug layout: Workspace with mock Editors in all 4 Areas.

Purpose: isolate the Workspace's layout bugs from the Editor's
(especially the TomographyEditor). This script does NOT use VTK,
does NOT use the MainWindow (which hard-codes the default spec),
and does NOT hide the lateral Areas.

Run:
    python scripts/debug/ui/workspace/debug_layout.py
"""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication, QMainWindow

from cranioz.application.event_bus import EventBus
from cranioz.application.project.in_memory_repository import (
    InMemoryProjectRepository,
)
from cranioz.application.project.access_policy import (
    AllowAllProjectAccessPolicy,
)
from cranioz.application.project.manager import ProjectManager
from cranioz.domain.patient.value_objects.patient_id import PatientId
from cranioz.domain.project.project_id import ProjectId
from cranioz.infrastructure.settings.in_memory_settings_service import (
    InMemorySettingsService,
)
from cranioz.ui.editors.editor_registry import EditorRegistry
from cranioz.ui.editors.mock.console import MockConsoleEditor
from cranioz.ui.editors.mock.objetos import MockObjetosEditor
from cranioz.ui.editors.mock.posicao import MockPosicaoEditor
from cranioz.ui.editors.mock.mpr import MockMPREditor
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
from cranioz.ui.workspace.structure.home_segment import HomeSegment
from cranioz.ui.workspace.structure.modules_segment import ModulesSegment
from cranioz.ui.workspace.structure.extras_segment import ExtrasSegment
from cranioz.ui.workspace.workspace import Workspace


def main() -> int:
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    settings = InMemorySettingsService()
    theme = ThemeService(settings=settings, default_mode=ThemeMode.DARK)
    icons = UnicodeIconProvider(theme)
    app.setStyleSheet(theme.compiled().qss)

    # ----- Project + Manager (in-memory) -----
    repository = InMemoryProjectRepository()
    manager = ProjectManager(
        repository=repository,
        event_bus=EventBus(),
        access_policy=AllowAllProjectAccessPolicy(),
    )
    manager.create_project(
        "debug",
        project_id=ProjectId("p-debug"),
        project_name="Debug Layout",
        patient_id=PatientId("pat-debug"),
        patient_display_name="Debug",
        clinical_procedure="orthognathic",
    )
    context = manager.open_project("debug", ProjectId("p-debug"))

    # ----- Editor + Tool registries -----
    editors = EditorRegistry()
    editors.register("editor.mock.posicao", MockPosicaoEditor)
    editors.register("editor.mock.objetos", MockObjetosEditor)
    editors.register("editor.mock.console", MockConsoleEditor)
    editors.register("editor.mock.mpr", MockMPREditor)

    tools = ToolRegistry()
    tools.register("tool.log", LogTool)
    tools.register("tool.toggle", ToggleTool)

    # ----- Workspace (direct construction, no MainWindow) -----
    workspace = Workspace(
        editor_registry=editors,
        tool_registry=tools,
        theme_service=theme,
        icon_provider=icons,
        project_context=context,
    )

    # ----- Top Bar segments (same as MainWindow would inject) -----
    home_segment = HomeSegment(icons)
    modules_segment = ModulesSegment(icons)
    extras_segment = ExtrasSegment(icons)
    modules_segment.set_modules((("tomography", "Tomografia"),))
    home_segment.set_project_open(True)

    workspace.top_overlay().set_left_content(home_segment)
    workspace.top_overlay().set_center_content(modules_segment)
    workspace.top_overlay().set_right_content(extras_segment)

    # ----- 4-Area spec with mock Editors -----
    debug_spec = ModuleUISpec(
        areas=(
            AreaSpec(
                area_id="area.right",
                title="Posição",
                placement=Placement.RIGHT,
                editor_layout=EditorLayoutSpec.leaf("editor.mock.posicao"),
            ),
            AreaSpec(
                area_id="area.central",
                title="Central",
                placement=Placement.CENTRAL,
                editor_layout=EditorLayoutSpec.leaf("editor.mock.mpr"),
            ),
            AreaSpec(
                area_id="area.left",
                title="Objetos",
                placement=Placement.LEFT,
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
    workspace.load_spec(debug_spec)

    # Show all 4 Areas (load_spec hides the laterals by default).
    for placement in (Placement.LEFT, Placement.RIGHT, Placement.BOTTOM):
        workspace.set_area_visible(placement, True)

    # ----- Minimal top-level window -----
    window = QMainWindow()
    window.setCentralWidget(workspace)
    window.setWindowTitle("CranioZ — debug layout")
    window.resize(1400, 900)
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())