"""Tests for the project management page."""

from __future__ import annotations

from pytestqt.qtbot import QtBot
from tests.conftest import make_icon_provider, make_theme_service

from cranioz.application.event_bus import EventBus
from cranioz.application.project.access_policy import AllowAllProjectAccessPolicy
from cranioz.application.project.catalog import ProjectCatalog
from cranioz.application.project.in_memory_index import InMemoryProjectIndex
from cranioz.application.project.in_memory_repository import InMemoryProjectRepository
from cranioz.application.project.index_synchronizer import (
    ProjectIndexSynchronizer,
    SynchronizedProjectIndex,
)
from cranioz.application.project.manager import ProjectManager
from cranioz.domain.patient.value_objects.patient_id import PatientId
from cranioz.domain.project.project_id import ProjectId
from cranioz.ui.home.project_management_page import ProjectManagementPage
from cranioz.ui.theme.tokens import ThemeMode


def _make_catalog_and_manager() -> tuple[ProjectCatalog, ProjectManager]:
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


def _page(qtbot: QtBot) -> ProjectManagementPage:
    catalog, manager = _make_catalog_and_manager()
    _seed(manager, "p-001", "Alpha")
    _seed(manager, "p-002", "Beta")
    icon_provider = make_icon_provider(make_theme_service(ThemeMode.DARK))
    page = ProjectManagementPage(catalog, icon_provider=icon_provider)
    qtbot.addWidget(page)
    return page


def test_lists_projects(qtbot: QtBot) -> None:
    assert _page(qtbot).row_count() == 2


def test_search_icon_reveals_filter_field(qtbot: QtBot) -> None:
    page = _page(qtbot)
    assert page._search_edit.isHidden() is True

    page._search_button.click()
    page._search_edit.setText("Alpha")

    assert page._search_edit.isHidden() is False
    assert page.row_count() == 1


def test_select_button_selects_all_projects(qtbot: QtBot) -> None:
    page = _page(qtbot)

    page._select_button.click()

    assert set(page.selected_project_ids()) == {
        ProjectId("p-001"),
        ProjectId("p-002"),
    }
    assert page._remove_button.isEnabled() is True


def test_remove_button_emits_selected_ids(qtbot: QtBot) -> None:
    page = _page(qtbot)
    page._select_button.click()

    with qtbot.waitSignal(page.remove_projects_requested, timeout=1000) as blocker:
        page._remove_button.click()

    assert set(blocker.args[0]) == {ProjectId("p-001"), ProjectId("p-002")}


def test_header_buttons_use_svg_icons(qtbot: QtBot) -> None:
    page = _page(qtbot)

    assert not page._new_button.icon().isNull()
    assert not page._search_button.icon().isNull()
    assert not page._back_button.icon().isNull()
