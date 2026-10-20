"""FlowList — the "Fluxos clínicos" section of the Home Page.

Displays the available Flow definitions (Bloco 9). Until the Flow
Catalog exists, the list is empty and shows a placeholder.

The list supports single selection. Selecting a flow emits
`flow_selected(flow_id)`. Deselecting (or no selection) emits
`flow_selected(None)`. The HomePage uses this to enable the StartButton.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class FlowList(QWidget):
    """Clinical flow listing with selection and a manage button."""

    flow_selected = Signal(object)  # str | None
    manage_flows_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("home_page.flow_list")
        self._selected_flow_id: str | None = None
        self._flow_buttons: dict[str, QPushButton] = {}

        title = QLabel("Fluxos clínicos")
        title.setObjectName("home_page.flow_list.title")
        title_font = title.font()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title.setFont(title_font)

        self._manage_button = QPushButton("Gerir Fluxos")
        self._manage_button.setObjectName("home_page.flow_list.manage")
        self._manage_button.clicked.connect(self.manage_flows_requested)

        header = QVBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header_row = QVBoxLayout()
        del header_row  # not used; simple vertical header below

        top = QWidget()
        top_layout = QVBoxLayout(top)
        top_layout.setContentsMargins(8, 8, 8, 0)
        row = QWidget()

        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.addWidget(title)
        row_layout.addStretch(1)
        row_layout.addWidget(self._manage_button)
        top_layout.addWidget(row)

        # Scroll area with placeholder.
        self._content = QWidget()
        self._content.setObjectName("home_page.flow_list.content")
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(8, 8, 8, 8)
        self._content_layout.setSpacing(6)

        self._placeholder = QLabel("Nenhum fluxo disponível")
        self._placeholder.setObjectName("home_page.flow_list.placeholder")
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._content_layout.addWidget(self._placeholder)
        self._content_layout.addStretch(1)

        scroll = QScrollArea()
        scroll.setObjectName("home_page.flow_list.scroll")
        scroll.setWidgetResizable(True)
        scroll.setWidget(self._content)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(top)
        root.addWidget(scroll, stretch=1)

    # ----- Public API -----------------------------------------------

    def set_flows(self, flows: list[tuple[str, str]]) -> None:
        """Populate the list with (flow_id, display_name) pairs.

        Clears any existing selection. Used by the Bloco 9 integration;
        today it is called only from tests to simulate content.
        """
        # Remove old flow buttons.
        for button in self._flow_buttons.values():
            button.setParent(None)
            button.deleteLater()
        self._flow_buttons.clear()

        # Remove placeholder if flows exist.
        if flows:
            self._placeholder.setParent(None)
            self._placeholder.deleteLater()

        for flow_id, display_name in flows:
            button = QPushButton(display_name)
            button.setObjectName(f"home_page.flow_list.flow.{flow_id}")
            button.setCheckable(True)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(
                lambda _=False, fid=flow_id: self._on_flow_clicked(fid)
            )
            self._content_layout.insertWidget(
                self._content_layout.count() - 1, button
            )
            self._flow_buttons[flow_id] = button

        self._selected_flow_id = None
        self.flow_selected.emit(None)

    def selected_flow_id(self) -> str | None:
        """Return the id of the selected flow, or None."""
        return self._selected_flow_id

    def flow_count(self) -> int:
        """Number of flow buttons currently displayed."""
        return len(self._flow_buttons)

    # ----- Internals ------------------------------------------------

    def _on_flow_clicked(self, flow_id: str) -> None:
        # Toggle behavior: clicking the selected flow deselects it.
        if self._selected_flow_id == flow_id:
            self._selected_flow_id = None
            for button in self._flow_buttons.values():
                button.setChecked(False)
        else:
            self._selected_flow_id = flow_id
            for fid, button in self._flow_buttons.items():
                button.setChecked(fid == flow_id)
        self.flow_selected.emit(self._selected_flow_id)
