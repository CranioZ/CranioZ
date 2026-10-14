# Patient

## 1. Purpose

The Patient domain defines the person associated with clinical data
in CranioZ. A Patient is a domain entity referenced by a Project;
it is the subject of the clinical planning workflow.

This document defines the concepts, responsibilities, structure,
and boundaries of the Patient domain. It is the reference for:

- The contract between the domain and the application layer.
- The mapping between the domain model and the UI (the Patient
  module in the Workspace).
- The persistence format consumed by the Project Repository.

The Patient domain is **independent of Qt, filesystem, persistence
technology, and any infrastructure concern**. It is a pure Python
package with no external dependencies beyond the standard library.

---

## 2. Architectural role

A Patient is a **domain entity**. It is not:

- A Project. The Project is the persistent clinical container; the
  Patient is the person referenced by it.
- An application authority. Within CranioZ, there is no
  `PatientManager`. The patient's lifecycle is managed through the
  Project Manager, in the context of the projects that reference
  the patient. This decision is deliberate (see `project_pt.md`
  §3): it prevents competing ownership between `PatientManager`
  and `ProjectManager`.
- A UI concept. The Patient module in the Workspace presents and
  edits the Patient, but the Patient itself has no knowledge of the
  UI.
- A container of unrelated clinical data. Imaging volumes, 3D
  meshes, photographs, odontogram data, and documents do **not**
  belong to the Patient. They belong to the Project and reference
  the Patient.

The distinction is important: it prevents the Patient from
becoming a "god object" that accumulates every datum somehow
related to the person.

---

## 3. Composed-by-sections design

The Patient is composed of **nine value objects**, one per
functional section of the patient record. Each section is a
frozen dataclass, testable in isolation, and carries no
knowledge of the other sections.

    Patient
    ├── identity: PatientIdentity (§1 Identificação)
    ├── documents: PatientDocuments (§2 Documentos e Contato)
    ├── filiation: PatientFiliation (§3 Filiação)
    ├── address: PatientAddress (§4 Endereço)
    ├── complaint: PatientComplaint (§5 Queixa e História)
    ├── comorbidities: PatientComorbidities (§6 Comorbidades)
    ├── medications: PatientMedications (§7 Medicamentos e Alergias)
    ├── antecedents: PatientAntecedents (§8 Antecedentes)
    └── habits: PatientHabits (§9 Hábitos e Vícios)


This composition is a deliberate design choice. The alternative — a
single dataclass with ~40 fields — is functionally equivalent but
harder to maintain, test, and evolve. With composition:

- Each section is a small, focused value object.
- Adding a field to one section does not touch the others.
- Each section can be validated, serialized, and tested on its own.
- The UI can render sections independently, in any order, using
  the section's own layout rules.

The Patient itself is the aggregate root. It carries the
`PatientId`, the composition of sections, and the **cross-section
invariants** (see §11). It is mutable, because it is the entity
through which updates are coordinated. The sections are immutable.

---

## 4. Section §1 — Identificação

The identity of the patient within the clinical record.

| Field | Type | Required | Notes |
|---|---|---|---|
| `full_name` | `str` | yes | Legal name. Non-empty, non-whitespace. |
| `social_name` | `str \| None` | no | Chosen name, when different from legal name. |
| `birth_date` | `date \| None` | no | Date of birth. |
| `sex` | `PatientSex \| None` | no | `MALE`, `FEMALE`, `OTHER`. |
| `race` | `PatientRace` | yes | IBGE categories. Defaults to `NAO_DECLARADA`. |
| `nationality` | `str \| None` | no | Free-form country name. |
| `blood_type` | `BloodType` | yes | Combined ABO + Rh. Defaults to `UNKNOWN`. |

**Age** is not stored. It is a computed property on the Patient:
`age(at_date: date | None = None) -> int | None`. When `birth_date`
is `None`, `age` returns `None`. The reference date defaults to
`date.today()`.

