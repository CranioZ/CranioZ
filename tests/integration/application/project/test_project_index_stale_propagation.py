"""ProjectIndexStaleError propagation (ADR-0016 §3.3, §3.4, §8).

Two staleness paths are covered:

1. **Query → rebuild fails** (the original tests). The index is
   marked stale; the next read triggers `ensure_fresh()` → rebuild;
   if the rebuild fails, `ProjectIndexStaleError` is raised instead
   of silently returning stale data.

2. **Mutation → handler fails → next query rebuilds** (Sprint J).
   A `ProjectDeleted` handler failure must NOT propagate to the
   caller (ADR-0016 §3.4: handlers never propagate). The index is
   marked stale; the next read rebuilds from the repository, which
   already reflects the deletion. If the rebuild also fails, the
   query raises `ProjectIndexStaleError`.

The `MainWindow` (or any UI layer) is expected to present the
`ProjectIndexStaleError`; the catalog must never silently return
data from a stale index (ADR-0016 §3.3).

Design notes:

- `_FailingRepository` (original) is a minimal stub: it exists only
  to make `list_metadata()` fail on demand. It is *not* a full
  `ProjectRepository` and must not be used with `ProjectManager`.

- `_FailingOnDeleteIndex` (Sprint J) subclasses `InMemoryProjectIndex`
  and fails only on `remove`. This lets the synchronizer's
  `_on_deleted` handler fail while the rest of the index works.

- `synchronizer._possibly_stale` is accessed directly. This mirrors
  the existing pattern in this file: the staleness flag is the
  observable contract between the synchronizer and the catalog, and
  the unit-level tests in `test_project_index_synchronizer.py`
  exercise it the same way.
"""

from __future__ import annotations

import pytest

from cranioz.application.event_bus import EventBus
from cranioz.application.project.access_policy import (
    AllowAllProjectAccessPolicy,
)
from cranioz.application.project.catalog import ProjectCatalog
from cranioz.application.project.in_memory_index import InMemoryProjectIndex
from cranioz.application.project.in_memory_repository import (
    InMemoryProjectRepository,
)
from cranioz.application.project.index import ProjectIndexStaleError
from cranioz.application.project.index_synchronizer import (
    ProjectIndexSynchronizer,
    SynchronizedProjectIndex,
)
from cranioz.application.project.manager import ProjectManager
from cranioz.domain.patient.value_objects.patient_id import PatientId
from cranioz.domain.project.project_id import ProjectId

# ---------------------------------------------------------------------
# Query → rebuild fails (original tests, unchanged behavior)
# ---------------------------------------------------------------------


class _FailingRepository:
    """Minimal repository stub used only to make `list_metadata` fail.

    Not a full `ProjectRepository`: the `ProjectManager` would not
    accept it. Used exclusively by the query-path tests below, which
    do not construct a `ProjectManager`.
    """

    def __init__(self) -> None:
        self.raise_on_list = False

    def list_metadata(self):
        if self.raise_on_list:
            raise RuntimeError("storage unavailable")
        return ()


def test_query_raises_stale_error_when_rebuild_fails() -> None:
    event_bus = EventBus()
    index = InMemoryProjectIndex()
    repository = _FailingRepository()

    synchronizer = ProjectIndexSynchronizer(index, repository, event_bus)
    synchronizer.start()
    synchronizer._possibly_stale = True
    repository.raise_on_list = True

    catalog = ProjectCatalog(SynchronizedProjectIndex(index, synchronizer))

    with pytest.raises(ProjectIndexStaleError):
        catalog.list_projects()


def test_catalog_recovers_after_rebuild_succeeds() -> None:
    event_bus = EventBus()
    index = InMemoryProjectIndex()
    repository = _FailingRepository()

    synchronizer = ProjectIndexSynchronizer(index, repository, event_bus)
    synchronizer.start()
    synchronizer._possibly_stale = True
    repository.raise_on_list = True

    catalog = ProjectCatalog(SynchronizedProjectIndex(index, synchronizer))

    with pytest.raises(ProjectIndexStaleError):
        catalog.list_projects()

    # Storage comes back.
    repository.raise_on_list = False
    # The next query rebuilds (the flag stays True until success).
    result = catalog.list_projects()
    assert result == ()


# ---------------------------------------------------------------------
# Mutation → handler fails → next query rebuilds (Sprint J, ADR-0016 §3.3/§3.4)
# ---------------------------------------------------------------------


class _FailingOnDeleteIndex(InMemoryProjectIndex):
    """Index whose `remove` raises, to force the synchronizer's
    `_on_deleted` handler to fail and mark `_possibly_stale`
    (ADR-0016 §3.4).
    """

    def remove(self, project_id: ProjectId) -> None:
        raise RuntimeError("simulated index failure on remove")


