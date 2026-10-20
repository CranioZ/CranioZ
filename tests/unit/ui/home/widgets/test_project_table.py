"""Tests for ProjectTable."""

from __future__ import annotations

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
from cranioz.ui.home.widgets.project_table import ProjectTable


def _make_catalog_and_manager() -> tuple[ProjectCatalog, ProjectManager]:
    repo = InMemoryProjectRepository()
    catalog = ProjectCatalog(repository=repo)
    manager = ProjectManager(
        repository=repo,
        event_bus=EventBus(),
        access_policy=AllowAllProjectAccessPolicy(),
    )
    return catalog, manager


def _seed(manager: ProjectManager, project_id: str, name: str) -> None:
    manager.create_project(
        "test",
        project_id=ProjectId(project_id),
        project_name=name,
        patient_id=PatientId("pat-001"),
        patient_display_name="Gabriel Silva",
        clinical_procedure="orthognathic",
    )


def test_starts_empty(qtbot: QtBot) -> None:
    catalog, _ = _make_catalog_and_manager()
    table = ProjectTable(catalog)
    qtbot.addWidget(table)
    assert table.row_count() == 0


def test_lists_projects(qtbot: QtBot) -> None:
    catalog, manager = _make_catalog_and_manager()
    _seed(manager, "p-001", "Alpha")
    _seed(manager, "p-002", "Beta")
    table = ProjectTable(catalog)
    qtbot.addWidget(table)
    assert table.row_count() == 2


def test_search_filters(qtbot: QtBot) -> None:
    catalog, manager = _make_catalog_and_manager()
    _seed(manager, "p-001", "Alpha")
    _seed(manager, "p-002", "Beta")
    table = ProjectTable(catalog)
    qtbot.addWidget(table)

    table._search_edit.setText("alpha")
    assert table.row_count() == 1


def test_search_empty_shows_all(qtbot: QtBot) -> None:
    catalog, manager = _make_catalog_and_manager()
    _seed(manager, "p-001", "Alpha")
    _seed(manager, "p-002", "Beta")
    table = ProjectTable(catalog)
    qtbot.addWidget(table)

    table._search_edit.setText("")
    assert table.row_count() == 2


def test_selection_emits_signal(qtbot: QtBot) -> None:
    catalog, manager = _make_catalog_and_manager()
    _seed(manager, "p-001", "Alpha")
    table = ProjectTable(catalog)
    qtbot.addWidget(table)

    with qtbot.waitSignal(table.project_selected, timeout=1000) as blocker:
        table._table.selectRow(0)

    assert blocker.args[0] == ProjectId("p-001")


def test_remove_button_emits_signal(qtbot: QtBot) -> None:
    catalog, manager = _make_catalog_and_manager()
    _seed(manager, "p-001", "Alpha")
    table = ProjectTable(catalog)
    qtbot.addWidget(table)
    table._table.selectRow(0)

    with qtbot.waitSignal(
        table.remove_project_requested, timeout=1000
    ) as blocker:
        table._remove_button.click()

    assert blocker.args[0] == ProjectId("p-001")


def test_remove_button_disabled_without_selection(qtbot: QtBot) -> None:
    catalog, manager = _make_catalog_and_manager()
    _seed(manager, "p-001", "Alpha")
    table = ProjectTable(catalog)
    qtbot.addWidget(table)
    assert table._remove_button.isEnabled() is False


def test_new_button_emits_signal(qtbot: QtBot) -> None:
    catalog, _ = _make_catalog_and_manager()
    table = ProjectTable(catalog)
    qtbot.addWidget(table)

    with qtbot.waitSignal(table.new_project_requested, timeout=1000):
        table._new_button.click()


def test_refresh_reloads(qtbot: QtBot) -> None:
    catalog, manager = _make_catalog_and_manager()
    table = ProjectTable(catalog)
    qtbot.addWidget(table)
    assert table.row_count() == 0

    _seed(manager, "p-001", "Alpha")
    table.refresh()
    assert table.row_count() == 1
