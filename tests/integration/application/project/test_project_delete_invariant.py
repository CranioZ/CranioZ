"""Sprint J — invariant: deleting a project removes only project.json.

The FilesystemProjectRepository owns exactly one file (project.json).
Sibling files belong to other persistence layers and must survive a
project deletion. This invariant protects:

- External Reference mode DICOM (Phase 4, storage/export §4.3.5):
  source data referenced by the project is never removed by delete.
- patient_record.json (owned by the Patient persistence layer).
- Future per-project assets (scene.json, imaging/, models/) whose
  owners are introduced in Phase 4.

See:
- FilesystemProjectRepository module docstring (design rule: "delete
  removes only project.json").
- implementation_plan.md §6 Phase 3, Sprint J ("External source data
  is never removed by project deletion").
- project.md §10 ("The Home Page must never delete project folders or
  files directly").
"""

from __future__ import annotations

from pathlib import Path

from cranioz.application.event_bus import EventBus
from cranioz.application.project.access_policy import AllowAllProjectAccessPolicy
from cranioz.application.project.manager import ProjectManager
from cranioz.domain.patient.value_objects.patient_id import PatientId
from cranioz.domain.project.project_id import ProjectId
from cranioz.infrastructure.project.filesystem_project_repository import (
    FilesystemProjectRepository,
)


def _seed_sibling_files(project_dir: Path) -> dict[Path, bytes]:
    """Create files a future Phase 4 owner (or External Reference) would own.

    The exact names are not yet fixed by Phase 4; these are
    representative of the layout documented in project.md §11 and
    anticipated by the storage/export deliverable.
    """
    siblings = {
        project_dir / "patient_record.json": b'{"patient": "external"}',
        project_dir / "scene.json": b'{"scene": "future"}',
        project_dir / "imaging" / "ct" / "slice.dcm": b"\x00" * 128,
        project_dir / "models" / "maxilla.stl": b"solid maxilla\nendsolid\n",
    }
    for path, content in siblings.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    return siblings


def _create_project(
    manager: ProjectManager,
    *,
    project_id: str = "p-001",
) -> None:
    manager.create_project(
        "test-actor",
        project_id=ProjectId(project_id),
        project_name=f"Case {project_id}",
        patient_id=PatientId("pat-001"),
        patient_display_name="João Silva",
        clinical_procedure="orthognathic",
    )


class TestDeleteInvariant:
    def test_delete_project_removes_only_project_json(self, tmp_path: Path) -> None:
        """Delete removes project.json; every sibling survives byte-identical."""
        repository = FilesystemProjectRepository(projects_root=tmp_path)
        manager = ProjectManager(
            repository=repository,
            event_bus=EventBus(),
            access_policy=AllowAllProjectAccessPolicy(),
        )
        _create_project(manager)

        project_dir = tmp_path / "p-001"
        project_json = project_dir / "project.json"
        assert project_json.is_file()

        siblings = _seed_sibling_files(project_dir)

        manager.delete_project("test-actor", ProjectId("p-001"))

        assert not project_json.exists(), "project.json must be removed"
        for path, original in siblings.items():
            assert path.is_file(), f"sibling {path} was removed"
            assert path.read_bytes() == original, f"sibling {path} was modified"

    def test_delete_project_leaves_parent_project_directory(self, tmp_path: Path) -> None:
        """The project directory itself survives; only project.json is removed.

        This documents the current boundary: a "delete" is "remove the
        project's discoverable marker", not "rmdir the directory". If
        Phase 4 decides otherwise, this test fails and forces a decision
        (and an ADR, per implementation_plan.md §8.10).
        """
        repository = FilesystemProjectRepository(projects_root=tmp_path)
        manager = ProjectManager(
            repository=repository,
            event_bus=EventBus(),
            access_policy=AllowAllProjectAccessPolicy(),
        )
        _create_project(manager)

        project_dir = tmp_path / "p-001"
        _seed_sibling_files(project_dir)

        manager.delete_project("test-actor", ProjectId("p-001"))

        assert project_dir.is_dir()
        # Sibling survives in place.
        assert (project_dir / "patient_record.json").is_file()
