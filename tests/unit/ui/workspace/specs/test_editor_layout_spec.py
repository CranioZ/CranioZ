"""Tests for EditorLayoutSpec."""

from __future__ import annotations

import pytest

from cranioz.ui.workspace.specs.editor_layout_spec import (
    EditorLayoutSpec,
    EditorLayoutSpecError,
    LayoutType,
    SplitDirection,
)


# ----- LEAF ---------------------------------------------------------


def test_leaf_factory_creates_leaf() -> None:
    spec = EditorLayoutSpec.leaf("editor.a")
    assert spec.type is LayoutType.LEAF
    assert spec.editor_id == "editor.a"
    assert spec.direction is None
    assert spec.children == ()


def test_leaf_without_editor_id_raises() -> None:
    with pytest.raises(EditorLayoutSpecError, match="editor_id"):
        EditorLayoutSpec(type=LayoutType.LEAF)


def test_leaf_with_children_raises() -> None:
    child = EditorLayoutSpec.leaf("editor.a")
    with pytest.raises(EditorLayoutSpecError, match="must not have children"):
        EditorLayoutSpec(
            type=LayoutType.LEAF,
            editor_id="editor.b",
            children=(child,),
        )


def test_leaf_with_direction_raises() -> None:
    with pytest.raises(EditorLayoutSpecError, match="must not declare direction"):
        EditorLayoutSpec(
            type=LayoutType.LEAF,
            editor_id="editor.a",
            direction=SplitDirection.HORIZONTAL,
        )


# ----- SPLIT --------------------------------------------------------


def test_split_factory_creates_split() -> None:
    a = EditorLayoutSpec.leaf("editor.a")
    b = EditorLayoutSpec.leaf("editor.b")
    spec = EditorLayoutSpec.split(SplitDirection.HORIZONTAL, (a, b))
    assert spec.type is LayoutType.SPLIT
    assert spec.direction is SplitDirection.HORIZONTAL
    assert spec.children == (a, b)
    assert spec.editor_id is None


def test_split_with_editor_id_raises() -> None:
    a = EditorLayoutSpec.leaf("editor.a")
    b = EditorLayoutSpec.leaf("editor.b")
    with pytest.raises(EditorLayoutSpecError, match="must not declare editor_id"):
        EditorLayoutSpec(
            type=LayoutType.SPLIT,
            direction=SplitDirection.HORIZONTAL,
            children=(a, b),
            editor_id="editor.c",
        )


def test_split_without_direction_raises() -> None:
    a = EditorLayoutSpec.leaf("editor.a")
    b = EditorLayoutSpec.leaf("editor.b")
    with pytest.raises(EditorLayoutSpecError, match="must declare direction"):
        EditorLayoutSpec(
            type=LayoutType.SPLIT,
            children=(a, b),
        )


def test_split_with_one_child_raises() -> None:
    a = EditorLayoutSpec.leaf("editor.a")
    with pytest.raises(EditorLayoutSpecError, match="at least two children"):
        EditorLayoutSpec.split(SplitDirection.HORIZONTAL, (a,))


def test_split_with_zero_children_raises() -> None:
    with pytest.raises(EditorLayoutSpecError, match="at least two children"):
        EditorLayoutSpec.split(SplitDirection.HORIZONTAL, ())


def test_nested_split_is_valid() -> None:
    """Replicates the prototype's 2x2 central area."""
    a = EditorLayoutSpec.leaf("editor.a")
    b = EditorLayoutSpec.leaf("editor.b")
    c = EditorLayoutSpec.leaf("editor.c")
    d = EditorLayoutSpec.leaf("editor.d")

    inner_left = EditorLayoutSpec.split(SplitDirection.VERTICAL, (a, b))
    inner_right = EditorLayoutSpec.split(SplitDirection.VERTICAL, (c, d))
    outer = EditorLayoutSpec.split(
        SplitDirection.HORIZONTAL, (inner_left, inner_right)
    )

    assert outer.type is LayoutType.SPLIT
    assert len(outer.children) == 2
    assert outer.children[0].type is LayoutType.SPLIT
    assert outer.children[1].type is LayoutType.SPLIT


def test_unknown_layout_type_raises() -> None:
    class Fake:
        pass

    with pytest.raises(EditorLayoutSpecError, match="unknown layout type"):
        EditorLayoutSpec(type=Fake)  # type: ignore[arg-type]