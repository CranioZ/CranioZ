"""Debug script: launch the Workspace with a fake ModuleUISpec.

This script is a development tool. It is NOT part of production.

It builds a Workspace with:

- A fake EditorRegistry populated with DebugEditor instances
  (no toolbars, so only the editor_id is visible).
- A ToolRegistry with LogTool and ToggleTool.
- A ThemeService (dark).
- A fake, coherent ProjectContext (ADR-0006 requires one).
- A ModuleUISpec that mirrors a typical clinical layout:
    LEFT     -> object_list
    CENTRAL  -> viewport_3d | (mpr_axial / mpr_sagittal)
    RIGHT    -> properties
    BOTTOM   -> console

The Workspace is created with ``debug_colors=True`` so that each
Area has a soft background color that makes its boundary visible:

    LEFT     -> soft blue
    CENTRAL  -> soft green
    RIGHT    -> soft yellow
    BOTTOM   -> soft lavender

The TopOverlay is registered automatically by the Workspace and
will be positioned over the Central Region. During debug it is
painted red so it becomes visible.

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
from cranioz.ui.editors.builtin.test_editor import DebugEditor
from cranioz.ui.editors.editor_registry import EditorRegistry
from cranioz.ui.theme.service import ThemeName, ThemeService
from cranioz.ui.tools.builtin.log_tool import LogTool
from cranioz.ui.tools.builtin.toggle_tool import ToggleTool
from cranioz.ui.tools.registry.tool_registry import ToolRegistry
from cranioz.ui.workspace.areas.placement import Placement
from cranioz.ui.workspace.specs.area_spec import AreaSpec
from cranioz.ui.workspace.specs.editor_layout_spec import (
    EditorLayoutSpec,
    SplitDirection,
)
from cranioz.ui.workspace.specs.module_ui_spec import ModuleUISpec
from cranioz.ui.workspace.workspace import Workspace

# ----- Project context ----------------------------------------------


def build_project_context() -> ProjectContext:
    """Build a fake, coherent ProjectContext for the debug Workspace.

    The Workspace never inspects the context beyond checking for its
    presence (see ADR-0006), but a coherent context keeps the debug
    run representative of production. All timestamps are timezone-aware
    UTC, as required by ProjectMetadata.
    """
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
    """Register DebugEditor under several editor_ids.

    DebugEditor is a DummyEditor without toolbars, so the debug
    visual shows only the editor_id (no Log/Toggle buttons).
    """
    registry = EditorRegistry()
    for editor_id in (
        "editor.viewport_3d",
        "editor.mpr_axial",
        "editor.mpr_sagittal",
        "editor.object_list",
        "editor.properties",
        "editor.console",
    ):
        registry.register(editor_id, DebugEditor)
    return registry


# ----- Tool registry ------------------------------------------------


def build_tool_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register("tool.log", LogTool)
    registry.register("tool.toggle", ToggleTool)
    return registry


# ----- ModuleUISpec -------------------------------------------------


def build_spec() -> ModuleUISpec:
    """Build a ModuleUISpec that mirrors the prototype layout."""
    return ModuleUISpec(
        areas=(
            AreaSpec(
                area_id="area.left",
                title="Lists",
                placement=Placement.LEFT,
                editor_layout=EditorLayoutSpec.leaf("editor.object_list"),
            ),
            AreaSpec(
                area_id="area.central",
                title="Editing",
                placement=Placement.CENTRAL,
                editor_layout=EditorLayoutSpec.split(
                    SplitDirection.HORIZONTAL,
                    (
                        EditorLayoutSpec.leaf("editor.viewport_3d"),
                        EditorLayoutSpec.split(
                            SplitDirection.VERTICAL,
                            (
                                EditorLayoutSpec.leaf("editor.mpr_axial"),
                                EditorLayoutSpec.leaf("editor.mpr_sagittal"),
                            ),
                        ),
                    ),
                ),
            ),
            AreaSpec(
                area_id="area.right",
                title="Tools",
                placement=Placement.RIGHT,
                editor_layout=EditorLayoutSpec.leaf("editor.properties"),
            ),
            AreaSpec(
                area_id="area.bottom",
                title="Console",
                placement=Placement.BOTTOM,
                editor_layout=EditorLayoutSpec.leaf("editor.console"),
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
    window.setWindowTitle("CranioZ — Workspace debug")
    window.setCentralWidget(workspace)
    window.resize(1280, 800)
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
