"""FilesystemProjectRepository — contract + filesystem-specific tests.

This file runs the *same contract* defined in Peça 7.1 against the
filesystem adapter. If the adapter honors the contract, the same test
bodies that pass for `InMemoryProjectRepository` must pass here.

Additional tests cover filesystem-specific behavior:

- `create` leaves no partial directory when project.json cannot be
  written.
- `exists` is keyed on `project.json`, not the directory (so a stray
  directory without project.json is not a project).
- `delete` removes only `project.json`; other files in the directory
  are left untouched (they belong to other persistence layers).
- `list_metadata` skips corrupted entries (a malformed project.json
  in one directory does not break the listing).
- `list_ids` skips non-project directories.

Qt-free, I/O is real but confined to `tmp_path`.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from cranioz.application.project.project_errors import (
    ProjectAlreadyExists,
    ProjectCorrupted,
    ProjectNotFound,
)
from cranioz.application.project.project_repository import ProjectRepository
from cranioz.domain.project.project import Project
from cranioz.domain.project.project_id import ProjectId
from cranioz.domain.project.project_metadata import ProjectMetadata
from cranioz.domain.project.project_status import ProjectStatus
from cranioz.domain.project.project_summary import ProjectSummary
from cranioz.infrastructure.project.filesystem_project_repository import (
    FilesystemProjectRepository,
)
from cranioz.infrastructure.project.project_serialization import (
    CURRENT_SCHEMA_VERSION,
    project_to_dict,
)

# ----- Helpers ------------------------------------------------------


def _now() -> datetime:
    return datetime(2026, 1, 1, 12, 0, tzinfo=UTC)


def _metadata(project_id: str = "p-001") -> ProjectMetadata:
    return ProjectMetadata(
        project_id=ProjectId(project_id),
        project_name=f"Case {project_id}",
        patient_id="pat-001",
        patient_display_name="Gabriel Silva",
        clinical_procedure="orthognathic",
        status=ProjectStatus.ACTIVE,
        created_at=_now(),
        updated_at=_now(),
        last_opened_at=None,
        schema_version=CURRENT_SCHEMA_VERSION,
    )


def _project(project_id: str = "p-001") -> Project:
    pid = ProjectId(project_id)
    return Project(project_id=pid, metadata=_metadata(project_id))


@pytest.fixture
def root(tmp_path: Path) -> Path:
    """Isolated projects root for the test."""
    projects = tmp_path / "projects"
    projects.mkdir()
    return projects


@pytest.fixture
def repo(root: Path) -> ProjectRepository:
    return FilesystemProjectRepository(projects_root=root)


# ====================================================================
# Contract — same bodies as Peça 7.1
# ====================================================================


def test_satisfies_protocol(repo: ProjectRepository) -> None:
    assert isinstance(repo, ProjectRepository)


def test_new_repository_is_empty(repo: ProjectRepository) -> None:
    assert repo.list_metadata() == ()
    assert repo.list_ids() == ()


def test_create_then_get_returns_project(repo: ProjectRepository) -> None:
    project = _project("p-001")
    repo.create(project)
    loaded = repo.get(ProjectId("p-001"))
    assert loaded.project_id == project.project_id
    assert loaded.metadata == project.metadata


def test_create_then_exists_is_true(repo: ProjectRepository) -> None:
    repo.create(_project("p-001"))
    assert repo.exists(ProjectId("p-001")) is True


def test_exists_false_for_missing_project(repo: ProjectRepository) -> None:
    assert repo.exists(ProjectId("p-999")) is False


def test_get_missing_raises_project_not_found(repo: ProjectRepository) -> None:
    with pytest.raises(ProjectNotFound) as exc_info:
        repo.get(ProjectId("p-999"))
    assert exc_info.value.project_id == ProjectId("p-999")


def test_create_duplicate_raises_project_already_exists(
    repo: ProjectRepository,
) -> None:
    repo.create(_project("p-001"))
    with pytest.raises(ProjectAlreadyExists) as exc_info:
        repo.create(_project("p-001"))
    assert exc_info.value.project_id == ProjectId("p-001")


def test_create_duplicate_does_not_overwrite(repo: ProjectRepository) -> None:
    first = _project("p-001")
    repo.create(first)
    with pytest.raises(ProjectAlreadyExists):
        repo.create(_project("p-001"))

    loaded = repo.get(ProjectId("p-001"))
    assert loaded.metadata == first.metadata


def test_update_replaces_stored_instance(repo: ProjectRepository) -> None:
    original = _project("p-001")
    repo.create(original)

    later = datetime(2026, 2, 1, tzinfo=UTC)
    updated = Project(
        project_id=original.project_id,
        metadata=original.metadata.with_name("Renamed", now=later),
    )
    repo.update(updated)

    loaded = repo.get(ProjectId("p-001"))
    assert loaded.metadata.project_name == "Renamed"


def test_update_missing_raises_project_not_found(repo: ProjectRepository) -> None:
    with pytest.raises(ProjectNotFound):
        repo.update(_project("p-999"))


def test_delete_removes_project(repo: ProjectRepository) -> None:
    repo.create(_project("p-001"))
    repo.delete(ProjectId("p-001"))
    assert repo.exists(ProjectId("p-001")) is False
    with pytest.raises(ProjectNotFound):
        repo.get(ProjectId("p-001"))


def test_delete_missing_raises_project_not_found(repo: ProjectRepository) -> None:
    with pytest.raises(ProjectNotFound):
        repo.delete(ProjectId("p-999"))


def test_list_metadata_returns_summaries(repo: ProjectRepository) -> None:
    repo.create(_project("p-001"))
    repo.create(_project("p-002"))

    result = repo.list_metadata()
    assert len(result) == 2
    for item in result:
        assert isinstance(item, ProjectSummary)


def test_list_metadata_reflects_current_state(repo: ProjectRepository) -> None:
    repo.create(_project("p-001"))
    repo.create(_project("p-002"))

    assert {s.project_id for s in repo.list_metadata()} == {
        ProjectId("p-001"),
        ProjectId("p-002"),
    }

    repo.delete(ProjectId("p-001"))
    assert {s.project_id for s in repo.list_metadata()} == {ProjectId("p-002")}


def test_list_ids_matches_created_ids(repo: ProjectRepository) -> None:
    repo.create(_project("p-001"))
    repo.create(_project("p-002"))
    assert set(repo.list_ids()) == {ProjectId("p-001"), ProjectId("p-002")}


def test_list_ids_empty_when_nothing_created(repo: ProjectRepository) -> None:
    assert repo.list_ids() == ()


# ====================================================================
# Filesystem-specific behavior
# ====================================================================


def test_create_writes_project_json(repo: ProjectRepository, root: Path) -> None:
    project = _project("p-001")
    repo.create(project)

    project_json = root / "p-001" / "project.json"
    assert project_json.is_file()
    data = json.loads(project_json.read_text(encoding="utf-8"))
    assert data == project_to_dict(project)


def test_create_does_not_write_patient_record(repo: ProjectRepository, root: Path) -> None:
    """patient_record.json belongs to the Patient persistence layer."""
    repo.create(_project("p-001"))
    assert not (root / "p-001" / "patient_record.json").exists()


def test_exists_is_false_for_directory_without_project_json(
    repo: ProjectRepository, root: Path
) -> None:
    """A stray directory is not a project.

    This can happen if a crash leaves a directory behind, or if
    another layer (e.g. patient persistence) created it first.
    """
    (root / "stray").mkdir()
    assert repo.exists(ProjectId("stray")) is False


def test_delete_removes_only_project_json(repo: ProjectRepository, root: Path) -> None:
    """Other files in the directory belong to other layers."""
    repo.create(_project("p-001"))
    # Simulate a patient record written by another layer.
    patient_record = root / "p-001" / "patient_record.json"
    patient_record.write_text("{}", encoding="utf-8")

    repo.delete(ProjectId("p-001"))

    assert not (root / "p-001" / "project.json").exists()
    assert patient_record.is_file()  # untouched


def test_list_ids_skips_non_project_directories(repo: ProjectRepository, root: Path) -> None:
    repo.create(_project("p-001"))
    (root / "stray").mkdir()  # no project.json

    assert repo.list_ids() == (ProjectId("p-001"),)


def test_list_ids_skips_non_directory_entries(repo: ProjectRepository, root: Path) -> None:
    repo.create(_project("p-001"))
    (root / "file.txt").write_text("x", encoding="utf-8")

    assert repo.list_ids() == (ProjectId("p-001"),)


def test_list_ids_includes_all_project_directories(repo: ProjectRepository, root: Path) -> None:
    """Any directory with a project.json is a project, regardless of name.

    The `ProjectId` value object itself does not reject path-unsafe
    names; that validation belongs to `ProjectPathResolver` at the
    point of use. `list_ids` reports what is on disk.
    """
    repo.create(_project("p-001"))
    repo.create(_project("weird.name"))

    ids = set(repo.list_ids())
    assert ProjectId("p-001") in ids
    assert ProjectId("weird.name") in ids


def test_get_corrupted_json_raises_project_corrupted(repo: ProjectRepository, root: Path) -> None:
    repo.create(_project("p-001"))
    (root / "p-001" / "project.json").write_text("{not-json", encoding="utf-8")

    with pytest.raises(ProjectCorrupted):
        repo.get(ProjectId("p-001"))


def test_get_non_object_json_raises_project_corrupted(repo: ProjectRepository, root: Path) -> None:
    repo.create(_project("p-001"))
    (root / "p-001" / "project.json").write_text("[1, 2, 3]", encoding="utf-8")

    with pytest.raises(ProjectCorrupted):
        repo.get(ProjectId("p-001"))


def test_get_schema_mismatch_raises_project_corrupted(repo: ProjectRepository, root: Path) -> None:
    repo.create(_project("p-001"))
    project_json = root / "p-001" / "project.json"
    data = json.loads(project_json.read_text(encoding="utf-8"))
    data["schema_version"] = 99
    project_json.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(ProjectCorrupted):
        repo.get(ProjectId("p-001"))


def test_list_metadata_skips_corrupted_entries(repo: ProjectRepository, root: Path) -> None:
    """One corrupted project does not break the listing."""
