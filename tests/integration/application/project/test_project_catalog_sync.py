"""End-to-end integration: ProjectManager ↔ ProjectCatalog (ADR-0016 §8).

Creates, updates, and deletes projects through the `ProjectManager`
and asserts that the catalog reflects the change on the next query,
without any explicit refresh.
"""

from __future__ import annotations

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
from cranioz.domain.project.project_id import ProjectId


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
    index = InMemoryProjectIndex()
    synchronizer = ProjectIndexSynchronizer(index, repository, event_bus)
    synchronizer.start()
    return ProjectCatalog(SynchronizedProjectIndex(index, synchronizer))


@pytest.fixture
def manager(
    repository: InMemoryProjectRepository,
    event_bus: EventBus,
) -> ProjectManager:
    return ProjectManager(
        repository=repository,
        event_bus=event_bus,
        access_policy=AllowAllProjectAccessPolicy(),
    )


def test_create_reflects_in_catalog(
    manager: ProjectManager,
    catalog: ProjectCatalog,
) -> None:
    manager.create_project(
        "actor",
        project_id=ProjectId("p-001"),
        project_name="New",
        patient_id=PatientId("pat-001"),
        patient_display_name="Gabriel Silva",
        clinical_procedure="orthognathic",
    )
    assert catalog.contains(ProjectId("p-001"))
    assert catalog.count() == 1


def test_update_reflects_in_catalog(
    manager: ProjectManager,
    catalog: ProjectCatalog,
    repository: InMemoryProjectRepository,
) -> None:
    project = manager.create_project(
        "actor",
        project_id=ProjectId("p-001"),
        project_name="Original",
        patient_id=PatientId("pat-001"),
        patient_display_name="Gabriel Silva",
        clinical_procedure="orthognathic",
    )
    new_metadata = project.metadata.with_name("Renamed", now=project.metadata.updated_at)
    updated = type(project)(project_id=project.project_id, metadata=new_metadata)
    manager.update_project("actor", updated)

    summary = catalog.get_project_summary(ProjectId("p-001"))
    assert summary is not None
    assert summary.project_name == "Renamed"


def test_delete_reflects_in_catalog(
    manager: ProjectManager,
    catalog: ProjectCatalog,
) -> None:
    manager.create_project(
        "actor",
        project_id=ProjectId("p-001"),
        project_name="New",
        patient_id=PatientId("pat-001"),
        patient_display_name="Gabriel Silva",
        clinical_procedure="orthognathic",
    )
    assert catalog.contains(ProjectId("p-001"))

    manager.delete_project("actor", ProjectId("p-001"))
    assert not catalog.contains(ProjectId("p-001"))
    assert catalog.count() == 0


def test_no_explicit_refresh_needed(
    manager: ProjectManager,
    catalog: ProjectCatalog,
) -> None:
    """The catalog has no `refresh()`. Freshness is automatic."""
    assert not hasattr(catalog, "refresh")
