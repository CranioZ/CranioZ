"""InMemoryFlowRepository — reference implementation of FlowRepository."""

from __future__ import annotations

from cranioz.application.flows.definition import FlowDefinition
from cranioz.application.flows.errors import (
    FlowCorrupted,
    FlowNotFound,
)
from cranioz.application.flows.summary import FlowSummary


class InMemoryFlowRepository:
    """Reference implementation of ``FlowRepository``."""

    def __init__(self) -> None:
        self._flows: dict[str, FlowDefinition] = {}
        self._corrupted: set[str] = set()

    def _mark_corrupted(self, flow_id: str) -> None:
        self._corrupted.add(flow_id)

    def add(self, flow: FlowDefinition) -> None:
        self._flows[flow.flow_id] = flow
        self._corrupted.discard(flow.flow_id)

    def list_summaries(self) -> tuple[FlowSummary, ...]:
        return tuple(
            FlowSummary.from_definition(f)
            for flow_id, f in self._flows.items()
            if flow_id not in self._corrupted
        )

    def list_ids(self) -> tuple[str, ...]:
        return tuple(self._flows.keys())

    def get(self, flow_id: str) -> FlowDefinition:
        if flow_id in self._corrupted:
            raise FlowCorrupted(
                f"flow is corrupted: {flow_id!r}", flow_id=flow_id
            )
        try:
            return self._flows[flow_id]
        except KeyError as exc:
            raise FlowNotFound(
                f"flow not found: {flow_id!r}", flow_id=flow_id
            ) from exc

    def exists(self, flow_id: str) -> bool:
        return flow_id in self._flows and flow_id not in self._corrupted
