"""PatientMedications (§7 Medicamentos e Alergias).

Current and past medication, plus allergies.

All fields are free-form text. Empty strings are accepted as the
default state. The ``allergies`` field is flagged with a warning in
the prototype; the domain treats it as a free-form string today, but
the UI is expected to present it prominently.

If structured allergy records (allergen, reaction, severity) become
necessary, they will be introduced as a dedicated value object
without affecting this section.

See ADR-0004 §10 for the design rationale.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PatientMedications:
    """Medications and allergies of the patient (§7)."""

    current_medications: str = ""
    previous_medications: str = ""
    allergies: str = ""