**PatientSex** is distinct from gender identity. It records the
biological sex relevant to clinical planning. If gender identity
becomes relevant to the domain, it will be introduced as a separate
field.

**PatientRace** uses the categories defined by the Brazilian IBGE.
The field is required at the domain level (defaulting to
`NAO_DECLARADA`) so that "not declared" is explicit, not missing.

---

## 5. Section §2 — Documentos e Contato

Identity documents and contact information.

| Field | Type | Required | Notes |
|---|---|---|---|
| `document_type` | `DocumentType \| None` | no | `RG`, `CPF`, `CNH`, `PASSAPORTE`, `OUTRO`. |
| `document_number` | `str \| None` | conditional | Required when `document_type` is set. |
| `phone_primary` | `PhoneNumber \| None` | no | Main phone, with kind. |
| `phone_secondary` | `PhoneNumber \| None` | no | Optional secondary phone. |
| `email` | `str \| None` | no | Email address. |
| `health_insurance` | `str \| None` | no | Health insurance name (free-form). |
| `insurance_card_number` | `str \| None` | conditional | Required when `health_insurance` is set. |
| `notes` | `str` | no | Free-form. Defaults to `""`. |

**Conditional rules** (enforced in `PatientDocuments.__post_init__`):

- If `document_type` is set, `document_number` must be non-empty.
- If `document_type` is `None`, `document_number` must be `None`.
- If `health_insurance` is set, `insurance_card_number` must be
  non-empty.
- If `health_insurance` is `None`, `insurance_card_number` must be
  `None`.

**PhoneNumber** is a value object composed of `number: str` and
`kind: PhoneKind`. The number itself is free-form: the domain does
not enforce a phone format.

**Health insurance** is a free-form string today. If the list of
insurances needs metadata (ANS code, contact, etc.), it will be
promoted to an entity referenced by the domain.

---

## 6. Section §3 — Filiação

The patient's parents.

| Field | Type | Required | Notes |
|---|---|---|---|
| `father_name` | `str \| None` | no | Free-form. |
| `mother_name` | `str \| None` | no | Free-form. |

Filiation is used primarily for identification and administrative
purposes, not for clinical decisions.

---

## 7. Section §4 — Endereço

The patient's address.

| Field | Type | Required | Notes |
|---|---|---|---|
| `postal_code` | `str \| None` | no | CEP, ZIP, or equivalent. |
| `street` | `str \| None` | no | |
| `number` | `str \| None` | no | Street number, free-form (can contain "S/N"). |
| `complement` | `str \| None` | no | |
| `district` | `str \| None` | no | Neighborhood. |
| `city` | `str \| None` | no | |
| `state` | `str \| None` | no | State or province. |
| `country` | `str \| None` | no | Country. |

All fields are optional. A patient may not have an address on
record. The domain does not validate postal codes or addresses:
that is a localization concern that belongs to the UI.

---

## 8. Section §5 — Queixa e História

The clinical complaint at the time of the consultation.

| Field | Type | Required | Notes |
|---|---|---|---|
| `chief_complaint` | `str` | no | Defaults to `""`. |
| `present_illness_history` | `str` | no | Defaults to `""`. |

This section is intentionally minimal. It captures the *narrative*
that begins the clinical encounter. Structured clinical data
(diagnoses, findings) belong to the Project, not to the Patient.

---

## 9. Section §6 — Comorbidades

Comorbidities, one field per category.

| Field | Type | Required | Notes |
|---|---|---|---|
| `cardiovascular` | `str` | no | Defaults to `""`. |
| `respiratory` | `str` | no | |
| `gastrointestinal` | `str` | no | |
| `hematological` | `str` | no | |
| `endocrine` | `str` | no | |
| `renal` | `str` | no | |
| `hepatic` | `str` | no | |
| `neurological` | `str` | no | |
| `musculoskeletal` | `str` | no | |
| `infectious_diseases` | `str` | no | |
| `others` | `str` | no | Free-form for anything not covered. |

