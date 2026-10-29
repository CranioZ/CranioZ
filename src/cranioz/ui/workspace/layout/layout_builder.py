"""LayoutBuilder.

Materializes a ModuleUISpec into pure domain structures:

- Instantiates Editors via the EditorRegistry.
- Creates Areas from the AreaSpecs.
- Builds the LayoutTree via LayoutTree.from_specs.
- Registers the Areas in an AreaManager.

The LayoutBuilder does NOT touch Qt. It does not create widgets, does
not create Toolbars, does not materialize anything visual. That
responsibility belongs to the LayoutRenderer (see ADR-0002).

Contract (see ADR-0002):

- For each AreaSpec, the LayoutBuilder walks its EditorLayoutSpec in
  depth-first order and creates one Editor instance per editor_id.
- Each Editor receives its own EditorContext. The editor_id is specific
  to that Editor; extras are copied per Editor, so mutations do not
  leak between Editors (hybrid EditorContext model, ADR-0002 §2.1).
- The EditorLayoutSpec is validated structurally by its own dataclass
  at construction time. The LayoutBuilder does not repeat that
  validation.
- An unknown editor_id raises KeyError, propagated from the
  EditorRegistry with a clear message.
- The LayoutBuilder never imports PySide6 and never requires a
  QApplication (ADR-0002 §2.2).

Extension point (ADR-0002 §2.3):

- build() accepts an optional ``shared_context`` mapping. Its values
  are intended to be propagated by reference into every EditorContext
  created during the build.

  Today, the EditorContext dataclass has no fields to receive shared
  services (SceneQuery, CommandDispatcher, EventSubscription). The
  shared_context parameter is accepted and validated for type, but
  its contents are not yet propagated. When the first shared service
  is implemented, EditorContext will gain the corresponding typed
  fields and this builder will propagate them by reference. The
  parameter exists now to keep the builder interface stable across
  that evolution.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from cranioz.ui.editors.base_editor import Editor
from cranioz.ui.editors.editor_context import EditorContext
from cranioz.ui.editors.editor_registry import EditorRegistry
from cranioz.ui.workspace.areas.area import Area
from cranioz.ui.workspace.areas.area_manager import AreaManager
from cranioz.ui.workspace.layout.layout_tree import LayoutTree
from cranioz.ui.workspace.specs.area_spec import AreaSpec
from cranioz.ui.workspace.specs.editor_layout_spec import (
    EditorLayoutSpec,
    LayoutType,
)
from cranioz.ui.workspace.specs.module_ui_spec import ModuleUISpec


class LayoutBuilderError(ValueError):
    """Raised when the LayoutBuilder cannot materialize a spec."""


@dataclass(frozen=True)
class BuildResult:
    """Result of materializing a ModuleUISpec.

    Contains pure domain structures:

    - The Areas that were created.
    - The LayoutTree that was built.
    - The AreaManager, already populated with the Areas.
    - The Editors, indexed by the area_id of the Area that hosts them.

    Because the same editor_id may appear in multiple Areas (as two
    independent instances), a single flat list of Editors would lose
    the association between Editor and Area. The ``editors_by_area``
    mapping preserves that association.
    """

    areas: tuple[Area, ...]
    tree: LayoutTree
    area_manager: AreaManager
    editors_by_area: dict[str, tuple[Editor, ...]] = field(default_factory=dict)

    def area(self, area_id: str) -> Area:
        """Return the Area with the given area_id.

        Raises KeyError if no such Area exists.
        """
        return self.area_manager.require(area_id)

    def editors(self, area_id: str) -> tuple[Editor, ...]:
        """Return the Editors hosted by the Area with the given area_id.

        Returns an empty tuple if the Area exists but hosts no Editors.
        Raises KeyError if no such Area exists.
        """
        if not self.area_manager.contains(area_id):
            raise KeyError(f"area_id not registered: {area_id}")
        return self.editors_by_area.get(area_id, ())


class LayoutBuilder:
    """Builds pure domain structures from a ModuleUISpec.

    The builder is stateless with respect to a single build(): it can
    be reused across builds. State that varies per build (for example,
    the context extras for the Editors) is passed as arguments to
    build(), not stored on the builder.
    """

    def __init__(self, editor_registry: EditorRegistry) -> None:
        self._registry = editor_registry

    def build(
        self,
        spec: ModuleUISpec,
        *,
        context_extras: dict[str, Any] | None = None,
        shared_context: dict[str, Any] | None = None,
    ) -> BuildResult:
        """Materialize the ModuleUISpec.

        Args:
            spec: the declarative UI composition.
            context_extras: extras propagated into each EditorContext.
                Each Editor receives a copy, so mutations do not leak
                between Editors (ADR-0002 §2.1).
            shared_context: shared services propagated by reference into
                each EditorContext. Accepted keys: ``task_manager``,
                ``telemetry``, ``correlation_id``, ``command_dispatcher``,
                ``scene_query``. The builder does not interpret the
                contents; it only propagates them (ADR-0002 §2.3).

        Returns:
            A BuildResult containing the Areas, the LayoutTree, the
            populated AreaManager, and the Editors indexed by Area.

        Raises:
            LayoutBuilderError: if the spec cannot be materialized.
            KeyError: if an editor_id is not registered in the
                EditorRegistry.
            TypeError: if context_extras or shared_context is not a
                mapping.
        """
        if context_extras is not None and not isinstance(context_extras, dict):
            raise TypeError(
                f"context_extras must be a dict or None, got {type(context_extras).__name__}"
            )
        if shared_context is not None and not isinstance(shared_context, dict):
            raise TypeError(
                f"shared_context must be a dict or None, got {type(shared_context).__name__}"
            )

        # Defensive copies: the builder does not retain references to
        # caller-owned mutable state beyond the build() call.
        extras = dict(context_extras) if context_extras else {}
        # shared_context is NOT copied. It is propagated by reference to
        # preserve resource identity across Editors (ADR-0002 §2.3).
        shared = shared_context if shared_context else {}

        # 1. Instantiate Editors and create Areas.
        areas: list[Area] = []
        areas_by_id: dict[str, Area] = {}
        editors_by_area: dict[str, tuple[Editor, ...]] = {}

        for area_spec in spec.areas:
            editors = self._instantiate_editors(area_spec, extras, shared)

            area = Area(
                area_id=area_spec.area_id,
                title=area_spec.title,
                placement=area_spec.placement,
            )
            for editor in editors:
                area.add_editor(editor)

            areas.append(area)
            areas_by_id[area.area_id] = area
            editors_by_area[area.area_id] = tuple(editors)

        # 2. Build the LayoutTree.
        try:
            tree = LayoutTree.from_specs(tuple(spec.areas), areas_by_id)
        except ValueError as exc:
            raise LayoutBuilderError(str(exc)) from exc

        # 3. Register the Areas in the AreaManager.
        manager = AreaManager()
        for area in areas:
            manager.register(area)

        return BuildResult(
            areas=tuple(areas),
            tree=tree,
            area_manager=manager,
            editors_by_area=editors_by_area,
        )

    # ----- Internals ------------------------------------------------

    def _instantiate_editors(
        self,
        area_spec: AreaSpec,
        extras: dict[str, Any],
        shared: dict[str, Any],
    ) -> list[Editor]:
        """Walk the EditorLayoutSpec depth-first and create one Editor
        per LEAF, each with its own EditorContext.

        The EditorContext is per Editor (ADR-0002 §2.1). The extras are
        copied per Editor so that mutations do not leak between them.
        The shared services are propagated by reference (ADR-0002 §2.3).
        """
        editor_ids = self._collect_editor_ids(area_spec.editor_layout)
        editors: list[Editor] = []

        for editor_id in editor_ids:
            editor = self._registry.create(
                editor_id,
                editor_id=editor_id,
                title=editor_id,
            )

            # A fresh EditorContext per Editor. extras is copied so
            # that two Editors with the same editor_id do not share
            # mutable state. shared is propagated by reference.
            context = EditorContext(
                editor_id=editor_id,
                extras=dict(extras),
                **shared,
            )
            editor.initialize(context)
            editors.append(editor)

        return editors

    @staticmethod
    def _collect_editor_ids(layout: EditorLayoutSpec) -> list[str]:
        """Collect editor_ids in depth-first order from an
        EditorLayoutSpec.

        The EditorLayoutSpec dataclass guarantees:
        - A LEAF node has a non-empty editor_id and no children.
        - A SPLIT node has a direction and at least two children.
        This method relies on those invariants and does not repeat them.
        """
        result: list[str] = []

        def visit(node: EditorLayoutSpec) -> None:
            if node.type is LayoutType.LEAF:
                editor_id = node.editor_id
                if editor_id is None:
                    raise LayoutBuilderError(
                        "LEAF EditorLayoutSpec has no editor_id; "
                        "this violates the EditorLayoutSpec invariant"
                    )
                result.append(editor_id)
                return
            for child in node.children:
                visit(child)

        visit(layout)
        return result
