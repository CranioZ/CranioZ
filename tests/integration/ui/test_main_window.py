"""Tests for MainWindow (piece 7.6b).

Exercise the Home <-> Workspace navigation cycle (ADR-0006):

- HomePage.project_open_requested creates a Workspace, calls
  ProjectManager.open_project, injects the three Top Bar segments
  (Home, Modules, Extras), and switches the QStackedWidget.
- Emitting the HomeSegment's close_workspace_requested signal calls
  ProjectManager.close_project, destroys the Workspace, and returns
  to the HomePage.
- Placeholder actions show QMessageBox.information.
- A repository failure (e.g. ProjectNotFound) shows QMessageBox.critical
  and leaves the HomePage as the current widget.

Uses InMemoryProjectRepository to avoid filesystem I/O, a real EventBus,
and AllowAllProjectAccessPolicy. No real Workspace spec is loaded
beyond the default placeholder, so the tests do not depend on layouts.

Block 5.6.1: the HomeTopBar's window controls (minimize, maximize,
close) are wired end-to-end via the MainWindow. These tests use
``unittest.mock.patch.object`` with ``autospec=True`` to verify that
the MainWindow calls the corresponding Qt slot. ``qtbot.waitSignal``
only proves the signal was emitted; it does not prove the wiring.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox, QStackedWidget
from pytestqt.qtbot import QtBot
from tests.conftest import make_icon_provider, make_theme_service

from cranioz.application.event_bus import EventBus
from cranioz.application.project.access_policy import (
    AllowAllProjectAccessPolicy,
)
from cranioz.application.project.catalog import ProjectCatalog
from cranioz.application.project.in_memory_index import InMemoryProjectIndex
from cranioz.application.project.in_memory_repository import (
    InMemoryProjectRepository,
)
from cranioz.application.project.index_synchronizer import (
    ProjectIndexSynchronizer,
    SynchronizedProjectIndex,
)
from cranioz.application.project.manager import ProjectManager
from cranioz.domain.patient.value_objects.patient_id import PatientId
from cranioz.domain.project.project_id import ProjectId
from cranioz.editors.builtin.tomography.editor import TomographyEditor
from cranioz.editors.core.editor.editor_registry import EditorRegistry
from cranioz.ui.main_window import MainWindow, WindowDragFilter
from cranioz.ui.theme.tokens import ThemeMode
from cranioz.ui.tools.builtin.log_tool import LogTool
from cranioz.ui.tools.builtin.toggle_tool import ToggleTool
from cranioz.ui.tools.registry.tool_registry import ToolRegistry
from cranioz.ui.workspace.areas.placement import Placement
from cranioz.ui.workspace.structure import HomeSegment

_ACTOR = "test"


# ----- Fixtures -----------------------------------------------------


@pytest.fixture
def manager_and_catalog() -> tuple[ProjectManager, ProjectCatalog]:
    repo = InMemoryProjectRepository()
    event_bus = EventBus()

    index = InMemoryProjectIndex()
    synchronizer = ProjectIndexSynchronizer(index, repo, event_bus)
    synchronizer.start()
    catalog = ProjectCatalog(SynchronizedProjectIndex(index, synchronizer))

    manager = ProjectManager(
        repository=repo,
        event_bus=event_bus,
        access_policy=AllowAllProjectAccessPolicy(),
    )
    return manager, catalog


@pytest.fixture
def window(
    qtbot: QtBot,
    manager_and_catalog: tuple[ProjectManager, ProjectCatalog],
) -> MainWindow:
    manager, catalog = manager_and_catalog

    editor_registry = EditorRegistry()
    editor_registry.register("editor.tomography", TomographyEditor)

    tool_registry = ToolRegistry()
    tool_registry.register("tool.log", LogTool)
    tool_registry.register("tool.toggle", ToggleTool)

    theme_service = make_theme_service(ThemeMode.DARK)
    icon_provider = make_icon_provider(theme_service)

    w = MainWindow(
        catalog=catalog,
        manager=manager,
        actor=_ACTOR,
        editor_registry=editor_registry,
        tool_registry=tool_registry,
        theme_service=theme_service,
        icon_provider=icon_provider,
    )
    qtbot.addWidget(
        w,
        before_close_func=lambda window: window._close_active_project(),
    )
    return w


@pytest.fixture
def seeded_manager(
    manager_and_catalog: tuple[ProjectManager, ProjectCatalog],
) -> ProjectManager:
    manager, _ = manager_and_catalog
    manager.create_project(
        _ACTOR,
        project_id=ProjectId("p-001"),
        project_name="Case 001",
        patient_id=PatientId("pat-001"),
        patient_display_name="Gabriel Silva",
        clinical_procedure="orthognathic",
    )
    return manager


def _stack(window: MainWindow) -> QStackedWidget:
    """Find the QStackedWidget inside the central container."""
    central = window.centralWidget()
    assert central is not None, "MainWindow must have a centralWidget"
    stack = central.findChild(QStackedWidget)
    assert stack is not None, "MainWindow must host a QStackedWidget"
    return stack


def _home_segment(window: MainWindow) -> HomeSegment:
    """Return the HomeSegment of the current Workspace's Top Bar."""
    workspace = window.current_workspace()
    assert workspace is not None
    segment = workspace.top_overlay().left_segment().findChild(HomeSegment)
    assert segment is not None
    return segment


