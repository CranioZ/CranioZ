"""Tests for FlowCatalog and InMemoryFlowRepository."""

from __future__ import annotations

import pytest

from cranioz.application.flows.catalog import FlowCatalog
from cranioz.application.flows.definition import (
    FlowDefinition,
    FlowStep,
)
from cranioz.application.flows.errors import (
    FlowCorrupted,
    FlowNotFound,
)
from cranioz.application.flows.in_memory_repository import (
    InMemoryFlowRepository,
)
from cranioz.application.flows.repository import FlowRepository


def _step(step_id: str = "s1") -> FlowStep:
    return FlowStep(step_id=step_id, name_key=f"steps.{step_id}", module_id="m")


def _flow(flow_id: str, steps: tuple[FlowStep, ...] = (_step(),)) -> FlowDefinition:
    return FlowDefinition(
        flow_id=flow_id,
        name_key=f"flows.{flow_id}",
        version=1,
        steps=steps,
    )


@pytest.fixture
def repository() -> InMemoryFlowRepository:
    return InMemoryFlowRepository()


@pytest.fixture
def catalog(repository: InMemoryFlowRepository) -> FlowCatalog:
    return FlowCatalog(repository=repository)


def test_repository_satisfies_protocol(
    repository: InMemoryFlowRepository,
) -> None:
    assert isinstance(repository, FlowRepository)


def test_empty_catalog(catalog: FlowCatalog) -> None:
    assert catalog.list_flows() == ()
    assert catalog.count() == 0
    assert catalog.is_empty() is True


def test_add_then_list(repository: InMemoryFlowRepository) -> None:
    repository.add(_flow("orthognathic"))
    catalog = FlowCatalog(repository=repository)
    summaries = catalog.list_flows()
    assert len(summaries) == 1
    assert summaries[0].flow_id == "orthognathic"
    assert summaries[0].step_count == 1


def test_get_flow(repository: InMemoryFlowRepository) -> None:
    repository.add(_flow("orthognathic"))
    catalog = FlowCatalog(repository=repository)
    flow = catalog.get_flow("orthognathic")
    assert flow.flow_id == "orthognathic"


def test_get_flow_missing_raises(catalog: FlowCatalog) -> None:
    with pytest.raises(FlowNotFound):
        catalog.get_flow("unknown")


def test_get_flow_summary_returns_none(catalog: FlowCatalog) -> None:
    assert catalog.get_flow_summary("unknown") is None


def test_contains(repository: InMemoryFlowRepository) -> None:
    repository.add(_flow("orthognathic"))
    catalog = FlowCatalog(repository=repository)
    assert catalog.contains("orthognathic") is True
    assert catalog.contains("unknown") is False


def test_search_empty_returns_all(
    repository: InMemoryFlowRepository,
) -> None:
    repository.add(_flow("a"))
    repository.add(_flow("b"))
    catalog = FlowCatalog(repository=repository)
    assert len(catalog.search_flows("")) == 2
    assert len(catalog.search_flows("   ")) == 2


def test_search_matches_name_key(
    repository: InMemoryFlowRepository,
) -> None:
    repository.add(_flow("orthognathic"))
    repository.add(_flow("implants"))
    catalog = FlowCatalog(repository=repository)
    result = catalog.search_flows("ortho")
    assert len(result) == 1
    assert result[0].flow_id == "orthognathic"


def test_corrupted_flow_is_invisible(
    repository: InMemoryFlowRepository,
) -> None:
    repository.add(_flow("ok"))
    repository.add(_flow("bad"))
    repository._mark_corrupted("bad")
    catalog = FlowCatalog(repository=repository)
    assert catalog.count() == 1
    with pytest.raises(FlowCorrupted):
        catalog.get_flow("bad")
