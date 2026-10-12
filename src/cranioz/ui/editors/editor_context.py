"""EditorContext.

Minimal execution context passed to an Editor at initialization.

This is intentionally small. Fields will be added as the UI system
grows. The context is a narrow interface: it does not become a
service locator.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class EditorContext:
    """Minimal execution context passed to an Editor."""

    editor_id: str
    extras: dict[str, Any] = field(default_factory=dict)
