"""EditorRegistry.

Registers Editor classes by identifier and creates instances.

Rules:
- The Registry registers types, not instances.
- The Registry resolves editor_id to a class (type[Editor]).
- Creating an instance delegates to the Editor's own constructor;
  the caller supplies the editor_id, title, and any extra keyword
  arguments the concrete Editor requires.
- Availability and enablement are not decided here; they are the
  responsibility of the EditorCatalog, which filters registered
  types by context.
- Re-registering the same identifier with the same class is
  idempotent; with a different class it raises ValueError.
- Resolving or creating an unknown identifier raises KeyError.
"""

from __future__ import annotations

from typing import Any

from cranioz.ui.editors.base_editor import Editor


class EditorRegistryError(ValueError):
    """Raised when registration violates a structural rule."""


class EditorRegistry:
    """Registry of Editor classes by identifier."""

    def __init__(self) -> None:
        self._types: dict[str, type[Editor]] = {}

    def register(self, editor_id: str, editor_type: type[Editor]) -> None:
        """Register an Editor class under editor_id.

        Idempotent when the same class is registered again.
        Raises EditorRegistryError when a different class is already
        registered under the same identifier, or when editor_id is
        empty.
        """
        if not editor_id:
            raise EditorRegistryError("editor_id must not be empty")
        if editor_id in self._types:
            if self._types[editor_id] is editor_type:
                return
            raise EditorRegistryError(
                f"editor_id already registered with a different type: {editor_id}"
            )
        self._types[editor_id] = editor_type

    def unregister(self, editor_id: str) -> None:
        """Remove a class. No-op if the identifier is not registered."""
        self._types.pop(editor_id, None)

    def resolve(self, editor_id: str) -> type[Editor]:
        """Return the class registered for editor_id.

        Raises KeyError if unknown.
        """
        try:
            return self._types[editor_id]
        except KeyError as exc:
            raise KeyError(f"editor_id not registered: {editor_id}") from exc

    def create(self, id_: str, **kwargs: Any) -> Editor:
        """Create a new Editor instance for the given editor id.

        The first parameter is named `id_` to avoid colliding with a
        keyword argument named `editor_id` that concrete Editors may
        accept in their constructors.

        The caller supplies keyword arguments accepted by the concrete
        Editor constructor. If none are given, the Editor must be
        constructible with no arguments.

        Raises KeyError if unknown.
        """
        editor_type = self.resolve(id_)
        return editor_type(**kwargs)

    def identifiers(self) -> tuple[str, ...]:
        """Return the registered identifiers in registration order."""
        return tuple(self._types.keys())

    def contains(self, editor_id: str) -> bool:
        """Return True if the identifier is registered."""
        return editor_id in self._types
