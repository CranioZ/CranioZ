"""AreaLayoutRenderer.

Separates inter-Area layout (LayoutRenderer) from intra-Area layout
(AreaLayoutRenderer).

Per ADR-0013 (revised), the AreaLayoutRenderer organizes *Editors*
inside an Area. It does **not** materialize Toolbars: Toolbars are
declared by Editors (editor-level) and by Views (view-level), and
materialized by the respective renderers (EditorLayoutRenderer /
ViewLayoutRenderer). See ADR-0013 §2.6, §2.7.

The AreaLayoutRenderer's responsibility is therefore limited to:

- For a single Editor: build the container widget for that Editor
  and its content (delegating to the Editor's own content_widget()).
- For multiple Editors: arrange the Editor containers in a QSplitter
  (the Editor Layout Tree, ADR-0013 §2.2).

See ADR-0013 §2.2, §2.7.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QSplitter, QWidget

from cranioz.ui.editors.base_editor import Editor
from cranioz.ui.workspace.areas.area import Area


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
            ValueError: if the Area is empty.
        """
        editors = area.editors()
        if not editors:
            raise ValueError(
                "AreaLayoutRenderer.render() requires a non-empty Area; "
                "the AreaWidget is responsible for the empty placeholder."
            )

        if len(editors) == 1:
            return self._build_editor_container(editors[0], area, content_widgets)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setObjectName(f"area_widget.{area.area_id}.splitter")
        splitter.setChildrenCollapsible(False)
        for editor in editors:
            splitter.addWidget(self._build_editor_container(editor, area, content_widgets))
        return splitter

    def _build_editor_container(
        self,
        editor: Editor,
        area: Area,
        content_widgets: dict[str, QWidget],
    ) -> QWidget:
        """Build the container widget for a single Editor.

        The Editor's content_widget() is already self-contained
        (e.g., TomographyEditor returns a widget with its View
        Layout Tree and View-level Toolbars). The container only
        namespaces it so that tests and the AreaWidget can identify
        it.
        """
        container = QWidget()
        container.setObjectName(f"area_widget.{area.area_id}.editor.{editor.editor_id}")

        content = editor.content_widget()
        content.setParent(container)
        content_widgets[editor.editor_id] = content

        return container
