"""FlowRepository — persistence port."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from cranioz.application.flows.definition import FlowDefinition
from cranioz.application.flows.summary import FlowSummary


@runtime_checkable
class FlowRepository(Protocol):
    """Persistence port for flows.

    Implementations must raise ``FlowNotFound``, ``FlowCorrupted``, or
    ``FlowError`` for every documented failure mode. They must not raise
    ``OSError`` or JSON ``DecodeError`` to the caller.
    """

    def list_summaries(self) -> tuple[FlowSummary, ...]: ...

    def list_ids(self) -> tuple[str, ...]: ...

    def get(self, flow_id: str) -> FlowDefinition: ...

    def exists(self, flow_id: str) -> bool: ...
