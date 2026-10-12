"""ToolSpec.

Declarative descriptor for a Tool, used for registration and discovery.

Different from the Tool Protocol: ToolSpec is data, Tool is behavior.
"""

from __future__ import annotations

from dataclasses import dataclass


class ToolSpecError(ValueError):
    """Raised when a ToolSpec violates structural rules."""


@dataclass(frozen=True)
class ToolSpec:
    """Declarative descriptor for a Tool."""

    identifier: str
    label: str
    description: str = ""
    icon: str | None = None
    category: str | None = None

    def __post_init__(self) -> None:
        if not self.identifier:
            raise ToolSpecError("identifier must not be empty")
        if not self.label:
            raise ToolSpecError("label must not be empty")