The categories are defined by `ComorbidityCategory`, which the UI
uses to iterate over fields with translated labels. The domain
keeps each category as a **named field**, not as a dict, so that:

- The type system knows each category.
- Validation is explicit per category.
- Serialization is stable and self-documenting.

Each field is a free-form text today. If a category needs
structured data later (e.g., a list of diagnoses with codes), it
can be promoted to its own value object without affecting the
other categories.

---

## 10. Section §7 — Medicamentos e Alergias

Current and past medication, plus allergies.

| Field | Type | Required | Notes |
|---|---|---|---|
| `current_medications` | `str` | no | Defaults to `""`. |
| `previous_medications` | `str` | no | Defaults to `""`. |
| `allergies` | `str` | no | **Critical.** Defaults to `""`. |

The `allergies` field is flagged with a warning icon in the
prototype. It has no special semantic status in the domain beyond
being a free-form string, but the UI is expected to present it
prominently. If the domain later requires structured allergy
records (allergen, reaction, severity), a dedicated value object
will be introduced.

---

## 11. Section §8 — Antecedentes

The patient's history beyond the current complaint, organized in
four subsections.

### §8.1 Histórico Cirúrgico

| Field | Type | Required | Notes |
|---|---|---|---|
| `previous_surgeries` | `str` | no | Defaults to `""`. |
| `anesthesia_history` | `str` | no | **Critical.** Defaults to `""`. |

### §8.2 Dispositivos e Implantes

| Field | Type | Required | Notes |
|---|---|---|---|
| `prostheses_implants` | `str` | no | Defaults to `""`. |

### §8.3 Antecedentes Familiares

| Field | Type | Required | Notes |
|---|---|---|---|
| `family_history` | `str` | no | Defaults to `""`. |

### §8.4 Saúde da Mulher (condicional)

| Field | Type | Required | Notes |
|---|---|---|---|
| `pregnancy_contraception` | `str` | no | Defaults to `""`. |
| `breastfeeding` | `str` | no | Defaults to `""`. |

**Conditional rule** (enforced at the `Patient` level, not at the
section level): the fields of §8.4 are meaningful only when the
patient's sex is `FEMALE`. The `Patient` aggregate enforces that,
when the sex is not `FEMALE`, both fields are empty. If the sex is
`None` (not recorded), the section is treated as not applicable.

This rule is enforced by the aggregate because it depends on a
field that lives in a different section (`identity.sex`). The
section itself does not know about the patient's sex.

---

## 12. Section §9 — Hábitos e Vícios

Lifestyle factors relevant to surgical planning.

| Field | Type | Required | Notes |
|---|---|---|---|
| `smoking` | `str` | no | Defaults to `""`. |
| `alcohol` | `str` | no | Defaults to `""`. |
| `drug_use` | `str` | no | Defaults to `""`. |

Free-form text. If structured data is needed later (frequency,
quantity, duration), the section can be promoted to a set of value
objects without affecting the Patient aggregate.

---

## 13. PatientSummary

`PatientSummary` is a lightweight read-only projection of the
Patient, used in contexts where the full record is not needed:

- The Project Catalog, to render patient names in project listings.
- The ProjectContext, to give the Workspace the patient's identity
  without loading the full record.
- Tooltips, breadcrumbs, and other brief UI elements.

The summary carries:

- `patient_id: PatientId`
- `display_name: str`
- `birth_date: date | None`
- `sex: PatientSex | None`

`display_name` is derived from the Patient: it prefers
`identity.social_name` when set, falling back to
`identity.full_name`. This matches common clinical and
administrative practice.

The summary is frozen and does not carry any clinical data. It does
not carry the section composition. It is a value object, not the
Patient.

---

## 14. Value objects and enums

The Patient domain defines the following value objects and enums:

