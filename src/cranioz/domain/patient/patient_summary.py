"""PatientSummary.

Lightweight read-only projection of a Patient.

The PatientSummary is designed for contexts where the full Patient
record is not needed: project listings, tooltips, breadcrumbs, and
the ProjectContext handed to the Workspace. It carries only the
fields required to *identify* and *display* the patient without
loading their complete clinical record.

The summary is a value object. It is derived from a Patient but is
not the Patient itself, and it does not carry any clinical data
(no medical history, no imaging references).

Derivation rules (see ADR-0004 §13):

- ``display_name`` is produced by ``Patient.display_name()``, which
  prefers ``identity.social_name`` when set, and falls back to
  ``identity.full_name``.
- ``birth_date`` and ``sex`` are taken directly from
  ``Patient.identity``.

The summary is a frozen value object. It is not updated when the
Patient changes; callers that need the current state must call
``Patient.summary()`` again.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from cranioz.domain.patient.enums.patient_sex import PatientSex
from cranioz.domain.patient.value_objects.patient_id import PatientId


@dataclass(frozen=True)
class PatientSummary:
    """Lightweight read-only projection of a Patient."""

    patient_id: PatientId
    display_name: str
    birth_date: date | None
    sex: PatientSex | None

    def __post_init__(self) -> None:
        if not self.display_name:
            raise ValueError("display_name must not be empty")
        if not self.display_name.strip():
            raise ValueError("display_name must not be whitespace only")
