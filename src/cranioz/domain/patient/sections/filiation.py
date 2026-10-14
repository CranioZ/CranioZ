"""PatientFiliation (§3 Filiação).

The patient's parents. Used primarily for identification and
administrative purposes, not for clinical decisions.

Both fields are optional and free-form. The domain does not enforce
any structure on names.

See ADR-0004 §6 for the design rationale.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PatientFiliation:
    """Filiation of the patient (§3)."""

    father_name: str | None = None
    mother_name: str | None = None

    def __post_init__(self) -> None:
        if self.father_name is not None and not self.father_name.strip():
            raise ValueError("father_name must not be whitespace only when set")
        if self.mother_name is not None and not self.mother_name.strip():
            raise ValueError("mother_name must not be whitespace only when set")
