"""SpatialRelationship — a typed relationship between two objects.

Relationships are not parent-child hierarchies (those are handled by
Scene.set_parent). A relationship is a semantic link between two
objects that is not a spatial containment.

Examples:
- Registration(CT, IOS)
- AttachedTo(Plate, Mandible)
- DerivedFrom(OsteotomySegment, Mandible)

The Scene stores relationships; the algorithms that establish them
belong to domain or application services.

See scene.md §13.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class SpatialRelationship:
    """A typed relationship between two objects."""

    relationship_type: str
    source_id: str
    target_id: str
    directed: bool = True
    data: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.relationship_type:
            raise ValueError("relationship_type must not be empty")
        if not self.source_id:
            raise ValueError("source_id must not be empty")
        if not self.target_id:
            raise ValueError("target_id must not be empty")
