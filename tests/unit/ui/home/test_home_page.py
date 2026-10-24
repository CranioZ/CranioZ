"""Tests for HomePage."""

from __future__ import annotations

from pytestqt.qtbot import QtBot

from cranioz.application.event_bus import EventBus
from cranioz.application.flows.definition import (
    FlowDefinition,
    FlowStep,
)
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
from cranioz.ui.home.home_page import HomePage


def _make_page() -> tuple[HomePage, ProjectCatalog, ProjectManager]:
    repo = InMemoryProjectRepository()
    catalog = ProjectCatalog(repository=repo)
    manager = ProjectManager(
        repository=repo,
        event_bus=EventBus(),
        access_policy=AllowAllProjectAccessPolicy(),
    )
    page = HomePage(catalog=catalog)
    return page, catalog, manager


def _seed(manager: ProjectManager, project_id: str, name: str) -> None:
    manager.create_project(
        "test",
        project_id=ProjectId(project_id),
        project_name=name,
        patient_id=PatientId("pat-001"),
        patient_display_name="Gabriel Silva",
        clinical_procedure="orthognathic",
    )


def _make_flow(flow_id: str = "orthognathic") -> FlowDefinition:
    return FlowDefinition(
        flow_id=flow_id,
        name_key=f"flows.{flow_id}.name",
        version=1,
        steps=(
            FlowStep(
                step_id=f"{flow_id}_s0",
                name_key=f"flows.{flow_id}.steps.s0",
                module_id="patient",
            ),
        ),
    )


def _select_flow(page: HomePage, flow_id: str = "orthognathic") -> None:
    """Populate the FlowList with one flow and select it."""
    page._flow_list_widget().set_flows((_make_flow(flow_id),))
    page._flow_list_widget()._on_row_selected(flow_id)


# ----- Composition --------------------------------------------------


def test_has_expected_object_name(qtbot: QtBot) -> None:
    page, _, _ = _make_page()
    qtbot.addWidget(page)
    assert page.objectName() == "home_page"


def test_starts_with_empty_table(qtbot: QtBot) -> None:
    page, _, _ = _make_page()
    qtbot.addWidget(page)
    assert page._project_table_widget().row_count() == 0


def test_refresh_reflects_new_projects(qtbot: QtBot) -> None:
    page, _, manager = _make_page()
    qtbot.addWidget(page)
    _seed(manager, "p-001", "Alpha")
    page.refresh()
    assert page._project_table_widget().row_count() == 1


# ----- Signal forwarding -------------------------------------------


def test_sidebar_hidden_by_default(qtbot: QtBot) -> None:
    """The CommunitySidebar starts hidden (extra resource)."""
    page, _, _ = _make_page()
    qtbot.addWidget(page)
    assert page._sidebar_widget().isHidden() is True


def test_top_bar_toggle_sidebar_signal_is_handled(qtbot: QtBot) -> None:
    """The ☰ toggles the CommunitySidebar visibility."""
    page, _, _ = _make_page()
    qtbot.addWidget(page)
    page.show()
    qtbot.waitExposed(page)

    assert page._sidebar_widget().isHidden() is True

    page._top_bar_widget()._menu_button.click()
    assert page._sidebar_widget().isHidden() is False

    page._top_bar_widget()._menu_button.click()
    assert page._sidebar_widget().isHidden() is True


def test_top_bar_help_signal_is_forwarded(qtbot: QtBot) -> None:
    page, _, _ = _make_page()
    qtbot.addWidget(page)

    with qtbot.waitSignal(page.help_requested, timeout=1000):
        page._top_bar_widget()._help_button.click()


def test_top_bar_settings_signal_is_forwarded(qtbot: QtBot) -> None:
    page, _, _ = _make_page()
    qtbot.addWidget(page)

    with qtbot.waitSignal(page.settings_requested, timeout=1000):
        page._top_bar_widget()._settings_button.click()


def test_sidebar_community_signal_is_forwarded(qtbot: QtBot) -> None:
    page, _, _ = _make_page()
    qtbot.addWidget(page)

    with qtbot.waitSignal(page.community_requested, timeout=1000):
        page._sidebar_widget().button_for("community").click()


