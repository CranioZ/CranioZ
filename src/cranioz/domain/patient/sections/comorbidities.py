"""PatientComorbidities (§6 Comorbidades).

Comorbidities, one field per category.

Each category is a free-form text field. Empty strings are accepted
as the default state. The categories are enumerated by
``ComorbidityCategory``, which the UI uses to iterate over fields
with translated labels.

The section keeps each category as a named field, not as a dict.
This gives the type system explicit knowledge of each category and
keeps serialization stable and self-documenting.

See ADR-0004 §9 for the design rationale.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PatientComorbidities:
    """Comorbidities of the patient (§6)."""

    cardiovascular: str = ""
    respiratory: str = ""
    gastrointestinal: str = ""
    hematological: str = ""
    endocrine: str = ""
    renal: str = ""
    hepatic: str = ""
    neurological: str = ""
    musculoskeletal: str = ""
    infectious_diseases: str = ""
    others: str = ""
