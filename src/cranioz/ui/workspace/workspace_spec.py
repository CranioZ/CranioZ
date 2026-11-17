"""WorkspaceSpec — predefined ModuleUISpec values.

Provides the spec used when a project is opened without an active
Flow (Bloco 9 not implemented yet). The Central Area hosts the
TomographyEditor (axial, coronal, sagittal, 3D Views). The lateral
Areas are declared but hidden by default; the user toggles them
from the Top Bar. When Bloco 9 delivers the Flow Catalog, the
Workspace will receive the Flow's ModuleUISpec instead.

Sprint H adds DEBUG_STACK to validate the EditorStack visually.
"""

from __future__ import annotations

from cranioz.editors.core.editor.placeholder_editor import (
    PLACEHOLDER_EDITOR_ID,
    PlaceholderEditor,
)
from cranioz.ui.workspace.areas.editor_layout_spec import (
    EditorLayoutSpec,
    EditorStackOrientation,
    SplitDirection,
)
from cranioz.ui.workspace.areas.placement import Placement
from cranioz.ui.workspace.specs.area_spec import AreaSpec
from cranioz.ui.workspace.specs.module_ui_spec import ModuleUISpec

__all__ = [
    "DEBUG_MESH",
    "DEBUG_STACK",
    "DEFAULT",
    "PLACEHOLDER_EDITOR_CLASS",
    "PLACEHOLDER_EDITOR_ID",
]

PLACEHOLDER_EDITOR_CLASS = PlaceholderEditor

DEFAULT: ModuleUISpec = ModuleUISpec(
    areas=(
        AreaSpec(
            area_id="area.left",
            title="Left",
            placement=Placement.LEFT,
            editor_layout=EditorLayoutSpec.leaf(PLACEHOLDER_EDITOR_ID),
        ),
        AreaSpec(
            area_id="area.central",
            title="Tomography",
            placement=Placement.CENTRAL,
            editor_layout=EditorLayoutSpec.leaf("editor.tomography"),
        ),
        AreaSpec(
            area_id="area.right",
            title="Right",
            placement=Placement.RIGHT,
            editor_layout=EditorLayoutSpec.leaf(PLACEHOLDER_EDITOR_ID),
        ),
        AreaSpec(
            area_id="area.bottom",
            title="Bottom",
            placement=Placement.BOTTOM,
            editor_layout=EditorLayoutSpec.leaf(PLACEHOLDER_EDITOR_ID),
        ),
    ),
)


DEBUG_MESH: ModuleUISpec = ModuleUISpec(
    areas=(
        AreaSpec(
            area_id="area.central",
            title="Mesh Debug",
            placement=Placement.CENTRAL,
            editor_layout=EditorLayoutSpec.leaf("editor.mesh_debug"),
        ),
    ),
)


# Sprint H: Spec de debug para validar o EditorStack visualmente.
# Empilha o TomographyEditor com o PlaceholderEditor.
DEBUG_STACK: ModuleUISpec = ModuleUISpec(
    areas=(
        AreaSpec(
            area_id="area.central",
            title="Central - Stack",
            placement=Placement.CENTRAL,
            # O nó STACK agrupa dois ou mais editores.
            # O 'direction=HORIZONTAL' coloca os botões de seleção embaixo.
            editor_layout=EditorLayoutSpec.stack(
                children=(
                    EditorLayoutSpec.leaf("editor.tomography"),
                    EditorLayoutSpec.leaf(PLACEHOLDER_EDITOR_ID),
                ),
                direction=SplitDirection.HORIZONTAL,
                orientation=EditorStackOrientation.BOTTOM,
            ),
        ),
    ),
)