def _make_delete_fixture() -> tuple[
    InMemoryProjectRepository,
    ProjectIndexSynchronizer,
    ProjectCatalog,
    ProjectManager,
]:
    """Build a composition root where the delete handler will fail.

    The bootstrap uses a real `InMemoryProjectIndex`, then swaps in a
    `_FailingOnDeleteIndex` for the synchronizer. This keeps the
    bootstrap successful (so `start()` does not mark the index stale
    on construction) while making subsequent `remove` calls fail.
    """
    event_bus = EventBus()
    repository = InMemoryProjectRepository()

    # Bootstrap with a well-behaved index first. This is what the
    # composition root does in production; it ensures `_possibly_stale`
    # starts False.
    real_index = InMemoryProjectIndex()
    bootstrapper = ProjectIndexSynchronizer(real_index, repository, event_bus)
    bootstrapper.start()

    # Swap in the failing index for the synchronizer that backs the
    # catalog. Seed it with the current summaries so the pre-delete
    # state is correct.
    failing_index = _FailingOnDeleteIndex()
    failing_index.replace_all(real_index.list_summaries())

    synchronizer = ProjectIndexSynchronizer(failing_index, repository, event_bus)
    synchronizer.start()

    catalog = ProjectCatalog(SynchronizedProjectIndex(failing_index, synchronizer))
    manager = ProjectManager(
        repository=repository,
        event_bus=event_bus,
        access_policy=AllowAllProjectAccessPolicy(),
    )
    return repository, synchronizer, catalog, manager


def _create_project(manager: ProjectManager, project_id: str = "p-001") -> None:
    manager.create_project(
        "test-actor",
        project_id=ProjectId(project_id),
        project_name=f"Case {project_id}",
        patient_id=PatientId("pat-001"),
        patient_display_name="João Silva",
        clinical_procedure="orthognathic",
    )


def test_delete_project_handler_failure_does_not_propagate_to_manager() -> None:
    """ADR-0016 §3.4: handler failures never propagate to the caller.

    The physical delete succeeded; the index is marked possibly stale;
    `delete_project` returns normally. If the handler propagated, the
    `EventBus` would re-raise as `EventBusError` and the caller would
    incorrectly believe the persistent mutation failed.
    """
    _repository, synchronizer, _catalog, manager = _make_delete_fixture()
    _create_project(manager)

    # Delete: the `_on_deleted` handler will fail on `index.remove`.
    manager.delete_project("test-actor", ProjectId("p-001"))  # must NOT raise

    assert synchronizer._possibly_stale is True


def test_delete_project_handler_failure_rebuilds_on_next_query() -> None:
    """After a failed handler, the next catalog query rebuilds from the
    repository and reflects the deletion (ADR-0016 §3.3).

    The repository no longer contains the project, so the rebuild
    produces a fresh index without it. The catalog must not return
    the pre-delete state.
    """
    _repository, _synchronizer, catalog, manager = _make_delete_fixture()
    _create_project(manager)
    assert catalog.contains(ProjectId("p-001")) is True

    manager.delete_project("test-actor", ProjectId("p-001"))

    # The next read triggers ensure_fresh → rebuild from repository.
    assert catalog.contains(ProjectId("p-001")) is False
    assert catalog.count() == 0


def test_delete_project_rebuild_failure_after_handler_failure_raises_stale(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """If both handler AND rebuild fail, ProjectIndexStaleError is raised.

    The catalog must NOT silently return the pre-delete state: the
    staleness rule (ADR-0016 §3.3) requires the query to fail rather
    than serve stale data.
    """
    event_bus = EventBus()
    repository = InMemoryProjectRepository()
    index = InMemoryProjectIndex()
    synchronizer = ProjectIndexSynchronizer(index, repository, event_bus)
    synchronizer.start()
    catalog = ProjectCatalog(SynchronizedProjectIndex(index, synchronizer))
    manager = ProjectManager(
        repository=repository,
        event_bus=event_bus,
        access_policy=AllowAllProjectAccessPolicy(),
    )
    _create_project(manager)
    assert catalog.contains(ProjectId("p-001")) is True

    # Force the delete handler to fail.
    def _raise_on_remove(_project_id: ProjectId) -> None:
        raise RuntimeError("simulated index failure on remove")

    monkeypatch.setattr(index, "remove", _raise_on_remove)

    # Force the subsequent rebuild to fail too.
    def _raise_on_list_metadata():
        raise RuntimeError("simulated repository failure on rebuild")

    monkeypatch.setattr(repository, "list_metadata", _raise_on_list_metadata)

    manager.delete_project("test-actor", ProjectId("p-001"))  # handler contained
    assert synchronizer._possibly_stale is True

    # The next read triggers rebuild → repository fails → stale error.
    with pytest.raises(ProjectIndexStaleError):
        catalog.contains(ProjectId("p-001"))