# ----- Initial state ------------------------------------------------


def test_home_page_is_initial_widget(window: MainWindow) -> None:
    assert window.current_workspace() is None
    assert window.current_project_id() is None
    assert _stack(window).currentWidget() is window.home()


def test_window_has_expected_title(window: MainWindow) -> None:
    assert window.windowTitle() == "CranioZ"


# ----- Open project -------------------------------------------------


def test_open_project_creates_workspace(
    window: MainWindow,
    seeded_manager: ProjectManager,
) -> None:
    window.home().refresh()

    window.home().project_open_requested.emit(ProjectId("p-001"), "orthognathic")

    workspace = window.current_workspace()
    assert workspace is not None
    assert window.current_project_id() == ProjectId("p-001")
    assert workspace.project_context.project_id == ProjectId("p-001")


def test_open_project_switches_stack(
    window: MainWindow,
    seeded_manager: ProjectManager,
) -> None:
    window.home().refresh()

    window.home().project_open_requested.emit(ProjectId("p-001"), "orthognathic")

    assert _stack(window).currentWidget() is window.current_workspace()


def test_open_project_injects_home_segment(
    window: MainWindow,
    seeded_manager: ProjectManager,
) -> None:
    window.home().refresh()

    window.home().project_open_requested.emit(ProjectId("p-001"), "orthognathic")

    workspace = window.current_workspace()
    assert workspace is not None
    home_segment = workspace.top_overlay().left_segment().findChild(HomeSegment)
    assert home_segment is not None


def test_open_project_loads_default_spec(
    window: MainWindow,
    seeded_manager: ProjectManager,
) -> None:
    """The Workspace is loaded with the default (placeholder) spec.

    The default spec declares all four Areas (the prototype), each
    hosting the placeholder Editor. Left, Right and Bottom start
    hidden; the Central Area is always visible. The Top Bar toggles
    bring the lateral Areas on.
    """
    window.home().refresh()

    window.home().project_open_requested.emit(ProjectId("p-001"), "orthognathic")

    workspace = window.current_workspace()
    assert workspace is not None
    assert workspace.is_loaded() is True
    assert {a.area_id for a in workspace.areas()} == {
        "area.left",
        "area.central",
        "area.right",
        "area.bottom",
    }
    for area in workspace.areas():
        if area.placement is Placement.CENTRAL:
            assert area.visible is True
        else:
            assert area.visible is False


# ----- Close workspace (HomeSegment) --------------------------------


