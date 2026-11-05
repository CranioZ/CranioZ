"""Debug script: exercise the Home -> Workspace -> Home cycle.

This script is a development tool. It is NOT part of production.

It seeds the filesystem repository (if needed), opens a project via
ProjectManager, builds the ProjectContext, closes the project, and
prints each step to the console. It does not open a GUI; it is a
logic-only exercise, useful to verify that the lifecycle works before
running the application.

Run with:

    .venv\\Scripts\\python.exe scripts\\debug_full_cycle.py
"""

from __future__ import annotations

import sys

from cranioz.application.event_bus import EventBus
from cranioz.application.project.project_access_policy import (
    AllowAllProjectAccessPolicy,
)
from cranioz.application.project.project_catalog import ProjectCatalog
from cranioz.application.project.project_events import (
    ProjectClosed,
    ProjectClosing,
    ProjectOpened,
)
from cranioz.application.project.project_manager import ProjectManager
from cranioz.config.loader import ConfigurationLoader
from cranioz.infrastructure.app.app_path_resolver import AppPathResolver
from cranioz.infrastructure.project.filesystem_project_repository import (
    FilesystemProjectRepository,
)

_ACTOR = "debug-script"


def main() -> int:
    config = ConfigurationLoader().load()
    app_paths = AppPathResolver()
    app_paths.initialize(config.paths)

    repository = FilesystemProjectRepository(projects_root=app_paths.projects_root)
    catalog = ProjectCatalog(repository=repository)
    event_bus = EventBus()
    manager = ProjectManager(
        repository=repository,
        event_bus=event_bus,
        access_policy=AllowAllProjectAccessPolicy(),
    )

    event_bus.subscribe(ProjectOpened, lambda e: print(f"[event] Opened {e.project_id}"))
    event_bus.subscribe(ProjectClosing, lambda e: print(f"[event] Closing {e.project_id}"))
    event_bus.subscribe(ProjectClosed, lambda e: print(f"[event] Closed {e.project_id}"))

    summaries = catalog.list_projects()
    print(f"\nCatalog contains {len(summaries)} project(s).")
    if not summaries:
        print("Run scripts/seed_projects.py first.")
        return 1

    first = summaries[0]
    print(f"\nSelected project: {first.project_id} ({first.project_name})")

    print("\n--- Opening ---")
    context = manager.open_project(
        _ACTOR,
        first.project_id,
        workflow_id="orthognathic",
        workflow_config={},
    )
    print(f"Context project_id: {context.project_id}")
    print(f"Context patient:    {context.patient_summary.display_name}")
    print(f"Context workflow:   {context.workflow_id}")

    print("\n--- Closing ---")
    manager.close_project(_ACTOR, first.project_id)
    print(f"Is open after close: {manager.is_open(first.project_id)}")

    print("\n--- Re-opening ---")
    manager.open_project(
        _ACTOR,
        first.project_id,
        workflow_id="orthognathic",
        workflow_config={},
    )
    print(f"Is open after reopen: {manager.is_open(first.project_id)}")

    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
