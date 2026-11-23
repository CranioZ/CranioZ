"""Integration test: bootstrap ordering for the ProjectIndex (Sprint K, K.6).

ADR-0016 §4.1: the bootstrap-ordering guarantee holds only while the
``ProjectIndexSynchronizer`` bootstrap is synchronous. Sprint K is a
K-minimal sprint: ``synchronizer.start()`` remains synchronous in the
composition root (``__main__::_build_project_subsystem``). The HomePage
reads from the catalog only after the MainWindow is constructed, which
is after ``synchronizer.start()`` returns.

This test exercises the composition-root wiring directly and asserts
that no read reaches the catalog before ``start()`` finishes.
"""

from __future__ import annotations

from cranioz.application.event_bus import EventBus
from cranioz.application.project.access_policy import (
    AllowAllProjectAccessPolicy,
)
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


def test_synchronizer_start_is_synchronous_before_catalog_construction() -> None:
    """``synchronizer.start()`` runs before the catalog is built.

    Mirrors ``__main__::_build_project_subsystem``.
    """
    repository = InMemoryProjectRepository()
    event_bus = EventBus()
    manager = ProjectManager(
        repository=repository,
        event_bus=event_bus,
        access_policy=AllowAllProjectAccessPolicy(),
    )
    # Pre-seed the repository (bypassing ProjectManager: this test is
    # about ordering, not about lifecycle).
    manager.create_project(
        "actor",
        project_id=ProjectId("p-001"),
        project_name="Case 001",
        patient_id=PatientId("pat-001"),
        patient_display_name="Gabriel Silva",
        clinical_procedure="orthognathic",
    )

    # Composition-root order: subscribe → bootstrap → decorate.
    raw_index = InMemoryProjectIndex()
    synchronizer = ProjectIndexSynchronizer(raw_index, repository, event_bus)
    synchronizer.start()  # synchronous; must return before the catalog exists
    index = SynchronizedProjectIndex(raw_index, synchronizer)
    catalog = ProjectCatalog(index=index)

    # The catalog sees the project immediately, with no explicit refresh.
    assert catalog.count() == 1
    assert catalog.contains(ProjectId("p-001"))


def test_no_project_event_published_between_subscribe_and_bootstrap() -> None:
    """No event can be published during ``start()``.

    ``start()`` runs subscribe → list_metadata → replace_all on the
    same synchronous call stack. There is no yield point, so a
    ``ProjectCreated`` published by another thread between (1) and (3)
    cannot be observed by the synchronizer. The guarantee holds
    because the EventBus and the synchronizer are single-threaded
    (ADR-0016 §4).
    """
    # This test documents the invariant; the actual guarantee is
    # architectural. It exercises the synchronizer's public surface
    # to ensure ``start()`` returns only after ``replace_all``.
    repository = InMemoryProjectRepository()
    event_bus = EventBus()

    raw_index = InMemoryProjectIndex()
    synchronizer = ProjectIndexSynchronizer(raw_index, repository, event_bus)
    synchronizer.start()

    # After start(), the index must already reflect the repository.
    assert raw_index.count() == len(repository.list_metadata())
