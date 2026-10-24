"""FlowSummary — lightweight read-only projection."""

from __future__ import annotations

from dataclasses import dataclass

from cranioz.application.flows.definition import FlowDefinition


@dataclass(frozen=True)
class FlowSummary:
    """Lightweight projection of a flow for the Home Page.

    Carries only what the ``FlowList`` needs to render a row: the flow
    id, the translation key for the display name, and the number of
    steps. Step details are loaded on demand.
    """

    flow_id: str
    name_key: str
    step_count: int

    def __post_init__(self) -> None:
        if not self.flow_id:
            raise ValueError("FlowSummary.flow_id must not be empty")
        if not self.name_key:
            raise ValueError("FlowSummary.name_key must not be empty")
        if self.step_count < 1:
            raise ValueError(f"FlowSummary.step_count must be >= 1, got {self.step_count}")

    @classmethod
    def from_definition(cls, definition: FlowDefinition) -> FlowSummary:
        return cls(
            flow_id=definition.flow_id,
            name_key=definition.name_key,
            step_count=definition.step_count(),
        )
