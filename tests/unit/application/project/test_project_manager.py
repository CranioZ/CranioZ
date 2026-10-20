"""Tests for ProjectManager.

Exercises the full lifecycle against InMemoryProjectRepository, a real
EventBus, and AllowAllProjectAccessPolicy. No Qt, no I/O.

Coverage:

- create_project: persists via repository, publishes ProjectCreated,
  respects access policy, rejects duplicates via repository.
- open_project: builds ProjectContext from project metadata,
  updates last_opened_at, publishes ProjectOpened once, returns the
  existing context on repeated open (idempotent), honors workflow_id
  and workflow_config, respects access policy.
- open_project PatientSummary: display_name and patient_id derived
  from project metadata; birth_date and sex are None (not carried).
- update_project: persists and publishes ProjectUpdated; respects
  access policy; no event on repository failure.
- close_project: publishes ProjectClosing then ProjectClosed, releases
  the context; silent no-op for non-open project.
- delete_project: refuses open project with ProjectInUse BEFORE
  mutating state or publishing events; respects access policy.
- Access policy denial blocks every operation and publishes nothing.
- No events are published when the underlying repository operation
  fails.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from cranioz.application.event_bus import EventBus
from cranioz.application.project.in_memory_project_repository import (
    InMemoryProjectRepository,
)
from cranioz.application.project.project_access_policy import (
    Actor,
    AllowAllProjectAccessPolicy,
    ProjectAccessPolicy,
)
from cranioz.application.project.project_context import ProjectContext
from cranioz.application.project.project_errors import (
    ProjectAccessDenied,
    ProjectAlreadyExists,
    ProjectInUse,
    ProjectNotFound,
)
from cranioz.application.project.project_events import (
    ProjectClosed,
    ProjectClosing,
    ProjectCreated,
    ProjectDeleted,
    ProjectOpened,
    ProjectUpdated,
)
from cranioz.application.project.project_manager import ProjectManager
from cranioz.domain.patient.value_objects.patient_id import PatientId
from cranioz.domain.project.project import Project
from cranioz.domain.project.project_id import ProjectId
from cranioz.domain.project.project_metadata import ProjectMetadata
from cranioz.domain.project.project_status import ProjectStatus

# ----- Helpers ------------------------------------------------------


_ACTOR: Actor = "test-user"


def _now() -> datetime:
    return datetime(2026, 1, 1, 12, 0, tzinfo=UTC)


def _make_project(project_id: str = "p-001") -> Project:
    pid = ProjectId(project_id)
    return Project(
        project_id=pid,
        metadata=ProjectMetadata(
            project_id=pid,
            project_name=f"Case {project_id}",
            patient_id="pat-001",
            patient_display_name="Gabriel Silva",
            clinical_procedure="orthognathic",
            status=ProjectStatus.ACTIVE,
            created_at=_now(),
            updated_at=_now(),
            last_opened_at=None,
            schema_version=1,
        ),
    )


def _make_manager(
    *,
    policy: ProjectAccessPolicy | None = None,
    bus: EventBus | None = None,
    repository: InMemoryProjectRepository | None = None,
) -> tuple[ProjectManager, InMemoryProjectRepository, EventBus]:
    repo = repository if repository is not None else InMemoryProjectRepository()
    event_bus = bus if bus is not None else EventBus()
    policy = policy if policy is not None else AllowAllProjectAccessPolicy()
    manager = ProjectManager(
        repository=repo,
        event_bus=event_bus,
        access_policy=policy,
    )
    return manager, repo, event_bus


def _create(
    manager: ProjectManager,
    project_id: str = "p-001",
    *,
    project_name: str = "Case 001",
    patient_display_name: str = "Gabriel Silva",
) -> Project:
    return manager.create_project(
        _ACTOR,
        project_id=ProjectId(project_id),
        project_name=project_name,
        patient_id=PatientId("pat-001"),
        patient_display_name=patient_display_name,
        clinical_procedure="orthognathic",
    )


class _DenyAllPolicy:
    """Deny-everything policy for negative tests."""

    def can_create(self, actor: Actor) -> bool:
        return False

    def can_open(self, actor: Actor, project_id: ProjectId) -> bool:
        return False

    def can_update(self, actor: Actor, project_id: ProjectId) -> bool:
        return False

    def can_delete(self, actor: Actor, project_id: ProjectId) -> bool:
        return False


class _DenyDeletePolicy:
    """Deny only deletes; allow the rest."""

    def can_create(self, actor: Actor) -> bool:
        return True

    def can_open(self, actor: Actor, project_id: ProjectId) -> bool:
        return True

    def can_update(self, actor: Actor, project_id: ProjectId) -> bool:
        return True

    def can_delete(self, actor: Actor, project_id: ProjectId) -> bool:
        return False


# ====================================================================
# create_project
# ====================================================================


def test_create_project_persists() -> None:
    manager, repo, _ = _make_manager()
    project = _create(manager, "p-001")

    assert repo.exists(ProjectId("p-001")) is True
    loaded = repo.get(ProjectId("p-001"))
    assert loaded.metadata.project_name == project.metadata.project_name


def test_create_project_publishes_created_event() -> None:
    manager, _, bus = _make_manager()
    received: list[ProjectCreated] = []
    bus.subscribe(ProjectCreated, received.append)

    _create(manager, "p-001")

    assert len(received) == 1
    assert received[0].project_id == ProjectId("p-001")


def test_create_project_returns_project() -> None:
    manager, _, _ = _make_manager()
    project = _create(manager, "p-001", project_name="Custom")
    assert project.project_id == ProjectId("p-001")
    assert project.metadata.project_name == "Custom"


def test_create_project_defaults_to_draft_status() -> None:
    manager, _, _ = _make_manager()
    project = _create(manager, "p-001")
    assert project.metadata.status is ProjectStatus.DRAFT


def test_create_project_denied_by_policy() -> None:
    manager, repo, bus = _make_manager(policy=_DenyAllPolicy())
    received: list[ProjectCreated] = []
    bus.subscribe(ProjectCreated, received.append)

    with pytest.raises(ProjectAccessDenied):
        _create(manager)

    assert repo.exists(ProjectId("p-001")) is False
    assert received == []


def test_create_project_duplicate_raises_from_repository() -> None:
    manager, _, _ = _make_manager()
    _create(manager, "p-001")
    with pytest.raises(ProjectAlreadyExists):
        _create(manager, "p-001")


def test_create_project_does_not_publish_on_repository_failure() -> None:
    """If the repository raises (here: duplicate), no event is published."""
    manager, _, bus = _make_manager()
    _create(manager, "p-001")

    received: list[ProjectCreated] = []
    bus.subscribe(ProjectCreated, received.append)

    with pytest.raises(ProjectAlreadyExists):
        _create(manager, "p-001")

    assert received == []


# ====================================================================
# open_project
# ====================================================================


def test_open_project_returns_context() -> None:
    manager, _, _ = _make_manager()
    _create(manager, "p-001")

    context = manager.open_project(_ACTOR, ProjectId("p-001"))

    assert isinstance(context, ProjectContext)
    assert context.project_id == ProjectId("p-001")
    assert manager.is_open(ProjectId("p-001")) is True


def test_open_project_patient_summary_is_projected_from_metadata() -> None:
    manager, _, _ = _make_manager()
    _create(manager, "p-001", patient_display_name="Maria Souza")

    context = manager.open_project(_ACTOR, ProjectId("p-001"))

    assert context.patient_summary.display_name == "Maria Souza"
    assert context.patient_summary.patient_id == PatientId("pat-001")
    # Not carried by the project; explicitly None.
    assert context.patient_summary.birth_date is None
    assert context.patient_summary.sex is None


def test_open_project_updates_last_opened() -> None:
    manager, repo, _ = _make_manager()
    _create(manager, "p-001")

    before = repo.get(ProjectId("p-001")).metadata.last_opened_at
    assert before is None

    manager.open_project(_ACTOR, ProjectId("p-001"))

    after = repo.get(ProjectId("p-001")).metadata.last_opened_at
    assert after is not None


def test_open_project_publishes_opened_event() -> None:
    manager, _, bus = _make_manager()
    _create(manager, "p-001")
    received: list[ProjectOpened] = []
    bus.subscribe(ProjectOpened, received.append)

    context = manager.open_project(_ACTOR, ProjectId("p-001"))

    assert len(received) == 1
    assert received[0].project_id == ProjectId("p-001")
    assert received[0].context is context


def test_open_project_is_idempotent() -> None:
    """Opening an already-open project returns the existing context."""
    manager, _, bus = _make_manager()
    _create(manager, "p-001")

    first = manager.open_project(_ACTOR, ProjectId("p-001"))
    second = manager.open_project(_ACTOR, ProjectId("p-001"))

    assert first is second
    # Only one event total (subscribed after the first open).
    received: list[ProjectOpened] = []
    bus.subscribe(ProjectOpened, received.append)
    manager.open_project(_ACTOR, ProjectId("p-001"))
    assert received == []


def test_open_project_with_workflow_propagates_to_context() -> None:
    manager, _, _ = _make_manager()
    _create(manager, "p-001")

    context = manager.open_project(
        _ACTOR,
        ProjectId("p-001"),
        workflow_id="orthognathic",
        workflow_config={"steps": ["a"]},
    )

    assert context.workflow_id == "orthognathic"
    assert context.workflow_config == {"steps": ["a"]}


def test_open_project_without_workflow() -> None:
    manager, _, _ = _make_manager()
    _create(manager, "p-001")

    context = manager.open_project(_ACTOR, ProjectId("p-001"))

    assert context.workflow_id is None
    assert context.workflow_config is None


def test_open_project_denied_by_policy() -> None:
    """Deny the open; do not touch state or publish events."""
    repo = InMemoryProjectRepository()
    repo.create(_make_project("p-001"))
    bus = EventBus()
    manager = ProjectManager(
        repository=repo,
        event_bus=bus,
        access_policy=_DenyAllPolicy(),
    )

    received: list[ProjectOpened] = []
    bus.subscribe(ProjectOpened, received.append)

    with pytest.raises(ProjectAccessDenied):
        manager.open_project(_ACTOR, ProjectId("p-001"))

    assert manager.is_open(ProjectId("p-001")) is False
    assert received == []


def test_open_project_missing_raises() -> None:
    manager, _, _ = _make_manager()
    with pytest.raises(ProjectNotFound):
        manager.open_project(_ACTOR, ProjectId("p-999"))


# ====================================================================
# update_project
# ====================================================================


def test_update_project_persists() -> None:
    manager, repo, _ = _make_manager()
    project = _create(manager, "p-001")

    later = project.metadata.created_at + timedelta(days=1)
    updated = Project(
        project_id=project.project_id,
        metadata=project.metadata.with_name("Renamed", now=later),
    )
    manager.update_project(_ACTOR, updated)

    loaded = repo.get(ProjectId("p-001"))
    assert loaded.metadata.project_name == "Renamed"


def test_update_project_publishes_updated_event() -> None:
    manager, _, bus = _make_manager()
    project = _create(manager, "p-001")
    received: list[ProjectUpdated] = []
    bus.subscribe(ProjectUpdated, received.append)

    later = project.metadata.created_at + timedelta(days=1)
    updated = Project(
        project_id=project.project_id,
        metadata=project.metadata.with_name("Renamed", now=later),
    )
    manager.update_project(_ACTOR, updated)

    assert len(received) == 1
    assert received[0].project_id == ProjectId("p-001")
    assert received[0].metadata.project_name == "Renamed"


def test_update_project_denied_by_policy() -> None:
    repo = InMemoryProjectRepository()
    repo.create(_make_project("p-001"))
    bus = EventBus()
    manager = ProjectManager(
        repository=repo,
        event_bus=bus,
        access_policy=_DenyAllPolicy(),
    )

    received: list[ProjectUpdated] = []
    bus.subscribe(ProjectUpdated, received.append)

    project = repo.get(ProjectId("p-001"))
    later = datetime(2026, 2, 1, tzinfo=UTC)
    updated = Project(
        project_id=project.project_id,
        metadata=project.metadata.with_name("X", now=later),
    )

    with pytest.raises(ProjectAccessDenied):
        manager.update_project(_ACTOR, updated)
    assert received == []


# ====================================================================
# close_project
# ====================================================================


def test_close_project_releases_context() -> None:
    manager, _, _ = _make_manager()
    _create(manager, "p-001")
    manager.open_project(_ACTOR, ProjectId("p-001"))

    manager.close_project(_ACTOR, ProjectId("p-001"))

    assert manager.is_open(ProjectId("p-001")) is False


def test_close_project_publishes_events_in_order() -> None:
    manager, _, bus = _make_manager()
    _create(manager, "p-001")
    manager.open_project(_ACTOR, ProjectId("p-001"))

    order: list[str] = []
    bus.subscribe(ProjectClosing, lambda _e: order.append("closing"))
    bus.subscribe(ProjectClosed, lambda _e: order.append("closed"))

    manager.close_project(_ACTOR, ProjectId("p-001"))

    assert order == ["closing", "closed"]


def test_close_project_does_not_modify_persisted_metadata() -> None:
    """last_opened_at is set on open; close does not update it."""
    manager, repo, _ = _make_manager()
    _create(manager, "p-001")
    manager.open_project(_ACTOR, ProjectId("p-001"))
    before = repo.get(ProjectId("p-001")).metadata

    manager.close_project(_ACTOR, ProjectId("p-001"))

    after = repo.get(ProjectId("p-001")).metadata
    assert after == before


def test_close_project_non_open_is_noop() -> None:
    """Closing a project that is not open does nothing and publishes nothing."""
    manager, _, bus = _make_manager()
    _create(manager, "p-001")
    # Not opened.

    received: list[object] = []
    bus.subscribe(ProjectClosing, received.append)
    bus.subscribe(ProjectClosed, received.append)

    manager.close_project(_ACTOR, ProjectId("p-001"))  # must not raise

    assert received == []
    assert manager.is_open(ProjectId("p-001")) is False


# ====================================================================
# delete_project
# ====================================================================


def test_delete_project_removes_from_repository() -> None:
    manager, repo, _ = _make_manager()
    _create(manager, "p-001")

    manager.delete_project(_ACTOR, ProjectId("p-001"))

    assert repo.exists(ProjectId("p-001")) is False


def test_delete_project_publishes_event() -> None:
    manager, _, bus = _make_manager()
    _create(manager, "p-001")
    received: list[ProjectDeleted] = []
    bus.subscribe(ProjectDeleted, received.append)

    manager.delete_project(_ACTOR, ProjectId("p-001"))

    assert len(received) == 1
    assert received[0].project_id == ProjectId("p-001")


def test_delete_project_rejects_open_project() -> None:
    """Deleting an open project raises ProjectInUse BEFORE mutating state."""
    manager, repo, bus = _make_manager()
    _create(manager, "p-001")
    manager.open_project(_ACTOR, ProjectId("p-001"))

    received: list[ProjectDeleted] = []
    bus.subscribe(ProjectDeleted, received.append)

    with pytest.raises(ProjectInUse, match="close it first"):
        manager.delete_project(_ACTOR, ProjectId("p-001"))

    # State was not modified.
    assert repo.exists(ProjectId("p-001")) is True
    # No event was published.
    assert received == []


def test_delete_project_denied_by_policy() -> None:
    """Deny the delete; do not remove from repository, do not publish."""
    repo = InMemoryProjectRepository()
    repo.create(_make_project("p-001"))
    bus = EventBus()
    manager = ProjectManager(
        repository=repo,
        event_bus=bus,
        access_policy=_DenyDeletePolicy(),
    )

    received: list[ProjectDeleted] = []
    bus.subscribe(ProjectDeleted, received.append)

    with pytest.raises(ProjectAccessDenied):
        manager.delete_project(_ACTOR, ProjectId("p-001"))

    assert repo.exists(ProjectId("p-001")) is True
    assert received == []


def test_delete_project_missing_raises() -> None:
    manager, _, _ = _make_manager()
    with pytest.raises(ProjectNotFound):
        manager.delete_project(_ACTOR, ProjectId("p-999"))


# ====================================================================
# get_active_context
# ====================================================================


def test_get_active_context_returns_none_before_open() -> None:
    manager, _, _ = _make_manager()
    _create(manager, "p-001")
    assert manager.get_active_context(ProjectId("p-001")) is None


def test_get_active_context_returns_context_after_open() -> None:
    manager, _, _ = _make_manager()
    _create(manager, "p-001")
    context = manager.open_project(_ACTOR, ProjectId("p-001"))

    assert manager.get_active_context(ProjectId("p-001")) is context


def test_get_active_context_returns_none_after_close() -> None:
    manager, _, _ = _make_manager()
    _create(manager, "p-001")
    manager.open_project(_ACTOR, ProjectId("p-001"))
    manager.close_project(_ACTOR, ProjectId("p-001"))

    assert manager.get_active_context(ProjectId("p-001")) is None


# ====================================================================
# is_open
# ====================================================================


def test_is_open_false_before_open() -> None:
    manager, _, _ = _make_manager()
    _create(manager, "p-001")
    assert manager.is_open(ProjectId("p-001")) is False


def test_is_open_true_after_open() -> None:
    manager, _, _ = _make_manager()
    _create(manager, "p-001")
    manager.open_project(_ACTOR, ProjectId("p-001"))
    assert manager.is_open(ProjectId("p-001")) is True


def test_is_open_false_after_close() -> None:
    manager, _, _ = _make_manager()
    _create(manager, "p-001")
    manager.open_project(_ACTOR, ProjectId("p-001"))
    manager.close_project(_ACTOR, ProjectId("p-001"))
    assert manager.is_open(ProjectId("p-001")) is False
