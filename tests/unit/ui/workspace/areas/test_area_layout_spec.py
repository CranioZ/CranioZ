"""Unit tests for AreaLayoutSpec (Sprint G).

These tests cover only the dataclass invariants. The integration
tests for the renderer (tests/integration/.../test_area_layout_renderer.py)
already cover the widget output; these tests cover the spec's own
validation, which the renderer relies on.
"""

from __future__ import annotations

import pytest

from cranioz.ui.workspace.areas.area_layout_spec import (
    AreaLayoutSpec,
    AreaLayoutType,
)


def test_single_requires_exactly_one_editor_id() -> None:
    with pytest.raises(ValueError, match="exactly one editor_id"):
        AreaLayoutSpec(AreaLayoutType.SINGLE, ("a", "b"))


def test_single_accepts_one_editor_id() -> None:
    spec = AreaLayoutSpec(AreaLayoutType.SINGLE, ("a",))
    assert spec.type is AreaLayoutType.SINGLE
    assert spec.editor_ids == ("a",)


def test_split_requires_at_least_two_editor_ids() -> None:
    with pytest.raises(ValueError, match="at least two editor_ids"):
        AreaLayoutSpec(AreaLayoutType.SPLIT, ("a",))


def test_split_accepts_two_editor_ids() -> None:
    spec = AreaLayoutSpec(AreaLayoutType.SPLIT, ("a", "b"))
    assert spec.type is AreaLayoutType.SPLIT
    assert spec.editor_ids == ("a", "b")


def test_stack_accepts_one_or_more_editor_ids() -> None:
    # A single-editor stack is a valid degenerate case for Sprint H.
    spec_one = AreaLayoutSpec(AreaLayoutType.STACK, ("a",))
    spec_two = AreaLayoutSpec(AreaLayoutType.STACK, ("a", "b"))
    assert spec_one.type is AreaLayoutType.STACK
    assert spec_two.type is AreaLayoutType.STACK


def test_empty_editor_ids_rejected() -> None:
    for layout_type in AreaLayoutType:
        with pytest.raises(ValueError, match="at least one editor_id"):
            AreaLayoutSpec(layout_type, ())
