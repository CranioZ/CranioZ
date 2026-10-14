"""Patient.

Aggregate root of the Patient domain.

A Patient is the person associated with clinical data in CranioZ.
Within the CranioZ architecture, there is no separate PatientManager:
the patient's lifecycle is managed through the Project Manager, in
the context of the projects that reference the patient.

The Patient is composed of nine section value objects, one per
functional section of the patient record (see ADR-0004):

    Patient
    ├── identity:        PatientIdentity          (§1 Identification)
    ├── documents:       PatientDocuments         (§2 Documents and Contact)
    ├── filiation:       PatientFiliation         (§3 Parentage)
    ├── address:         PatientAddress           (§4 Address)
    ├── complaint:       PatientComplaint         (§5 Complaint and History)
    ├── comorbidities:   PatientComorbidities     (§6 Comorbidities)
    ├── medications:     PatientMedications       (§7 Medications and Allergies)
    ├── antecedents:     PatientAntecedents       (§8 Medical History)
    └── habits:          PatientHabits            (§9 Habits and Addictions)

Design rules (see ADR-0004 §2 and §5):

- The Patient carries the PatientId, the nine section value objects,
  and the cross-section invariants.
- Cross-section invariants are enforced by this aggregate, not by
  the sections. Sections are responsible only for the invariants
  they can verify in isolation.
- The Patient does not carry references to imaging, meshes,
  photographs, odontogram, or documents. Those entities reference
  the Patient, not the other way around.
- There is no ``extras`` dict. If a future piece genuinely needs a
  free-form escape hatch, it will be reintroduced with a specific
  purpose.
- The Patient is mutable, because it is the entity through which
  updates are coordinated. The section value objects are immutable.

Cross-section invariants enforced here:

1. Women's health applicability. The fields
   ``antecedents.pregnancy_contraception`` and
   ``antecedents.breastfeeding`` are meaningful only when
   ``identity.sex is PatientSex.FEMALE``. When the sex is not
   FEMALE (including ``None``), both fields must be empty.

Document coherence and insurance coherence are enforced by
``PatientDocuments`` itself, because they depend only on fields
inside that section.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from cranioz.domain.patient.enums.patient_sex import PatientSex
from cranioz.domain.patient.patient_summary import PatientSummary
from cranioz.domain.patient.sections.address import PatientAddress
from cranioz.domain.patient.sections.antecedents import PatientAntecedents
from cranioz.domain.patient.sections.comorbidities import (
    PatientComorbidities,
)
from cranioz.domain.patient.sections.complaint import PatientComplaint
from cranioz.domain.patient.sections.documents import PatientDocuments
from cranioz.domain.patient.sections.filiation import PatientFiliation
from cranioz.domain.patient.sections.habits import PatientHabits
from cranioz.domain.patient.sections.identity import PatientIdentity
from cranioz.domain.patient.sections.medications import PatientMedications
from cranioz.domain.patient.value_objects.patient_id import PatientId


@dataclass
class Patient:
    """Aggregate root of the Patient domain."""

    patient_id: PatientId
    identity: PatientIdentity
    documents: PatientDocuments
    filiation: PatientFiliation
    address: PatientAddress
    complaint: PatientComplaint
    comorbidities: PatientComorbidities
    medications: PatientMedications
    antecedents: PatientAntecedents
    habits: PatientHabits

    # ----- Validation -------------------------------------------------

    def __post_init__(self) -> None:
        self._validate_womens_health_applicability()

    def _validate_womens_health_applicability(self) -> None:
        """Enforce the cross-section invariant on women's health.

        The fields of ``antecedents.pregnancy_contraception`` and
        ``antecedents.breastfeeding`` are meaningful only when the
        patient's sex is ``FEMALE``. When the sex is not FEMALE
        (including ``None``), both fields must be empty.
        """
        sex = self.identity.sex
        if sex is PatientSex.FEMALE:
            return

        if self.antecedents.pregnancy_contraception:
            raise ValueError(
                "antecedents.pregnancy_contraception must be empty when identity.sex is not FEMALE"
            )
        if self.antecedents.breastfeeding:
            raise ValueError(
                "antecedents.breastfeeding must be empty when identity.sex is not FEMALE"
            )

    # ----- Convenience -----------------------------------------------

    def display_name(self) -> str:
        """Return the name used to present the patient in the UI.

        The rule (ADR-0004 §13): prefer ``identity.social_name``
        when set, and fall back to ``identity.full_name``.
        """
        if self.identity.social_name:
            return self.identity.social_name
        return self.identity.full_name

    def age(self, at_date: date | None = None) -> int | None:
        """Return the patient's age in years.

        Returns ``None`` when the birth date is not recorded.

        The reference date defaults to today. The computation
        accounts for whether the birthday has already occurred in
        the reference year: a person born on 2000-12-31 is 25 on
        2026-01-01, not 26.
        """
        if self.identity.birth_date is None:
            return None
        ref = at_date if at_date is not None else date.today()
        years = ref.year - self.identity.birth_date.year
        # Subtract one if the birthday has not yet occurred in ref.
        if (ref.month, ref.day) < (
            self.identity.birth_date.month,
            self.identity.birth_date.day,
        ):
            years -= 1
        return years

    def summary(self) -> PatientSummary:
        """Return a lightweight projection of this Patient.

        See ``PatientSummary`` for the derivation rules.
        """
        return PatientSummary(
            patient_id=self.patient_id,
            display_name=self.display_name(),
            birth_date=self.identity.birth_date,
            sex=self.identity.sex,
        )

    # ----- Representation --------------------------------------------

    def __repr__(self) -> str:
        return (
            f"Patient(patient_id={self.patient_id.value!r}, display_name={self.display_name()!r})"
        )

    def __eq__(self, other: object) -> bool:
        """Two patients are equal if they share the same PatientId.

        This makes Patient usable in sets and as dict keys, and it
        is consistent with the identity semantics of a domain
        entity. The value objects inside the aggregate are
        compared by value (frozen dataclasses), so the id is the
        only discriminating field that matters at the aggregate
        level.
        """
        if not isinstance(other, Patient):
            return NotImplemented
        return self.patient_id == other.patient_id

    def __hash__(self) -> int:
        """Hash based on PatientId, consistent with ``__eq__``."""
        return hash(self.patient_id)
