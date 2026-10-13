"""Integration tests for LayoutBuilder.

These tests exercise the full path:

    ModuleUISpec
        → LayoutBuilder.build()
        → BuildResult
              ├── Area instances (with Editors)
              ├── LayoutTree
              ├── AreaManager (populated)
              └── editors_by_area

The LayoutBuilder is a pure composition step and does NOT touch Qt.
Therefore, unlike the widget tests, these tests do NOT require a
QApplication. They run without ``qtbot`` and without ``qapp``.

The DummyEditor used in these tests does use QWidget internally
(its content_widget() returns a QLabel), but the LayoutBuilder never
calls content_widget(). It only calls:

- EditorRegistry.create()          → constructs the instance
- Editor.initialize(context)       → stores the context
- Editor.editor_id / .title        → reads metadata

Since DummyEditor.initialize() does not instantiate any QWidget, the
builder runs without a QApplication. This is the property that makes
the LayoutBuilder testable in milliseconds and free of Qt platform
constraints.

What these tests cover:

- Building a spec with a single CENTRAL Area.
- Building a spec with LEFT + CENTRAL + RIGHT Areas.
- Building a spec with all four Areas (LEFT, CENTRAL, RIGHT, BOTTOM).
- Building a spec where a single Area hosts a nested 2x2 SPLIT of
  Editors (the prototype's central grid).
- The AreaManager is populated with every Area created.
- editors_by_area maps each area_id to the Editors it hosts, in
  depth-first order.
- BuildResult.area() and BuildResult.editors() accessors.
- Unknown editor_id → KeyError with a clear message.
- context_extras are copied per Editor (hybrid EditorContext model,
  ADR-0002 §2.1).
- shared_context is accepted without error but is not yet propagated
  (ADR-0002 §2.3).
- Invalid argument types raise TypeError.
"""
from __future__ import annotations

import re

import pytest

from cranioz.ui.editors.builtin.test_editor import DummyEditor
from cranioz.ui.editors.editor_registry import EditorRegistry
from cranioz.ui.workspace.areas.area import AreaError
from cranioz.ui.workspace.areas.placement import Placement
from cranioz.ui.workspace.layout.layout_builder import (
    BuildResult,
    LayoutBuilder,
)
from cranioz.ui.workspace.layout.layout_tree import Leaf, Split
from cranioz.ui.workspace.specs.area_spec import AreaSpec
from cranioz.ui.workspace.specs.editor_layout_spec import (
    EditorLayoutSpec,
    SplitDirection,
)
from cranioz.ui.workspace.specs.module_ui_spec import (
    ModuleUISpec,
    ModuleUISpecError,
)

# ----- Local helpers ------------------------------------------------


def _leaf(editor_id: str) -> EditorLayoutSpec:
    """Shorthand for a LEAF EditorLayoutSpec."""
    return EditorLayoutSpec.leaf(editor_id)


def _area(
    area_id: str,
    placement: Placement,
    editor_layout: EditorLayoutSpec,
    title: str | None = None,
) -> AreaSpec:
    """Build a minimal AreaSpec for tests."""
    return AreaSpec(
        area_id=area_id,
        title=title if title is not None else area_id,
        placement=placement,
        editor_layout=editor_layout,
    )


def _spec(*areas: AreaSpec) -> ModuleUISpec:
    """Build a ModuleUISpec from the given AreaSpecs."""
    return ModuleUISpec(areas=tuple(areas))


# ----- Fixtures local to this module --------------------------------


@pytest.fixture
def registry() -> EditorRegistry:
    """An EditorRegistry pre-populated with the editor_ids used below.

    A single DummyEditor class is registered under several editor_ids
    so that the builder can create independent instances for each
    editor_id appearing in a spec. This mirrors the future reality
    where several distinct Editor classes will be registered under
    distinct ids.
    """
    reg = EditorRegistry()
    for editor_id in (
        "editor.patient",
        "editor.viewport_3d",
        "editor.mpr_axial",
        "editor.mpr_sagittal",
        "editor.mpr_coronal",
        "editor.object_list",
        "editor.properties",
        "editor.material",
        "editor.console",
        "editor.history",
        "editor.ai_assistant",
    ):
        reg.register(editor_id, DummyEditor)
    return reg


