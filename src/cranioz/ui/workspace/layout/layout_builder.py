"""LayoutBuilder."""

from __future__ import annotations

import logging  # <-- Adicionado
from dataclasses import dataclass, field
from typing import Any

from cranioz.editors.core.editor.base_editor import Editor
from cranioz.editors.core.editor.editor_context import EditorContext
from cranioz.editors.core.editor.editor_registry import EditorRegistry
from cranioz.ui.workspace.areas.area import Area
from cranioz.ui.workspace.areas.area_manager import AreaManager
from cranioz.ui.workspace.areas.editor_layout_spec import (
    EditorLayoutSpec,
)
from cranioz.ui.workspace.layout.layout_tree import LayoutTree
from cranioz.ui.workspace.specs.area_spec import AreaSpec
from cranioz.ui.workspace.specs.module_ui_spec import ModuleUISpec

_logger = logging.getLogger(__name__)  # <-- Adicionado


class LayoutBuilderError(ValueError):
    """Raised when the LayoutBuilder cannot materialize a spec."""


@dataclass(frozen=True)
class BuildResult:
    areas: tuple[Area, ...]
    tree: LayoutTree
    area_manager: AreaManager
    editors_by_area: dict[str, tuple[Editor, ...]] = field(default_factory=dict)

    def area(self, area_id: str) -> Area:
        return self.area_manager.require(area_id)

    def editors(self, area_id: str) -> tuple[Editor, ...]:
        if not self.area_manager.contains(area_id):
            raise KeyError(f"area_id not registered: {area_id}")
        return self.editors_by_area.get(area_id, ())


class LayoutBuilder:
    def __init__(self, editor_registry: EditorRegistry) -> None:
        self._registry = editor_registry

    def build(
        self,
        spec: ModuleUISpec,
        *,
        context_extras: dict[str, Any] | None = None,
        shared_context: dict[str, Any] | None = None,
    ) -> BuildResult:
        if context_extras is not None and not isinstance(context_extras, dict):
            raise TypeError("context_extras must be a dict or None")
        if shared_context is not None and not isinstance(shared_context, dict):
            raise TypeError("shared_context must be a dict or None")

        extras = dict(context_extras) if context_extras else {}
        shared = shared_context if shared_context else {}

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

            # Sprint H: Anexa a spec na Area
            area.set_editor_layout_spec(area_spec.editor_layout)

            areas.append(area)
            areas_by_id[area.area_id] = area
            editors_by_area[area.area_id] = tuple(editors)

        try:
            tree = LayoutTree.from_specs(tuple(spec.areas), areas_by_id)
        except ValueError as exc:
            raise LayoutBuilderError(str(exc)) from exc

        manager = AreaManager()
        for area in areas:
            manager.register(area)

        return BuildResult(
            areas=tuple(areas),
            tree=tree,
            area_manager=manager,
            editors_by_area=editors_by_area,
        )

    def _instantiate_editors(
        self,
        area_spec: AreaSpec,
        extras: dict[str, Any],
        shared: dict[str, Any],
    ) -> list[Editor]:
        editor_ids = self._collect_editor_ids(area_spec.editor_layout)

        _logger.debug("LayoutBuilder: Área %s, IDs encontrados: %s", area_spec.area_id, editor_ids)

        editors: list[Editor] = []

        for editor_id in editor_ids:
            _logger.debug("LayoutBuilder: Criando instância do editor: %s", editor_id)
            editor = self._registry.create(
                editor_id,
                editor_id=editor_id,
                title=editor_id,
            )
            context = EditorContext(
                editor_id=editor_id,
                extras=dict(extras),
                **shared,
            )
            editor.initialize(context)
            editors.append(editor)

        _logger.debug(
            "LayoutBuilder: Total de editores criados na área %s: %d",
            area_spec.area_id,
            len(editors),
        )
        return editors

    @staticmethod
    def _collect_editor_ids(layout: EditorLayoutSpec) -> list[str]:
        """Collect editor_ids in depth-first order from an EditorLayoutSpec.

        A LEAF node has an editor_id and no children.
        A SPLIT/STACK node has children and no editor_id.
        """
        result: list[str] = []

        def visit(node: EditorLayoutSpec) -> None:
            # Se o nó tem editor_id, é uma folha.
            if node.editor_id is not None:
                result.append(node.editor_id)
                return
            # Caso contrário, desce nos filhos (SPLIT ou STACK).
            for child in node.children:
                visit(child)

        visit(layout)
        return result