def test_new_project_signal_is_forwarded(qtbot: QtBot) -> None:
    page, _, _ = _make_page()
    qtbot.addWidget(page)

    with qtbot.waitSignal(page.new_project_requested, timeout=1000):
        page._project_table_widget()._new_button.click()


def test_manage_projects_signal_is_forwarded(qtbot: QtBot) -> None:
    page, _, _ = _make_page()
    qtbot.addWidget(page)

    with qtbot.waitSignal(page.manage_projects_requested, timeout=1000):
        page._project_table_widget()._manage_button.click()


# ----- Start button behavior ---------------------------------------


def test_start_button_disabled_initially(qtbot: QtBot) -> None:
    page, _, _ = _make_page()
    qtbot.addWidget(page)
    assert page._start_button_widget().isEnabled() is False


def test_start_button_stays_disabled_with_only_project(qtbot: QtBot) -> None:
    page, _, manager = _make_page()
    qtbot.addWidget(page)
    _seed(manager, "p-001", "Alpha")
    page.refresh()
    page._project_table_widget()._table.selectRow(0)
    assert page._start_button_widget().isEnabled() is False


def test_start_button_stays_disabled_with_only_flow(qtbot: QtBot) -> None:
    page, _, _ = _make_page()
    qtbot.addWidget(page)
    _select_flow(page)
    assert page._start_button_widget().isEnabled() is False


def test_start_button_enables_with_project_and_flow(qtbot: QtBot) -> None:
    page, _, manager = _make_page()
    qtbot.addWidget(page)
    _seed(manager, "p-001", "Alpha")
    page.refresh()

    page._project_table_widget()._table.selectRow(0)
    _select_flow(page)

    assert page._start_button_widget().isEnabled() is True


def test_start_button_emits_open_requested(qtbot: QtBot) -> None:
    page, _, manager = _make_page()
    qtbot.addWidget(page)
    _seed(manager, "p-001", "Alpha")
    page.refresh()

    page._project_table_widget()._table.selectRow(0)
    _select_flow(page)

    with qtbot.waitSignal(page.project_open_requested, timeout=1000) as blocker:
        page._start_button_widget().click()

    assert blocker.args[0] == ProjectId("p-001")
    assert blocker.args[1] == "orthognathic"


# ----- Architectural contract --------------------------------------


def test_home_page_has_no_project_manager_reference(
    qtbot: QtBot,
) -> None:
    """HomePage must not hold a ProjectManager; only the ProjectCatalog."""
    page, _, _ = _make_page()
    qtbot.addWidget(page)
    assert not hasattr(page, "_manager")


# ----- Bottom bar composition --------------------------------------


def test_bottom_bar_is_present(qtbot: QtBot) -> None:
    page, _, _ = _make_page()
    qtbot.addWidget(page)
    assert page._bottom_bar_widget() is not None
    assert page._bottom_bar_widget().start_button() is page._start_button_widget()


def test_bottom_bar_is_ancestor_of_start_button(qtbot: QtBot) -> None:
    page, _, _ = _make_page()
    qtbot.addWidget(page)
    assert page._bottom_bar_widget().isAncestorOf(page._start_button_widget())


# ----- Regression: deselection / search filter ---------------------


def test_start_button_disables_when_selection_cleared(
    qtbot: QtBot,
) -> None:
    """Clearing the project table selection must disable StartButton."""
    page, _, manager = _make_page()
    qtbot.addWidget(page)
    _seed(manager, "p-001", "Alpha")
    page.refresh()

    page._project_table_widget()._table.selectRow(0)
    _select_flow(page)

    assert page._start_button_widget().isEnabled() is True

    page._project_table_widget()._table.clearSelection()

    assert page._start_button_widget().isEnabled() is False


def test_start_button_disables_when_search_filters_selected_project(
    qtbot: QtBot,
) -> None:
    """Filtering the selected project away must disable the StartButton."""
    page, _, manager = _make_page()
    qtbot.addWidget(page)
    _seed(manager, "p-001", "Alpha")
    _seed(manager, "p-002", "Beta")
    page.refresh()

    page._project_table_widget()._table.selectRow(0)  # Alpha
    _select_flow(page)
    assert page._start_button_widget().isEnabled() is True

    page._project_table_widget()._search_edit.setText("beta")

    assert page._start_button_widget().isEnabled() is False
