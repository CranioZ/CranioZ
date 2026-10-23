"""FlowCatalog — read-only projection for the Home Page.

The catalog delegates every call to the repository. It does not cache.
It does not execute flows. It does not load step details until
``get_flow`` is called.
"""

from __future__ import annotations

from cranioz.application.flows.definition import FlowDefinition
from cranioz.application.flows.repository import FlowRepository
from cranioz.application.flows.summary import FlowSummary


class FlowCatalog:
    """Read-only projection of flows known to a repository."""

    def __init__(self, repository: FlowRepository) -> None:
        self._repository = repository

    def list_flows(self) -> tuple[FlowSummary, ...]:
        return self._repository.list_summaries()

    def get_flow(self, flow_id: str) -> FlowDefinition:
        return self._repository.get(flow_id)

    def get_flow_summary(self, flow_id: str) -> FlowSummary | None:
        for summary in self._repository.list_summaries():
            if summary.flow_id == flow_id:
                return summary
        return None

    def search_flows(self, query: str) -> tuple[FlowSummary, ...]:
        normalized = query.strip().lower()
        all_summaries = self._repository.list_summaries()
        if not normalized:
            return all_summaries
        matches: list[FlowSummary] = []
        for summary in all_summaries:
            # Search by name_key (translated later by the UI).
            if normalized in summary.name_key.lower():
                matches.append(summary)
        return tuple(matches)

    def count(self) -> int:
        return len(self._repository.list_summaries())

    def is_empty(self) -> bool:
        return len(self._repository.list_summaries()) == 0

    def contains(self, flow_id: str) -> bool:
        return self._repository.exists(flow_id)
