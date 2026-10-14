Status: Accepted
Date: 2026-10-13
Deciders: Architecture team
Related: ADR-0001_Area_and_Editor.md, ADR-0002_EditorContext_and_Toolbar_Materialization.md,
         ADR-0003_UI_Widgets_and_Editor_Overlays.md,
         project_pt.md, patient.md, Prototipagem_UI_08.pdf

---

# 1. Context

The Patient domain is the clinical subject of CranioZ. A Patient is
the person associated with the imaging, planning, and documents of
a case. The domain model for the Patient must be decided before the
Patient module is implemented, because the model drives:

- The structure of the `cranioz.domain.patient` package.
- The contract between the domain and the application layer.
- The mapping between the domain and the Patient module UI.
- The persistence format consumed by the Project Repository.
- The relationship between the Patient and other domain entities
  (imaging, documents, odontogram, photographs).

The Patient module UI (Prototipagem_UI_08.pdf) presents the patient
record as **nine functional sections**:

1. Identificação
2. Documentos e Contato
3. Filiação
4. Endereço
5. Queixa e História
6. Comorbidades
7. Medicamentos e Alergias
8. Antecedentes (with four subsections: cirúrgico, dispositivos e
   implantes, familiares, saúde da mulher)
9. Hábitos e Vícios

Three design questions had to be answered before implementation:

1. **Composition.** Should the Patient be a single dataclass with
   ~40 fields, or should it be composed of value objects, one per
   functional section?
2. **Boundary.** Should the Patient carry references to the imaging,
   photographs, odontogram, and documents associated with the
   person, or should those entities be separated and reference the
   Patient?