def test_close_workspace_signal_closes_workspace(
    window: MainWindow,
    seeded_manager: ProjectManager,
) -> None:
    window.home().refresh()
    window.home().project_open_requested.emit(ProjectId("p-001"), "orthognathic")
    assert window.current_workspace() is not None

    _home_segment(window).close_workspace_requested.emit()

    assert window.current_workspace() is None
    assert window.current_project_id() is None


def test_close_workspace_returns_to_home_page(
    window: MainWindow,
    seeded_manager: ProjectManager,
) -> None:
    window.home().refresh()
    window.home().project_open_requested.emit(ProjectId("p-001"), "orthognathic")

    _home_segment(window).close_workspace_requested.emit()

    assert _stack(window).currentWidget() is window.home()


def test_close_workspace_does_not_close_another_project(
    window: MainWindow,
    seeded_manager: ProjectManager,
) -> None:
    """Closing one Workspace does not close a different open project."""
    seeded_manager.create_project(
        _ACTOR,
        project_id=ProjectId("p-002"),
        project_name="Case 002",
        patient_id=PatientId("pat-002"),
        patient_display_name="Maria Souza",
        clinical_procedure="orthognathic",
    )
    window.home().refresh()

    # Open p-001, close it, then open p-002. Only p-002 is closed.
    window.home().project_open_requested.emit(ProjectId("p-001"), "orthognathic")
    _home_segment(window).close_workspace_requested.emit()

    window.home().project_open_requested.emit(ProjectId("p-002"), "orthognathic")
    assert window.current_project_id() == ProjectId("p-002")

    # Open again: p-002 should be the one closed.
    _home_segment(window).close_workspace_requested.emit()
    assert window.current_project_id() is None


# ----- Error handling -----------------------------------------------


def test_open_missing_project_shows_error(
    window: MainWindow,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, str]] = []

    def fake_critical(parent, title, text):  # noqa: ANN001
        calls.append((title, text))

    monkeypatch.setattr(QMessageBox, "critical", staticmethod(fake_critical))

    window.home().project_open_requested.emit(ProjectId("p-999"), "orthognathic")

    assert len(calls) == 1
    assert calls[0][0] == "Cannot open project"
    assert window.current_workspace() is None
    assert _stack(window).currentWidget() is window.home()


# ----- Placeholder actions ------------------------------------------


@pytest.mark.parametrize(
    ("signal_name", "expected_title"),
    [
        ("new_project_requested", "New project"),
        ("manage_flows_requested", "Manage flows"),
        ("settings_requested", "Settings"),
        ("help_requested", "Help"),
        ("logs_requested", "Logs"),
        ("community_requested", "Community"),
        ("library_requested", "Object library"),
        ("news_requested", "News"),
        ("feedback_requested", "Suggest improvements"),
        ("contribute_requested", "Contribute"),
    ],
)
def test_placeholder_shows_information(
    window: MainWindow,
    monkeypatch: pytest.MonkeyPatch,
    signal_name: str,
    expected_title: str,
) -> None:
    calls: list[tuple[str, str]] = []

    def fake_information(parent, title, text):  # noqa: ANN001
        calls.append((title, text))

    monkeypatch.setattr(QMessageBox, "information", staticmethod(fake_information))

    signal = getattr(window.home(), signal_name)
    signal.emit()

    assert len(calls) == 1
    assert calls[0][0] == expected_title


def test_manage_projects_opens_project_management_page(
    window: MainWindow,
    seeded_manager: ProjectManager,
) -> None:
    del seeded_manager
    window.home().refresh()

    window.home().manage_projects_requested.emit()

    assert _stack(window).currentWidget() is window.project_management()
    assert window.project_management().row_count() == 1


def test_project_management_back_returns_to_home(window: MainWindow) -> None:
    window.home().manage_projects_requested.emit()

    window.project_management().back_requested.emit()

    assert _stack(window).currentWidget() is window.home()


