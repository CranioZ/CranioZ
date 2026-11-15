"""AreaLayoutSpec — declarative layout of Editors inside an Area.

Mirrors ViewLayoutSpec (ADR-0013 §2.4) at the Area level.

Sprint G: SINGLE and SPLIT are materialized. STACK is declared and
reserved for Sprint H (EditorStack). The renderer raises
``NotImplementedError`` for STACK until Sprint H implements it, so
that enabling STACK by accident is a loud, testable failure instead
of a silent fallback to the current splitter behavior.

The spec is pure data: no Qt, no Editor instances. It is computed by
the AreaLayoutRenderer from the Area's Editors (``_resolve_spec``).
When Sprint H adds the Editor Layout Tree (ADR-0013 §2.2) to the
Area, the spec becomes the input of that tree, and the renderer
switches to ``_render_stack`` without changing the public render()
contract.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class AreaLayoutType(Enum):
    """How Editors are arranged inside a single Area."""

    #: Exactly one Editor fills the entire Area.
    SINGLE = "single"

    #: Two or more Editors arranged side by side in a QSplitter.
    #: This is the current behavior when an Area hosts multiple
    #: Editors. It is a placeholder for the real Editor Layout Tree
    #: (ADR-0013 §2.2), which arrives with the EditorStack (Sprint H).
    SPLIT = "split"

    #: Two or more Editors arranged as tabs (EditorStack).
    #: Reserved for Sprint H. Not yet materialized.
    STACK = "stack"


@dataclass(frozen=True)
class AreaLayoutSpec:
    """Declarative layout of Editors inside an Area.

    Invariants (validated in ``__post_init__``):

    - ``editor_ids`` is non-empty.
    - ``SINGLE`` requires exactly one editor_id.
    - ``SPLIT`` requires at least two editor_ids.
    - ``STACK`` requires at least one editor_id.
    """

    type: AreaLayoutType
    editor_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.editor_ids:
            raise ValueError("AreaLayoutSpec requires at least one editor_id")

        if self.type is AreaLayoutType.SINGLE:
            if len(self.editor_ids) != 1:
                raise ValueError(
                    "AreaLayoutType.SINGLE requires exactly one editor_id, "
                    f"got {len(self.editor_ids)}"
                )
        elif self.type is AreaLayoutType.SPLIT:
            if len(self.editor_ids) < 2:
                raise ValueError(
                    "AreaLayoutType.SPLIT requires at least two editor_ids, "
                    f"got {len(self.editor_ids)}"
                )
        elif self.type is AreaLayoutType.STACK:
            # STACK requires at least one editor_id (already checked
            # above). No further constraint: a single-editor stack is
            # a valid degenerate case for Sprint H.
            pass
        else:
            raise ValueError(f"unknown AreaLayoutType: {self.type!r}")
