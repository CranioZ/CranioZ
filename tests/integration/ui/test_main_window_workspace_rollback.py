"""Integration tests: Workspace creation rollback (Sprint K, K.4).

When ``MainWindow._create_workspace`` raises after a project has been
successfully opened, the MainWindow must close the project so the
lifecycle remains consistent. This is the rollback path required by
Sprint K.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
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
from cranioz.editors.core.editor.editor_registry import EditorRegistry
from cranioz.ui.main_window import MainWindow
from cranioz.ui.theme.tokens import ThemeMode
from cranioz.ui.tools.registry.tool_registry import ToolRegistry
from cranioz.ui.workspace.workspace_spec import (
    PLACEHOLDER_EDITOR_CLASS,
    PLACEHOLDER_EDITOR_ID,
)

_ACTOR = "test-actor"


@pytest.fixture
def window(qtbot: QtBot) -> MainWindow:
    repository = InMemoryProjectRepository()
    event_bus = EventBus()

    index = InMemoryProjectIndex()
    synchronizer = ProjectIndexSynchronizer(index, repository, event_bus)
    synchronizer.start()
    catalog = ProjectCatalog(SynchronizedProjectIndex(index, synchronizer))

    manager = ProjectManager(
        repository=repository,
        event_bus=event_bus,
        access_policy=AllowAllProjectAccessPolicy(),
    )
    manager.create_project(
        _ACTOR,
        project_id=ProjectId("p-001"),
        project_name="Case 001",
        patient_id=PatientId("pat-001"),
        patient_display_name="Gabriel Silva",
        clinical_procedure="orthognathic",
    )

    editor_registry = EditorRegistry()
    editor_registry.register(PLACEHOLDER_EDITOR_ID, PLACEHOLDER_EDITOR_CLASS)

    theme_service = make_theme_service(ThemeMode.DARK)
    icon_provider = make_icon_provider(theme_service)

    w = MainWindow(
        catalog=catalog,
        manager=manager,
        actor=_ACTOR,
        editor_registry=editor_registry,
        tool_registry=ToolRegistry(),
        theme_service=theme_service,
        icon_provider=icon_provider,
    )
    qtbot.addWidget(w)
    return w


def test_workspace_creation_failure_rolls_back_project(
    window: MainWindow,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """If ``_create_workspace`` raises, the project is closed."""
    closed: list[ProjectId] = []

    original_close = window._manager.close_project  # noqa: SLF001

    def spy_close(actor: str, project_id: ProjectId) -> None:
        closed.append(project_id)
        original_close(actor, project_id)

    monkeypatch.setattr(window._manager, "close_project", spy_close)  # noqa: SLF001

    with patch.object(
        MainWindow,
        "_create_workspace",
        side_effect=RuntimeError("workspace boom"),
    ):
        window.home().project_open_requested.emit(ProjectId("p-001"), "orthognathic")

    assert closed == [ProjectId("p-001")]
    assert window.current_project_id() is None
    assert window.current_workspace() is None


def test_workspace_creation_failure_shows_dialog(
    window: MainWindow,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The failure surfaces a QMessageBox.critical to the user."""
    calls: list[tuple[str, str]] = []

    def fake_critical(parent, title, text):  # noqa: ANN001
        calls.append((title, text))

    monkeypatch.setattr(QMessageBox, "critical", staticmethod(fake_critical))

    with patch.object(
        MainWindow,
        "_create_workspace",
        side_effect=RuntimeError("workspace boom"),
    ):
        window.home().project_open_requested.emit(ProjectId("p-001"), "orthognathic")

    assert len(calls) == 1
    assert "workspace boom" in calls[0][1]


def test_workspace_creation_failure_keeps_home_visible(
    window: MainWindow,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """After a rollback, the HomePage remains the current widget."""
    monkeypatch.setattr(QMessageBox, "critical", staticmethod(lambda *a, **kw: None))

    with patch.object(
        MainWindow,
        "_create_workspace",
        side_effect=RuntimeError("workspace boom"),
    ):
        window.home().project_open_requested.emit(ProjectId("p-001"), "orthognathic")

    central = window.centralWidget()
    assert central is not None
    stack = central.findChild(QStackedWidget)
    assert stack is not None
    assert stack.currentWidget() is window.home()
