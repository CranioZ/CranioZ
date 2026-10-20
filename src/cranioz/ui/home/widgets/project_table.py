"""ProjectTable — the "Lista de projetos" section of the Home Page.

Displays the ProjectSummaries from the ProjectCatalog. Emits signals
for user actions: selection, new project, remove project. It does not
create, delete, or open projects; the HomePage re-emits the signals
and the MainWindow (piece 7.6b) executes the operations.

Widget choice: QTableWidget, not QTableView + model. A surgeon
typically has dozens of projects, not thousands. QTableWidget handles
that with zero ceremony. Migration to QTableView + ProjectTableModel
is a separate decision, to be taken only if the list needs
server-side sorting, dynamic filtering, or virtualization.
"""

from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from cranioz.application.project.project_catalog import ProjectCatalog
from cranioz.domain.project.project_id import ProjectId
from cranioz.domain.project.project_summary import ProjectSummary

_COLUMNS = ("Nome", "ID", "Sexo", "Idade", "Criação do projeto", "Última modificação")


class ProjectTable(QWidget):
    """Project listing with search, create/remove buttons, and selection."""

    new_project_requested = Signal()
    remove_project_requested = Signal(object)  # ProjectId
    project_selected = Signal(object)  # ProjectId

    def __init__(
        self,
        catalog: ProjectCatalog,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._catalog = catalog
        self.setObjectName("home_page.project_table")

        # ----- Header -----
        title = QLabel("Lista de projetos")
        title.setObjectName("home_page.project_table.title")
        title_font = title.font()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title.setFont(title_font)

        self._new_button = QPushButton("Novo projeto")
        self._new_button.setObjectName("home_page.project_table.new")
        self._new_button.clicked.connect(self.new_project_requested)

        self._remove_button = QPushButton("Remover projeto")
        self._remove_button.setObjectName("home_page.project_table.remove")
        self._remove_button.setEnabled(False)
        self._remove_button.clicked.connect(self._on_remove_clicked)

        self._search_edit = QLineEdit()
        self._search_edit.setObjectName("home_page.project_table.search")
        self._search_edit.setPlaceholderText("Buscar por nome do projeto ou do paciente")
        self._search_edit.setMaximumWidth(280)
        self._search_edit.textChanged.connect(self.refresh)

        header = QHBoxLayout()
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(self._new_button)
        header.addWidget(self._remove_button)
        header.addWidget(self._search_edit)

        # ----- Table -----
        self._table = QTableWidget(0, len(_COLUMNS))
        self._table.setObjectName("home_page.project_table.table")
        self._table.setHorizontalHeaderLabels(_COLUMNS)
        self._table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self._table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.itemSelectionChanged.connect(self._on_selection_changed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)
        layout.addLayout(header)
        layout.addWidget(self._table, stretch=1)

        self.refresh()

    # ----- Public API -----------------------------------------------

    def refresh(self) -> None:
        """Reload the table from the catalog, honoring the current search."""
        query = self._search_edit.text()
        if query.strip():
            summaries = self._catalog.search_projects(query)
        else:
            summaries = self._catalog.list_projects()
        self._populate(summaries)

    def selected_project_id(self) -> ProjectId | None:
        """Return the id of the selected row, or None."""
        selection = self._table.selectionModel()
        rows = selection.selectedRows()
        if not rows:
            return None
        text = self._id_text_at_row(rows[0].row())
        return ProjectId(text) if text else None

    def row_count(self) -> int:
        """Number of rows currently displayed."""
        return self._table.rowCount()

    # ----- Internals ------------------------------------------------

    def _id_text_at_row(self, row: int) -> str:
        item = self._table.item(row, 1)
        if item is None:
            return ""
        return item.text()

    def _populate(self, summaries: tuple[ProjectSummary, ...]) -> None:
        # Clear selection first, to avoid signals during repopulation.
        self._table.clearSelection()
        self._table.setRowCount(len(summaries))
        for row, summary in enumerate(summaries):
            self._set_cell(row, 0, summary.project_name)
            self._set_cell(row, 1, summary.project_id.value)
            self._set_cell(row, 2, _format_sex(summary))
            self._set_cell(row, 3, _format_age(summary))
            self._set_cell(row, 4, _format_datetime(summary.created_at))
            self._set_cell(row, 5, _format_datetime(summary.updated_at))
        self._remove_button.setEnabled(False)

    def _set_cell(self, row: int, column: int, text: str) -> None:
        item = QTableWidgetItem(text)
        item.setTextAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        self._table.setItem(row, column, item)

    def _on_selection_changed(self) -> None:
        project_id = self.selected_project_id()
        self._remove_button.setEnabled(project_id is not None)
        if project_id is not None:
            self.project_selected.emit(project_id)

    def _on_remove_clicked(self) -> None:
        project_id = self.selected_project_id()
        if project_id is not None:
            self.remove_project_requested.emit(project_id)


# ----- Formatting helpers --------------------------------------------


def _format_sex(summary: ProjectSummary) -> str:
    # The ProjectSummary does not carry sex; the project metadata only
    # has patient_display_name. Column is reserved, filled later when
    # the Patient module provides sex. Empty placeholder is honest.
    del summary
    return ""


def _format_age(summary: ProjectSummary) -> str:
    # Same rationale as _format_sex.
    del summary
    return ""


def _format_datetime(value: datetime) -> str:
    return value.strftime("%d/%m/%Y")