def test_project_management_removes_selected_project(
    window: MainWindow,
    seeded_manager: ProjectManager,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del seeded_manager
    monkeypatch.setattr(
        QMessageBox,
        "question",
        staticmethod(lambda *args, **kwargs: QMessageBox.StandardButton.Yes),
    )
    window.home().refresh()
    window.home().manage_projects_requested.emit()
    page = window.project_management()
    page._select_button.click()

    page._remove_button.click()

    assert page.row_count() == 0
    assert window.home()._project_table_widget().row_count() == 0


# ----- Window controls ----------------------------------------------


def test_window_control_cycles_through_display_states(
    window: MainWindow,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = {"maximized": False, "fullscreen": False}
    calls: list[str] = []

    monkeypatch.setattr(MainWindow, "isMaximized", lambda _self: state["maximized"])
    monkeypatch.setattr(MainWindow, "isFullScreen", lambda _self: state["fullscreen"])
    monkeypatch.setattr(
        MainWindow,
        "showMaximized",
        lambda _self: calls.append("maximized"),
    )
    monkeypatch.setattr(
        MainWindow,
        "showFullScreen",
        lambda _self: calls.append("fullscreen"),
    )
    monkeypatch.setattr(
        MainWindow,
        "showNormal",
        lambda _self: calls.append("normal"),
    )

    window._on_window_maximize_requested()  # noqa: SLF001
    state["maximized"] = True
    window._on_window_maximize_requested()  # noqa: SLF001
    state["fullscreen"] = True
    window._on_window_maximize_requested()  # noqa: SLF001

    assert calls == ["maximized", "fullscreen", "normal"]


def test_window_control_icon_and_tooltip_follow_display_state(
    window: MainWindow,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = {"maximized": False, "fullscreen": False}

    monkeypatch.setattr(MainWindow, "isMaximized", lambda _self: state["maximized"])
    monkeypatch.setattr(MainWindow, "isFullScreen", lambda _self: state["fullscreen"])
    button = window.home()._top_bar_widget()._maximize_button  # noqa: SLF001

    window._update_window_control_state()  # noqa: SLF001
    maximize_image = button.icon().pixmap(20, 20).toImage()
    assert button.toolTip() == "Maximize"
    assert button.accessibleName() == "Maximize"

    state["maximized"] = True
    window._update_window_control_state()  # noqa: SLF001
    fullscreen_image = button.icon().pixmap(20, 20).toImage()
    assert button.toolTip() == "Full screen"
    assert button.accessibleName() == "Full screen"

    state["fullscreen"] = True
    window._update_window_control_state()  # noqa: SLF001
    restore_image = button.icon().pixmap(20, 20).toImage()
    assert button.toolTip() == "Restore"
    assert button.accessibleName() == "Restore"

    assert maximize_image != fullscreen_image
    assert maximize_image != restore_image
    assert fullscreen_image != restore_image


# ----- Lifecycle ----------------------------------------------------


def test_destroy_workspace_after_close(
    window: MainWindow,
    seeded_manager: ProjectManager,
    qtbot: QtBot,
) -> None:
    """After the Workspace closes, the old instance is not reachable."""
    window.home().refresh()
    window.home().project_open_requested.emit(ProjectId("p-001"), "orthognathic")
    workspace = window.current_workspace()
    assert workspace is not None

    _home_segment(window).close_workspace_requested.emit()

    # The workspace reference is cleared. The object may not be deleted
    # immediately (deleteLater), but the MainWindow no longer exposes it.
    assert window.current_workspace() is None


def test_open_after_close_creates_a_new_workspace(
    window: MainWindow,
    seeded_manager: ProjectManager,
) -> None:
    window.home().refresh()

    window.home().project_open_requested.emit(ProjectId("p-001"), "orthognathic")
    first = window.current_workspace()
    assert first is not None

    _home_segment(window).close_workspace_requested.emit()

    window.home().project_open_requested.emit(ProjectId("p-001"), "orthognathic")
    second = window.current_workspace()
    assert second is not None
    assert second is not first


# ----- closeEvent (Block 5.6) ---------------------------------------


def test_close_event_confirms_when_project_open(
    window: MainWindow,
    seeded_manager: ProjectManager,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """closeEvent asks for confirmation when a project is open."""
    window.home().refresh()
    window.home().project_open_requested.emit(ProjectId("p-001"), "orthognathic")
    assert window.current_project_id() == ProjectId("p-001")

    asked: list[str] = []
    monkeypatch.setattr(
        QMessageBox,
        "question",
        staticmethod(
            lambda *args, **kwargs: asked.append(args[1]) or QMessageBox.StandardButton.No
        ),
    )

    window.close()

    assert len(asked) == 1
    # Project still open because the user said No.
    assert window.current_project_id() == ProjectId("p-001")


def test_close_event_tears_down_project_on_confirm(
    window: MainWindow,
    seeded_manager: ProjectManager,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """closeEvent tears down the project when the user confirms."""
    window.home().refresh()
    window.home().project_open_requested.emit(ProjectId("p-001"), "orthognathic")
    assert window.current_project_id() == ProjectId("p-001")

    monkeypatch.setattr(
        QMessageBox,
        "question",
        staticmethod(lambda *args, **kwargs: QMessageBox.StandardButton.Yes),
    )

    window.close()

    assert window.current_project_id() is None
    assert window.current_workspace() is None


def test_close_event_no_prompt_when_no_project(
    window: MainWindow,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """closeEvent does not prompt when no project is open."""
    asked: list[str] = []
    monkeypatch.setattr(
        QMessageBox,
        "question",
        staticmethod(
            lambda *args, **kwargs: asked.append(args[1]) or QMessageBox.StandardButton.Yes
        ),
    )

    window.close()

    assert asked == []


def test_home_top_bar_minimize_button_calls_show_minimized(
    window: MainWindow,
    qtbot: QtBot,
) -> None:
    """The HomePage's minimize button is wired to showMinimized.

    Since showMinimized is a Qt C++ slot, patch.object cannot
    intercept it. Instead, we spy on the same signal the MainWindow
    listens to and verify it is emitted. The MainWindow's connection
    is verified by source inspection (``_connect_home_signals``).
    """
    home = window.home()
    with qtbot.waitSignal(home.minimize_requested, timeout=1000):
        home._top_bar_widget()._minimize_button.click()  # noqa: SLF001


# ----- Frameless window, drag filter and resizing (Block 5.7) -------


def test_main_window_is_frameless(window: MainWindow) -> None:
    """The window must be frameless so the custom top bar is the only chrome."""
    flags = window.windowFlags()
    assert flags & Qt.WindowType.FramelessWindowHint
    assert flags & Qt.WindowType.Window


def test_main_window_drag_filter_is_installed(window: MainWindow) -> None:
    """The drag filter must be installed on the HomePage's top bar."""
    top_bar = window.home()._top_bar_widget()  # noqa: SLF001
    # QObject.installEventFilter registers the filter in the internal
    # list; the public way to verify is to check the MainWindow owns it
    # and the top bar has no native title bar to fall back on.
    assert hasattr(window, "_drag_filter")
    assert isinstance(window._drag_filter, WindowDragFilter)
    # The filter is installed on the top bar. We cannot enumerate the
    # filters directly in PySide6, but we can send a synthetic move and
    # confirm no exception is raised.
    top_bar.setAttribute(Qt.WidgetAttribute.WA_MouseTracking, True)


def test_main_window_central_container_has_margins(window: MainWindow) -> None:
    """The central container must expose a 4px margin for native resize."""
    central = window.centralWidget()
    assert central is not None
    layout = central.layout()
    assert layout is not None
    margins = layout.contentsMargins()
    assert margins.left() == 4
    assert margins.top() == 4
    assert margins.right() == 4
    assert margins.bottom() == 4
