"""Bootstrap ordering test (ADR-0016 §4, §8).

Verifies that, under a synchronous EventBus, no event published
between `subscribe` and `replace_all` is lost or duplicated.
"""

from __future__ import annotations

from datetime import UTC, datetime

from cranioz.application.event_bus import EventBus
from cranioz.application.project.events import ProjectCreated
from cranioz.application.project.in_memory_index import InMemoryProjectIndex
from cranioz.application.project.index_synchronizer import (
    ProjectIndexSynchronizer,
)
from cranioz.domain.project.project_id import ProjectId
from cranioz.domain.project.project_metadata import ProjectMetadata
from cranioz.domain.project.project_status import ProjectStatus
from cranioz.domain.project.project_summary import ProjectSummary


def _now() -> datetime:
    return datetime(2026, 1, 1, 12, 0, tzinfo=UTC)


def _metadata(project_id: str) -> ProjectMetadata:
    return ProjectMetadata(
        project_id=ProjectId(project_id),
        project_name="Case",
        patient_id="pat-001",
        patient_display_name="Gabriel Silva",
        clinical_procedure="orthognathic",
        status=ProjectStatus.ACTIVE,
        created_at=_now(),
        updated_at=_now(),
        last_opened_at=None,
        schema_version=1,
    )


class _RepositoryThatPublishesDuringListMetadata:
    """A repository double whose `list_metadata` publishes an event.

    This simulates the worst case under a synchronous bus: a
    subscriber re-enters `EventBus.publish` while the synchronizer is
    between `subscribe` and `replace_all`. The ordering guarantee
    says the event is handled by the just-subscribed handler, and
    then `replace_all` overwrites the index with the repository's
    snapshot — which, by construction, already includes the event's
    effect. No loss, no duplication.
    """

    def __init__(
        self,
        event_bus: EventBus,
        event_to_publish: ProjectCreated,
        summaries: tuple,
    ) -> None:
        self._event_bus = event_bus
        self._event_to_publish = event_to_publish
        self._summaries = summaries
        self.published_once = False

    def list_metadata(self):
        if not self.published_once:
            self.published_once = True
            self._event_bus.publish(self._event_to_publish)
        return self._summaries


def test_event_published_during_bootstrap_is_not_lost() -> None:
    event_bus = EventBus()
    index = InMemoryProjectIndex()

    new_metadata = _metadata("p-new")
    new_event = ProjectCreated(project_id=ProjectId("p-new"), metadata=new_metadata)
    # The repository snapshot already includes the new project: it is
    # the authoritative source, and the event announces a mutation
    # that the repository has already applied.
    snapshot = (ProjectSummary.from_metadata(new_metadata),)

    repository = _RepositoryThatPublishesDuringListMetadata(
        event_bus=event_bus,
        event_to_publish=new_event,
        summaries=snapshot,
    )

    synchronizer = ProjectIndexSynchronizer(index, repository, event_bus)
    synchronizer.start()

    # The index contains exactly the project, once. No loss (the event
    # was handled by the subscribed handler), no duplication
    # (`replace_all` overwrites with the snapshot).
    assert index.count() == 1
    assert index.contains(ProjectId("p-new"))
