"""Tests for ProjectIndexSynchronizer and SynchronizedProjectIndex.

Covers: bootstrap, event handlers (created/updated/deleted), handler
error containment, `rebuild`, `ensure_fresh`, and the staleness rule
(ADR-0016 §3, §4).
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from cranioz.application.event_bus import EventBus
from cranioz.application.project.events import (
    ProjectCreated,
    ProjectDeleted,
    ProjectUpdated,
)
from cranioz.application.project.in_memory_index import InMemoryProjectIndex
from cranioz.application.project.index import ProjectIndexStaleError
from cranioz.application.project.index_synchronizer import (
    ProjectIndexSynchronizer,
    SynchronizedProjectIndex,
)
from cranioz.domain.project.project_id import ProjectId
from cranioz.domain.project.project_metadata import ProjectMetadata
from cranioz.domain.project.project_status import ProjectStatus
from cranioz.domain.project.project_summary import ProjectSummary


def _now() -> datetime:
    return datetime(2026, 1, 1, 12, 0, tzinfo=UTC)


def _metadata(project_id: str = "p-001", name: str = "Case 001") -> ProjectMetadata:
    return ProjectMetadata(
        project_id=ProjectId(project_id),
        project_name=name,
        patient_id="pat-001",
        patient_display_name="Gabriel Silva",
        clinical_procedure="orthognathic",
        status=ProjectStatus.ACTIVE,
        created_at=_now(),
        updated_at=_now(),
        last_opened_at=None,
        schema_version=1,
    )


class _FakeRepository:
    """Minimal repository double: only `list_metadata` is used by the
    synchronizer. Other methods are not exercised here."""

    def __init__(self, summaries: tuple = ()) -> None:
        self._summaries = summaries
        self.list_metadata_calls = 0
        self.raise_on_list: Exception | None = None

    def list_metadata(self):
        self.list_metadata_calls += 1
        if self.raise_on_list is not None:
            raise self.raise_on_list
        return self._summaries

    def set_summaries(self, summaries: tuple) -> None:
        self._summaries = summaries


@pytest.fixture
def event_bus() -> EventBus:
    return EventBus()


@pytest.fixture
def index() -> InMemoryProjectIndex:
    return InMemoryProjectIndex()


@pytest.fixture
def repository() -> _FakeRepository:
    return _FakeRepository()


@pytest.fixture
def synchronizer(
    index: InMemoryProjectIndex,
    repository: _FakeRepository,
    event_bus: EventBus,
) -> ProjectIndexSynchronizer:
    return ProjectIndexSynchronizer(index, repository, event_bus)


# ----- start / bootstrap ---------------------------------------------


def test_start_bootstraps_from_repository(
    synchronizer: ProjectIndexSynchronizer,
    index: InMemoryProjectIndex,
    repository: _FakeRepository,
) -> None:
    repository.set_summaries((ProjectSummary.from_metadata(_metadata("p-001")),))
    synchronizer.start()
    assert index.count() == 1
    assert index.contains(ProjectId("p-001"))


def test_start_twice_raises(synchronizer: ProjectIndexSynchronizer) -> None:
    synchronizer.start()
    with pytest.raises(RuntimeError, match="called twice"):
        synchronizer.start()


# ----- handlers ------------------------------------------------------


def test_created_handler_adds_summary(
    synchronizer: ProjectIndexSynchronizer,
    index: InMemoryProjectIndex,
) -> None:
    synchronizer.start()
    synchronizer._on_created(
        ProjectCreated(project_id=ProjectId("p-new"), metadata=_metadata("p-new"))
    )
    assert index.contains(ProjectId("p-new"))


def test_updated_handler_replaces_summary(
    synchronizer: ProjectIndexSynchronizer,
    index: InMemoryProjectIndex,
) -> None:
    synchronizer.start()
    synchronizer._on_created(
        ProjectCreated(project_id=ProjectId("p-1"), metadata=_metadata("p-1", "First"))
    )
    synchronizer._on_updated(
        ProjectUpdated(project_id=ProjectId("p-1"), metadata=_metadata("p-1", "Second"))
    )
    assert index.lookup(ProjectId("p-1")).project_name == "Second"


def test_deleted_handler_removes_summary(
    synchronizer: ProjectIndexSynchronizer,
    index: InMemoryProjectIndex,
) -> None:
    synchronizer.start()
    synchronizer._on_created(ProjectCreated(project_id=ProjectId("p-1"), metadata=_metadata("p-1")))
    synchronizer._on_deleted(ProjectDeleted(project_id=ProjectId("p-1")))
    assert not index.contains(ProjectId("p-1"))


# ----- handler error containment -------------------------------------


def test_handler_failure_marks_stale_and_does_not_propagate(
    synchronizer: ProjectIndexSynchronizer,
    index: InMemoryProjectIndex,
) -> None:
    """A failing handler must not propagate to the EventBus (ADR-0016 §3.4)."""

    # Monkeypatch `add` to raise.
    def _boom(_summary) -> None:
        raise RuntimeError("boom")

    index.add = _boom  # type: ignore[method-assign]

    synchronizer.start()  # bootstrap uses replace_all, not add
    # Should not raise.
    synchronizer._on_created(ProjectCreated(project_id=ProjectId("p-1"), metadata=_metadata("p-1")))
    assert synchronizer._possibly_stale is True


def test_handler_failure_logs_only_project_id_and_operation(
    synchronizer: ProjectIndexSynchronizer,
    index: InMemoryProjectIndex,
    caplog: pytest.LogCaptureFixture,
) -> None:
    def _boom(_summary) -> None:
        raise RuntimeError("boom")

    index.add = _boom  # type: ignore[method-assign]

    synchronizer.start()
    with caplog.at_level("WARNING", logger="cranioz.application.project.index_synchronizer"):
        synchronizer._on_created(
            ProjectCreated(
                project_id=ProjectId("p-1"),
                metadata=_metadata("p-1", "Secret Name"),
            )
        )

    # project_id and operation are logged; project_name must NOT be.
    assert "p-1" in caplog.text
    assert "create" in caplog.text
    assert "Secret Name" not in caplog.text


# ----- rebuild -------------------------------------------------------


def test_rebuild_replaces_index_contents(
    synchronizer: ProjectIndexSynchronizer,
    index: InMemoryProjectIndex,
    repository: _FakeRepository,
) -> None:
    synchronizer.start()
    index.add(ProjectSummary.from_metadata(_metadata("p-stale")))
    repository.set_summaries((ProjectSummary.from_metadata(_metadata("p-fresh")),))
    synchronizer.rebuild()
    assert index.contains(ProjectId("p-fresh"))
    assert not index.contains(ProjectId("p-stale"))


# ----- ensure_fresh --------------------------------------------------


def test_ensure_fresh_is_noop_when_not_stale(
    synchronizer: ProjectIndexSynchronizer,
    repository: _FakeRepository,
) -> None:
    synchronizer.start()
    calls_before = repository.list_metadata_calls
    synchronizer.ensure_fresh()
    assert repository.list_metadata_calls == calls_before


def test_ensure_fresh_rebuilds_when_stale(
    synchronizer: ProjectIndexSynchronizer,
    index: InMemoryProjectIndex,
    repository: _FakeRepository,
) -> None:
    synchronizer.start()
    synchronizer._possibly_stale = True
    synchronizer.ensure_fresh()
    assert synchronizer._possibly_stale is False


def test_ensure_fresh_raises_stale_error_if_rebuild_fails(
    synchronizer: ProjectIndexSynchronizer,
    repository: _FakeRepository,
) -> None:
    synchronizer.start()
    synchronizer._possibly_stale = True
    repository.raise_on_list = RuntimeError("cannot read")

    with pytest.raises(ProjectIndexStaleError):
        synchronizer.ensure_fresh()


# ----- SynchronizedProjectIndex --------------------------------------


def test_synchronized_index_calls_ensure_fresh_on_reads(
    synchronizer: ProjectIndexSynchronizer,
    index: InMemoryProjectIndex,
) -> None:
    synchronizer.start()
    synchronized = SynchronizedProjectIndex(index, synchronizer)

    synchronizer._possibly_stale = True
    calls_before = synchronizer._repository.list_metadata_calls
    synchronized.list_summaries()
    assert synchronizer._repository.list_metadata_calls == calls_before + 1


def test_synchronized_index_does_not_check_freshness_on_writes(
    synchronizer: ProjectIndexSynchronizer,
    index: InMemoryProjectIndex,
) -> None:
    synchronizer.start()
    synchronized = SynchronizedProjectIndex(index, synchronizer)
    calls_before = synchronizer._repository.list_metadata_calls
    synchronized.add(ProjectSummary.from_metadata(_metadata("p-1")))
    synchronized.remove(ProjectId("p-1"))
    assert synchronizer._repository.list_metadata_calls == calls_before
