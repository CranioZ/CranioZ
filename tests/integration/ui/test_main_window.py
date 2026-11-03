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
"""

from __future__ import annotations

import pytest
from PySide6.QtWidgets import QMessageBox, QStackedWidget
from pytestqt.qtbot import QtBot

from cranioz.application.event_bus import EventBus
from cranioz.application.project.in_memory_project_repository import (
    InMemoryProjectRepository,
)
from cranioz.application.project.project_access_policy import (
    AllowAllProjectAccessPolicy,
)
from cranioz.application.project.project_catalog import ProjectCatalog
from cranioz.application.project.project_manager import ProjectManager
from cranioz.domain.patient.value_objects.patient_id import PatientId
from cranioz.domain.project.project_id import ProjectId
from cranioz.ui.editors.editor_registry import EditorRegistry
from cranioz.ui.editors.tomography.editor import TomographyEditor
from cranioz.ui.main_window import MainWindow
from cranioz.ui.theme.service import ThemeName, ThemeService
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
    catalog = ProjectCatalog(repository=repo)
    manager = ProjectManager(
        repository=repo,
        event_bus=EventBus(),
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
    theme_service = ThemeService(theme=ThemeName.DARK)

    w = MainWindow(
        catalog=catalog,
        manager=manager,
        actor=_ACTOR,
        editor_registry=editor_registry,
        tool_registry=tool_registry,
        theme_service=theme_service,
    )
    qtbot.addWidget(w)
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
    stack = window.findChild(QStackedWidget)
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
        ("manage_projects_requested", "Manage projects"),
        ("manage_flows_requested", "Manage flows"),
        ("settings_requested", "Settings"),
        ("help_requested", "Help"),
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
