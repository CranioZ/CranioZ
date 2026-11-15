import pytest

from cranioz.ui.workspace.areas.editor_layout_spec import (
    EditorLayoutSpec,
    LayoutType,
    SplitDirection,
)


def test_leaf_creation():
    spec = EditorLayoutSpec.leaf("editor.a")
    assert spec.type is LayoutType.LEAF
    assert spec.editor_id == "editor.a"
    assert spec.children == ()
    assert spec.direction is None
    assert spec.stacked is False


def test_split_creation():
    spec = EditorLayoutSpec.split(
        SplitDirection.HORIZONTAL,
        (EditorLayoutSpec.leaf("editor.a"), EditorLayoutSpec.leaf("editor.b")),
    )
    assert spec.type is LayoutType.SPLIT
    assert spec.direction is SplitDirection.HORIZONTAL
    assert len(spec.children) == 2
    assert spec.stacked is False


def test_stack_creation():
    spec = EditorLayoutSpec.stack(
        (EditorLayoutSpec.leaf("editor.a"), EditorLayoutSpec.leaf("editor.b")),
        direction=SplitDirection.VERTICAL,
    )
    assert spec.type is LayoutType.SPLIT
    assert spec.direction is SplitDirection.VERTICAL
    assert spec.stacked is True
    assert len(spec.children) == 2


def test_leaf_cannot_have_children():
    with pytest.raises(ValueError, match="LEAF must not have children"):
        EditorLayoutSpec(
            type=LayoutType.LEAF,
            editor_id="editor.a",
            children=(EditorLayoutSpec.leaf("editor.b"),),
        )


def test_split_requires_at_least_two_children():
    with pytest.raises(ValueError, match="SPLIT must have at least two children"):
        EditorLayoutSpec.split(SplitDirection.HORIZONTAL, (EditorLayoutSpec.leaf("editor.a"),))


def test_leaf_cannot_be_stacked():
    with pytest.raises(ValueError, match="LEAF must not declare stacked"):
        EditorLayoutSpec(
            type=LayoutType.LEAF,
            editor_id="editor.a",
            stacked=True,
        )
