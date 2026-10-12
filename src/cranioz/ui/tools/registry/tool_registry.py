"""ToolRegistry.

Registers Tool implementations by identifier and creates instances.

Rules:
- The Registry registers types, not instances.
- The Registry resolves tool_id to a factory (a zero-argument callable).
- The Registry does not decide availability or enablement; that is
  the responsibility of the Tool itself via is_available and is_enabled,
  given a ToolContext.
- Re-registering the same identifier raises ValueError unless the same
  type is registered again (idempotent) — this avoids silent overrides.
- Resolving or creating an unknown identifier raises KeyError.
"""

from __future__ import annotations

from collections.abc import Callable

from cranioz.ui.tools.registry.tool_definition import Tool


class ToolRegistryError(ValueError):
    """Raised when registration violates a structural rule."""


ToolFactory = Callable[[], Tool]


class ToolRegistry:
    """Registry of Tool factories by identifier."""

    def __init__(self) -> None:
        self._factories: dict[str, ToolFactory] = {}

    def register(self, tool_id: str, factory: ToolFactory) -> None:
        """Register a factory under tool_id.

        Idempotent for the same factory; raises if a different factory
        is already registered under the same identifier.
        """
        if not tool_id:
            raise ToolRegistryError("tool_id must not be empty")
        if tool_id in self._factories:
            if self._factories[tool_id] is factory:
                return
            raise ToolRegistryError(
                f"tool_id already registered with a different factory: {tool_id}"
            )
        self._factories[tool_id] = factory

    def unregister(self, tool_id: str) -> None:
        """Remove a factory. No-op if the identifier is not registered."""
        self._factories.pop(tool_id, None)

    def resolve(self, tool_id: str) -> ToolFactory:
        """Return the factory for tool_id.

        Raises KeyError if unknown.
        """
        try:
            return self._factories[tool_id]
        except KeyError as exc:
            raise KeyError(f"tool_id not registered: {tool_id}") from exc

    def create(self, tool_id: str) -> Tool:
        """Create a new Tool instance for tool_id.

        Raises KeyError if unknown.
        """
        return self.resolve(tool_id)()

    def identifiers(self) -> tuple[str, ...]:
        """Return the registered identifiers in registration order."""
        return tuple(self._factories.keys())

    def contains(self, tool_id: str) -> bool:
        """Return True if the identifier is registered."""
        return tool_id in self._factories
