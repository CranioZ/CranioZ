"""Contract tests for ProjectIndex implementations.

Parametrizable: the same suite runs against `InMemoryProjectIndex`
today and against `SqliteProjectIndex` when Phase 8 delivers it.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime

import pytest

from cranioz.application.project.in_memory_index import InMemoryProjectIndex
from cranioz.application.project.index import ProjectIndex
from cranioz.domain.project.project_id import ProjectId
from cranioz.domain.project.project_status import ProjectStatus
from cranioz.domain.project.project_summary import ProjectSummary


def _now() -> datetime:
    return datetime(2026, 1, 1, 12, 0, tzinfo=UTC)


def _summary(project_id: str = "p-001", name: str = "Case 001") -> ProjectSummary:
    return ProjectSummary(
        project_id=ProjectId(project_id),
        project_name=name,
        patient_display_name="Gabriel Silva",
        status=ProjectStatus.ACTIVE,
        procedure="orthognathic",
        created_at=_now(),
        updated_at=_now(),
        last_opened_at=None,
    )


# Parametrize by factory so SqliteProjectIndex can be added later
# without rewriting the suite. Each factory returns a fresh, empty
# index.
_INDEX_FACTORIES: tuple[Callable[[], ProjectIndex], ...] = (InMemoryProjectIndex,)


@pytest.fixture(params=_INDEX_FACTORIES, ids=lambda f: f.__name__)
def index(request: pytest.FixtureRequest) -> ProjectIndex:
    factory = request.param
    return factory()


# ----- add / lookup --------------------------------------------------


def test_lookup_missing_returns_none(index: ProjectIndex) -> None:
    assert index.lookup(ProjectId("missing")) is None


def test_add_then_lookup(index: ProjectIndex) -> None:
    summary = _summary()
    index.add(summary)
    assert index.lookup(summary.project_id) == summary


def test_add_is_upsert(index: ProjectIndex) -> None:
    """Adding a summary with the same id replaces the previous one.

    This is the mechanism through which ProjectUpdated events are
    reflected in the index (ADR-0016 §2.1).
    """
    first = _summary(name="First")
    second = _summary(name="Second")
    index.add(first)
    index.add(second)
    assert index.lookup(first.project_id) == second
    assert index.count() == 1


# ----- remove --------------------------------------------------------


def test_remove_missing_is_noop(index: ProjectIndex) -> None:
    index.remove(ProjectId("missing"))
    assert index.count() == 0


def test_remove_existing(index: ProjectIndex) -> None:
    summary = _summary()
    index.add(summary)
    index.remove(summary.project_id)
    assert index.lookup(summary.project_id) is None
    assert index.count() == 0


# ----- list_summaries / list_ids -------------------------------------


def test_list_summaries_empty(index: ProjectIndex) -> None:
    assert index.list_summaries() == ()


def test_list_ids_empty(index: ProjectIndex) -> None:
    assert index.list_ids() == ()


def test_list_summaries_returns_tuple(index: ProjectIndex) -> None:
    index.add(_summary("p-001"))
    index.add(_summary("p-002"))
    result = index.list_summaries()
    assert isinstance(result, tuple)
    assert len(result) == 2


def test_list_ids_returns_tuple(index: ProjectIndex) -> None:
    index.add(_summary("p-001"))
    result = index.list_ids()
    assert isinstance(result, tuple)
    assert ProjectId("p-001") in result


# ----- count / contains ----------------------------------------------


def test_count_empty(index: ProjectIndex) -> None:
    assert index.count() == 0


def test_count_after_add(index: ProjectIndex) -> None:
    index.add(_summary("p-001"))
    index.add(_summary("p-002"))
    assert index.count() == 2


def test_contains_false_when_empty(index: ProjectIndex) -> None:
    assert index.contains(ProjectId("missing")) is False


def test_contains_true_after_add(index: ProjectIndex) -> None:
    summary = _summary()
    index.add(summary)
    assert index.contains(summary.project_id) is True


# ----- replace_all ---------------------------------------------------


def test_replace_all_discards_previous(index: ProjectIndex) -> None:
    index.add(_summary("p-old"))
    index.replace_all([_summary("p-new")])
    assert index.lookup(ProjectId("p-old")) is None
    assert index.lookup(ProjectId("p-new")) is not None
    assert index.count() == 1


def test_replace_all_with_empty_clears(index: ProjectIndex) -> None:
    index.add(_summary("p-001"))
    index.replace_all([])
    assert index.count() == 0


def test_replace_all_is_atomic(index: ProjectIndex) -> None:
    index.add(_summary("p-old"))
    index.replace_all([_summary("p-a"), _summary("p-b")])
    assert index.count() == 2
    assert index.contains(ProjectId("p-a"))
    assert index.contains(ProjectId("p-b"))
    assert not index.contains(ProjectId("p-old"))
