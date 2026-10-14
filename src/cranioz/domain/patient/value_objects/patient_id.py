"""PatientId.

A PatientId is a value object that uniquely identifies a Patient
within the CranioZ application. Like ProjectId, it is deliberately
distinct from any human-readable field: a patient's name can change,
but their PatientId must remain stable for the lifetime of the
record.

The identifier is stored as a string to remain agnostic of the
underlying generator (UUID, institutional ID, slug, etc.). The
domain does not enforce a specific format; it only enforces that
the identifier is non-empty.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PatientId:
    """Stable identifier of a Patient."""

    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("PatientId.value must not be empty")
        if not self.value.strip():
            raise ValueError("PatientId.value must not be whitespace only")

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"PatientId({self.value!r})"
