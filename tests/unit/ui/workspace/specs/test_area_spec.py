"""Tests for AreaSpec."""

from __future__ import annotations

import pytest

from cranioz.ui.workspace.areas.placement import Placement
from cranioz.ui.workspace.specs.area_spec import AreaSpec, AreaSpecError
from cranioz.ui.workspace.specs.editor_layout_spec import EditorLayoutSpec


def _leaf(editor_id: str) -> EditorLayoutSpec:
    return EditorLayoutSpec.leaf(editor_id)


def test_area_spec_holds_fields() -> None:
    spec = AreaSpec(
        area_id="area.central",
        title="Central",
        placement=Placement.CENTRAL,
        editor_layout=_leaf("editor.a"),
    )
    assert spec.area_id == "area.central"
    assert spec.title == "Central"
    assert spec.placement is Placement.CENTRAL
    assert spec.editor_layout.editor_id == "editor.a"


def test_empty_area_id_raises() -> None:
    with pytest.raises(AreaSpecError, match="area_id"):
        AreaSpec(
            area_id="",
            title="X",
            placement=Placement.CENTRAL,
            editor_layout=_leaf("editor.a"),
        )


def test_empty_title_raises() -> None:
    with pytest.raises(AreaSpecError, match="title"):
        AreaSpec(
            area_id="area.x",
            title="",
            placement=Placement.CENTRAL,
            editor_layout=_leaf("editor.a"),
        )
