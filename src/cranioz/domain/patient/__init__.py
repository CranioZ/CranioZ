"""Patient domain.

The Patient domain defines the person associated with clinical data
in CranioZ. A Patient is a domain entity referenced by a Project.

The Patient is composed of nine section value objects, one per
functional section of the patient record (see ADR-0004):

    Patient
    ├── identity:        PatientIdentity          (§1 Identificação)
    ├── documents:       PatientDocuments         (§2 Documentos e Contato)
    ├── filiation:       PatientFiliation         (§3 Filiação)
    ├── address:         PatientAddress           (§4 Endereço)
    ├── complaint:       PatientComplaint         (§5 Queixa e História)
    ├── comorbidities:   PatientComorbidities     (§6 Comorbidades)
    ├── medications:     PatientMedications       (§7 Medicamentos e Alergias)
    ├── antecedents:     PatientAntecedents       (§8 Antecedentes)
    └── habits:          PatientHabits            (§9 Hábitos e Vícios)

Public API:

- PatientId              — stable identity value object
- PatientSex             — sex enum
- PatientRace            — race/color enum (IBGE categories)
- BloodType              — combined ABO + Rh enum
- DocumentType           — identity document kind enum
- PhoneKind              — phone kind enum
- PhoneNumber            — phone number + kind value object
- ComorbidityCategory    — comorbidity category enum

- PatientIdentity        — §1 Identificação
- PatientDocuments       — §2 Documentos e Contato
- PatientFiliation       — §3 Filiação
- PatientAddress         — §4 Endereço
- PatientComplaint       — §5 Queixa e História
- PatientComorbidities   — §6 Comorbidades
- PatientMedications     — §7 Medicamentos e Alergias
- PatientAntecedents     — §8 Antecedentes
- PatientHabits          — §9 Hábitos e Vícios

- PatientSummary         — lightweight read-only projection
- Patient                — aggregate root
"""

from cranioz.domain.patient.enums.blood_type import BloodType
from cranioz.domain.patient.enums.comorbidity_category import (
    ComorbidityCategory,
)
from cranioz.domain.patient.enums.document_type import DocumentType
from cranioz.domain.patient.enums.patient_race import PatientRace
from cranioz.domain.patient.enums.patient_sex import PatientSex
from cranioz.domain.patient.enums.phone_kind import PhoneKind
from cranioz.domain.patient.patient import Patient
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
from cranioz.domain.patient.value_objects.phone_number import PhoneNumber

__all__ = [
    "BloodType",
    "ComorbidityCategory",
    "DocumentType",
    "Patient",
    "PatientAddress",
    "PatientAntecedents",
    "PatientComorbidities",
    "PatientComplaint",
    "PatientDocuments",
    "PatientFiliation",
    "PatientHabits",
    "PatientId",
    "PatientIdentity",
    "PatientMedications",
    "PatientRace",
    "PatientSex",
    "PatientSummary",
    "PhoneKind",
    "PhoneNumber",
]
