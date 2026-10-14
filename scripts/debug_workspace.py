"""Debug script: launch the Workspace with a fake ModuleUISpec.

This script is a development tool. It is NOT part of production.

It builds a Workspace with:

- A fake EditorRegistry populated with DummyEditor instances.
- A ToolRegistry with LogTool and ToggleTool.
- A ThemeService (dark).
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

from PySide6.QtWidgets import QApplication, QMainWindow

from cranioz.ui.editors.builtin.test_editor import DummyEditor
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

# ----- Editor registry ----------------------------------------------


def build_editor_registry() -> EditorRegistry:
    """Register DummyEditor under several editor_ids.

    A single DummyEditor class is registered under several ids so
    that the LayoutBuilder can create independent instances for
    each slot. This mirrors the future reality where several
    concrete Editor classes will be registered under distinct ids.
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
        registry.register(editor_id, DummyEditor)
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
