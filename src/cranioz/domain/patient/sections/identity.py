"""PatientIdentity (§1 Identificação).

The identity of the patient within the clinical record.

This section carries the fields that answer "who is this person":
the legal name, the optional social name, the birth date, the
biological sex, the self-declared race/color, the nationality, the
blood type, and the optional reference to the patient's
identification photo.

Rules:

- ``full_name`` is required and non-empty (whitespace-only values
  are rejected).
- ``social_name`` is optional. When set, it must be non-empty and
  not whitespace-only.
- ``race`` defaults to ``NOT_DECLARED``, which is a valid explicit
  value distinct from "not applicable".
- ``blood_type`` defaults to ``UNKNOWN``, for the common case where
  the blood type is not recorded at the first consultation.
- ``photo_reference`` is optional. When set, it is a logical
  resource name (e.g., ``"patient/photo/portrait"``) resolved by
  the ``ProjectPathResolver``. The domain does not interpret the
  reference; it only enforces that it is non-empty when set.

The section does not compute the patient's age. Age is a property of
the Patient aggregate (``Patient.age()``), because it depends on a
reference date and is derived, not stored.

See ADR-0004 §4 for the design rationale.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from cranioz.domain.patient.enums.blood_type import BloodType
from cranioz.domain.patient.enums.patient_race import PatientRace
from cranioz.domain.patient.enums.patient_sex import PatientSex


@dataclass(frozen=True)
class PatientIdentity:
    """Identity of the patient (§1 Identificação)."""

    full_name: str
    social_name: str | None = None
    birth_date: date | None = None
    sex: PatientSex | None = None
    race: PatientRace = PatientRace.NOT_DECLARED
    nationality: str | None = None
    blood_type: BloodType = BloodType.UNKNOWN
    photo_reference: str | None = None

    def __post_init__(self) -> None:
        if not self.full_name:
            raise ValueError("full_name must not be empty")
        if not self.full_name.strip():
            raise ValueError("full_name must not be whitespace only")
        if self.social_name is not None and not self.social_name.strip():
            raise ValueError(
                "social_name must not be whitespace only when set"
            )
        if self.photo_reference is not None:
            if not self.photo_reference:
                raise ValueError(
                    "photo_reference must not be empty when set"
                )
            if not self.photo_reference.strip():
                raise ValueError(
                    "photo_reference must not be whitespace only"
                )
