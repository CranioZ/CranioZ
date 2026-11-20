"""Tests for ProjectCatalog.

Under ADR-0016, the catalog consumes a `ProjectIndex`, not a
`ProjectRepository`. The index is maintained by a
`ProjectIndexSynchronizer` and wrapped by a `SynchronizedProjectIndex`,
which guarantees freshness before every read.

The tests below construct the full chain (repository → index →
synchronizer → catalog) because the catalog must be exercised against
the same wiring used by the composition root. A bare
`InMemoryProjectIndex` would not prove that the catalog reads through
the synchronized decorator; it would only prove that it calls
`list_summaries()` and friends.

Two tests are intentionally **not** present here:

- `test_catalog_holds_repository` was removed: the catalog no longer
  holds the repository (ADR-0016 §6.3). The negative invariant is
  covered by `test_project_catalog_uses_index.py::test_catalog_does_not_hold_repository`.
- `test_list_projects_delegates_to_repository` was renamed to
  `test_list_projects_delegates_to_index`, because the catalog's read
  source is the index, not the repository.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from cranioz.application.event_bus import EventBus
from cranioz.application.project.access_policy import AllowAllProjectAccessPolicy
from cranioz.application.project.catalog import ProjectCatalog
from cranioz.application.project.in_memory_index import InMemoryProjectIndex
from cranioz.application.project.in_memory_repository import (
    InMemoryProjectRepository,
)
from cranioz.application.project.index_synchronizer import (
    ProjectIndexSynchronizer,
    SynchronizedProjectIndex,
)
from cranioz.application.project.manager import ProjectManager
from cranioz.domain.patient.value_objects.patient_id import PatientId
from cranioz.domain.project.project import Project
from cranioz.domain.project.project_id import ProjectId
from cranioz.domain.project.project_metadata import ProjectMetadata
from cranioz.domain.project.project_status import ProjectStatus

# ----- Helpers ------------------------------------------------------


def _now() -> datetime:
    return datetime(2026, 1, 1, 12, 0, tzinfo=UTC)


def _project(
    project_id: str,
    *,
    project_name: str = "Case 001",
    patient_display_name: str = "Gabriel Silva",
) -> Project:
    pid = ProjectId(project_id)
    metadata = ProjectMetadata(
        project_id=pid,
        project_name=project_name,
        patient_id="pat-001",
        patient_display_name=patient_display_name,
        clinical_procedure="orthognathic",
        status=ProjectStatus.ACTIVE,
        created_at=_now(),
        updated_at=_now(),
        last_opened_at=None,
        schema_version=1,
    )
    return Project(project_id=pid, metadata=metadata)


def _build_catalog(
    repository: InMemoryProjectRepository,
    event_bus: EventBus,
) -> ProjectCatalog:
    """Build the catalog through the same wiring as the composition root."""
    index = InMemoryProjectIndex()
    synchronizer = ProjectIndexSynchronizer(index, repository, event_bus)
    synchronizer.start()
    return ProjectCatalog(SynchronizedProjectIndex(index, synchronizer))


# ----- Fixtures -----------------------------------------------------


@pytest.fixture
def event_bus() -> EventBus:
    return EventBus()


@pytest.fixture
def repository() -> InMemoryProjectRepository:
    return InMemoryProjectRepository()


@pytest.fixture
def catalog(
    repository: InMemoryProjectRepository,
    event_bus: EventBus,
) -> ProjectCatalog:
    """Catalog over an empty repository.

    Tests that need projects must create them **before** this fixture
    runs, via a test-specific setup. Use `_build_catalog` directly
    when you need to control the population order.
    """
    return _build_catalog(repository, event_bus)


# ----- Listing ------------------------------------------------------


def test_list_projects_empty(catalog: ProjectCatalog) -> None:
    assert catalog.list_projects() == ()
    assert catalog.count() == 0
    assert catalog.is_empty() is True


def test_list_projects_returns_all(
    repository: InMemoryProjectRepository,
    event_bus: EventBus,
) -> None:
    repository.create(_project("p-001"))
    repository.create(_project("p-002"))
    catalog = _build_catalog(repository, event_bus)

    result = catalog.list_projects()
    assert len(result) == 2
    ids = {summary.project_id for summary in result}
    assert ids == {ProjectId("p-001"), ProjectId("p-002")}


def test_list_projects_delegates_to_index(
    repository: InMemoryProjectRepository,
    event_bus: EventBus,
) -> None:
    """The catalog must not maintain its own list.

    If it did, mutations after the first query would not be visible.
    The catalog reads from the index; the index is refreshed by the
    synchronizer on lifecycle events.
    """
    repository.create(_project("p-001"))
    catalog = _build_catalog(repository, event_bus)

    first = catalog.list_projects()
    assert len(first) == 1

    # Create a second project through the ProjectManager so the
    # ProjectCreated event reaches the synchronizer and the index is
    # updated. A direct repository.create would NOT update the index
    # (ADR-0016 §3.2: external mutations are not detected
    # automatically).
    manager = ProjectManager(
        repository=repository,
        event_bus=event_bus,
        access_policy=AllowAllProjectAccessPolicy(),
    )
    manager.create_project(
        "actor",
        project_id=ProjectId("p-002"),
        project_name="Second",
        patient_id=PatientId("pat-002"),
        patient_display_name="Maria Souza",
        clinical_procedure="orthognathic",
    )

    second = catalog.list_projects()
    assert len(second) == 2


# ----- Lookup -------------------------------------------------------


def test_get_project_summary_returns_summary(
    repository: InMemoryProjectRepository,
    event_bus: EventBus,
) -> None:
    repository.create(_project("p-001", project_name="Alpha"))
    catalog = _build_catalog(repository, event_bus)

    summary = catalog.get_project_summary(ProjectId("p-001"))
    assert summary is not None
    assert summary.project_name == "Alpha"


def test_get_project_summary_returns_none_for_missing(
    catalog: ProjectCatalog,
) -> None:
    assert catalog.get_project_summary(ProjectId("missing")) is None


def test_get_project_summary_does_not_raise_for_missing(
    catalog: ProjectCatalog,
) -> None:
    """The catalog returns None for unknown ids; it never raises.

    For discovery purposes, "not in the catalog" and "not persisted"
    are equivalent (see the ProjectCatalog docstring).
    """
    # No exception, regardless of whether the id was ever persisted.
    assert catalog.get_project_summary(ProjectId("never-existed")) is None


# ----- Search -------------------------------------------------------


def test_search_empty_query_returns_all(
    repository: InMemoryProjectRepository,
    event_bus: EventBus,
) -> None:
    repository.create(_project("p-001"))
    repository.create(_project("p-002"))
    catalog = _build_catalog(repository, event_bus)

    assert len(catalog.search_projects("")) == 2
    assert len(catalog.search_projects("   ")) == 2


def test_search_no_match_returns_empty(
    repository: InMemoryProjectRepository,
    event_bus: EventBus,
) -> None:
    repository.create(_project("p-001", project_name="Alpha"))
    catalog = _build_catalog(repository, event_bus)

    assert catalog.search_projects("zzz") == ()


def test_search_matches_project_name_case_insensitive(
    repository: InMemoryProjectRepository,
    event_bus: EventBus,
) -> None:
    repository.create(_project("p-001", project_name="Alpha Case"))
    repository.create(_project("p-002", project_name="Beta Case"))
    catalog = _build_catalog(repository, event_bus)

    result = catalog.search_projects("ALPHA")
    assert len(result) == 1
    assert result[0].project_name == "Alpha Case"


def test_search_matches_patient_display_name(
    repository: InMemoryProjectRepository,
    event_bus: EventBus,
) -> None:
    repository.create(_project("p-001", project_name="A", patient_display_name="Maria Souza"))
    repository.create(_project("p-002", project_name="B", patient_display_name="Gabriel Silva"))
    catalog = _build_catalog(repository, event_bus)

    result = catalog.search_projects("maria")
    assert len(result) == 1
    assert result[0].patient_display_name == "Maria Souza"


def test_search_substring_matches(
    repository: InMemoryProjectRepository,
    event_bus: EventBus,
) -> None:
    """Substring, not prefix. 'ognath' matches 'Orthognathic'."""
    repository.create(_project("p-001", project_name="Orthognathic Case"))
    catalog = _build_catalog(repository, event_bus)

    assert len(catalog.search_projects("ognath")) == 1


def test_search_does_not_use_regex(
    repository: InMemoryProjectRepository,
    event_bus: EventBus,
) -> None:
    """A regex-looking query is treated literally.

    If the catalog used regex, '.' would match any character. Here it
    must match only a literal dot. The project name contains 'a.b',
    so 'a.b' matches but 'axb' does not.
    """
    repository.create(_project("p-001", project_name="a.b"))
    catalog = _build_catalog(repository, event_bus)

    assert len(catalog.search_projects("a.b")) == 1
    assert catalog.search_projects("axb") == ()


# ----- Count / is_empty / contains ---------------------------------


def test_count_reflects_index(
    repository: InMemoryProjectRepository,
    event_bus: EventBus,
) -> None:
    repository.create(_project("p-001"))
    repository.create(_project("p-002"))
    catalog = _build_catalog(repository, event_bus)

    assert catalog.count() == 2


def test_is_empty_reflects_index(catalog: ProjectCatalog) -> None:
    assert catalog.is_empty() is True


def test_contains_true_for_existing(
    repository: InMemoryProjectRepository,
    event_bus: EventBus,
) -> None:
    repository.create(_project("p-001"))
    catalog = _build_catalog(repository, event_bus)

    assert catalog.contains(ProjectId("p-001")) is True


def test_contains_false_for_missing(catalog: ProjectCatalog) -> None:
    assert catalog.contains(ProjectId("missing")) is False


# ----- Deletion -----------------------------------------------------


def test_list_projects_reflects_deletion(
    repository: InMemoryProjectRepository,
    event_bus: EventBus,
) -> None:
    """Deletion is reflected via the ProjectManager, not the repository.

    ADR-0016 §3.2: external mutations (a direct repository.delete) are
    not detected automatically. The ProjectManager publishes
    ProjectDeleted, which the synchronizer consumes. The catalog
    reflects the deletion on the next query, without an explicit
    refresh.
    """
    manager = ProjectManager(
        repository=repository,
        event_bus=event_bus,
        access_policy=AllowAllProjectAccessPolicy(),
    )
    manager.create_project(
        "actor",
        project_id=ProjectId("p-001"),
        project_name="One",
        patient_id=PatientId("pat-001"),
        patient_display_name="Gabriel Silva",
        clinical_procedure="orthognathic",
    )
    manager.create_project(
        "actor",
        project_id=ProjectId("p-002"),
        project_name="Two",
        patient_id=PatientId("pat-002"),
        patient_display_name="Maria Souza",
        clinical_procedure="orthognathic",
    )

    catalog = _build_catalog(repository, event_bus)
    assert catalog.count() == 2

    manager.delete_project("actor", ProjectId("p-001"))

    assert catalog.count() == 1
    assert catalog.contains(ProjectId("p-001")) is False
    assert catalog.contains(ProjectId("p-002")) is True


# ----- Corruption ---------------------------------------------------


def test_corrupted_entries_are_invisible(
    repository: InMemoryProjectRepository,
    event_bus: EventBus,
) -> None:
    """The catalog relies on list_metadata, which skips corrupted entries.

    The synchronizer's bootstrap reads from `list_metadata()`. A
    corrupted entry never reaches `replace_all`, so it never reaches
    the index, so the catalog never sees it.
    """
    repository.create(_project("p-ok"))
    repository.create(_project("p-bad"))
    repository._mark_corrupted(ProjectId("p-bad"))

    catalog = _build_catalog(repository, event_bus)

    assert catalog.contains(ProjectId("p-ok")) is True
    assert catalog.contains(ProjectId("p-bad")) is False
    assert catalog.count() == 1


# ----- Architectural invariants -------------------------------------


def test_catalog_has_no_create_method(catalog: ProjectCatalog) -> None:
    assert not hasattr(catalog, "create_project")
    assert not hasattr(catalog, "create")


def test_catalog_has_no_update_method(catalog: ProjectCatalog) -> None:
    assert not hasattr(catalog, "update_project")
    assert not hasattr(catalog, "update")


def test_catalog_has_no_delete_method(catalog: ProjectCatalog) -> None:
    assert not hasattr(catalog, "delete_project")
    assert not hasattr(catalog, "delete")


def test_catalog_has_no_open_method(catalog: ProjectCatalog) -> None:
    assert not hasattr(catalog, "open_project")
    assert not hasattr(catalog, "open")
