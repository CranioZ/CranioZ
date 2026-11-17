"""EditorStack — a compact switcher for multiple Editors in one Area Leaf.

Per ADR-0013 §2.5, the EditorStack is NOT a QTabWidget. It is a
QStackedWidget with a dedicated EditorStackSwitcher widget (a row or
column of buttons) and the Editor's content placed into the stacked
page.

Lazy materialization: only the active Editor's content_widget() is
materialized eagerly. When an Editor becomes active for the first time,
its content_widget() replaces the placeholder page.

Lifecycle: activate()/deactivate() fire on tab switch;
dispose() fires once per Editor when the stack is disposed.
"""

from __future__ import annotations

import logging

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from cranioz.editors.core.editor.base_editor import Editor
from cranioz.ui.icons.provider import IconProvider
from cranioz.ui.workspace.areas.editor_layout_spec import EditorStackOrientation

_logger = logging.getLogger(__name__)


class EditorStackSwitcher(QWidget):
    """Compact switcher for the EditorStack.

    One QPushButton per Editor, laid out in a single row (BOTTOM/TOP)
    or column (LEFT/RIGHT). No QTabBar, no QTabWidget.
    """

    editor_selected = Signal(str)

    def __init__(
        self,
        orientation: EditorStackOrientation,
        icon_provider: IconProvider | None,
        *,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._orientation = orientation
        self._icon_provider = icon_provider
        self._buttons: dict[str, QPushButton] = {}

        if orientation in (EditorStackOrientation.TOP, EditorStackOrientation.BOTTOM):
            layout: QHBoxLayout | QVBoxLayout = QHBoxLayout(self)
            self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        else:
            layout = QVBoxLayout(self)
            self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        self._layout = layout

        # Aplica o estilo escuro e moderno diretamente nos botões
        self.setStyleSheet("""
            QWidget {
                background-color: #252526;
            }
            QPushButton {
                background-color: transparent;
                color: #A8A8A8;
                border: 1px solid transparent;
                border-radius: 4px;
                padding: 4px 12px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #3A3A3C;
                color: #E8E8E8;
            }
            QPushButton:checked {
                background-color: #1F5FCC;
                color: #FFFFFF;
                border: 1px solid #4A90D9;
            }
        """)

    def add_editor(self, editor: Editor) -> None:
        btn = QPushButton(self)
        btn.setCheckable(True)
        btn.setAutoExclusive(True)
        btn.setText(editor.title)
        btn.setToolTip(editor.title)
        btn.setAccessibleName(editor.title)

        if self._icon_provider is not None:
            icon_name = getattr(editor, "icon_name", None)
            if callable(icon_name):
                btn.setIcon(self._icon_provider.icon(icon_name()))

        btn.clicked.connect(
            lambda _checked=False, eid=editor.editor_id: self.editor_selected.emit(eid)
        )
        self._buttons[editor.editor_id] = btn
        self._layout.addWidget(btn)

    def set_active(self, editor_id: str) -> None:
        btn = self._buttons.get(editor_id)
        if btn is not None:
            btn.setChecked(True)


class EditorStack(QWidget):
    """A QStackedWidget with a compact switcher. Not a QTabWidget."""

    active_editor_changed = Signal(str)

    def __init__(
        self,
        editors: tuple[Editor, ...],
        orientation: EditorStackOrientation = EditorStackOrientation.BOTTOM,
        active_editor_id: str | None = None,
        *,
        icon_provider: IconProvider | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        if len(editors) < 2:
            raise ValueError("EditorStack requires at least two Editors.")

        self._editors: dict[str, Editor] = {e.editor_id: e for e in editors}
        self._orientation = orientation
        # CORREÇÃO: Inicializa como None para que _set_active não pule a
        # primeira ativação devido à verificação de "já é o ativo".
        self._active_editor_id: str | None = None
        self._materialized: set[str] = set()
        self._disposed: set[str] = set()

        self._stack = QStackedWidget(self)
        self._switcher = EditorStackSwitcher(
            orientation,
            icon_provider,
            parent=self,
        )

        self._build(editors)
        target_id = active_editor_id or editors[0].editor_id
        self._set_active(target_id, emit_signal=False)

    def _build(self, editors: tuple[Editor, ...]) -> None:
        for editor in editors:
            self._switcher.add_editor(editor)
            placeholder = QWidget(self)
            placeholder.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
            self._stack.addWidget(placeholder)

        self._switcher.editor_selected.connect(self._set_active)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        if self._orientation in (EditorStackOrientation.TOP, EditorStackOrientation.BOTTOM):
            if self._orientation is EditorStackOrientation.TOP:
                outer.addWidget(self._switcher)
                outer.addWidget(self._stack)
            else:
                outer.addWidget(self._stack)
                outer.addWidget(self._switcher)
        else:
            row = QHBoxLayout()
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(0)
            if self._orientation is EditorStackOrientation.LEFT:
                row.addWidget(self._switcher)
                row.addWidget(self._stack)
            else:
                row.addWidget(self._stack)
                row.addWidget(self._switcher)
            outer.addLayout(row)

    def _set_active(self, editor_id: str, emit_signal: bool = True) -> None:
        if editor_id not in self._editors:
            _logger.warning(
                "EditorStack: ignoring unknown editor_id %r (known: %r)",
                editor_id,
                sorted(self._editors),
            )
            return

        # If the requested editor is already the active one, do nothing.
        if self._active_editor_id == editor_id:
            return

        # Deactivate the previous editor (if any).
        if self._active_editor_id is not None and self._active_editor_id in self._editors:
            self._editors[self._active_editor_id].deactivate()

        self._active_editor_id = editor_id
        active_editor = self._editors[editor_id]

        index = list(self._editors).index(editor_id)
        page = self._stack.widget(index)

        if editor_id not in self._materialized:
            content = active_editor.content_widget()
            if page is not None:
                self._stack.removeWidget(page)
                page.deleteLater()
            self._stack.insertWidget(index, content)
            self._materialized.add(editor_id)

        self._stack.setCurrentIndex(index)
        self._switcher.set_active(editor_id)
        active_editor.activate()

        if emit_signal:
            self.active_editor_changed.emit(editor_id)

    def dispose(self) -> None:
        """Dispose every Editor exactly once, in insertion order."""
        for editor_id, editor in self._editors.items():
            if editor_id in self._disposed:
                continue
            try:
                editor.deactivate()
                editor.dispose()
            except Exception:
                _logger.exception("EditorStack: dispose() failed for %r", editor_id)
            finally:
                self._disposed.add(editor_id)

        # CORREÇÃO: mypy acusa que 'page' pode ser None.
        # Verificamos explicitamente antes de chamar removeWidget.
        while self._stack.count():
            page = self._stack.widget(0)
            if page is not None:
                self._stack.removeWidget(page)
                page.deleteLater()

        self._editors.clear()
