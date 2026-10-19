"""Contract tests for ProjectRepository.

These tests define the expected behavior of *any* ProjectRepository
implementation. The same suite is run against:

- `InMemoryProjectRepository` (this file).
- `FilesystemProjectRepository` (Peça 7.3, in a separate file that
  imports the same fixtures and test bodies).

The strategy is the classic "contract test" pattern: the test suite
is the specification, and every implementation must pass it. If a new
implementation is added, it must be accompanied by its own parameterized
version of this file — not a re-implementation of the same tests.

The tests do not depend on Qt, filesystem, or infrastructure.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from cranioz.application.project.in_memory_project_repository import (
    InMemoryProjectRepository,
)
from cranioz.application.project.project_errors import (
    ProjectAlreadyExists,
    ProjectCorrupted,
    ProjectNotFound,
    ProjectRepositoryError,
)
from cranioz.application.project.project_repository import ProjectRepository
from cranioz.domain.project.project import Project
from cranioz.domain.project.project_id import ProjectId
from cranioz.domain.project.project_metadata import ProjectMetadata
from cranioz.domain.project.project_status import ProjectStatus
from cranioz.domain.project.project_summary import ProjectSummary

# ----- Fixtures -----------------------------------------------------


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
        schema_version=1,
    )


def _project(project_id: str = "p-001") -> Project:
    pid = ProjectId(project_id)
    return Project(project_id=pid, metadata=_metadata(project_id))


@pytest.fixture
def repo() -> ProjectRepository:
    """Fresh repository per test."""
    return InMemoryProjectRepository()


# ----- Sanity --------------------------------------------------------


def test_in_memory_repository_satisfies_protocol(repo: ProjectRepository) -> None:
    """Sanity: the in-memory repository satisfies the Protocol at runtime."""
    assert isinstance(repo, ProjectRepository)


def test_new_repository_is_empty(repo: ProjectRepository) -> None:
    assert repo.list_metadata() == ()
    assert repo.list_ids() == ()


# ----- create / get round-trip ---------------------------------------


def test_create_then_get_returns_same_project(repo: ProjectRepository) -> None:
    project = _project("p-001")
    repo.create(project)

    loaded = repo.get(ProjectId("p-001"))
    assert loaded is project


def test_create_then_exists_is_true(repo: ProjectRepository) -> None:
    repo.create(_project("p-001"))
    assert repo.exists(ProjectId("p-001")) is True


def test_exists_false_for_missing_project(repo: ProjectRepository) -> None:
    assert repo.exists(ProjectId("p-999")) is False


def test_get_missing_raises_project_not_found(repo: ProjectRepository) -> None:
    with pytest.raises(ProjectNotFound) as exc_info:
        repo.get(ProjectId("p-999"))
    assert exc_info.value.project_id == ProjectId("p-999")
    assert "p-999" in str(exc_info.value)


def test_create_duplicate_raises_project_already_exists(
    repo: ProjectRepository,
) -> None:
    repo.create(_project("p-001"))
    with pytest.raises(ProjectAlreadyExists) as exc_info:
        repo.create(_project("p-001"))
    assert exc_info.value.project_id == ProjectId("p-001")


def test_create_duplicate_does_not_overwrite(repo: ProjectRepository) -> None:
    first = _project("p-001")
    second = _project("p-001")
    repo.create(first)

    with pytest.raises(ProjectAlreadyExists):
        repo.create(second)

    # The original is untouched.
    assert repo.get(ProjectId("p-001")) is first


# ----- update --------------------------------------------------------


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
    assert loaded is updated
    assert loaded.metadata.project_name == "Renamed"


def test_update_missing_raises_project_not_found(repo: ProjectRepository) -> None:
    with pytest.raises(ProjectNotFound):
        repo.update(_project("p-999"))


# ----- delete --------------------------------------------------------


def test_delete_removes_project(repo: ProjectRepository) -> None:
    repo.create(_project("p-001"))
    repo.delete(ProjectId("p-001"))

    assert repo.exists(ProjectId("p-001")) is False
    with pytest.raises(ProjectNotFound):
        repo.get(ProjectId("p-001"))


def test_delete_missing_raises_project_not_found(repo: ProjectRepository) -> None:
    """The contract requires explicit ProjectNotFound, not a silent no-op.

    Rationale (project_repository.py docstring): the Project Manager
    needs to distinguish "deleted now" from "already gone" to publish
    the right lifecycle event. Idempotent callers check `exists` first.
    """
    with pytest.raises(ProjectNotFound):
        repo.delete(ProjectId("p-999"))


# ----- list_metadata -------------------------------------------------


def test_list_metadata_returns_summaries_not_projects(
    repo: ProjectRepository,
) -> None:
    repo.create(_project("p-001"))
    repo.create(_project("p-002"))

    result = repo.list_metadata()

    assert len(result) == 2
    for item in result:
        assert isinstance(item, ProjectSummary)
        # Sanity: no Project leaks through.
        assert not isinstance(item, Project)


def test_list_metadata_reflects_current_state(repo: ProjectRepository) -> None:
    repo.create(_project("p-001"))
    repo.create(_project("p-002"))

    ids = {summary.project_id for summary in repo.list_metadata()}
    assert ids == {ProjectId("p-001"), ProjectId("p-002")}

    repo.delete(ProjectId("p-001"))
    ids = {summary.project_id for summary in repo.list_metadata()}
    assert ids == {ProjectId("p-002")}


def test_list_metadata_order_is_unspecified(repo: ProjectRepository) -> None:
    """The contract documents that order is not guaranteed.

    This test documents that the returned order matches insertion for
    the current in-memory implementation, but it explicitly checks the
    *set*, not the *sequence*, so that a future implementation may
    legitimately return a different order.
    """
    repo.create(_project("p-b"))
    repo.create(_project("p-a"))

    summaries = repo.list_metadata()
    assert {s.project_id for s in summaries} == {
        ProjectId("p-a"),
        ProjectId("p-b"),
    }


# ----- list_ids ------------------------------------------------------


def test_list_ids_matches_created_ids(repo: ProjectRepository) -> None:
    repo.create(_project("p-001"))
    repo.create(_project("p-002"))

    ids = set(repo.list_ids())
    assert ids == {ProjectId("p-001"), ProjectId("p-002")}


def test_list_ids_empty_when_nothing_created(repo: ProjectRepository) -> None:
    assert repo.list_ids() == ()


# ----- error hierarchy -----------------------------------------------


def test_all_repository_errors_share_a_base() -> None:
    """Every repository error derives from ProjectRepositoryError.

    This lets the Project Manager catch the whole family with one
    `except ProjectRepositoryError:` and still discriminate more
    specific failures by subclass.
    """
    for cls in (
        ProjectNotFound,
        ProjectAlreadyExists,
        ProjectCorrupted,
    ):
        assert issubclass(cls, ProjectRepositoryError)


def test_project_not_found_is_not_a_key_error() -> None:
    """The error is domain-aware; it must not be caught by `except KeyError`.

    The repository uses dicts internally, so a naive implementation
    might raise `KeyError`. The contract forbids this. This test
    documents the boundary.
    """
    assert not issubclass(ProjectNotFound, KeyError)


# ----- ProjectCorrupted (test hook) ----------------------------------


def test_marked_corrupted_project_raises_on_get(
    repo: ProjectRepository,
) -> None:
    """The in-memory repository supports a test-only corruption hook.

    This lets tests exercise the `ProjectCorrupted` path without a
    filesystem. The FilesystemProjectRepository (Peça 7.3) will
    produce the same error through a real corrupted file.
    """
    assert isinstance(repo, InMemoryProjectRepository)
    repo.create(_project("p-001"))
    repo._mark_corrupted(ProjectId("p-001"))

    with pytest.raises(ProjectCorrupted) as exc_info:
        repo.get(ProjectId("p-001"))
    assert exc_info.value.project_id == ProjectId("p-001")


def test_list_metadata_skips_corrupted_entries(
    repo: ProjectRepository,
) -> None:
    """A corrupted project does not hide the others from the listing.

    The read model is resilient: `list_metadata` returns what it can
    read. A corrupt entry is the Project Manager's problem to surface
    (Peça 7.5), not something that should crash the Home Page.
    """
    assert isinstance(repo, InMemoryProjectRepository)
    repo.create(_project("p-ok"))
    repo.create(_project("p-bad"))
    repo._mark_corrupted(ProjectId("p-bad"))

    summaries = repo.list_metadata()
    assert {s.project_id for s in summaries} == {ProjectId("p-ok")}


def test_delete_clears_corruption_marker(repo: ProjectRepository) -> None:
    """Deleting a corrupted project removes the marker too.

    Otherwise `_corrupted` would grow unbounded across a long test
    session. The set is an implementation detail, but its cleanup is
    observable through behavior: after delete, recreating the id must
    succeed and `get` must return the new project.
    """
    assert isinstance(repo, InMemoryProjectRepository)
    repo.create(_project("p-001"))
    repo._mark_corrupted(ProjectId("p-001"))
    repo.delete(ProjectId("p-001"))

    repo.create(_project("p-001"))
    assert repo.get(ProjectId("p-001")).project_id == ProjectId("p-001")


# ----- Type narrowing ------------------------------------------------


def test_repository_error_factory_helpers() -> None:
    """Sanity: constructing each error produces a usable instance.

    Ensures the `project_id` attribute is always present, so logs can
    rely on it without `getattr(..., None)` gymnastics.
    """
    not_found = ProjectNotFound("x", project_id=ProjectId("p-1"))
    assert not_found.project_id == ProjectId("p-1")

    already = ProjectAlreadyExists("x", project_id=ProjectId("p-2"))
    assert already.project_id == ProjectId("p-2")

    corrupted = ProjectCorrupted("x", project_id=ProjectId("p-3"))
    assert corrupted.project_id == ProjectId("p-3")

    # The attribute is optional.
    no_id = ProjectNotFound("x")
    assert no_id.project_id is None
