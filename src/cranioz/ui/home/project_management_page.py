"""Project management page loaded by the Home Page expand action."""

from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import QSize, Qt, Signal
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

from cranioz.application.project.catalog import ProjectCatalog
from cranioz.domain.project.project_id import ProjectId
from cranioz.domain.project.project_summary import ProjectSummary
from cranioz.infrastructure.i18n import tr
from cranioz.ui.home.widgets.home_top_bar import HomeTopBar
from cranioz.ui.icons.provider import IconProvider


class ProjectManagementPage(QWidget):
    """Present projects and request bulk management operations."""

    back_requested = Signal()
    new_project_requested = Signal()
    remove_projects_requested = Signal(object)
    export_projects_requested = Signal(object)
    import_projects_requested = Signal()

    logs_requested = Signal()
    help_requested = Signal()
    settings_requested = Signal()
    minimize_requested = Signal()
    maximize_requested = Signal()
    close_requested = Signal()

    def __init__(
        self,
        catalog: ProjectCatalog,
        *,
        icon_provider: IconProvider,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._catalog = catalog
        self._icon_provider = icon_provider
        self.setObjectName("home_page.project_management")

        self._top_bar = HomeTopBar(
            icon_provider,
            show_menu=False,
            parent=self,
        )

        self._panel = QWidget(self)
        self._panel.setObjectName("home_page_project_management")
        panel_layout = QVBoxLayout(self._panel)
        panel_layout.setContentsMargins(8, 8, 8, 8)
        panel_layout.setSpacing(8)
        panel_layout.addLayout(self._build_header())
        panel_layout.addWidget(self._build_table(), stretch=1)
        panel_layout.addLayout(self._build_actions())
        panel_layout.addLayout(self._build_footer())

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._top_bar)
        root.addWidget(self._panel, stretch=1)

        self._connect_signals()
        self.refresh()

    # ----- Public API ------------------------------------------------

    def refresh(self) -> None:
        query = self._search_edit.text()
        summaries = (
            self._catalog.search_projects(query) if query.strip() else self._catalog.list_projects()
        )
        previously_selected = set(self.selected_project_ids())

        self._table.blockSignals(True)
        self._table.setSortingEnabled(False)
        try:
            self._table.setRowCount(len(summaries))
            for row, summary in enumerate(summaries):
                self._populate_row(row, summary, previously_selected)
        finally:
            self._table.setSortingEnabled(True)
            self._table.blockSignals(False)

        self._sync_actions()

    def selected_project_ids(self) -> tuple[ProjectId, ...]:
        selected: list[ProjectId] = []
        for row in range(self._table.rowCount()):
            check_item = self._table.item(row, 0)
            if check_item is None or check_item.checkState() != Qt.CheckState.Checked:
                continue
            project_id = check_item.data(Qt.ItemDataRole.UserRole)
            if isinstance(project_id, ProjectId):
                selected.append(project_id)
        return tuple(selected)

    def row_count(self) -> int:
        return self._table.rowCount()

    def top_bar(self) -> HomeTopBar:
        return self._top_bar

    # ----- Construction ----------------------------------------------

    def _build_header(self) -> QHBoxLayout:
        title = QLabel(tr("homepage.project_management.title", "Project list"))
        title.setObjectName("home_page.project_management.title")

        self._new_button = QPushButton(tr("homepage.project_management.new_project", "New project"))
        self._new_button.setObjectName("home_page.project_management.new")
        self._set_button_icon(self._new_button, "project_new")

        self._search_button = QPushButton()
        self._search_button.setObjectName("home_page.project_management.search_button")
        self._search_button.setProperty("class", "icon")
        self._search_button.setFlat(True)
        self._search_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._set_button_icon(self._search_button, "project_search")
        search_label = tr(
            "homepage.project_management.search",
            "Search by project or patient name",
        )
        self._search_button.setToolTip(search_label)
        self._search_button.setAccessibleName(search_label)

        self._search_edit = QLineEdit()
        self._search_edit.setObjectName("home_page.project_management.search")
        self._search_edit.setPlaceholderText(
            tr(
                "homepage.project_management.search_placeholder",
                "Search by project or patient name",
            )
        )
        self._search_edit.setMinimumWidth(240)
        self._search_edit.setMaximumWidth(360)
        self._search_edit.setVisible(False)

        header = QHBoxLayout()
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(self._new_button)
        header.addWidget(self._search_button)
        header.addWidget(self._search_edit)
        return header

    def _build_table(self) -> QTableWidget:
        columns = (
            "",
            tr("homepage.project_list.columns.name", "Name"),
            tr("homepage.project_list.columns.id", "ID"),
            tr("homepage.project_list.columns.sex", "Sex"),
            tr("homepage.project_list.columns.age", "Age"),
            tr("homepage.project_list.columns.created_at", "Project creation"),
            tr("homepage.project_list.columns.updated_at", "Last modification"),
        )
        self._table = QTableWidget(0, len(columns))
        self._table.setObjectName("home_page.project_management.table")
        self._table.setHorizontalHeaderLabels(columns)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.setSortingEnabled(True)
        self._table.verticalHeader().setVisible(False)

        header_view = self._table.horizontalHeader()
        header_view.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        for column in range(2, len(columns) - 1):
            header_view.setSectionResizeMode(column, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setSectionResizeMode(len(columns) - 1, QHeaderView.ResizeMode.Stretch)
        header_view.setMinimumSectionSize(72)
        return self._table

    def _build_actions(self) -> QHBoxLayout:
        self._select_button = QPushButton(
            tr("homepage.project_management.select_projects", "Select projects")
        )
        self._select_button.setObjectName("home_page.project_management.select")

        self._remove_button = QPushButton(
            tr("homepage.project_management.remove_projects", "Remove project")
        )
        self._remove_button.setObjectName("home_page.project_management.remove")
        self._remove_button.setProperty("class", "secondary")

        self._export_button = QPushButton(
            tr("homepage.project_management.export_projects", "Export project")
        )
        self._export_button.setObjectName("home_page.project_management.export")
        self._export_button.setProperty("class", "secondary")

        self._import_button = QPushButton(
            tr("homepage.project_management.import_projects", "Import project")
        )
        self._import_button.setObjectName("home_page.project_management.import")
        self._import_button.setProperty("class", "secondary")

        actions = QHBoxLayout()
        actions.setSpacing(6)
        actions.addWidget(self._select_button)
        actions.addWidget(self._remove_button)
        actions.addWidget(self._export_button)
        actions.addWidget(self._import_button)
        actions.addStretch(1)
        return actions

    def _build_footer(self) -> QHBoxLayout:
        self._back_button = QPushButton()
        self._back_button.setObjectName("home_page_project_management_back")
        self._back_button.setIcon(self._icon_provider.icon("start", size=28))
        self._back_button.setIconSize(QSize(28, 28))
        back_label = tr("homepage.project_management.back", "Back")
        self._back_button.setToolTip(back_label)
        self._back_button.setAccessibleName(back_label)
        self._back_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._back_button.setFixedSize(52, 52)

        footer = QHBoxLayout()
        footer.addStretch(1)
        footer.addWidget(self._back_button)
        return footer

    def _connect_signals(self) -> None:
        self._new_button.clicked.connect(self.new_project_requested)
        self._search_button.clicked.connect(self._show_search)
        self._search_edit.textChanged.connect(lambda _text: self.refresh())
        self._select_button.clicked.connect(self._toggle_select_all)
        self._remove_button.clicked.connect(self._emit_remove)
        self._export_button.clicked.connect(self._emit_export)
        self._import_button.clicked.connect(self.import_projects_requested)
        self._back_button.clicked.connect(self.back_requested)
        self._table.itemChanged.connect(lambda _item: self._sync_actions())

        self._top_bar.logs_requested.connect(self.logs_requested)
        self._top_bar.help_requested.connect(self.help_requested)
        self._top_bar.settings_requested.connect(self.settings_requested)
        self._top_bar.minimize_requested.connect(self.minimize_requested)
        self._top_bar.maximize_requested.connect(self.maximize_requested)
        self._top_bar.close_requested.connect(self.close_requested)

    # ----- Internals -------------------------------------------------

    def _populate_row(
        self,
        row: int,
        summary: ProjectSummary,
        previously_selected: set[ProjectId],
    ) -> None:
        check_item = QTableWidgetItem()
        check_item.setFlags(
            Qt.ItemFlag.ItemIsEnabled
            | Qt.ItemFlag.ItemIsSelectable
            | Qt.ItemFlag.ItemIsUserCheckable
        )
        check_item.setData(Qt.ItemDataRole.UserRole, summary.project_id)
        check_item.setCheckState(
            Qt.CheckState.Checked
            if summary.project_id in previously_selected
            else Qt.CheckState.Unchecked
        )
        self._table.setItem(row, 0, check_item)

        values = (
            summary.project_name,
            summary.project_id.value,
            "—",
            "—",
            _format_datetime(summary.created_at),
            _format_datetime(summary.updated_at),
        )
        for column, value in enumerate(values, start=1):
            item = QTableWidgetItem(value)
            item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self._table.setItem(row, column, item)

    def _show_search(self) -> None:
        self._search_edit.setVisible(True)
        self._search_edit.setFocus(Qt.FocusReason.ShortcutFocusReason)

    def _toggle_select_all(self) -> None:
        select = len(self.selected_project_ids()) != self._table.rowCount()
        state = Qt.CheckState.Checked if select else Qt.CheckState.Unchecked
        self._table.blockSignals(True)
        try:
            for row in range(self._table.rowCount()):
                item = self._table.item(row, 0)
                if item is not None:
                    item.setCheckState(state)
        finally:
            self._table.blockSignals(False)
        self._sync_actions()

    def _sync_actions(self) -> None:
        selected_count = len(self.selected_project_ids())
        has_rows = self._table.rowCount() > 0
        has_selection = selected_count > 0
        self._select_button.setEnabled(has_rows)
        self._remove_button.setEnabled(has_selection)
        self._export_button.setEnabled(has_selection)

        select_all = has_rows and selected_count == self._table.rowCount()
        key = (
            "homepage.project_management.deselect_projects"
            if select_all
            else "homepage.project_management.select_projects"
        )
        source = "Deselect projects" if select_all else "Select projects"
        self._select_button.setText(tr(key, source))

    def _emit_remove(self) -> None:
        project_ids = self.selected_project_ids()
        if project_ids:
            self.remove_projects_requested.emit(project_ids)

    def _emit_export(self) -> None:
        project_ids = self.selected_project_ids()
        if project_ids:
            self.export_projects_requested.emit(project_ids)

    def _set_button_icon(self, button: QPushButton, icon_name: str) -> None:
        button.setIcon(self._icon_provider.icon(icon_name, size=18))
        button.setIconSize(QSize(18, 18))


def _format_datetime(value: datetime) -> str:
    return value.strftime("%d/%m/%Y")
