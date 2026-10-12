"""Tests for ModuleUISpec."""

from __future__ import annotations

import pytest

from cranioz.ui.workspace.areas.placement import Placement
from cranioz.ui.workspace.specs.area_spec import AreaSpec
from cranioz.ui.workspace.specs.editor_layout_spec import EditorLayoutSpec
from cranioz.ui.workspace.specs.module_ui_spec import (
    ModuleUISpec,
    ModuleUISpecError,
)


def _area(area_id: str, placement: Placement, editor_id: str) -> AreaSpec:
    return AreaSpec(
        area_id=area_id,
        title=area_id,
        placement=placement,
        editor_layout=EditorLayoutSpec.leaf(editor_id),
    )


def test_single_central_is_valid() -> None:
    spec = ModuleUISpec(
        areas=(_area("area.central", Placement.CENTRAL, "editor.a"),)
    )
    assert len(spec.areas) == 1
    assert spec.overlays == ()


def test_left_central_right_is_valid() -> None:
    spec = ModuleUISpec(
        areas=(
            _area("area.left", Placement.LEFT, "editor.left"),
            _area("area.central", Placement.CENTRAL, "editor.central"),
            _area("area.right", Placement.RIGHT, "editor.right"),
        )
    )
    assert len(spec.areas) == 3


def test_four_areas_is_valid() -> None:
    spec = ModuleUISpec(
        areas=(
            _area("area.left", Placement.LEFT, "editor.left"),
            _area("area.central", Placement.CENTRAL, "editor.central"),
            _area("area.right", Placement.RIGHT, "editor.right"),
            _area("area.bottom", Placement.BOTTOM, "editor.bottom"),
        )
    )
    assert len(spec.areas) == 4


def test_without_central_raises() -> None:
    with pytest.raises(ModuleUISpecError, match="CENTRAL"):
        ModuleUISpec(
            areas=(
                _area("area.left", Placement.LEFT, "editor.left"),
                _area("area.right", Placement.RIGHT, "editor.right"),
            )
        )


def test_duplicate_area_id_raises() -> None:
    with pytest.raises(ModuleUISpecError, match="unique"):
        ModuleUISpec(
            areas=(
                _area("area.central", Placement.CENTRAL, "editor.a"),
                _area("area.central", Placement.CENTRAL, "editor.b"),
            )
        )


def test_empty_areas_raises() -> None:
    with pytest.raises(ModuleUISpecError, match="at least one Area"):
        ModuleUISpec(areas=())