| Name | Kind | Purpose |
|---|---|---|
| `PatientId` | value object | Stable identity of the patient. |
| `PatientSex` | enum | `MALE`, `FEMALE`, `OTHER`. |
| `PatientRace` | enum | IBGE categories. |
| `BloodType` | enum | Combined ABO + Rh. |
| `DocumentType` | enum | `RG`, `CPF`, `CNH`, `PASSPORT`, `OTHER`. |
| `PhoneKind` | enum | `MOBILE`, `HOME`, `WORK`, `OTHER`. |
| `PhoneNumber` | value object | Number + kind. |
| `ComorbidityCategory` | enum | 11 categories of comorbidities. |
| `PatientIdentity` | value object | §1. |
| `PatientDocuments` | value object | §2. |
| `PatientFiliation` | value object | §3. |
| `PatientAddress` | value object | §4. |
| `PatientComplaint` | value object | §5. |
| `PatientComorbidities` | value object | §6. |
| `PatientMedications` | value object | §7. |
| `PatientAntecedents` | value object | §8. |
| `PatientHabits` | value object | §9. |
| `PatientSummary` | value object | Lightweight projection. |
| `Patient` | aggregate root | The patient itself. |

---

## 15. Domain invariants

The Patient aggregate enforces the following invariants:

1. **Identity is complete.** `full_name` is non-empty and
   non-whitespace.
2. **Document coherence.** If `document_type` is set,
   `document_number` is non-empty; and vice versa.
3. **Insurance coherence.** If `health_insurance` is set,
   `insurance_card_number` is non-empty; and vice versa.
4. **Women's health applicability.** The fields of
   `antecedents.pregnancy_contraception` and
   `antecedents.breastfeeding` must be empty when
   `identity.sex` is not `FEMALE`.
5. **Blood type is a valid value.** Enforced by the `BloodType`
   enum.
6. **Race is a valid value.** Enforced by the `PatientRace` enum.

Invariants that depend on multiple sections (2, 3, 4) are enforced
by the aggregate's `__post_init__`, not by the sections
themselves. Each section is responsible only for the invariants it
can verify in isolation.

---

## 16. What does NOT belong to the Patient

To avoid the "god object" trap, the following concepts belong to
the Project or to dedicated entities, not to the Patient:

- **Imaging volumes (DICOM, CT, CBCT).** Belong to the Project.
  Reference the Patient.
- **3D meshes (STL, OBJ, PLY).** Belong to the Project.
- **Clinical photographs.** Belong to the Project.
- **Odontogram (teeth, procedures).** Will be a dedicated entity
  referencing the Patient.
- **Documents (anamneses, prescriptions, certificates).** Will be
  dedicated entities referencing the Patient and the Project.
- **Surgical planning data (osteotomies, splints, guides).**
  Belong to the Project.

The Patient does not carry a list of these. It does not carry
paths, IDs, or references to them. The relationship is *inverted*:
those entities reference the Patient, not the other way around.

This inversion is what keeps the Patient a clean, focused entity.

---

## 17. Persistence

The Patient is persisted as part of the Project. The persistence
format is defined by the Project Repository and the persistence
specification.

The domain does not concern itself with:

- The serialization format (JSON, database, etc.).
- The physical location of the data.
- The schema version of the Patient representation.

The Project Repository is responsible for translating the Patient
domain object to and from its persistent representation. The
mapping is defined in the persistence specification, not here.

This separation allows the persistence format to evolve without
changing the domain model.

---

## 18. Related documents

- `project_pt.md` — the Project Management boundary. Explains why
  there is no separate `PatientManager`.
- `objects.md` — the general Object model.
- `docs/architecture/domain/README.md` — index of domain
  documentation.

---

## 19. Summary

The Patient domain defines the person associated with clinical data
in CranioZ. It is a composed entity with nine sections, each a
small value object. It is independent of Qt, filesystem, and
infrastructure. It is referenced by the Project and by the entities
that will be introduced in later pieces (imaging, photographs,
odontogram, documents).

The Patient is intentionally **not** a container of clinical data.
It is the *subject* of the clinical data, not its holder.