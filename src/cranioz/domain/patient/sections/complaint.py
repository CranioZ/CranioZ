"""PatientComplaint (§5 Queixa e História).

The narrative of the clinical encounter: the chief complaint and
the history of the present illness.

Both fields are free-form text. Empty strings are accepted as the
default state. This section is intentionally minimal: it captures
the narrative that begins the encounter. Structured clinical data
(diagnoses, findings) belongs to the Project, not to the Patient.

See ADR-0004 §8 for the design rationale.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PatientComplaint:
    """Chief complaint and present illness history (§5)."""

    chief_complaint: str = ""
    present_illness_history: str = ""
