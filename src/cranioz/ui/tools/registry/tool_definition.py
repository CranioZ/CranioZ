"""Tool contract.

A Tool is an interaction contract: it describes what the user can
trigger and when it is available. It does not depend on Qt.

This module lives in ui/tools/registry/ because a Tool is materialized
by a Toolbar, which is a UI component. Tools are declared by Modules,
but their contract is a UI-facing interaction contract.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass(frozen=True)
class ToolContext:
    """Minimal execution context passed to a Tool.

    Concrete fields will be added as the tool system grows. This is
    intentionally small.
    """

    extras: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class Tool(Protocol):
    """Tool contract.

    Implementations must expose these attributes and methods.
    No Qt dependency is required by the contract itself.
    """

    identifier: str
    label: str
    description: str
    icon: str | None
    category: str | None

    def is_available(self, context: ToolContext) -> bool: ...

    def is_enabled(self, context: ToolContext) -> bool: ...