@pytest.fixture
def builder(registry: EditorRegistry) -> LayoutBuilder:
    """A LayoutBuilder backed by the populated registry."""
    return LayoutBuilder(registry)


# ----- Building a single CENTRAL Area -------------------------------


def test_build_single_central_creates_leaf_tree(builder: LayoutBuilder) -> None:
    spec = _spec(
        _area("area.central", Placement.CENTRAL, _leaf("editor.patient")),
    )

    result = builder.build(spec)

    assert isinstance(result, BuildResult)
    assert len(result.areas) == 1
    assert result.areas[0].area_id == "area.central"
    assert isinstance(result.tree.root, Leaf)
    assert result.tree.root.area.area_id == "area.central"


def test_build_single_central_registers_area(builder: LayoutBuilder) -> None:
    spec = _spec(
        _area("area.central", Placement.CENTRAL, _leaf("editor.patient")),
    )

    result = builder.build(spec)

    assert result.area_manager.contains("area.central")
    assert result.area_manager.area_count() == 1
    assert result.area_manager.has_central()


def test_build_single_central_creates_editor(builder: LayoutBuilder) -> None:
    spec = _spec(
        _area("area.central", Placement.CENTRAL, _leaf("editor.patient")),
    )

    result = builder.build(spec)

    editors = result.editors("area.central")
    assert len(editors) == 1
    assert editors[0].editor_id == "editor.patient"
    assert isinstance(editors[0], DummyEditor)


# ----- Building LEFT + CENTRAL + RIGHT ------------------------------


def test_build_left_central_right_tree_shape(builder: LayoutBuilder) -> None:
    spec = _spec(
        _area("area.left", Placement.LEFT, _leaf("editor.object_list")),
        _area("area.central", Placement.CENTRAL, _leaf("editor.viewport_3d")),
        _area("area.right", Placement.RIGHT, _leaf("editor.properties")),
    )

    result = builder.build(spec)

    assert isinstance(result.tree.root, Split)
    assert result.tree.root.direction is SplitDirection.HORIZONTAL
    assert len(result.tree.root.children) == 3
    assert [a.area_id for a in result.tree.areas()] == [
        "area.left",
        "area.central",
        "area.right",
    ]


def test_build_left_central_right_registers_all_areas(
    builder: LayoutBuilder,
) -> None:
    spec = _spec(
        _area("area.left", Placement.LEFT, _leaf("editor.object_list")),
        _area("area.central", Placement.CENTRAL, _leaf("editor.viewport_3d")),
        _area("area.right", Placement.RIGHT, _leaf("editor.properties")),
    )

    result = builder.build(spec)

    assert result.area_manager.area_count() == 3
    assert result.area_manager.contains("area.left")
    assert result.area_manager.contains("area.central")
    assert result.area_manager.contains("area.right")


def test_build_left_central_right_populates_editors(
    builder: LayoutBuilder,
) -> None:
    spec = _spec(
        _area("area.left", Placement.LEFT, _leaf("editor.object_list")),
        _area("area.central", Placement.CENTRAL, _leaf("editor.viewport_3d")),
        _area("area.right", Placement.RIGHT, _leaf("editor.properties")),
    )

    result = builder.build(spec)

    assert [e.editor_id for e in result.editors("area.left")] == [
        "editor.object_list",
    ]
    assert [e.editor_id for e in result.editors("area.central")] == [
        "editor.viewport_3d",
    ]
    assert [e.editor_id for e in result.editors("area.right")] == [
        "editor.properties",
    ]


# ----- Building all four Areas --------------------------------------


