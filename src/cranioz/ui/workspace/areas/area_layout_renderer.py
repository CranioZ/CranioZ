"""AreaLayoutRenderer.

Separates inter-Area layout (LayoutRenderer) from intra-Area layout
(AreaLayoutRenderer).

Per ADR-0013 (revised), the AreaLayoutRenderer organizes *Editors*
inside an Area. It does **not** materialize Toolbars: Toolbars are
declared by Editors (editor-level) and by Views (view-level), and
materialized by the respective renderers (EditorLayoutRenderer /
ViewLayoutRenderer). See ADR-0013 §2.6, §2.7.

The AreaLayoutRenderer's responsibility is therefore limited to:

- Resolving the Area's Editor composition into an ``AreaLayoutSpec``.
- For a SINGLE Editor: building the container widget for that
  Editor and its content (delegating to the Editor's own
  ``content_widget()``).
- For SPLIT (multiple Editors): arranging the Editor containers in
  a QSplitter (a placeholder for the Editor Layout Tree, ADR-0013
  §2.2).
- For STACK: raising ``NotImplementedError``. STACK is reserved for
  Sprint H (EditorStack) and is not yet materialized.

Sprint G delivers the ``AreaLayoutSpec`` and the explicit STACK point
of extension. The current behavior (single Editor, or a horizontal
splitter for multiple Editors) is preserved. Sprint H will replace
``_render_split`` with ``_render_stack`` and flip ``_resolve_spec``
to return STACK for multiple Editors.

See ADR-0013 §2.2, §2.7.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QSizePolicy, QSplitter, QVBoxLayout, QWidget

from cranioz.ui.editors.base_editor import Editor
from cranioz.ui.workspace.areas.area import Area
from cranioz.ui.workspace.areas.area_layout_spec import (
    AreaLayoutSpec,
    AreaLayoutType,
)


class AreaLayoutRenderer:
    """Materializes the intra-Area layout (Editors only)."""

    def render(
        self,
        area: Area,
        content_widgets: dict[str, QWidget],
    ) -> QWidget:
        """Render the contents of a single Area.

        Args:
            area: the Area whose Editors are rendered. Must be
                non-empty.
            content_widgets: mapping populated with
                ``{editor_id: content_widget}`` for cleanup.

        Returns:
            A QWidget containing the Area's contents: either a single
            Editor container (when there is one Editor) or a QSplitter
            with one container per Editor (when there are multiple).

        Raises:
            ValueError: if the Area is empty, or if the resolved spec
                violates its own invariants.
            NotImplementedError: if the resolved spec is STACK (Sprint
                H, EditorStack; not yet materialized).
        """
        editors = area.editors()
        if not editors:
            raise ValueError(
                "AreaLayoutRenderer.render() requires a non-empty Area; "
                "the AreaWidget is responsible for the empty placeholder."
            )

        spec = self._resolve_spec(area)
        return self._materialize(spec, editors, area, content_widgets)

    # ----- Spec resolution -------------------------------------------

    def _resolve_spec(self, area: Area) -> AreaLayoutSpec:
        """Resolve the Area's Editor composition into an AreaLayoutSpec.

        Current behavior (Sprint G):

        - One Editor → SINGLE.
        - Multiple Editors → SPLIT (horizontal QSplitter).

        Sprint H will change the multiple-Editor case to STACK
        (EditorStack) once the Editor Layout Tree (ADR-0013 §2.2) is
        materialized. This method is the single point that needs to
        change.
        """
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

    # ----- Materialization -------------------------------------------

    def _materialize(
        self,
        spec: AreaLayoutSpec,
        editors: tuple[Editor, ...],
        area: Area,
        content_widgets: dict[str, QWidget],
    ) -> QWidget:
        """Materialize the resolved spec into a widget.

        The ``editors`` tuple is passed explicitly (rather than looked
        up again from ``area``) so that the spec's ``editor_ids`` and
        the Editor instances stay in lockstep. If the two ever
        disagree, that is a bug in ``_resolve_spec`` and we want it
        to surface as a KeyError, not as a silently wrong layout.
        """
        by_id = {e.editor_id: e for e in editors}

        # Validate that the spec references exactly the Editors of the
        # Area. This guards against future changes in _resolve_spec
        # that forget to update the editor_ids.
        if set(spec.editor_ids) != set(by_id):
            raise ValueError(
                "AreaLayoutSpec.editor_ids does not match the Area's "
                f"Editors: spec={sorted(spec.editor_ids)!r}, "
                f"area={sorted(by_id)!r}"
            )

        if spec.type is AreaLayoutType.SINGLE:
            return self._build_editor_container(by_id[spec.editor_ids[0]], area, content_widgets)

        if spec.type is AreaLayoutType.SPLIT:
            return self._render_split(spec, by_id, area, content_widgets)

        if spec.type is AreaLayoutType.STACK:
            raise NotImplementedError(
                "AreaLayoutType.STACK is reserved for Sprint H "
                "(EditorStack). It is not yet materialized."
            )

        # Defensive: AreaLayoutSpec validates its own type in
        # __post_init__, so this branch is unreachable for well-formed
        # specs. Keeping it makes the error explicit if a future
        # AreaLayoutType is added without updating this method.
        raise ValueError(f"unknown AreaLayoutType: {spec.type!r}")

    def _render_split(
        self,
        spec: AreaLayoutSpec,
        by_id: dict[str, Editor],
        area: Area,
        content_widgets: dict[str, QWidget],
    ) -> QSplitter:
        """Render a SPLIT spec: one container per Editor in a QSplitter.

        This is the current behavior for multiple Editors. Sprint H
        will replace it with ``_render_stack`` and flip
        ``_resolve_spec`` to return STACK.
        """
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setObjectName(f"area_widget.{area.area_id}.splitter")
        splitter.setChildrenCollapsible(False)
        for editor_id in spec.editor_ids:
            splitter.addWidget(
                self._build_editor_container(by_id[editor_id], area, content_widgets)
            )
        return splitter

    # ----- Single-Editor container -----------------------------------

    def _build_editor_container(
        self,
        editor: Editor,
        area: Area,
        content_widgets: dict[str, QWidget],
    ) -> QWidget:
        """Build the container widget for a single Editor.

        The container has a QVBoxLayout that hosts the Editor's
        ``content_widget``. Both the container and the content are given
        ``QSizePolicy.Expanding`` / ``Ignored`` and ``setMinimumSize(0, 0)``
        so the parent QSplitter respects the percentage-based sizes
        computed by the Workspace, even when the placeholder or the
        TomographyEditor has a large ``sizeHint``.
        """
        container = QWidget()
        container.setObjectName(f"area_widget.{area.area_id}.editor.{editor.editor_id}")
        container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        container.setMinimumSize(0, 0)  # Allow the container to shrink to 0.

        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        content = editor.content_widget()
        # Force the content to ignore its sizeHint so it does not
        # expand the parent QSplitter beyond the percentage-based sizes.
        content.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        content.setMinimumSize(0, 0)  # Allow the content to shrink to 0.

        content.setParent(container)
        layout.addWidget(content)
        content_widgets[editor.editor_id] = content
        return container
