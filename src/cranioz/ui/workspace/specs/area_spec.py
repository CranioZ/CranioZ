"""AreaSpec.

Declarative description of an Area produced by a Module.

An AreaSpec declares the identity of an Area, its semantic placement,
and the Editor Layout Tree it hosts.
"""

from __future__ import annotations

from dataclasses import dataclass

from cranioz.ui.workspace.areas.placement import Placement
from cranioz.ui.workspace.specs.editor_layout_spec import EditorLayoutSpec


class AreaSpecError(ValueError):
    """Raised when an AreaSpec violates structural rules."""


@dataclass(frozen=True)
class AreaSpec:
    """Declarative description of an Area."""

    area_id: str
    title: str
    placement: Placement
    editor_layout: EditorLayoutSpec

    def __post_init__(self) -> None:
        if not self.area_id:
            raise AreaSpecError("area_id must not be empty")
        if not self.title:
            raise AreaSpecError("title must not be empty")