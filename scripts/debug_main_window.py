"""Debug script: launch the MainWindow with fake data."""

from __future__ import annotations

import sys
from datetime import UTC, datetime

from PySide6.QtWidgets import QApplication

from cranioz.application.event_bus import EventBus
from cranioz.application.project.in_memory_project_repository import (
    InMemoryProjectRepository,
)
from cranioz.application.project.project_access_policy import (
    AllowAllProjectAccessPolicy,
)
from cranioz.application.project.project_catalog import ProjectCatalog
from cranioz.application.project.project_manager import ProjectManager
from cranioz.domain.project.project import Project
from cranioz.domain.project.project_id import ProjectId
from cranioz.domain.project.project_metadata import ProjectMetadata
from cranioz.domain.project.project_status import ProjectStatus
from cranioz.ui.editors.editor_registry import EditorRegistry
from cranioz.ui.main_window import MainWindow
from cranioz.ui.theme.service import ThemeName, ThemeService
from cranioz.ui.tools.builtin.log_tool import LogTool
from cranioz.ui.tools.builtin.toggle_tool import ToggleTool
from cranioz.ui.tools.registry.tool_registry import ToolRegistry

_FAKE_PROJECTS = [
    ("Gabriel Silva", "12652", "22/06/2025", "22/06/2026"),
    ("Camila Souza", "52269", "02/10/2025", "02/10/2026"),
    ("Lucas Ferreira", "25892", "22/07/2026", "22/07/2026"),
    ("Beatriz Oliveira", "11286", "15/07/2026", "15/07/2026"),
    ("Rafael Santos", "21358", "14/04/2025", "14/10/2025"),
]


def _parse_br_date(value: str) -> datetime:
    return datetime.strptime(value, "%d/%m/%Y").replace(tzinfo=UTC)


def _seed_projects(repository: InMemoryProjectRepository) -> None:
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


def main() -> int:
    app = QApplication.instance() or QApplication([])
    app.setStyle("Fusion")

    repository = InMemoryProjectRepository()
    _seed_projects(repository)
    catalog = ProjectCatalog(repository=repository)
    manager = ProjectManager(
        repository=repository,
        event_bus=EventBus(),
        access_policy=AllowAllProjectAccessPolicy(),
    )

    editor_registry = EditorRegistry()
    tool_registry = ToolRegistry()
    tool_registry.register("tool.log", LogTool)
    tool_registry.register("tool.toggle", ToggleTool)
    theme_service = ThemeService(theme=ThemeName.DARK)

    window = MainWindow(
        catalog=catalog,
        manager=manager,
        actor="debug",
        editor_registry=editor_registry,
        tool_registry=tool_registry,
        theme_service=theme_service,
    )

    window.home()._flow_list_widget().set_flows(
        [
            ("orthognathic_basic", "Cirurgia Ortognática"),
            ("orthognathic_advanced", "Cirurgia Ortognática Avançada"),
            ("facial_implants", "Implantes Faciais"),
        ]
    )

    # ----- Diagnostics (temporary) -----
    window.home().project_selected.connect(
        lambda pid: print(
            f"[selected] project={pid!r} current={window.home().selected_project_id()!r}"
        )
    )
    window.home().flow_selected.connect(
        lambda fid: print(
            f"[selected] flow={fid!r} current={window.home().selected_flow_id()!r}"
        )
    )

    _orig_set_ready = window.home()._start_button_widget().set_ready

    def _traced_set_ready(ready: bool) -> None:
        print(f"[start_button] set_ready({ready})")
        _orig_set_ready(ready)

    window.home()._start_button_widget().set_ready = _traced_set_ready

    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())