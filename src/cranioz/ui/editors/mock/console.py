"""MockConsoleEditor — mimics the Console panel.

Renders a horizontal panel with:
- A tab bar ("Console" | "History" | "Animation" | "AI Assistant" | "Nodes").
- A monospaced text area with fake log lines.

Used as the Bottom Area in debug_layout.py. Not a production Editor.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from cranioz.editors.core.editor.base_editor import Editor
from cranioz.editors.core.editor.editor_context import EditorContext

_LOG_LINES = (
    "14:15 - DICOM / Tomografia (CASE_001) carregada.",
    "14:18 - Segmentação 3D concluída: Skull, Maxilla, Mandible, Teeth.",
    "14:21 - Visibilidade da cena ajustada: isolamento do complexo maxilomandibular.",
    "14:24 - Ferramenta ativada: Osteotomia Le Fort I.",
    "14:25 - Plano de corte Le Fort I definido e aplicado.",
    '14:26 - Comando IA executado: "Avance a maxila 4.0 mm".',
    "14:27 - Ferramenta ativada: Osteotomia BSSO (Mandible).",
    '14:30 - Comando IA executado: "Avance a mandíbula 6.0 mm com preservação condilar".',
    "14:32 - Operação booleana: União de segmentos osteotomizados.",
    "14:35 - Verificação de oclusão e métricas de distância realizadas.",
)


class MockConsoleEditor(Editor):
    """A minimal Editor that mimics the Console panel."""

    def __init__(
        self,
        editor_id: str = "editor.mock.console",
        title: str = "Console",
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
        root.setObjectName("mock_console")
        root.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Tab bar
        tab_bar = QWidget()
        tab_bar_layout = QHBoxLayout(tab_bar)
        tab_bar_layout.setContentsMargins(4, 4, 4, 4)
        for label in ("Console", "History", "Animation", "AI Assistant", "Nodes"):
            tab_bar_layout.addWidget(QPushButton(label))
        tab_bar_layout.addStretch(1)
        layout.addWidget(tab_bar)

        # Log area
        log = QPlainTextEdit()
        log.setReadOnly(True)
        log.setPlainText("\n".join(_LOG_LINES))
        log.setStyleSheet("font-family: Consolas, monospace;")
        layout.addWidget(log, stretch=1)

        self._content = root
        return root

    def dispose(self) -> None:
        if self._content is not None:
            self._content.setParent(None)
            self._content.deleteLater()
            self._content = None