def test_build_four_areas_tree_shape(builder: LayoutBuilder) -> None:
    spec = _spec(
        _area("area.left", Placement.LEFT, _leaf("editor.object_list")),
        _area("area.central", Placement.CENTRAL, _leaf("editor.viewport_3d")),
        _area("area.right", Placement.RIGHT, _leaf("editor.properties")),
        _area("area.bottom", Placement.BOTTOM, _leaf("editor.console")),
    )

    result = builder.build(spec)

    # Root is VERTICAL because there is a bottom row.
    assert isinstance(result.tree.root, Split)
    assert result.tree.root.direction is SplitDirection.VERTICAL
    top, bottom = result.tree.root.children
    assert isinstance(top, Split)
    assert top.direction is SplitDirection.HORIZONTAL
    assert isinstance(bottom, Leaf)
    assert bottom.area.area_id == "area.bottom"


def test_build_four_areas_registers_all(builder: LayoutBuilder) -> None:
    spec = _spec(
        _area("area.left", Placement.LEFT, _leaf("editor.object_list")),
        _area("area.central", Placement.CENTRAL, _leaf("editor.viewport_3d")),
        _area("area.right", Placement.RIGHT, _leaf("editor.properties")),
        _area("area.bottom", Placement.BOTTOM, _leaf("editor.console")),
    )

    result = builder.build(spec)

    assert result.area_manager.area_count() == 4
    for area_id in ("area.left", "area.central", "area.right", "area.bottom"):
        assert result.area_manager.contains(area_id)


# ----- A single Area hosting a nested 2x2 SPLIT ---------------------


def test_build_central_with_2x2_split(builder: LayoutBuilder) -> None:
    """Replicates the prototype's central grid: 2x2 of MPR + 3D."""
    central_layout = EditorLayoutSpec.split(
        SplitDirection.HORIZONTAL,
        (
            EditorLayoutSpec.split(
                SplitDirection.VERTICAL,
                (
                    _leaf("editor.mpr_axial"),
                    _leaf("editor.mpr_sagittal"),
                ),
            ),
            EditorLayoutSpec.split(
                SplitDirection.VERTICAL,
                (
                    _leaf("editor.mpr_coronal"),
                    _leaf("editor.viewport_3d"),
                ),
            ),
        ),
    )
    spec = _spec(
        _area("area.central", Placement.CENTRAL, central_layout),
    )

    result = builder.build(spec)

    # The tree has a single Area (CENTRAL), so the root is a Leaf.
    assert isinstance(result.tree.root, Leaf)
    assert result.tree.area_count() == 1

    # The single Area hosts four Editors, in depth-first order.
    editors = result.editors("area.central")
    assert [e.editor_id for e in editors] == [
        "editor.mpr_axial",
        "editor.mpr_sagittal",
        "editor.mpr_coronal",
        "editor.viewport_3d",
    ]


def test_build_central_split_editor_order_is_depth_first(
    builder: LayoutBuilder,
) -> None:
    """Order of Editors is the depth-first order of the EditorLayoutSpec."""
    central_layout = EditorLayoutSpec.split(
        SplitDirection.HORIZONTAL,
        (
            _leaf("editor.mpr_axial"),
            _leaf("editor.mpr_sagittal"),
            _leaf("editor.mpr_coronal"),
        ),
    )
    spec = _spec(
        _area("area.central", Placement.CENTRAL, central_layout),
    )

    result = builder.build(spec)

    assert [e.editor_id for e in result.editors("area.central")] == [
        "editor.mpr_axial",
        "editor.mpr_sagittal",
        "editor.mpr_coronal",
    ]


# ----- BuildResult accessors ----------------------------------------


def test_build_result_area_accessor(builder: LayoutBuilder) -> None:
    spec = _spec(
        _area("area.central", Placement.CENTRAL, _leaf("editor.patient")),
    )
    result = builder.build(spec)

    area = result.area("area.central")
    assert area.area_id == "area.central"
    assert area.placement is Placement.CENTRAL


def test_build_result_area_accessor_unknown_raises(
    builder: LayoutBuilder,
) -> None:
    spec = _spec(
        _area("area.central", Placement.CENTRAL, _leaf("editor.patient")),
    )
    result = builder.build(spec)

    with pytest.raises(KeyError, match="not registered"):
        result.area("area.unknown")


