"""MockObjetosEditor — mimics the Objetos panel.

Renders a panel with:
- A tab bar at the top ("Objetos" | "Cefalometria").
- A tree-like list of object groups and items with color swatches.
- Three filter chips ("Todos" | "Anatomia" | "Superfícies").
- A text filter line.

Used as the Right Area in debug_layout.py. Not a production Editor.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from cranioz.ui.editors.base_editor import Editor
from cranioz.ui.editors.editor_context import EditorContext

_SWATCH_COLORS = (
    "#3B82F6",  # blue
    "#FBBF24",  # yellow
    "#10B981",  # green
    "#EF4444",  # red
    "#A855F7",  # purple
    "#6B7280",  # gray
    "#06B6D4",  # cyan
    "#EC4899",  # pink
)


class MockObjetosEditor(Editor):
    """A minimal Editor that mimics the Objetos panel."""

    def __init__(
        self,
        editor_id: str = "editor.mock.objetos",
        title: str = "Objetos",
    ) -> None:
        super().__init__(editor_id=editor_id, title=title)
        self._content: QWidget | None = None
        self._context: EditorContext | None = None

    def initialize(self, context: EditorContext) -> None:
        self._context = context

    def content_widget(self) -> QWidget:
        if self._content is not None:
            return self._content

        root = QWidget()
        root.setObjectName("mock_objetos")
        root.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Tab bar
        tab_bar = QWidget()
        tab_bar_layout = QHBoxLayout(tab_bar)
        tab_bar_layout.setContentsMargins(4, 4, 4, 4)
        tab_bar_layout.addWidget(QPushButton("Objetos"))
        tab_bar_layout.addWidget(QPushButton("Cefalometria"))
        tab_bar_layout.addStretch(1)
        tab_bar_layout.addWidget(QPushButton("+"))
        layout.addWidget(tab_bar)

        # Tree
        tree = QTreeWidget()
        tree.setHeaderHidden(True)
        for group_index in range(4):
            group = QTreeWidgetItem(tree, [f"Grupo de objeto {group_index + 1}"])
            for item_index in range(3):
                color = _SWATCH_COLORS[(group_index * 3 + item_index) % len(_SWATCH_COLORS)]
                item = QTreeWidgetItem(group, [f"Objeto {item_index + 1}"])
                item.setForeground(0, Qt.GlobalColor.white)
                # Simulate a color swatch via icon-less text (QTreeWidget
                # does not support colored blocks natively without
                # QIcon; we just note the color in the tooltip).
                item.setToolTip(0, color)
            group.setExpanded(True)
        layout.addWidget(tree, stretch=1)

        # Filter chips
        chips = QWidget()
        chips_layout = QHBoxLayout(chips)
        chips_layout.setContentsMargins(4, 4, 4, 4)
        for label in ("Todos", "Anatomia", "Superfícies"):
            button = QPushButton(label)
            button.setCheckable(True)
            chips_layout.addWidget(button)
        chips_layout.addStretch(1)
        layout.addWidget(chips)

        # Text filter
        filter_edit = QLineEdit()
        filter_edit.setPlaceholderText("Filtrar etiquetas")
        layout.addWidget(filter_edit)

        self._content = root
        return root

    def dispose(self) -> None:
        if self._content is not None:
            self._content.setParent(None)
            self._content.deleteLater()
            self._content = None