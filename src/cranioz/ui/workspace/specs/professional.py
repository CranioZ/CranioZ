"""Workspace composition for the Professional Editor."""

from __future__ import annotations

from cranioz.editors.builtin.professional import PROFESSIONAL_EDITOR_ID
from cranioz.ui.workspace.areas.placement import Placement
from cranioz.ui.workspace.specs.area_spec import AreaSpec
from cranioz.ui.workspace.specs.editor_layout_spec import EditorLayoutSpec
from cranioz.ui.workspace.specs.module_ui_spec import ModuleUISpec

PROFESSIONAL_UI_SPEC = ModuleUISpec(
    areas=(
        AreaSpec(
            area_id="area.professional.central",
            title="Professional",
            placement=Placement.CENTRAL,
            editor_layout=EditorLayoutSpec.leaf(PROFESSIONAL_EDITOR_ID),
        ),
    ),
)

__all__ = ["PROFESSIONAL_UI_SPEC"]
