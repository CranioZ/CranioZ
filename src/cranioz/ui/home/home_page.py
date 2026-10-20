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
    └── QHBoxLayout
        ├── CommunitySidebar (200 px, hidden by default, full height)
        └── QVBoxLayout
            ├── HomeTopBar       (stretch 8  — ~8%)
            ├── ProjectTable     (stretch 42 — ~42%)
            ├── FlowList         (stretch 42 — ~42%)
            └── HomeBottomBar    (stretch 8  — ~8%)

The right column uses a plain QVBoxLayout with stretch factors,
not a QSplitter. The prototype shows fixed panels, not a draggable
divider. Proportional heights (8/42/42/8) keep the four bars
visually balanced regardless of window size; setMinimumHeight on
the top and bottom bars protects against very small windows.

CommunitySidebar is hidden by default. The ☰ button in the top bar
toggles it. The sidebar is an "extra" resource, not part of the
default workflow. It fills the full height of the HomePage; when
visible, it aligns with the top and bottom edges of the right
column, not just the content above the bottom bar.

StartButton state:

- Disabled (grey) by default.
- Enabled (green) only when BOTH a project and a flow are selected.
- Clicking emits `project_open_requested(project_id, flow_id)`.
"""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
)

from cranioz.application.project.project_catalog import ProjectCatalog
from cranioz.domain.project.project_id import ProjectId
from cranioz.ui.home.widgets.community_sidebar import CommunitySidebar
from cranioz.ui.home.widgets.flow_list import FlowList
from cranioz.ui.home.widgets.home_bottom_bar import HomeBottomBar
from cranioz.ui.home.widgets.home_top_bar import HomeTopBar
from cranioz.ui.home.widgets.project_table import ProjectTable
from cranioz.ui.home.widgets.start_button import StartButton


class HomePage(QWidget):
    """Entry point of the application."""

    # ----- Top bar ---------------------------------------------------

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
    manage_projects_requested = Signal()
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
        self._start_button = StartButton()
        self._bottom_bar = HomeBottomBar(self._start_button, self)

        # ----- Right column: proportional heights 8 / 42 / 42 / 8 ----
        # No QSplitter: the prototype shows fixed panels, not a
        # draggable divider. If per-user proportions are ever needed,
        # that is a separate piece (LayoutState persistence).
        right_column = QWidget(self)
        right_layout = QVBoxLayout(right_column)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        right_layout.addWidget(self._top_bar, stretch=8)
        right_layout.addWidget(self._project_table, stretch=42)
        right_layout.addWidget(self._flow_list, stretch=42)
        right_layout.addWidget(self._bottom_bar, stretch=8)

        # ----- Whole page: sidebar (left) | right column ---------------
        # The sidebar uses QSizePolicy.Expanding vertically (see its
        # class), so it fills the full height of the HomePage — not
        # just the height of the content above the bottom bar.
        content = QWidget(self)
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        content_layout.addWidget(self._sidebar)
        content_layout.addWidget(right_column, stretch=1)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(content)

        self._connect_signals()
        self._sync_start_button()

        # CommunitySidebar is hidden by default. The ☰ button toggles it.
        self._sidebar.setVisible(False)

    # ----- Public API -----------------------------------------------

    def refresh(self) -> None:
        """Reload the project table from the catalog."""
        self._project_table.refresh()

    def selected_project_id(self) -> ProjectId | None:
        return self._selected_project_id

    def selected_flow_id(self) -> str | None:
        return self._selected_flow_id

    # ----- Internals ------------------------------------------------

    def _connect_signals(self) -> None:
        tb = self._top_bar
        tb.toggle_sidebar_requested.connect(self._on_toggle_sidebar)
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
        pt.manage_projects_requested.connect(self.manage_projects_requested)
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

    def _on_toggle_sidebar(self) -> None:
        self._sidebar.setVisible(not self._sidebar.isVisible())

    # ----- Convenience for tests ------------------------------------

    def _top_bar_widget(self) -> HomeTopBar:
        return self._top_bar

    def _sidebar_widget(self) -> CommunitySidebar:
        return self._sidebar

    def _project_table_widget(self) -> ProjectTable:
        return self._project_table

    def _flow_list_widget(self) -> FlowList:
        return self._flow_list

    def _bottom_bar_widget(self) -> HomeBottomBar:
        return self._bottom_bar

    def _start_button_widget(self) -> StartButton:
        return self._start_button
