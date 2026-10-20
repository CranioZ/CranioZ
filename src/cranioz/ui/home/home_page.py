"""HomePage — the application's entry point and project discovery screen.

The HomePage is a presentation and dispatch layer. It lists projects
and flows, and emits signals for every user intention. It does not
create, delete, open, or close projects; it does not execute flows.
Those operations belong to the Application layer, coordinated by the
MainWindow (piece 7.6b), which listens to the HomePage's signals.

See `home_page.md` §3, §4, §8, §22:

> If an operation changes Project state, the operation does not belong
> to the Homepage.

The HomePage may provide the button; the button emits a signal; the
Application executes.

Layout:

    HomePage
    ├── HomeTopBar (menu, title, help, settings)
    ├── QHBoxLayout
    │   ├── CommunitySidebar (community, library, news, feedback, contribute)
    │   └── QSplitter(Vertical)
    │       ├── ProjectTable (list, search, new/remove, selection)
    │       └── FlowList (list, manage, selection)
    └── StartButton (floating, bottom-right)

StartButton state:

- Disabled (grey) by default.
- Enabled (green) only when BOTH a project and a flow are selected.
- Clicking emits `project_open_requested(project_id, flow_id)`.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QResizeEvent
from PySide6.QtWidgets import (
    QHBoxLayout,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from cranioz.application.project.project_catalog import ProjectCatalog
from cranioz.domain.project.project_id import ProjectId
from cranioz.ui.home.widgets.community_sidebar import CommunitySidebar
from cranioz.ui.home.widgets.flow_list import FlowList
from cranioz.ui.home.widgets.home_top_bar import HomeTopBar
from cranioz.ui.home.widgets.project_table import ProjectTable
from cranioz.ui.home.widgets.start_button import StartButton


class HomePage(QWidget):
    """Entry point of the application."""

    # ----- Top bar ---------------------------------------------------

    menu_requested = Signal()
    help_requested = Signal()
    settings_requested = Signal()

    # ----- Community sidebar -----------------------------------------

    community_requested = Signal()
    library_requested = Signal()
    news_requested = Signal()
    feedback_requested = Signal()
    contribute_requested = Signal()

    # ----- Project table ---------------------------------------------

    new_project_requested = Signal()
    remove_project_requested = Signal(object)  # ProjectId
    project_selected = Signal(object)  # ProjectId

    # ----- Flow list -------------------------------------------------

    flow_selected = Signal(object)  # str | None
    manage_flows_requested = Signal()

    # ----- Start button ----------------------------------------------

    project_open_requested = Signal(object, str)  # ProjectId, flow_id

    def __init__(
        self,
        catalog: ProjectCatalog,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._catalog = catalog
        self._selected_project_id: ProjectId | None = None
        self._selected_flow_id: str | None = None

        self.setObjectName("home_page")

        self._top_bar = HomeTopBar(self)
        self._sidebar = CommunitySidebar(self)
        self._project_table = ProjectTable(catalog, self)
        self._flow_list = FlowList(self)
        self._start_button = StartButton(self)

        splitter = QSplitter(Qt.Orientation.Vertical, self)
        splitter.setObjectName("home_page.splitter")
        splitter.addWidget(self._project_table)
        splitter.addWidget(self._flow_list)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)

        content = QWidget(self)
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        content_layout.addWidget(self._sidebar)
        content_layout.addWidget(splitter, stretch=1)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._top_bar)
        root.addWidget(content, stretch=1)

        self._connect_signals()
        self._sync_start_button()

    # ----- Public API -----------------------------------------------

    def refresh(self) -> None:
        """Reload the project table from the catalog."""
        self._project_table.refresh()

    def selected_project_id(self) -> ProjectId | None:
        return self._selected_project_id

    def selected_flow_id(self) -> str | None:
        return self._selected_flow_id

    # ----- Qt events ------------------------------------------------

    def resizeEvent(self, event: QResizeEvent) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._reposition_start_button()

    # ----- Internals ------------------------------------------------

    def _connect_signals(self) -> None:
        tb = self._top_bar
        tb.menu_requested.connect(self.menu_requested)
        tb.help_requested.connect(self.help_requested)
        tb.settings_requested.connect(self.settings_requested)

        sb = self._sidebar
        sb.community_requested.connect(self.community_requested)
        sb.library_requested.connect(self.library_requested)
        sb.news_requested.connect(self.news_requested)
        sb.feedback_requested.connect(self.feedback_requested)
        sb.contribute_requested.connect(self.contribute_requested)

        pt = self._project_table
        pt.new_project_requested.connect(self.new_project_requested)
        pt.remove_project_requested.connect(self.remove_project_requested)
        pt.project_selected.connect(self._on_project_selected)

        fl = self._flow_list
        fl.flow_selected.connect(self._on_flow_selected)
        fl.manage_flows_requested.connect(self.manage_flows_requested)

        self._start_button.start_requested.connect(self._on_start_requested)

    def _on_project_selected(self, project_id: ProjectId) -> None:
        self._selected_project_id = project_id
        self.project_selected.emit(project_id)
        self._sync_start_button()

    def _on_flow_selected(self, flow_id: object) -> None:
        self._selected_flow_id = flow_id if isinstance(flow_id, str) else None
        self.flow_selected.emit(self._selected_flow_id)
        self._sync_start_button()

    def _sync_start_button(self) -> None:
        ready = (
            self._selected_project_id is not None
            and self._selected_flow_id is not None
        )
        self._start_button.set_ready(ready)

    def _on_start_requested(self) -> None:
        if self._selected_project_id is None or self._selected_flow_id is None:
            return  # defensive; button should not be enabled
        self.project_open_requested.emit(
            self._selected_project_id, self._selected_flow_id
        )

    def _reposition_start_button(self) -> None:
        margin = 24
        size = self._start_button.size()
        x = self.width() - size.width() - margin
        y = self.height() - size.height() - margin
        self._start_button.move(x, y)
        self._start_button.raise_()

    # ----- Convenience for tests ------------------------------------

    def _top_bar_widget(self) -> HomeTopBar:
        return self._top_bar

    def _sidebar_widget(self) -> CommunitySidebar:
        return self._sidebar

    def _project_table_widget(self) -> ProjectTable:
        return self._project_table

    def _flow_list_widget(self) -> FlowList:
        return self._flow_list

    def _start_button_widget(self) -> StartButton:
        return self._start_button
