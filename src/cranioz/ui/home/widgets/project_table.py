"""ProjectTable — the "Lista de projetos" section of the Home Page.

Displays the ProjectSummaries from the ProjectCatalog. Emits signals
for user actions: selection, new project, manage projects. It does not
create, delete, or open projects; the HomePage re-emits the signals
and the MainWindow (piece 7.6b) executes the operations.

The "Gerir projetos" button replaces the previous "Remover projeto".
Rationale: the HomePage should not expose destructive operations
directly. Project deletion belongs in a management page (settings /
project management, piece 7.6d) where the user has context: archive,
export, import, delete. The HomePage opens that page; it does not
delete a project with one click.

Widget choice: QTableWidget, not QTableView + model. A surgeon
typically has dozens of projects, not thousands. QTableWidget handles
that with zero ceremony. Migration to QTableView + ProjectTableModel
is a separate decision, to be taken only if the list needs
server-side sorting, dynamic filtering, or virtualization.

Selection semantics:

``project_selected`` is emitted with the ``ProjectId`` of the
selected row, **or with ``None`` when the selection is cleared**.
HomePage relies on the ``None`` emission to clear its own
``_selected_project_id`` and to disable the StartButton; without
it, the StartButton would stay enabled after the row disappears
(e.g. via search filtering). ``refresh()`` preserves the selection
when the same project is still present in the results, and emits
``None`` only when the selected project is gone.
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
    """Project listing with search, create/manage buttons, and selection."""

    new_project_requested = Signal()
    manage_projects_requested = Signal()
    project_selected = Signal(object)  # ProjectId | None

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

        self._manage_button = QPushButton("Gerir projetos")
        self._manage_button.setObjectName("home_page.project_table.manage")
        self._manage_button.clicked.connect(self.manage_projects_requested)

        self._search_edit = QLineEdit()
        self._search_edit.setObjectName("home_page.project_table.search")
        self._search_edit.setPlaceholderText("Buscar por nome do projeto ou do paciente")
        self._search_edit.setMaximumWidth(280)
        self._search_edit.textChanged.connect(self.refresh)

        header = QHBoxLayout()
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(self._new_button)
        header.addWidget(self._manage_button)
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
        """Reload the table from the catalog, honoring the current search.

        Preserves the current selection when the selected project is
        still in the results. Emits ``project_selected(None)`` when
        the selected project disappears (e.g. filtered out by search),
        so HomePage can clear its state and disable the StartButton.
        """
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
        """Rebuild the table from ``summaries``.

        Preserves the previous selection when the same project id is
        still present in the new summaries. Emits ``project_selected(None)``
        only when the previously selected project is gone, to keep
        HomePage in sync without spuriously disabling the StartButton
        on every refresh.
        """
        previous_selection = self.selected_project_id()

        # Block table signals during the rebuild so that intermediate
        # clearSelection() / setRowCount() do not fire
        # itemSelectionChanged for states the user never actually chose.
        self._table.blockSignals(True)
        try:
            self._table.clearSelection()
            self._table.setRowCount(len(summaries))
            for row, summary in enumerate(summaries):
                self._set_cell(row, 0, summary.project_name)
                self._set_cell(row, 1, summary.project_id.value)
                self._set_cell(row, 2, _format_sex(summary))
                self._set_cell(row, 3, _format_age(summary))
                self._set_cell(row, 4, _format_datetime(summary.created_at))
                self._set_cell(row, 5, _format_datetime(summary.updated_at))
        finally:
            self._table.blockSignals(False)

        # Restore the previous selection when possible. selectRow()
        # triggers itemSelectionChanged, which emits the project id
        # via _on_selection_changed. No manual emission needed here.
        if previous_selection is not None:
            for row, summary in enumerate(summaries):
                if summary.project_id == previous_selection:
                    self._table.selectRow(row)
                    return

        # The previously selected project is no longer in the table.
        # Tell HomePage that the selection is now empty.
        if previous_selection is not None:
            self.project_selected.emit(None)

    def _set_cell(self, row: int, column: int, text: str) -> None:
        item = QTableWidgetItem(text)
        item.setTextAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        self._table.setItem(row, column, item)

    def _on_selection_changed(self) -> None:
        """Emit the current selection (ProjectId or None) to HomePage.

        HomePage relies on receiving ``None`` when the selection is
        cleared, so that it can clear its own ``_selected_project_id``
        and disable the StartButton. Emitting only non-None values
        would leave a stale selection behind (the previous bug).
        """
        self.project_selected.emit(self.selected_project_id())


# ----- Formatting helpers --------------------------------------------


def _format_sex(summary: ProjectSummary) -> str:
    # The ProjectSummary does not carry sex; the project metadata only
    # has patient_display_name. Column is reserved, filled later when
    # the Patient module provides sex. An em-dash placeholder is
    # honest: it says "not available" rather than "missing".
    del summary
    return "—"


def _format_age(summary: ProjectSummary) -> str:
    # Same rationale as _format_sex.
    del summary
    return "—"


def _format_datetime(value: datetime) -> str:
    return value.strftime("%d/%m/%Y")