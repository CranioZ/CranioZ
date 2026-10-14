"""PatientHabits.

Lifestyle factors relevant to surgical planning.

All fields are free-form text. Empty strings are accepted as the
default state.

If structured data is needed later (frequency, quantity,
duration), this section can be promoted to a set of value objects
without affecting the Patient aggregate.

See ADR-0004 §12 for the design rationale.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PatientHabits:
    """Habits and addictions of the patient (§9)."""

    smoking: str = ""
    alcohol: str = ""
    drug_use: str = ""
