"""Debug script: launch the HomePage with fake data.

This script is a development tool. It is NOT part of production.

It builds a HomePage with:

- An in-memory ProjectCatalog with 5 fake projects (the names from
  Prototipagem_UI_14 p. 37), with fixed creation/update dates.
- Three fake flows in the FlowList, so the StartButton can transition
  from grey to green when a project and a flow are selected.
- All 14 HomePage signals connected to print(), so you can see them
  fire in the console.
- Project table column headers are clickable for sorting validation.

Run with:

    .venv\\Scripts\\python.exe scripts\\debug\\ui\\home_page\\debug_home_page.py

Close the window to exit.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime

from PySide6.QtWidgets import QApplication, QMainWindow

from cranioz.application.event_bus import EventBus
from cranioz.application.flows.definition import FlowDefinition, FlowStep
from cranioz.application.project.catalog import ProjectCatalog
from cranioz.application.project.in_memory_index import InMemoryProjectIndex
from cranioz.application.project.in_memory_repository import (
    InMemoryProjectRepository,
)
from cranioz.application.project.index_synchronizer import (
    ProjectIndexSynchronizer,
    SynchronizedProjectIndex,
)
from cranioz.domain.project.project import Project
from cranioz.domain.project.project_id import ProjectId
from cranioz.domain.project.project_metadata import ProjectMetadata
from cranioz.domain.project.project_status import ProjectStatus
from cranioz.infrastructure.settings.in_memory_settings_service import (
    InMemorySettingsService,
)
from cranioz.ui.home.home_page import HomePage
from cranioz.ui.icons.unicode import UnicodeIconProvider
from cranioz.ui.theme.service import ThemeService
from cranioz.ui.theme.tokens import ThemeMode

# ----- Seed data ----------------------------------------------------

# name, patient_id, created, updated
_FAKE_PROJECTS = [
    ("Gabriel Silva", "12652", "22/06/2025", "22/06/2026"),
    ("Camila Souza", "52269", "02/10/2025", "02/10/2026"),
    ("Lucas Ferreira", "25892", "22/07/2026", "22/07/2026"),
    ("Beatriz Oliveira", "11286", "15/07/2026", "15/07/2026"),
    ("Rafael Santos", "21358", "14/04/2025", "14/10/2025"),
]


def _parse_br_date(value: str) -> datetime:
    """Parse 'DD/MM/YYYY' as a UTC datetime."""
    return datetime.strptime(value, "%d/%m/%Y").replace(tzinfo=UTC)


def _seed_projects(repository: InMemoryProjectRepository) -> None:
    """Create 5 fake projects with fixed timestamps."""
    for name, patient_id, created, updated in _FAKE_PROJECTS:
        pid = ProjectId(patient_id)
        project = Project(
            project_id=pid,
            metadata=ProjectMetadata(
                project_id=pid,
                project_name=f"Caso {name}",
                patient_id=patient_id,
                patient_display_name=name,
                clinical_procedure="orthognathic",
                status=ProjectStatus.ACTIVE,
                created_at=_parse_br_date(created),
                updated_at=_parse_br_date(updated),
                last_opened_at=None,
                schema_version=1,
            ),
        )
        repository.create(project)


def _build_catalog(repository: InMemoryProjectRepository) -> ProjectCatalog:
    """Build the synchronized catalog consumed by the Home Page."""
    event_bus = EventBus()
    index = InMemoryProjectIndex()
    synchronizer = ProjectIndexSynchronizer(index, repository, event_bus)
    synchronizer.start()
    return ProjectCatalog(SynchronizedProjectIndex(index, synchronizer))


def _flow_list(page: HomePage) -> None:
    """Populate the FlowList with three fake flows."""
    page._flow_list_widget().set_flows(
        (
            _flow(
                "orthognathic_basic",
                "Cirurgia Ortognática",
                "Paciente",
                "Tomografia",
                "Osteotomia",
                "Guia",
            ),
            _flow(
                "orthognathic_advanced",
                "Cirurgia Ortognática Avançada",
                "Paciente",
                "Tomografia",
                "Cefalometria",
                "Registro",
                "Osteotomia",
            ),
            _flow(
                "facial_implants",
                "Implantes Faciais",
                "Paciente",
                "Tomografia",
                "Implantes Faciais",
                "Contenção",
                "Molde Bipartido",
            ),
        )
    )


def _flow(flow_id: str, name: str, *steps: str) -> FlowDefinition:
    """Create a debug flow with display labels used as fallback keys."""
    return FlowDefinition(
        flow_id=flow_id,
        name_key=name,
        version=1,
        steps=tuple(
            FlowStep(
                step_id=f"{flow_id}.step-{index}",
                name_key=step,
                module_id="debug.preview",
            )
            for index, step in enumerate(steps)
        ),
    )


def _connect_debug_signals(page: HomePage) -> None:
    """Connect every HomePage signal to a print() for debugging."""

    def _log(signal_name: str):
        def _handler(*args: object) -> None:
            print(f"[signal] {signal_name} -> {args}")

        return _handler

    page.help_requested.connect(_log("help_requested"))
    page.settings_requested.connect(_log("settings_requested"))
    page.community_requested.connect(_log("community_requested"))
    page.library_requested.connect(_log("library_requested"))
    page.news_requested.connect(_log("news_requested"))
    page.feedback_requested.connect(_log("feedback_requested"))
    page.contribute_requested.connect(_log("contribute_requested"))
    page.new_project_requested.connect(_log("new_project_requested"))
    page.manage_projects_requested.connect(_log("manage_projects_requested"))
    page.project_selected.connect(_log("project_selected"))
    page.flow_selected.connect(_log("flow_selected"))
    page.manage_flows_requested.connect(_log("manage_flows_requested"))
    page.project_open_requested.connect(_log("project_open_requested"))
    page._top_bar_widget().toggle_sidebar_requested.connect(
        lambda: print(f"[toggle] sidebar hidden={page._sidebar_widget().isHidden()}")
    )


# ----- Main ---------------------------------------------------------


def main() -> int:
    app = QApplication.instance() or QApplication([])
    app.setStyle("Fusion")

    repository = InMemoryProjectRepository()
    _seed_projects(repository)
    catalog = _build_catalog(repository)

    theme = ThemeService(
        settings=InMemorySettingsService(),
        default_mode=ThemeMode.DARK,
    )
    theme.compiler().apply(theme.compiled())
    icon_provider = UnicodeIconProvider(theme)

    page = HomePage(catalog=catalog, icon_provider=icon_provider)
    _flow_list(page)
    _connect_debug_signals(page)

    window = QMainWindow()
    window.setWindowTitle("CranioZ — Home Page debug")
    window.setCentralWidget(page)
    window.resize(1280, 800)
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
