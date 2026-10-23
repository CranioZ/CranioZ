"""FlowList — the "Fluxos clínicos" section of the Home Page.

Renders each available flow as a horizontal ``FlowRow`` (name + steps
connected by arrows). Flows are loaded from a ``FlowCatalog`` by the
``MainWindow``; the ``FlowList`` itself does not know about the catalog.

The list has single-selection semantics: at most one ``FlowRow`` is
checked. Selecting a row emits ``flow_selected(flow_id)``; deselecting
(clicking the checked row) emits ``flow_selected(None)``. This matches
the ``StartButton``'s contract: it enables only when both a project and
a flow are selected.

The list does not execute flows. It only presents them and emits
selection. Execution belongs to the ``WorkflowEngine`` (Phase 5).
"""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from cranioz.application.flows.definition import FlowDefinition
from cranioz.ui.home.widgets.flow_row import FlowRow


class FlowList(QWidget):
    """Clinical flow listing with row selection and a manage button."""

    flow_selected = Signal(object)  # str | None
    manage_flows_requested = Signal()

    def __init__(
        self,
        *,
        translate: Callable[[str], str] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("home_page.flow_list")
        self._translate: Callable[[str], str] = translate or (lambda key: key)
        self._selected_flow_id: str | None = None
        self._rows: dict[str, FlowRow] = {}

        title = QLabel("Fluxos clínicos")
        title.setObjectName("home_page.flow_list.title")
        title_font = title.font()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title.setFont(title_font)

        self._manage_button = QPushButton("Gerir Fluxos")
        self._manage_button.setObjectName("home_page.flow_list.manage")
        self._manage_button.clicked.connect(self.manage_flows_requested)

        top = QWidget()
        top_layout = QHBoxLayout(top)
        top_layout.setContentsMargins(8, 8, 8, 0)
        top_layout.addWidget(title)
        top_layout.addStretch(1)
        top_layout.addWidget(self._manage_button)

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

    def set_flows(self, flows: tuple[FlowDefinition, ...]) -> None:
        """Replace the rendered flows with ``flows``.

        The rendered order is deterministic: flows are sorted by
        ``flow_id``, independent of the order in which they arrive
        (e.g., filesystem ``iterdir()``). When the flow schema gains an
        ``order`` field, this sort is the single place to change.

        Clears any existing selection and emits ``flow_selected(None)``
        so the caller's state is consistent with the (empty) selection.
        """
        for row in self._rows.values():
            row.setParent(None)
            row.deleteLater()
        self._rows.clear()

        if flows:
            self._placeholder.setParent(None)
            self._placeholder.deleteLater()

        for flow in sorted(flows, key=lambda f: f.flow_id):
            row = FlowRow(flow, translate=self._translate, parent=self._content)
            row.selected.connect(self._on_row_selected)
            self._content_layout.insertWidget(self._content_layout.count() - 1, row)
            self._rows[flow.flow_id] = row

        self._selected_flow_id = None
        self.flow_selected.emit(None)

    def selected_flow_id(self) -> str | None:
        return self._selected_flow_id

    def flow_count(self) -> int:
        return len(self._rows)

    # ----- Internals ------------------------------------------------

    def _on_row_selected(self, flow_id: object) -> None:
        if flow_id is None:
            self._selected_flow_id = None
            for row in self._rows.values():
                row.set_checked(False)
            self.flow_selected.emit(None)
            return

        if not isinstance(flow_id, str):
            return

        self._selected_flow_id = flow_id
        for fid, row in self._rows.items():
            row.set_checked(fid == flow_id)
        self.flow_selected.emit(flow_id)
