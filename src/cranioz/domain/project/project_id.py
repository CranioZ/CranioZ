"""ProjectId.

A ProjectId is a value object that uniquely identifies a Project
within the CranioZ application. It is deliberately distinct from
the project's display name, the patient's identity, and the
filesystem path: those can all change, but the ProjectId must remain
stable for the lifetime of the project.

The identifier is stored as a string to remain agnostic of the
underlying generator (UUID4, ULID, a slug, etc.). The domain does
not enforce a specific format; it only enforces that the identifier
is non-empty.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProjectId:
    """Stable identifier of a Project."""

    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("ProjectId.value must not be empty")
        if not self.value.strip():
            raise ValueError("ProjectId.value must not be whitespace only")

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"ProjectId({self.value!r})"
