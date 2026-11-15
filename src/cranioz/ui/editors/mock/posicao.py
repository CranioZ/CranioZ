"""MockPosicaoEditor — mimics the Posição panel.

Renders a fixed-size panel with sliders labeled X/Y/Z for
Localização, Rotação, Escala, plus a "Pintar Máscaras" section.
The panel is intentionally rendered with real QWidgets (sliders,
labels, sections) so its sizeHint is realistic (~280px wide).

Used as the Left Area in debug_layout.py. Not a production Editor.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QLabel,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from cranioz.ui.editors.base_editor import Editor
from cranioz.ui.editors.editor_context import EditorContext


class MockPosicaoEditor(Editor):
    """A minimal Editor that mimics the Posição panel."""

    def __init__(
        self,
        editor_id: str = "editor.mock.posicao",
        title: str = "Posição",
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
        root.setObjectName("mock_posicao")
        root.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        layout.addWidget(self._section("Localização", ("X", "Y", "Z")))
        layout.addWidget(self._section("Rotação", ("X", "Y", "Z")))
        layout.addWidget(self._section("Escala", ("X", "Y", "Z")))

        ferramenta = QGroupBox("Pintar Máscaras")
        ferramenta_layout = QVBoxLayout(ferramenta)
        ferramenta_layout.addWidget(QLabel("Diâmetro: 10 px"))
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setMinimum(1)
        slider.setMaximum(100)
        slider.setValue(10)
        ferramenta_layout.addWidget(slider)
        ferramenta_layout.addWidget(QLabel("Limiar: Min -100  Max 1500"))
        layout.addWidget(ferramenta)

        layout.addStretch(1)

        self._content = root
        return root

    def _section(self, title: str, axes: tuple[str, ...]) -> QGroupBox:
        box = QGroupBox(title)
        form = QFormLayout(box)
        form.setContentsMargins(8, 8, 8, 8)
        form.setSpacing(4)
        for axis in axes:
            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setMinimum(-100)
            slider.setMaximum(100)
            slider.setValue(0)
            form.addRow(QLabel(f"{axis}  0 mm"), slider)
        return box

    def dispose(self) -> None:
        if self._content is not None:
            self._content.setParent(None)
            self._content.deleteLater()
            self._content = None
