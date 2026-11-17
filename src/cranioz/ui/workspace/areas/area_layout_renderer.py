"""AreaLayoutRenderer."""

from __future__ import annotations

import logging  # <-- Adicionado
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QSizePolicy, QSplitter, QVBoxLayout, QWidget

from cranioz.ui.editors.base_editor import Editor
from cranioz.ui.workspace.areas.area import Area
from cranioz.ui.workspace.areas.area_layout_spec import (
    AreaLayoutSpec,
    AreaLayoutType,
)
from cranioz.ui.workspace.areas.editor_layout_spec import (
    EditorLayoutSpec,
    EditorStackOrientation,
    LayoutType,
    SplitDirection,
)
from cranioz.ui.workspace.areas.editor_stack import EditorStack

if TYPE_CHECKING:
    from cranioz.ui.icons.provider import IconProvider

_logger = logging.getLogger(__name__)  # <-- Adicionado


class AreaLayoutRenderer:
    """Materializes the intra-Area layout (Editors only)."""

    def __init__(self, icon_provider: IconProvider | None = None) -> None:
        self._icon_provider = icon_provider

    def render(
        self,
        area: Area,
        content_widgets: dict[str, QWidget],
    ) -> QWidget:
        editors = area.editors()
        _logger.debug("Renderer: render(%s) - Editores: %d", area.area_id, len(editors))

        if not editors:
            raise ValueError("AreaLayoutRenderer.render() requires a non-empty Area.")

        layout_spec: EditorLayoutSpec | None = getattr(area, "editor_layout_spec", None)
        _logger.debug("Renderer: Layout Spec: %s", layout_spec)

        if layout_spec is not None:
            return self._materialize_tree(layout_spec, editors, area, content_widgets)

        _logger.debug("Renderer: Sem layout_spec -> Fallback para flat")
        spec = self._resolve_spec(area)
        return self._materialize_flat(spec, editors, area, content_widgets)

    def _materialize_tree(
        self,
        node: EditorLayoutSpec,
        editors: tuple[Editor, ...],
        area: Area,
        content_widgets: dict[str, QWidget],
    ) -> QWidget:
        by_id = {e.editor_id: e for e in editors}

        if node.type is LayoutType.LEAF:
            editor_id = node.editor_id
            if editor_id is None:
                raise ValueError("LEAF node has no editor_id.")
            editor = by_id.get(editor_id)
            if editor is None:
                raise ValueError(f"Editor {editor_id!r} not found in Area.")
            return self._build_editor_container(editor, area, content_widgets)

        if node.type is LayoutType.SPLIT:
            if node.stacked:
                _logger.debug("Renderer: Materializando STACK com %d filhos.", len(node.children))
                return self._materialize_stack(node, by_id, area, content_widgets)
            _logger.debug("Renderer: Materializando SPLIT com %d filhos.", len(node.children))
            return self._materialize_split(node, by_id, area, content_widgets)

        raise ValueError(f"Unknown EditorLayoutSpec type: {node.type!r}")

    def _materialize_split(
        self,
        node: EditorLayoutSpec,
        by_id: dict[str, Editor],
        area: Area,
        content_widgets: dict[str, QWidget],
    ) -> QSplitter:
        orientation = (
            Qt.Orientation.Horizontal
            if node.direction is SplitDirection.HORIZONTAL
            else Qt.Orientation.Vertical
        )
        splitter = QSplitter(orientation)
        splitter.setObjectName(f"area_widget.{area.area_id}.split")
        splitter.setChildrenCollapsible(False)

        for child in node.children:
            widget = self._materialize_tree(child, tuple(by_id.values()), area, content_widgets)
            splitter.addWidget(widget)

        return splitter

    def _materialize_stack(
        self,
        node: EditorLayoutSpec,
        by_id: dict[str, Editor],
        area: Area,
        content_widgets: dict[str, QWidget],
    ) -> EditorStack:
        editor_ids: list[str] = []
        for child in node.children:
            if child.type is not LayoutType.LEAF or child.editor_id is None:
                raise ValueError("Stack children must be LEAF nodes.")
            editor_ids.append(child.editor_id)

        editors = tuple(by_id[eid] for eid in editor_ids)

        orientation = node.orientation or EditorStackOrientation.BOTTOM
        active_editor_id = area.active_editor_id or editor_ids[0]

        stack = EditorStack(
            editors=editors,
            orientation=orientation,
            active_editor_id=active_editor_id,
            icon_provider=self._icon_provider,
        )
        content_widgets["__editor_stack__"] = stack
        return stack

    def _resolve_spec(self, area: Area) -> AreaLayoutSpec:
        editors = area.editors()
        if len(editors) == 1:
            return AreaLayoutSpec(
                type=AreaLayoutType.SINGLE,
                editor_ids=(editors[0].editor_id,),
            )
        return AreaLayoutSpec(
            type=AreaLayoutType.SPLIT,
            editor_ids=tuple(e.editor_id for e in editors),
        )

    def _materialize_flat(
        self,
        spec: AreaLayoutSpec,
        editors: tuple[Editor, ...],
        area: Area,
        content_widgets: dict[str, QWidget],
    ) -> QWidget:
        by_id = {e.editor_id: e for e in editors}

        if set(spec.editor_ids) != set(by_id):
            raise ValueError("AreaLayoutSpec.editor_ids does not match the Area's Editors.")

        if spec.type is AreaLayoutType.SINGLE:
            return self._build_editor_container(by_id[spec.editor_ids[0]], area, content_widgets)

        if spec.type is AreaLayoutType.SPLIT:
            return self._render_split(spec, by_id, area, content_widgets)

        raise ValueError("Flat AreaLayoutSpec of type STACK is not supported.")

    def _render_split(
        self,
        spec: AreaLayoutSpec,
        by_id: dict[str, Editor],
        area: Area,
        content_widgets: dict[str, QWidget],
    ) -> QSplitter:
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setObjectName(f"area_widget.{area.area_id}.splitter")
        splitter.setChildrenCollapsible(False)
        for editor_id in spec.editor_ids:
            splitter.addWidget(
                self._build_editor_container(by_id[editor_id], area, content_widgets)
            )
        return splitter

    def _build_editor_container(
        self,
        editor: Editor,
        area: Area,
        content_widgets: dict[str, QWidget],
    ) -> QWidget:
        container = QWidget()
        container.setObjectName(f"area_widget.{area.area_id}.editor.{editor.editor_id}")
        container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        container.setMinimumSize(0, 0)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        content = editor.content_widget()
        content.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        content.setMinimumSize(0, 0)

        content.setParent(container)
        layout.addWidget(content)
        content_widgets[editor.editor_id] = content
        return container
