"""Area.

An Area is a structural container that hosts Editors. It provides
the space where Editors are placed; it does not decide where it is
placed within the Workspace.

Rules:
- An Area has a stable id, a title, and a placement.
- The placement expresses the Area's semantic role in the Workspace
  (CENTRAL, LEFT, RIGHT, BOTTOM). It is a property of the Area,
  because the Area needs to know its role to be rendered correctly
  even when empty.
- The Area does not know where it is placed in the Workspace. Placement
  is a semantic role, not a position. Positions are decided by the
  LayoutTree.
- The Area does not know what its Editors do. It provides add/remove
  and activation, nothing more.
- The Area does not materialize Toolbars. Toolbars are internal to
  Editors (see ADR-0002).
- The Area does not know about Modules, Scenes, Commands, or the
  Workspace. It is a UI container.
- An Area may be empty (zero Editors). This is a valid state,
  especially for the CENTRAL Area, which must always exist as a
  container even when it hosts nothing.

This is a pure UI container. It has no Qt dependency at this level;
the widget materialization is the LayoutRenderer's job.
"""

from __future__ import annotations

from cranioz.ui.editors.base_editor import Editor
from cranioz.ui.workspace.areas.placement import Placement


class AreaError(ValueError):
    """Raised when an Area operation violates a structural rule."""


class Area:
    """A structural container that hosts Editors."""

    def __init__(
        self,
        area_id: str,
        title: str,
        placement: Placement,
    ) -> None:
        if not area_id:
            raise AreaError("area_id must not be empty")
        if not title:
            raise AreaError("title must not be empty")

        self._area_id = area_id
        self._title = title
        self._placement = placement
        self._editors: list[Editor] = []
        self._active_editor_id: str | None = None
        self._visible = True

    # ----- Identity ---------------------------------------------------

    @property
    def area_id(self) -> str:
        return self._area_id

    @property
    def title(self) -> str:
        return self._title

    @property
    def placement(self) -> Placement:
        return self._placement

    # ----- Visibility -------------------------------------------------

    @property
    def visible(self) -> bool:
        return self._visible

    def show(self) -> None:
        self._visible = True

    def hide(self) -> None:
        self._visible = False

    # ----- Editor management -----------------------------------------

    def add_editor(self, editor: Editor) -> None:
        """Add an Editor to this Area.

        Raises AreaError if an Editor with the same editor_id is
        already hosted by this Area.
        """
        for existing in self._editors:
            if existing.editor_id == editor.editor_id:
                raise AreaError(
                    f"editor_id already hosted by this Area: {editor.editor_id}"
                )
        self._editors.append(editor)
        if self._active_editor_id is None:
            self._active_editor_id = editor.editor_id

    def remove_editor(self, editor_id: str) -> Editor | None:
        """Remove an Editor by editor_id.

        Returns the removed Editor, or None if not found.
        If the removed Editor was active, the next hosted Editor
        becomes active. If no Editors remain, the active id is cleared.
        Removing the last Editor does NOT remove the Area. An empty
        Area is a valid state, especially for the CENTRAL Area.
        """
        for index, editor in enumerate(self._editors):
            if editor.editor_id == editor_id:
                removed = self._editors.pop(index)
                if self._active_editor_id == editor_id:
                    self._active_editor_id = (
                        self._editors[0].editor_id if self._editors else None
                    )
                return removed
        return None

    def editors(self) -> tuple[Editor, ...]:
        """Return the hosted Editors in insertion order."""
        return tuple(self._editors)

    def get_editor(self, editor_id: str) -> Editor | None:
        """Return the Editor with the given editor_id, or None."""
        for editor in self._editors:
            if editor.editor_id == editor_id:
                return editor
        return None

    def contains(self, editor_id: str) -> bool:
        """Return True if an Editor with the given id is hosted."""
        return any(e.editor_id == editor_id for e in self._editors)

    def editor_count(self) -> int:
        """Return the number of hosted Editors."""
        return len(self._editors)

    def is_empty(self) -> bool:
        """Return True if the Area hosts no Editors."""
        return not self._editors

    # ----- Active Editor ---------------------------------------------

    @property
    def active_editor_id(self) -> str | None:
        return self._active_editor_id

    @property
    def active_editor(self) -> Editor | None:
        if self._active_editor_id is None:
            return None
        return self.get_editor(self._active_editor_id)

    def set_active_editor(self, editor_id: str) -> None:
        """Set the active Editor by editor_id.

        Raises AreaError if the Editor is not hosted by this Area.
        """
        if not self.contains(editor_id):
            raise AreaError(
                f"editor_id is not hosted by this Area: {editor_id}"
            )
        self._active_editor_id = editor_id

    # ----- Representation --------------------------------------------

    def __repr__(self) -> str:
        return (
            f"Area(area_id={self._area_id!r}, "
            f"title={self._title!r}, "
            f"placement={self._placement.value!r}, "
            f"visible={self._visible}, "
            f"editors={len(self._editors)}, "
            f"active={self._active_editor_id!r})"
        )
