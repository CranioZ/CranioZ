"""ProjectIndexStaleError propagation (ADR-0016 §3.3, §8).

When the index is stale and the rebuild fails, the query raises
`ProjectIndexStaleError` instead of returning stale data. The
`MainWindow` (or any UI layer) is expected to present the error.
"""

from __future__ import annotations

import pytest

from cranioz.application.event_bus import EventBus
from cranioz.application.project.catalog import ProjectCatalog
from cranioz.application.project.in_memory_index import InMemoryProjectIndex
from cranioz.application.project.index import ProjectIndexStaleError
from cranioz.application.project.index_synchronizer import (
    ProjectIndexSynchronizer,
    SynchronizedProjectIndex,
)


class _FailingRepository:
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
