"""Seed the filesystem repository with fake projects for manual testing.

This script is a development tool. It is NOT part of production.

It creates 5 fake projects in the CranioZ projects root, using the
same names as ``scripts/debug_home_page.py``. It is idempotent: a
project whose id already exists is skipped, so the script can be run
multiple times without error.

Run with:

    .venv\\Scripts\\python.exe scripts\\seed_projects.py

After running, ``python -m cranioz`` will list these projects in the
Home Page's ProjectTable.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path

from cranioz.application.event_bus import EventBus
from cranioz.application.project.project_access_policy import (
    AllowAllProjectAccessPolicy,
)
from cranioz.application.project.project_manager import ProjectManager
from cranioz.config.loader import ConfigurationLoader
from cranioz.domain.patient.value_objects.patient_id import PatientId
from cranioz.domain.project.project_id import ProjectId
from cranioz.infrastructure.app.app_path_resolver import AppPathResolver
from cranioz.infrastructure.project.filesystem_project_repository import (
    FilesystemProjectRepository,
)

# name, patient_id
_FAKE_PROJECTS = [
    ("Gabriel Silva", "12652"),
    ("Camila Souza", "52269"),
    ("Lucas Ferreira", "25892"),
    ("Beatriz Oliveira", "11286"),
    ("Rafael Santos", "21358"),
]

_SEED_ACTOR = "seed-script"


def _projects_root() -> Path:
    """Resolve the projects root using the same logic as the application."""
    config = ConfigurationLoader().load()
    app_paths = AppPathResolver()
    app_paths.initialize(config.paths)
    return app_paths.projects_root


def main() -> int:
    root = _projects_root()
    print(f"Projects root: {root}")

    repository = FilesystemProjectRepository(projects_root=root)
    manager = ProjectManager(
        repository=repository,
        event_bus=EventBus(),
        access_policy=AllowAllProjectAccessPolicy(),
    )

    created = 0
    skipped = 0
    for name, patient_id in _FAKE_PROJECTS:
        pid = ProjectId(patient_id)
        if repository.exists(pid):
            print(f"  skip   {name!r} ({patient_id}) — already exists")
            skipped += 1
            continue

        manager.create_project(
            _SEED_ACTOR,
            project_id=pid,
            project_name=f"Caso {name}",
            patient_id=PatientId(patient_id),
            patient_display_name=name,
            clinical_procedure="orthognathic",
        )
        print(f"  create {name!r} ({patient_id})")
        created += 1

    print(f"\nDone. Created: {created}, skipped: {skipped}.")
    if created:
        print("Restart the application to see the projects in the Home Page.")
    return 0


if __name__ == "__main__":
    sys.exit(main())