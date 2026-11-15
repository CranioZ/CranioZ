"""MockMPREditor — a non-VTK mock of the TomographyEditor's 2x2 grid.

Renders four colored viewports (Axial, Coronal, Sagittal, 3D) to
diagnose layout issues in the Workspace without involving VTK,
OpenGL, or real medical imaging.

Not a production Editor. Used by scripts/debug/ui/workspace/debug_layout.py
and by integration tests that need a 2x2 grid without VTK.

The colors are debug-only and intentionally hardcoded. They are not
part of the theme system. The file is listed in
tests/architecture/test_no_hardcoded_appearance.py::_KNOWN_DEBT_FILES
for this reason.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from cranioz.ui.editors.base_editor import Editor
from cranioz.ui.editors.editor_context import EditorContext

#: Debug-only colors, one per viewport. Not part of the theme; not
#: used in production. Changing these does not affect the app.
_VIEWPORT_COLORS: dict[str, str] = {
    "Axial": "#cc0000",
    "Coronal": "#009933",
    "Sagittal": "#e6b800",
    "3D": "#708090",
}

_VIEWPORT_TITLES: tuple[str, ...] = ("Axial", "Coronal", "Sagittal", "3D")


class _ViewportPanel(QFrame):
    """A colored panel representing one viewport.

    Debug-only. Uses an inline stylesheet (not the theme) and is
    intentionally small: it only displays a centered title.
    """

    def __init__(
        self,
        title: str,
        bg_color: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName(f"mock_viewport.{title.lower()}")
        self.setFrameShape(QFrame.Shape.Box)
        self.setLineWidth(1)
        # Debug-only inline style (not part of the theme).
        self.setStyleSheet(
            f"QFrame#mock_viewport\\_{title.lower()} {{"
            f"  background-color: {bg_color};"
            f"  border: 1px solid #333333;"
            f"}}"
            f"QLabel {{"
            f"  color: #ffffff;"
            f"  font-weight: bold;"
            f"  font-size: 14px;"
            f"  background-color: rgba(0, 0, 0, 100);"
            f"  padding: 4px 8px;"
            f"  border-radius: 4px;"
            f"}}"
        )
        # Expanding so the grid distributes space among the 4 panels
        # instead of giving each one only its sizeHint.
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._label = QLabel(title, self)
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._label)


class MockMPREditor(Editor):
    """A non-VTK mock of the TomographyEditor's 2x2 grid.

    Renders a 2x2 grid of colored viewports (Axial, Coronal, Sagittal,
    3D) with a top bar (tab label) and a bottom bar (mode label).

    Used to diagnose Workspace layout issues independently of the
    TomographyEditor, which involves VTK and rendering.
    """

    def __init__(
        self,
        editor_id: str = "editor.mock.mpr",
        title: str = "Tomografia (Mock)",
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
        root.setObjectName("mock_tomography_mpr")
        root.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        main_layout = QVBoxLayout(root)
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.setSpacing(2)

        # ----- Top bar: tab label + stretch -----
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(4, 4, 4, 4)
        tab_btn = QPushButton(self.title, root)
        tab_btn.setStyleSheet(
            "QPushButton {"
            "  background-color: #e0e0e0;"
            "  color: #000000;"
            "  font-weight: bold;"
            "  padding: 4px 12px;"
            "  border-radius: 3px;"
            "}"
        )
        top_bar.addWidget(tab_btn)
        top_bar.addStretch(1)
        main_layout.addLayout(top_bar)

        # ----- 2x2 grid of viewports -----
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(2)
        panels = {
            title: _ViewportPanel(title, _VIEWPORT_COLORS[title], root)
            for title in _VIEWPORT_TITLES
        }
        grid.addWidget(panels["Axial"], 0, 0)
        grid.addWidget(panels["Coronal"], 0, 1)
        grid.addWidget(panels["Sagittal"], 1, 0)
        grid.addWidget(panels["3D"], 1, 1)
        main_layout.addLayout(grid, stretch=1)

        # ----- Bottom bar: mode label -----
        bottom_bar = QHBoxLayout()
        bottom_bar.setContentsMargins(4, 4, 4, 4)
        bottom_bar.addStretch(1)
        info = QLabel("Modo Mock Ativo - Teste de Area Central", root)
        info.setStyleSheet("color: #666666; font-size: 11px;")
        bottom_bar.addWidget(info)
        main_layout.addLayout(bottom_bar)

        self._content = root
        return root

    def dispose(self) -> None:
        if self._content is not None:
            self._content.setParent(None)
            self._content.deleteLater()
            self._content = None
        self._context = None
