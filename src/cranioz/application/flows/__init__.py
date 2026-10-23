"""Application Flows — clinical workflow definitions (ADR-0009, clinical_workflows.md).

Public API:

- ``FlowDefinition`` — full definition loaded from ``flow.json``.
- ``FlowStep`` — one step of a flow.
- ``FlowSummary`` — lightweight projection for the Home Page.
- ``FlowRepository`` — persistence port (Protocol).
- ``InMemoryFlowRepository`` — reference implementation for tests.
- ``FlowCatalog`` — read-only projection (list, get, search).
- ``FlowError`` and subclasses — application-level errors.

The package is data + projection. It does not execute flows; the
``WorkflowEngine`` (Phase 5) is responsible for execution.
"""

from cranioz.application.flows.catalog import FlowCatalog
from cranioz.application.flows.definition import (
    FlowDefinition,
    FlowStep,
)
from cranioz.application.flows.errors import (
    FlowCorrupted,
    FlowError,
    FlowNotFound,
    FlowStorageError,
)
from cranioz.application.flows.in_memory_repository import (
    InMemoryFlowRepository,
)
from cranioz.application.flows.repository import FlowRepository
from cranioz.application.flows.summary import FlowSummary

__all__ = [
    "FlowCatalog",
    "FlowCorrupted",
    "FlowDefinition",
    "FlowError",
    "FlowNotFound",
    "FlowRepository",
    "FlowStep",
    "FlowStorageError",
    "FlowSummary",
    "InMemoryFlowRepository",
]
