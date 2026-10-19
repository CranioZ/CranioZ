"""Tests for ProjectCatalog.

The catalog is a thin read-only projection over a ProjectRepository.
Tests exercise it against InMemoryProjectRepository — pure Python, no
I/O, no Qt.

Coverage:

- `list_projects` delegates to `repository.list_metadata`.
- `get_project_summary` returns the summary when present, None when
  not. It does not raise `ProjectNotFound`.
- `search_projects` is case-insensitive substring over project name
  and patient display name. Empty query returns all.
- `count`, `is_empty`, `contains` reflect the repository state.
- The catalog does not cache: mutations to the repository are
  reflected on the next call.
- A corrupted entry in the repository is invisible to the catalog
  (because `list_metadata` skips corrupted entries).
- The catalog does not expose lifecycle methods (create, delete, ...).
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from cranioz.application.project.in_memory_project_repository import (
    InMemoryProjectRepository,
)
from cranioz.application.project.project_catalog import ProjectCatalog
from cranioz.domain.project.project import Project
from cranioz.domain.project.project_id import ProjectId
from cranioz.domain.project.project_metadata import ProjectMetadata
from cranioz.domain.project.project_status import ProjectStatus
from cranioz.domain.project.project_summary import ProjectSummary

# ----- Helpers ------------------------------------------------------


def _now() -> datetime:
    return datetime(2026, 1, 1, 12, 0, tzinfo=UTC)


def _project(
    project_id: str,
    *,
    project_name: str | None = None,
    patient_display_name: str = "Gabriel Silva",
) -> Project:
    pid = ProjectId(project_id)
    return Project(
        project_id=pid,
        metadata=ProjectMetadata(
            project_id=pid,
            project_name=project_name or f"Case {project_id}",
            patient_id="pat-001",
            patient_display_name=patient_display_name,
            clinical_procedure="orthognathic",
            status=ProjectStatus.ACTIVE,
            created_at=_now(),
            updated_at=_now(),
            last_opened_at=None,
            schema_version=1,
        ),
    )


@pytest.fixture
def repository() -> InMemoryProjectRepository:
    return InMemoryProjectRepository()


@pytest.fixture
def catalog(repository: InMemoryProjectRepository) -> ProjectCatalog:
    return ProjectCatalog(repository=repository)


# ----- Construction -------------------------------------------------


def test_catalog_holds_repository(repository: InMemoryProjectRepository) -> None:
    catalog = ProjectCatalog(repository=repository)
    # Sanity: constructing does not raise; the catalog is usable.
    assert catalog.list_projects() == ()


# ----- list_projects ------------------------------------------------


def test_list_projects_empty(catalog: ProjectCatalog) -> None:
    assert catalog.list_projects() == ()


def test_list_projects_returns_all(repository: InMemoryProjectRepository) -> None:
    repository.create(_project("p-001"))
    repository.create(_project("p-002"))
    catalog = ProjectCatalog(repository=repository)

    result = catalog.list_projects()
    assert len(result) == 2
    for item in result:
        assert isinstance(item, ProjectSummary)


def test_list_projects_delegates_to_repository(
    repository: InMemoryProjectRepository,
) -> None:
    """The catalog must not maintain its own list.

    If it did, mutations after the first call would not be visible.
    """
    catalog = ProjectCatalog(repository=repository)

    repository.create(_project("p-001"))
    assert len(catalog.list_projects()) == 1

    repository.create(_project("p-002"))
    assert len(catalog.list_projects()) == 2


def test_list_projects_reflects_deletion(
    repository: InMemoryProjectRepository,
) -> None:
    repository.create(_project("p-001"))
    repository.create(_project("p-002"))
    catalog = ProjectCatalog(repository=repository)

    repository.delete(ProjectId("p-001"))
    ids = {s.project_id for s in catalog.list_projects()}
    assert ids == {ProjectId("p-002")}


# ----- get_project_summary -----------------------------------------


def test_get_project_summary_returns_summary(
    repository: InMemoryProjectRepository,
) -> None:
    repository.create(_project("p-001", project_name="Alpha"))
    catalog = ProjectCatalog(repository=repository)

    summary = catalog.get_project_summary(ProjectId("p-001"))
    assert summary is not None
    assert summary.project_id == ProjectId("p-001")
    assert summary.project_name == "Alpha"


def test_get_project_summary_returns_none_for_missing(
    catalog: ProjectCatalog,
) -> None:
    """The catalog returns None, it does not raise."""
    assert catalog.get_project_summary(ProjectId("p-999")) is None


def test_get_project_summary_does_not_raise_for_missing(
    catalog: ProjectCatalog,
) -> None:
    """Explicit: no exception escapes get_project_summary for a missing id."""
    try:
        catalog.get_project_summary(ProjectId("p-999"))
    except Exception as exc:  # noqa: BLE001
        pytest.fail(f"unexpected exception: {exc!r}")


# ----- search_projects ---------------------------------------------


def test_search_empty_query_returns_all(
    repository: InMemoryProjectRepository,
) -> None:
    repository.create(_project("p-001"))
    repository.create(_project("p-002"))
    catalog = ProjectCatalog(repository=repository)

    assert len(catalog.search_projects("")) == 2
    assert len(catalog.search_projects("   ")) == 2


def test_search_matches_project_name_case_insensitive(
    repository: InMemoryProjectRepository,
) -> None:
    repository.create(_project("p-001", project_name="Alpha Case"))
    repository.create(_project("p-002", project_name="Beta Case"))
    catalog = ProjectCatalog(repository=repository)

    result = catalog.search_projects("alpha")
    assert len(result) == 1
    assert result[0].project_name == "Alpha Case"

    result = catalog.search_projects("ALPHA")
    assert len(result) == 1


def test_search_matches_patient_display_name(
    repository: InMemoryProjectRepository,
) -> None:
    repository.create(
        _project("p-001", project_name="A", patient_display_name="Maria Souza")
    )
    repository.create(
        _project("p-002", project_name="B", patient_display_name="Gabriel Silva")
    )
    catalog = ProjectCatalog(repository=repository)

    result = catalog.search_projects("maria")
    assert len(result) == 1
    assert result[0].patient_display_name == "Maria Souza"


def test_search_substring_matches(
    repository: InMemoryProjectRepository,
) -> None:
    """Substring, not prefix. 'ognath' matches 'Orthognathic'."""
    repository.create(_project("p-001", project_name="Orthognathic Case"))
    catalog = ProjectCatalog(repository=repository)

    assert len(catalog.search_projects("ognath")) == 1


def test_search_no_match_returns_empty(
    catalog: ProjectCatalog,
) -> None:
    assert catalog.search_projects("zzz") == ()


def test_search_does_not_use_regex(
    repository: InMemoryProjectRepository,
) -> None:
    """A regex-looking query is treated literally.

    If the catalog used regex, '.' would match any character. Here it
    must match only a literal dot. The project name contains 'a.b',
    so 'a.b' matches but 'axb' does not.
    """
    repository.create(_project("p-001", project_name="a.b"))
    catalog = ProjectCatalog(repository=repository)

    assert len(catalog.search_projects("a.b")) == 1
    assert len(catalog.search_projects("axb")) == 0


# ----- count / is_empty / contains ---------------------------------


def test_count_reflects_repository(catalog: ProjectCatalog, repository) -> None:
    assert catalog.count() == 0
    repository.create(_project("p-001"))
    assert catalog.count() == 1
    repository.create(_project("p-002"))
    assert catalog.count() == 2


def test_is_empty_reflects_repository(catalog: ProjectCatalog, repository) -> None:
    assert catalog.is_empty() is True
    repository.create(_project("p-001"))
    assert catalog.is_empty() is False


def test_contains_true_for_existing(catalog: ProjectCatalog, repository) -> None:
    repository.create(_project("p-001"))
    assert catalog.contains(ProjectId("p-001")) is True


def test_contains_false_for_missing(catalog: ProjectCatalog) -> None:
    assert catalog.contains(ProjectId("p-999")) is False


# ----- Corrupted entries -------------------------------------------


def test_corrupted_entries_are_invisible(
    repository: InMemoryProjectRepository,
) -> None:
    """The catalog relies on list_metadata, which skips corrupted entries."""
    repository.create(_project("p-ok"))
    repository.create(_project("p-bad"))
    repository._mark_corrupted(ProjectId("p-bad"))
    catalog = ProjectCatalog(repository=repository)

    assert catalog.count() == 1
    assert catalog.contains(ProjectId("p-ok")) is True
    assert catalog.contains(ProjectId("p-bad")) is False


# ----- No lifecycle methods ----------------------------------------


def test_catalog_has_no_create_method(catalog: ProjectCatalog) -> None:
    """The catalog is read-only. It must not expose create()."""
    assert not hasattr(catalog, "create")


def test_catalog_has_no_update_method(catalog: ProjectCatalog) -> None:
    assert not hasattr(catalog, "update")


def test_catalog_has_no_delete_method(catalog: ProjectCatalog) -> None:
    assert not hasattr(catalog, "delete")


def test_catalog_has_no_open_method(catalog: ProjectCatalog) -> None:
    assert not hasattr(catalog, "open_project")