def test_build_result_editors_accessor_unknown_raises(
    builder: LayoutBuilder,
) -> None:
    spec = _spec(
        _area("area.central", Placement.CENTRAL, _leaf("editor.patient")),
    )
    result = builder.build(spec)

    with pytest.raises(KeyError, match="not registered"):
        result.editors("area.unknown")


# ----- Errors -------------------------------------------------------


def test_build_unknown_editor_id_raises_key_error(
    builder: LayoutBuilder,
) -> None:
    spec = _spec(
        _area("area.central", Placement.CENTRAL, _leaf("editor.does_not_exist")),
    )

    with pytest.raises(KeyError, match=re.escape("editor.does_not_exist")):
        builder.build(spec)


def test_build_unknown_editor_id_in_nested_split_raises(
    builder: LayoutBuilder,
) -> None:
    central_layout = EditorLayoutSpec.split(
        SplitDirection.HORIZONTAL,
        (
            _leaf("editor.mpr_axial"),
            _leaf("editor.does_not_exist"),
        ),
    )
    spec = _spec(
        _area("area.central", Placement.CENTRAL, central_layout),
    )

    with pytest.raises(KeyError, match=re.escape("editor.does_not_exist")):
        builder.build(spec)


def test_build_module_ui_spec_without_central_raises_at_spec_construction(
    builder: LayoutBuilder,
) -> None:
    """ModuleUISpec itself rejects the spec, before the builder sees it.

    This test documents the layering: the invariant "at least one
    CENTRAL" is enforced by ModuleUISpec, not by the LayoutBuilder.
    """

    with pytest.raises(ModuleUISpecError, match="CENTRAL"):
        _spec(
            _area("area.left", Placement.LEFT, _leaf("editor.object_list")),
            _area("area.right", Placement.RIGHT, _leaf("editor.properties")),
        )


# ----- context_extras (hybrid EditorContext) ------------------------


def test_build_propagates_extras_to_each_editor(
    builder: LayoutBuilder,
) -> None:
    spec = _spec(
        _area(
            "area.central",
            Placement.CENTRAL,
            EditorLayoutSpec.split(
                SplitDirection.HORIZONTAL,
                (_leaf("editor.mpr_axial"), _leaf("editor.mpr_sagittal")),
            ),
        ),
    )

    result = builder.build(spec, context_extras={"project": "P-001"})

    editors = result.editors("area.central")
    assert len(editors) == 2
    for editor in editors:
        state = editor.persistent_state()
        assert state["extras"] == {"project": "P-001"}


def test_build_extras_are_copies_not_shared_references(
    builder: LayoutBuilder,
) -> None:
    """Each Editor receives its own copy of the extras dict.

    Mutating one Editor's extras must not affect another's. This is
    the hybrid EditorContext property (ADR-0002 §2.1).
    """
    spec = _spec(
        _area(
            "area.central",
            Placement.CENTRAL,
            EditorLayoutSpec.split(
                SplitDirection.HORIZONTAL,
                (_leaf("editor.mpr_axial"), _leaf("editor.mpr_sagittal")),
            ),
        ),
    )

    result = builder.build(spec, context_extras={"shared_key": "value"})

    a, b = result.editors("area.central")
    # Each Editor sees the same initial content...
    assert a.persistent_state()["extras"] == {"shared_key": "value"}
    assert b.persistent_state()["extras"] == {"shared_key": "value"}

    # ...but the two dicts are distinct objects.
    # We reach into the private attribute only in the test to prove
    # the invariant; production code never does this.
    extras_a = a.persistent_state()["extras"]  # type: ignore[attr-defined]
    extras_b = b.persistent_state()["extras"]  # type: ignore[attr-defined]
    assert extras_a is not extras_b


def test_build_without_extras_gives_empty_dicts(
    builder: LayoutBuilder,
) -> None:
    spec = _spec(
        _area("area.central", Placement.CENTRAL, _leaf("editor.patient")),
    )

    result = builder.build(spec)

    editor = result.editors("area.central")[0]
    assert editor.persistent_state()["extras"] == {}


