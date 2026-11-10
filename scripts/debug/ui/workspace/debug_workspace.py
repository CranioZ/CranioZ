"""Debug script: launch the Workspace with the real TomographyEditor.

This script is a development tool. It is NOT part of production.

It builds a Workspace with:
- A real EditorRegistry populated with TomographyEditor.
- A ToolRegistry with LogTool and ToggleTool.
- A ThemeService (dark).
- A fake, coherent ProjectContext (ADR-0006 requires one).
- A ModuleUISpec with a single Central Area hosting the
  TomographyEditor (editor.tomography).

What you should see:
- The Top Bar floating over the Central Area.
- A 2x2 grid of Views inside the TomographyEditor:
    Axial (top-left) | Coronal (top-right)
    Sagittal (bottom-left) | 3D (bottom-right)
- Two Toolbars inside the Editor:
    "Image Tools" on the LEFT, "Visibility" on the RIGHT.
- No QTabWidget at the bottom of the Area.

Run with:

    .venv\\Scripts\\python.exe scripts\\debug_workspace.py

Close the window to exit.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime

from PySide6.QtWidgets import QApplication, QMainWindow

from cranioz.application.project.project_context import ProjectContext
from cranioz.domain.patient.enums.patient_sex import PatientSex
from cranioz.domain.patient.patient_summary import PatientSummary
from cranioz.domain.patient.value_objects.patient_id import PatientId
from cranioz.domain.project.project_id import ProjectId
from cranioz.domain.project.project_metadata import ProjectMetadata
from cranioz.domain.project.project_status import ProjectStatus
from cranioz.ui.editors.editor_registry import EditorRegistry
from cranioz.ui.editors.tomography.editor import TomographyEditor
from cranioz.ui.theme.service import ThemeName, ThemeService
from cranioz.ui.tools.builtin.log_tool import LogTool
from cranioz.ui.tools.builtin.toggle_tool import ToggleTool
from cranioz.ui.tools.registry.tool_registry import ToolRegistry
from cranioz.ui.workspace.areas.placement import Placement
from cranioz.ui.workspace.specs.area_spec import AreaSpec
from cranioz.ui.workspace.specs.editor_layout_spec import EditorLayoutSpec
from cranioz.ui.workspace.specs.module_ui_spec import ModuleUISpec
from cranioz.ui.workspace.workspace import Workspace

# ----- Project context ----------------------------------------------


def build_project_context() -> ProjectContext:
    """Build a fake, coherent ProjectContext for the debug Workspace."""
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


# ----- Editor registry ----------------------------------------------


def build_editor_registry() -> EditorRegistry:
    """Register the real TomographyEditor."""
    registry = EditorRegistry()
    registry.register("editor.tomography", TomographyEditor)
    return registry


# ----- Tool registry ------------------------------------------------


def build_tool_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register("tool.log", LogTool)
    registry.register("tool.toggle", ToggleTool)
    return registry


# ----- ModuleUISpec -------------------------------------------------


def build_spec() -> ModuleUISpec:
    """Build a ModuleUISpec with a single Central Area hosting TomographyEditor."""
    return ModuleUISpec(
        areas=(
            AreaSpec(
                area_id="area.central",
                title="Tomography",
                placement=Placement.CENTRAL,
                editor_layout=EditorLayoutSpec.leaf("editor.tomography"),
            ),
        ),
    )


# ----- Main ---------------------------------------------------------


def main() -> int:
    app = QApplication.instance() or QApplication([])
    app.setStyle("Fusion")

    workspace = Workspace(
        editor_registry=build_editor_registry(),
        tool_registry=build_tool_registry(),
        theme_service=ThemeService(theme=ThemeName.DARK),
        project_context=build_project_context(),
        debug_colors=True,
    )
    workspace.load_spec(build_spec())

    window = QMainWindow()
    window.setWindowTitle("CranioZ — TomographyEditor debug")
    window.setCentralWidget(workspace)
    window.resize(1280, 800)
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
