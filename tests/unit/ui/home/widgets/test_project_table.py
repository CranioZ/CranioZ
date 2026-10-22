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


def test_manage_button_emits_signal(qtbot: QtBot) -> None:
    """The 'Gerir projetos' button emits manage_projects_requested (no arg)."""
    catalog, _ = _make_catalog_and_manager()
    table = ProjectTable(catalog)
    qtbot.addWidget(table)

    with qtbot.waitSignal(
        table.manage_projects_requested, timeout=1000
    ) as blocker:
        table._manage_button.click()

    # No argument: managing projects is not about a specific project.
    assert blocker.args == []


def test_manage_button_is_always_enabled(qtbot: QtBot) -> None:
    """The 'Gerir projetos' button does not depend on selection."""
    catalog, manager = _make_catalog_and_manager()
    _seed(manager, "p-001", "Alpha")
    table = ProjectTable(catalog)
    qtbot.addWidget(table)
    assert table._manage_button.isEnabled() is True


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


# ----- Selection lifecycle (None emission) ---------------------------


def test_clearing_selection_emits_none(qtbot: QtBot) -> None:
    """Deselect the only row: ProjectTable must emit project_selected(None).

    Regression guard: previously _on_selection_changed only emitted
    when a row was selected, so HomePage kept a stale _selected_project_id
    and the StartButton stayed enabled after the row was deselected.
    """
    catalog, manager = _make_catalog_and_manager()
    _seed(manager, "p-001", "Alpha")
    table = ProjectTable(catalog)
    qtbot.addWidget(table)

    table._table.selectRow(0)
    assert table.selected_project_id() == ProjectId("p-001")

    with qtbot.waitSignal(table.project_selected, timeout=1000) as blocker:
        table._table.clearSelection()

    assert blocker.args[0] is None
    assert table.selected_project_id() is None


def test_refresh_preserves_selection_when_project_still_present(
    qtbot: QtBot,
) -> None:
    """refresh() must NOT clear the selection if the same project remains."""
    catalog, manager = _make_catalog_and_manager()
    _seed(manager, "p-001", "Alpha")
    _seed(manager, "p-002", "Beta")
    table = ProjectTable(catalog)
    qtbot.addWidget(table)

    table._table.selectRow(0)
    assert table.selected_project_id() == ProjectId("p-001")

    table.refresh()

    assert table.selected_project_id() == ProjectId("p-001")


def test_refresh_preserves_selection_through_unchanged_search(
    qtbot: QtBot,
) -> None:
    """Selecting a row, then refreshing, emits no None to the HomePage."""
    catalog, manager = _make_catalog_and_manager()
    _seed(manager, "p-001", "Alpha")
    table = ProjectTable(catalog)
    qtbot.addWidget(table)

    table._table.selectRow(0)

    emitted: list[object] = []
    table.project_selected.connect(emitted.append)
    table.refresh()

    # No None emitted, because the project is still in the results.
    assert None not in emitted


def test_refresh_emits_none_when_selected_project_is_filtered_out(
    qtbot: QtBot,
) -> None:
    """Search filtering the selected project away must clear HomePage state."""
    catalog, manager = _make_catalog_and_manager()
    _seed(manager, "p-001", "Alpha")
    _seed(manager, "p-002", "Beta")
    table = ProjectTable(catalog)
    qtbot.addWidget(table)

    table._table.selectRow(0)  # Alpha, p-001
    assert table.selected_project_id() == ProjectId("p-001")

    with qtbot.waitSignal(table.project_selected, timeout=1000) as blocker:
        table._search_edit.setText("beta")  # filters out Alpha

    assert blocker.args[0] is None
    assert table.selected_project_id() is None
    assert table.row_count() == 1


def test_populate_does_not_emit_none_when_nothing_was_selected(
    qtbot: QtBot,
) -> None:
    """An initial or repeated refresh with no prior selection must stay silent."""
    catalog, manager = _make_catalog_and_manager()
    _seed(manager, "p-001", "Alpha")
    table = ProjectTable(catalog)
    qtbot.addWidget(table)

    emitted: list[object] = []
    table.project_selected.connect(emitted.append)
    table.refresh()

    assert emitted == []


def test_populate_blocks_intermediate_signals(qtbot: QtBot) -> None:
    """During repopulation, only the final selection state is emitted.

    If blockSignals() were missing, clearSelection() inside _populate
    would emit None, then selectRow() would emit the ProjectId — the
    HomePage would see a None-then-id flicker on every refresh.
    """
    catalog, manager = _make_catalog_and_manager()
    _seed(manager, "p-001", "Alpha")
    _seed(manager, "p-002", "Beta")
    table = ProjectTable(catalog)
    qtbot.addWidget(table)

    table._table.selectRow(0)  # p-001

    emitted: list[object] = []
    table.project_selected.connect(emitted.append)
    table.refresh()

    # Exactly one emission (if any), and it must be the ProjectId,
    # never a bare None.
    assert None not in emitted