3. **Conditional invariants.** Should rules that depend on fields in
   different sections (e.g., "women's health fields must be empty
   when the patient is not female") be enforced by each section, or
   by the aggregate?

The contradiction that motivated this ADR: the initial draft of the
Patient domain (piece 7.2) proposed a minimal model with a single
`medical_history: str` field and an `extras: dict` placeholder.
This model was insufficient for the sections required by the
prototype, and it invited a "god object" pattern. A decision was
needed on how to structure the domain correctly before expanding
it.

This ADR records the resolution.

---

# 2. Decision

## 2.1 Composition by sections

The Patient is **composed of nine value objects**, one per
functional section:

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


Each section is a frozen dataclass. Each section is testable in
isolation. Each section carries no knowledge of the other
sections.

The Patient itself is the aggregate root. It carries the
`PatientId`, the composition of the nine sections, and the
cross-section invariants.

## 2.2 Boundary: entities that reference the Patient

The following concepts do **not** belong to the Patient:

- Imaging volumes (DICOM, CT, CBCT)
- 3D meshes (STL, OBJ, PLY)
- Clinical photographs
- Odontogram (teeth, procedures)
- Documents (anamneses, prescriptions, certificates)
- Surgical planning data (osteotomies, splints, guides)

These entities belong to the Project, or to dedicated entities that
reference both the Patient and the Project. The relationship is
**inverted**: those entities reference the Patient, not the other
way around.

The Patient does not carry a list of them. It does not carry paths,
IDs, or references to them.

## 2.3 Cross-section invariants are enforced by the aggregate

Rules that depend on fields living in **different sections** are
enforced by the `Patient.__post_init__`, not by the sections
themselves.

Rules that depend only on fields inside a single section are
enforced by that section's `__post_init__`.

The distinction is deliberate: a section is responsible only for
the invariants it can verify in isolation. Any rule that needs
information from another section is an aggregate concern.

## 2.4 Value objects and enums

The domain defines the following value objects and enums:

| Name | Kind | Purpose |
|---|---|---|
| `PatientId` | value object | Stable identity of the patient. |
| `PatientSex` | enum | `MALE`, `FEMALE`, `OTHER`. |
| `PatientRace` | enum | IBGE categories. |
| `BloodType` | enum | Combined ABO + Rh. |
| `DocumentType` | enum | `RG`, `CPF`, `CNH`, `PASSPORT`, `OTHER`. |
| `PhoneKind` | enum | `MOBILE`, `HOME`, `WORK`, `OTHER`. |
| `PhoneNumber` | value object | Number + kind. |
| `ComorbidityCategory` | enum | 11 categories. |
| `PatientIdentity` ... `PatientHabits` | value objects | §1–§9. |
| `PatientSummary` | value object | Lightweight projection. |
| `Patient` | aggregate root | The patient itself. |

## 2.5 No `PatientManager`

Consistent with `project_pt.md` §3, there is no `PatientManager`.
The Patient is a domain entity referenced by a Project. The
patient's lifecycle is managed through the Project Manager, in the
context of the projects that reference the patient.

## 2.6 Age is computed, not stored

The Patient exposes `age(at_date: date | None = None) -> int | None`.
The value is derived from `identity.birth_date`. It is not stored.
This avoids a redundant field that would become stale.

---

# 3. Rationale

## 3.1 The prototype requires the structure

The Patient module UI presents the record as nine sections. A
single dataclass with ~40 fields would force the UI to know the
field list of every section, and would make partial updates
(e.g., saving only the §6 Comorbidades section) awkward. The
composed model matches the UI structure and makes partial updates
natural.

## 3.2 Composition prevents the "god object"

The naive reading of the prototype would put imaging, photographs,
odontogram, and documents *inside* the Patient. This is a known
anti-pattern: the entity accumulates data that is not intrinsic to
its identity. With composition and inversion:

- The Patient stays focused on the person.
- Each supporting entity (imaging, odontogram, document) references
  the Patient and lives on its own.
- The Patient's persistence format stays small and stable.

This mirrors the Object model (`objects.md`), where clinical
semantics and data representations are separated.

## 3.3 The aggregate is the right boundary for cross-section rules

A rule like "women's health fields must be empty when the patient
is not female" depends on `identity.sex` and
`antecedents.pregnancy_contraception`. If the rule lived in
`PatientAntecedents`, the section would need a reference to the
patient's sex, coupling the two sections. If the rule lived in
`PatientIdentity`, the section would need to know about the
antecedents, which is worse. The aggregate is the only boundary
that already knows about both, and it is the natural place for
rules that span sections.

## 3.4 Value objects are cheap and testable

Each section is a small frozen dataclass. Tests for a section do
not need to construct the whole Patient. Tests for the aggregate
focus on the cross-section invariants, not on the internal
validations of each section.

This keeps the test suite fast and the failures localized: when a
section validation fails, the failing test is about that section,
not about the Patient aggregate.

## 3.5 Consistency with existing ADRs

- **ADR-0001** establishes the Area / Editor distinction. This ADR
  applies the same principle to the domain: identity of the entity
  vs. content associated with it.
- **ADR-0002** establishes the hybrid context model for Editors.
  This ADR does not touch the UI layer; it stays in the domain.
- **ADR-0003** establishes the three homes for UI widgets. The
  Patient module UI will use those homes; the domain does not.

The ADR is therefore additive: it does not contradict any previous
decision.

---

# 4. Consequences

## 4.1 Positive consequences

- **Clear separation of concerns.** Each section has a single
  responsibility. Adding a field to one section does not affect the
  others.
- **Testable in isolation.** Each section and each enum is tested
  independently. The aggregate tests focus on cross-section rules.
- **The Patient stays a domain entity, not a container.** Imaging,
  photographs, odontogram, and documents are separate.
- **The UI structure mirrors the domain structure.** The nine
  sections of the prototype are the nine value objects of the
  domain.
- **Persistence is modular.** Each section can be serialized
  independently. A partial update touches only one section.
- **i18n is clean.** Each section's fields have stable identifiers
  for translation keys.
- **Future extensions are local.** Promoting a free-form field to a
  structured value object (e.g., turning `allergies: str` into a
  list of `Allergy` records) affects only that section.

## 4.2 Negative consequences

- **More files.** Nine sections plus nine enums plus value objects
  means ~18 files in `cranioz.domain.patient`. This is more files
  than a single dataclass would require. The trade-off is
  accepted: the files are small, focused, and testable.
- **Cross-section invariants live in the aggregate.** Developers
  must know that some rules are not in the section that appears to
  "own" the field. The ADR documents this clearly, and the
  aggregate is the only place that can enforce them.
- **Some redundancy between section and aggregate.** The aggregate
  must construct and validate the sections. This is minor
  boilerplate, not a design smell.

## 4.3 Neutral consequences

- **`extras: dict` is removed.** The initial draft had a placeholder
  `extras` dict. It is gone. If a future piece genuinely needs a
  free-form escape hatch, it will be reintroduced with a specific
  purpose.
- **`medical_history: str` is decomposed.** The initial draft had a
  single free-form field. It is replaced by eight fields across
  §5 (Queixa e História), §6 (Comorbidades), §7 (Medicamentos e
  Alergias), and §8 (Antecedentes).
- **The field names are in English in the code.** The prototype
  uses Portuguese labels. This is consistent with the rest of the
  codebase and the i18n approach.

---

# 5. Rules applied by this ADR

1. The Patient is composed of nine section value objects, one per
   functional section of the record.
2. Each section is a frozen dataclass, independent of the other
   sections.
3. The Patient is the aggregate root. It carries the `PatientId`,
   the sections, and the cross-section invariants.
4. Cross-section invariants are enforced by `Patient.__post_init__`,
   not by individual sections.
5. Imaging, meshes, photographs, odontogram, and documents are
   separate entities that reference the Patient. They are not part
   of the Patient.
6. There is no `PatientManager`. The Patient's lifecycle is managed
   through the Project Manager.
7. Age is computed from `birth_date`. It is not stored.
8. `PatientSummary` is a lightweight projection carrying only
   `patient_id`, `display_name`, `birth_date`, and `sex`.
9. `display_name` prefers `identity.social_name` and falls back to
   `identity.full_name`.
10. All value objects are frozen. The `Patient` aggregate is
    mutable, because it is the boundary through which updates are
    coordinated.
11. Field names are in English in the code. User-facing labels are
    localized via i18n.
12. The domain layer has no dependency on Qt, filesystem,
    persistence technology, or any infrastructure concern.

---

# 6. Alternatives considered

## 6.1 Single dataclass with ~40 fields

Rejected. Would force the UI to know the field list of every
section. Would make partial updates awkward. Would obscure the
structure that the prototype already establishes.

## 6.2 Composition with sections as nested dicts

Rejected. A dict loses the type information and makes validation
implicit. The section structure is known at design time; it should
be encoded in the type system, not in a runtime lookup.

## 6.3 Composition with sections as a flat hierarchy (no aggregate)

Rejected. Some invariants depend on fields in different sections
(e.g., women's health fields vs. patient sex). Without an
aggregate to enforce them, the invariant would either be
duplicated in two sections or enforced only at the application
layer, which is worse.

## 6.4 Patient carries references to imaging, photographs, etc.

Rejected. This would make the Patient a "god object". The
supporting entities reference the Patient, not the other way
around. This mirrors the Object model of the rest of the
architecture.

## 6.5 A `PatientManager` parallel to the `ProjectManager`

Rejected. Consistent with `project_pt.md` §3: the Patient is a
domain entity referenced by a Project. A separate manager would
create competing ownership with the `ProjectManager`. The
patient's lifecycle is managed in the context of the projects
that reference it.

## 6.6 Age stored as a field

Rejected. Age is derived from `birth_date`. Storing it would
create a redundant field that becomes stale. Computing it on
demand is correct and cheap.

## 6.7 Fields in Portuguese in the code

Rejected. The codebase uses English for identifiers. The prototype
uses Portuguese for labels. i18n bridges the two. Mixing languages
in the code would be inconsistent with the rest of the project.

---

# 7. Example

## 7.1 A minimal Patient

```python
from datetime import date

from cranioz.domain.patient import (
    BloodType,
    Patient,
    PatientAddress,
    PatientAntecedents,
    PatientComorbidities,
    PatientComplaint,
    PatientDocuments,
    PatientFiliation,
    PatientHabits,
    PatientId,
    PatientIdentity,
    PatientMedications,
    PatientRace,
    PatientSex,
)

patient = Patient(
    patient_id=PatientId("5489"),
    identity=PatientIdentity(
        full_name="Gabriel Silva",
        birth_date=date(1990, 5, 12),
        sex=PatientSex.MALE,
        race=PatientRace.PARDA,
        blood_type=BloodType.O_POSITIVE,
    ),
    documents=PatientDocuments(),
    filiation=PatientFiliation(),
    address=PatientAddress(),
    complaint=PatientComplaint(),
    comorbidities=PatientComorbidities(),
    medications=PatientMedications(),
    antecedents=PatientAntecedents(),
    habits=PatientHabits(),
)

assert patient.display_name() == "Gabriel Silva"
assert patient.age() == 36  # at 2026
```

7.2 A cross-section invariant is enforced

    # A male patient with women's health data is invalid.
    try:
        Patient(
            patient_id=PatientId("p-1"),
            identity=PatientIdentity(
                full_name="X",
                sex=PatientSex.MALE,
            ),
            # ...
            antecedents=PatientAntecedents(
                pregnancy_contraception="Not applicable",
            ),
            # ...
        )
    except ValueError as exc:
        assert "women's health" in str(exc) or "female" in str(exc)

The exact error message is specified in the Patient class.
The important property is: the aggregate rejects the combination,
not the section.

### 7.3 A separate entity references the Patient
Imaging volumes will be introduced in a later piece. Their
relationship to the Patient is:

    # In a future piece:
    @dataclass
    class ImagingVolume:
        volume_id: VolumeId
        patient_id: PatientId   # reference, not ownership
        project_id: ProjectId   # reference, not ownership
        # ... volume data

The Patient does not carry a list of ImagingVolume. The
ImagingVolume carries the patient_id.