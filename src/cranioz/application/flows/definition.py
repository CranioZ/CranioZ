"""FlowDefinition and FlowStep — declarative flow content."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class FlowStep:
    """One step of a clinical flow.

    Steps are ordered. ``module_id`` is the id of the Module that
    handles this step. ``name_key`` is a translation key for the
    user-facing label.
    """

    step_id: str
    name_key: str
    module_id: str

    def __post_init__(self) -> None:
        if not self.step_id:
            raise ValueError("FlowStep.step_id must not be empty")
        if not self.name_key:
            raise ValueError("FlowStep.name_key must not be empty")
        if not self.module_id:
            raise ValueError("FlowStep.module_id must not be empty")


@dataclass(frozen=True)
class FlowDefinition:
    """A clinical flow, loaded from ``flow.json``."""

    flow_id: str
    name_key: str
    version: int
    steps: tuple[FlowStep, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.flow_id:
            raise ValueError("FlowDefinition.flow_id must not be empty")
        if not self.name_key:
            raise ValueError("FlowDefinition.name_key must not be empty")
        if self.version < 1:
            raise ValueError(f"FlowDefinition.version must be >= 1, got {self.version}")
        if not self.steps:
            raise ValueError("FlowDefinition.steps must not be empty")
        ids = [s.step_id for s in self.steps]
        if len(ids) != len(set(ids)):
            raise ValueError("FlowDefinition.steps must have unique step_ids")

    def step_count(self) -> int:
        return len(self.steps)