def test_build_does_not_mutate_caller_extras(
    builder: LayoutBuilder,
) -> None:
    """The builder must not mutate the caller's dict."""
    spec = _spec(
        _area("area.central", Placement.CENTRAL, _leaf("editor.patient")),
    )
    original = {"project": "P-001"}
    snapshot = dict(original)

    builder.build(spec, context_extras=original)

    assert original == snapshot


# ----- shared_context (extension point, ADR-0002 §2.3) --------------


def test_build_accepts_shared_context_without_error(
    builder: LayoutBuilder,
) -> None:
    """shared_context is accepted today as an extension point.

    It is not yet propagated, because EditorContext has no fields to
    receive shared services. This test documents that the parameter
    exists and does not break the build.
    """
    spec = _spec(
        _area("area.central", Placement.CENTRAL, _leaf("editor.patient")),
    )

    # Passing a dict must not raise.
    result = builder.build(spec, shared_context={"scene_query": object()})
    assert len(result.areas) == 1


def test_build_rejects_non_mapping_context_extras(
    builder: LayoutBuilder,
) -> None:
    spec = _spec(
        _area("area.central", Placement.CENTRAL, _leaf("editor.patient")),
    )

    with pytest.raises(TypeError, match="context_extras"):
        builder.build(spec, context_extras=["not", "a", "dict"])  # type: ignore[arg-type]


def test_build_rejects_non_mapping_shared_context(
    builder: LayoutBuilder,
) -> None:
    spec = _spec(
        _area("area.central", Placement.CENTRAL, _leaf("editor.patient")),
    )

    with pytest.raises(TypeError, match="shared_context"):
        builder.build(spec, shared_context=["not", "a", "dict"])  # type: ignore[arg-type]


# ----- Builder reuse ------------------------------------------------


def test_builder_is_reusable_across_builds(builder: LayoutBuilder) -> None:
    """The builder carries no per-build state and can be reused."""
    spec_a = _spec(
        _area("area.central", Placement.CENTRAL, _leaf("editor.patient")),
    )
    spec_b = _spec(
        _area(
            "area.central",
            Placement.CENTRAL,
            EditorLayoutSpec.split(
                SplitDirection.HORIZONTAL,
                (_leaf("editor.mpr_axial"), _leaf("editor.mpr_sagittal")),
            ),
        ),
    )

    result_a = builder.build(spec_a)
    result_b = builder.build(spec_b)

    assert result_a.area_manager.area_count() == 1
    assert len(result_a.editors("area.central")) == 1
    assert result_b.area_manager.area_count() == 1
    assert len(result_b.editors("area.central")) == 2

    # The two results do not share state.
    assert result_a.area_manager is not result_b.area_manager
    assert result_a.tree is not result_b.tree


def test_builder_creates_distinct_editor_instances_per_build(
    builder: LayoutBuilder,
) -> None:
    """Two builds of the same spec produce independent Editor instances."""
    spec = _spec(
        _area("area.central", Placement.CENTRAL, _leaf("editor.patient")),
    )

    result_a = builder.build(spec)
    result_b = builder.build(spec)

    editor_a = result_a.editors("area.central")[0]
    editor_b = result_b.editors("area.central")[0]
    assert editor_a is not editor_b


def test_area_rejects_duplicate_editor_id_in_same_build(
    builder: LayoutBuilder,
) -> None:
    """The Area rejects two Editors with the same editor_id.

    Each editor_id within an Area must be unique. A user who wants
    two Viewport3D Editors in the same Area must register them under
    distinct editor_ids (e.g. editor.viewport_3d.left and
    editor.viewport_3d.right) pointing to the same Editor class.

    The invariant is enforced by Area.add_editor, not by the builder.
    The builder propagates the error without swallowing it.
    """
    spec = _spec(
        _area(
            "area.central",
            Placement.CENTRAL,
            EditorLayoutSpec.split(
                SplitDirection.HORIZONTAL,
                (_leaf("editor.viewport_3d"), _leaf("editor.viewport_3d")),
            ),
        ),
    )

    with pytest.raises(AreaError, match="already hosted"):
        builder.build(spec)
