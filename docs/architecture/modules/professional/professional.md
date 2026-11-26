# Professional Module

**Module ID:** `professional`

**Status:** Implementation in progress (Sprint L.2)

**Scope:** Professional profile, administrative management, procedures, documents, schedule, and budgets

**Persistence:** Dedicated SQLite database outside clinical projects (ADR-0018)

**Initial Regional Profile:** `BR` (Brazil)

**Implementation:** L.1 implemented and visually approved on 2026-11-26; L.2 in progress

---

## 1. Purpose

The **Professional Module** manages the surgeon's professional profile and administrative activities.

It provides:

- Professional and clinic information.
- Procedure and specialty catalogs.
- Document templates.
- Appointment scheduling.
- Budgets and budget items.
- Professional attachments, such as logos and signature images.

The module does not manage clinical data. It references patients and projects through their identifiers and integrates with the Patient and Project modules through explicit contracts.

The module works independently of an open clinical project. Its data is stored outside individual projects and can be reused across them.

## 2. Core Principles

1. **Independent persistence:** Professional data is stored outside clinical projects.
2. **Single ownership:** `ProfessionalService` is the only application service responsible for accessing the professional database.
3. **Command-based mutations:** Persistent changes are performed through application Commands.
4. **Patient data ownership:** The Patient Module remains the source of truth for patient information and generated patient documents.
5. **Regional independence:** The domain model must not depend on Brazilian-specific registration types, identifiers, or codes.
6. **Internationalization:** Interface, document, and entity languages are independent.
7. **Data integrity:** Financial values, document versions, and schedule transitions must follow explicit validation rules.
8. **Privacy:** Store only the information required for professional and administrative operations.

## 3. Ownership and Boundaries

### 3.1 Module-owned data

- Professional profile and registrations.
- Practice information.
- Specialty, category, and procedure catalogs.
- Document templates and their versions.
- Appointments and schedule entries.
- Budgets and budget items.
- Professional attachments.
- User-defined translations and catalog entries.

### 3.2 Referenced data

| Data | Owner | Reference |
|---|---|---|
| Patients | Patient Module | `patient_id` |
| Clinical records | Patient Module | Patient-owned records |
| Projects | Project Module | `project_id` |
| Generated patient documents | Patient Module | Document identifier |
| Osteotomy patterns | Shared catalog | ADR-0006 |

The Professional Module must not create, modify, or delete patients or projects.

### 3.3 Patient integration

Patient information is obtained through the Patient Module when needed.

The Professional Module may retain a minimal display label for administrative lists, but it must not store national identifiers or duplicate the patient's complete record.

The display label must contain only the patient's name. It must be removed when the patient is deleted or anonymized.

If the patient cannot be resolved, the interface must display an explicit unavailable-patient state.

Generated patient documents belong to the Patient Module. The Professional Module retains only the generation provenance, including the template version and rendering timestamp.

Temporary files may be created in `exports/`, but they must be cleaned up. Document generation is considered complete only after the Patient Module confirms persistence.

---

## 4. Regionalization and Internationalization

### 4.1 Regional profiles

The module uses a regional profile to provide initial configuration and catalog seeds.

Initial profiles:

- `BR`: Brazil.
- `GENERIC`: No country-specific seeds; language, currency, and regional formats are selected by the user.

The core domain must remain country-independent.

A regional profile may provide:

- Default currency.
- Registration authorities.
- Identifier types.
- Initial specialty and procedure catalogs.
- Document templates.
- Address and telephone formats.
- Regional legal metadata.

Regional profile versions must be recorded. Updating regional seeds must never overwrite user-modified or user-referenced data.

### 4.2 Professional registrations

Registrations must use an extensible model rather than a fixed enum.

Each registration contains:

- Authority.
- Country (`ISO 3166-1`).
- Region (`ISO 3166-2` when applicable).
- Registration number stored as text.
- Primary registration flag.

Authorities may include CRM, CRO, GMC, or user-defined authorities.

For Brazil, CRM registrations require a state identifier.

The professional may have no registrations. If registrations exist, exactly one must be primary. Removing the primary registration must select another registration in the same transaction, when one remains.

### 4.3 Codes and identifiers

Codes must use an extensible structure:

- `CodeSystem`
- `EntityCode`
- `purpose`, such as `DIAGNOSIS` or `PROCEDURE`

Initial code systems may include ICD-10 for diagnosis and TUSS for procedures.

Users may add code systems, but system-defined code-system metadata remains controlled by CranioZ.

Patient identifiers must use a neutral identifier type, such as CPF, SSN, or NIF. The Brazilian CPF is an initial regional option, not a domain-level requirement.

### 4.4 Language

The following language settings are independent:

- **Interface language:** Controlled by application preferences.
- **Document language:** Selected for each generated document.
- **Entity language:** Source language of user-created catalog entries.

English (`en`) is the source language for system keys, built-in definitions, and final fallback.

Document language resolution follows:

1. Template language.
2. Practice language.
3. Regional profile language.
4. English (`en`).

The existing `TranslationService` must be used. The Professional Module must not create a competing translation infrastructure.

User-defined entity translations may be stored separately, using stable entity identifiers.

---

## 5. Persistence

### 5.1 Location

The professional database is stored outside clinical projects.

```text
~/.cranioz/professional/
    professional.db
    templates/
    attachments/
    exports/
```

The application must resolve the actual platform-specific path through the existing configuration-path infrastructure.

The `templates/` directory stores immutable template versions. It must not contain an ambiguous `source/` directory that duplicates the versioned storage model.

The `exports/` directory is temporary staging for generated files, not the permanent owner of patient documents.

### 5.2 Database

SQLite is used for:

- Relational integrity.
- Indexed queries.
- Transactions.
- Schema migrations.
- Local persistence.

The database has a schema version and uses explicit migrations.

The initial profile implementation must use SQLite directly. Temporary JSON persistence is not permitted.

Ownership, database location, schema versioning, migration, access, and
testing are governed by `ADR-0018_Professional_Module_SQLite_Persistence.md`.

### 5.3 Settings

The module uses the `professional.*` settings namespace for interface and presentation preferences.

Examples:

- `professional.ui.navigation_order`
- `professional.ui.visible_sections`
- `professional.ui.last_section`

Professional profile data must not be duplicated in application settings.

`persistent_state()` and `restore_state()` are reserved for Editor visual state.

### 5.4 System preferences

The module consumes application preferences through a read-only `SystemPreferencesProvider` contract.

Relevant preferences include:

- Interface language.
- Formatting locale.
- Date and time format.
- First day of the week.
- Timezone.
- Country preference.

Changes are communicated through `SystemPreferencesChanged`.

Preference changes may update presentation, but must not rewrite historical financial values, document content, or previously stored regional data.

---

## 6. Functional Areas

The module is organized into five main areas.

| Area | Purpose |
|---|---|
| Professional | Professional and practice profile |
| Procedures | Specialty, category, and procedure catalogs |
| Budgets | Budget creation and management |
| Schedule | Appointments, tasks, and scheduled activities |
| Document Templates | Reusable administrative and clinical document templates |

The initial implementation may expose these areas progressively. Their presence in this specification does not mean they must all be implemented in Sprint L.

### 6.1 Professional profile

The profile contains:

- Full name.
- Preferred name.
- Salutation.
- Professional registrations.
- Email and telephone.
- Address.
- Practice information.
- Logo and signature references.
- Regional profile.
- Document language preference.

The initial release supports one practice or clinic per installation.

The model should allow future extension to multiple practice locations, but a complete multi-clinic management system is not part of the initial implementation.

A profile preview must show how professional information will appear in generated documents.

### 6.2 Procedures

The procedure catalog organizes:

- Specialties.
- Categories.
- Procedures.
- Procedure codes.
- Default prices.

Specialties and categories are extensible catalogs, not fixed enums.

Users can create, rename, reorder, and deactivate entries.

System-provided entries use stable identifiers. They must not be physically deleted or overwritten when referenced by user data.

Seed updates must preserve user modifications.

Procedure prices include their currency. A budget cannot contain items with different currencies.

### 6.3 Budgets

A budget contains:

- Unique identifier.
- Patient reference.
- Optional project reference.
- Creation date.
- Expiration date.
- Items.
- Currency.
- Subtotal.
- Absolute discount.
- Total.
- Status.
- Relevant timestamps.

Money must use integer minor units or an equivalent exact decimal representation. Floating-point values must not be used for financial calculations.

Budget items preserve snapshots of procedure descriptions and prices at the time of creation.

Updating the procedure catalog must not change existing budgets.

An explicit action may refresh prices from the catalog.

Supported statuses:

- `DRAFT`
- `SENT`
- `ACCEPTED`
- `REJECTED`
- `CANCELLED`
- `EXPIRED`

Expiration must be derived from the expiration date or updated through an explicit mechanism.

An expired budget may only be accepted after explicit user confirmation.

A sent budget cannot return directly to draft. The user must cancel it or create a duplicate.

Only draft budgets may be deleted.

Budget duplication preserves the original item snapshots. Updating prices is a separate operation.

Budget numbering must be human-readable and sequential. `sent_at` and `accepted_at` must be recorded when applicable.

PDF generation uses the selected document locale and the existing `TranslationService`.

### 6.4 Schedule

The schedule supports:

- Appointments.
- Tasks.
- Blocks.
- Scheduled surgeries.
- Patient references.
- Optional project references.

Appointments use an extensible appointment-type catalog. Initial types are regional seeds, not a closed enum.

Each timed event must satisfy:

- Start before end.
- Positive duration.
- Valid timezone interpretation.

All-day events and tasks without an end time must be supported.

Conflict detection is mandatory. The implementation must define whether conflicts block saving or generate a warning.

The schedule uses the installation's clinic-local timezone. The timezone identifier must be persisted.

Supported appointment states:

- `SCHEDULED`
- `COMPLETED`
- `CANCELLED`
- `NO_SHOW`

Transitions to completed, cancelled, and no-show are terminal by default. Reopening an appointment is an explicit operation that returns it to `SCHEDULED`.

### 6.5 Document templates

Templates support:

- Orientations.
- Contracts.
- Consent terms.
- Prescriptions.
- Certificates.
- Declarations.
- User-defined categories.

Each template has a stable identity independent of its versions.

Template versions are immutable. Editing a template creates a new version and must never overwrite an existing version.

Each version records:

- Version identifier.
- Language (`BCP 47`).
- Jurisdiction, when applicable.
- Creation timestamp.
- Source content.
- Relevant metadata.

Brazilian templates are regional seeds marked with `pt-BR` and appropriate jurisdiction metadata. They are not universal legal documents and must be reviewed for their intended jurisdiction.

English examples may include `en-US` and `en-GB`.

Templates may be soft-deleted. Existing generated documents must retain their original provenance.

Supported placeholders must be explicitly declared and validated before rendering.

Patient-sensitive placeholders must be resolved at generation time through the Patient Module. Preview and logs must not expose sensitive patient information unnecessarily.

---

## 7. Application Architecture

### 7.1 Main components

The module follows the existing CranioZ architecture.

- `ProfessionalModule`: declarative module definition.
- `PROFESSIONAL_UI_SPEC`: Workspace composition owned by the UI Workspace layer.
- `ProfessionalEditor`: concrete Editor implementation.
- `ProfessionalService`: application service and database owner.
- `ProfessionalRepository`: persistence abstraction.
- `ProfessionalCommands`: persistent mutation operations.
- `ProfessionalQueries`: read operations.
- `ProfessionalMigrationService`: database schema migrations.

The Workspace composition layer owns `PROFESSIONAL_UI_SPEC` in
`src/cranioz/ui/workspace/specs/professional.py`. The composition root
is responsible for selecting and registering that spec while registering the Editor.
`ProfessionalModule` remains declarative and must not import Workspace
components or concrete Editors.

The Editor is registered in `EditorRegistry` and hosted by the central Workspace Area.

### 7.2 Commands

Persistent changes must use Commands.

Examples:

**Profile**
- `UpdateProfessionalProfileCommand`

**Catalog**
- `CreateProcedureCommand`
- `UpdateProcedureCommand`
- `DeactivateProcedureCommand`
- `CreateCategoryCommand`
- `UpdateCategoryCommand`

**Templates**
- `CreateDocumentTemplateCommand`
- `CreateDocumentTemplateVersionCommand`
- `DeleteDocumentTemplateCommand`
- `ImportDocumentTemplateCommand`

**Schedule**
- `CreateAppointmentCommand`
- `UpdateAppointmentCommand`
- `CancelAppointmentCommand`
- `CompleteAppointmentCommand`
- `ReopenAppointmentCommand`

**Budgets**
- `CreateBudgetCommand`
- `UpdateBudgetCommand`
- `DeleteBudgetCommand`
- `ChangeBudgetStatusCommand`
- `ExportBudgetPdfCommand`

**Data transfer**
- `BackupProfessionalDataCommand`
- `ExportProfessionalDataCommand`
- `ImportProfessionalDataCommand`
- `RestoreProfessionalDataCommand`

File generation and data transfer may use application services, but persistent state changes must remain explicit and validated.

### 7.3 Data transfer

The module must distinguish:

- **Backup:** Complete recoverable copy of the professional database and associated files.
- **Selective export:** Selected catalogs and templates without patient data.
- **Full export:** Complete professional data package, with a privacy warning.

Packages must include a manifest containing format version, schema version, and stable identifiers.

Import must validate the package before changing the database. Conflicts must be resolved explicitly.

Password-based encryption may be introduced as a separate implementation stage. Until then, database and archive access must be restricted to the operating-system user.

### 7.4 Security and privacy

- Restrict access to the professional data directory.
- Do not write patient identifiers or sensitive document content to logs.
- Warn before exporting archives containing identifying information.
- Apply the same privacy policy to backups and export archives.
- Define backup retention and rotation.
- Keep encryption at rest as an explicit configuration decision.
- Do not retain temporary generated patient documents after successful transfer.

---

## 8. System Widget Catalog and Reuse

The Professional Module must use the system-wide widget catalog as the authoritative reference for reusable UI components.

**Reference:** `docs/architecture/widgets/widget_catalog.md`

### 8.1 Widget selection

Before implementing any UI component, the developer must:

1. Consult `widget_catalog.md` and identify existing components that meet the requirement.
2. Reuse existing system widgets whenever possible.
3. Compose existing widgets when a more specialized interface is required.
4. Implement a new system widget only when a clear reuse case exists beyond the Professional Module.
5. Keep Professional-specific compositions inside the Professional Editor unless another module has a demonstrated need for them.

### 8.2 Architectural classification

Follow the classifications defined in ADR-0003 and `widget_catalog.md`:

- **System Widgets:** Reusable components located in `src/cranioz/ui/widgets/`.
- **Editor Overlays:** Contextual visual components owned by the Editor architecture.
- **Professional Compositions:** Components combining system widgets for Professional-specific workflows. These remain inside the Professional Editor.

Do not place Editor-specific overlays or Professional-specific components in the generic system widget package.

### 8.3 Implementation requirements

When a new reusable widget is justified:

- Define its public API and expected behavior.
- Follow the existing theme, icon, translation, and accessibility contracts.
- Implement unit tests.
- Provide a visual debug harness when appropriate.
- Register the component and its implementation status in `widget_catalog.md`.
- Update the catalog when its API, dependencies, or status changes.

### 8.4 Professional Editor composition

The Professional Editor should be built primarily through composition of existing system widgets.

Examples include:

- `IconSidebar` for internal navigation.
- `CollapsibleSection` for grouped configuration sections.
- `DragList` for configurable ordering.
- `FormField`, `FormCombo`, and `FilePicker` for profile forms.
- `SignaturePreview` for professional signature presentation.
- `DateField` and other form widgets where applicable.

Professional-specific structures, such as `ProfessionalSidebar`, `ProfessionalSectionTree`, and `ProfessionalConfigPanel`, must remain consumer-specific compositions unless a separate system-wide reuse requirement is established.

The widget catalog is an evolving system contract. Its presence does not authorize implementation outside the current roadmap or sprint scope.

# 9. Implementation Plan

The implementation is incremental. The stages below describe the target delivery sequence; they do not create new CranioZ phases or automatically expand Sprint L.

## Stage 0 — Foundation and contracts

**Goal:** Establish the module's technical foundation.

**Implementation**
- Define domain entities and invariants.
- Define repository and service contracts.
- Define the SQLite database location.
- Implement schema versioning and migrations.
- Define regional profile and language contracts.
- Define Patient Module integration boundaries.

**Tests**
- Domain validation tests.
- Repository contract tests.
- SQLite transaction and rollback tests.
- Migration tests.
- Regional profile and language resolution tests.

**Completion criteria**
- Domain contracts are documented.
- Database can be created and migrated.
- Invalid data is rejected.
- Tests pass.

## Stage 1 — Professional profile (Sprint L.1)

**Goal:** Deliver the first functional Professional Editor.

**Status:** Implemented and visually approved on 2026-11-26.

**Implementation**
- Implement `ProfessionalEditor`.
- Register it in `EditorRegistry`.
- Implement the Professional Workspace composition in the UI Workspace layer.
- Host the Editor in the central Area.
- Implement the initial profile interface (Tela 2 of the UI prototype).
- Integrate `professional.*` settings.
- Persist profile data in SQLite.
- Implement profile preview.

**Tests**
- Editor lifecycle and contract tests.
- ModuleUISpec registration tests.
- Profile validation tests.
- SQLite persistence and reload tests.
- Settings integration tests.
- Workspace integration tests.

**Completion criteria**
- Editor is materialized through the established architecture.
- Profile can be created, edited, saved, and reloaded.
- No profile data is stored through Editor visual-state persistence.
- Integration tests pass.

## Stage 2 — Navigation and configuration (Sprint L.2)

**Goal:** Complete the Professional Editor's internal navigation.

**Implementation**
- Integrate `IconSidebar`.
- Integrate `CollapsibleSection`.
- Integrate `DragList`.
- Integrate visibility controls.
- Implement the navigation and configuration screens from the UI prototype.
- Persist navigation order and visibility.
- Complete required theme and translation integration.

**Tests**
- Navigation behavior tests.
- Reordering and visibility tests.
- Settings persistence tests.
- Dark and Light theme checks.
- HiDPI visual checks.
- Regression tests for shared widgets.

**Completion criteria**
- Navigation and configuration work as specified.
- Presentation state survives application restart.
- No unnecessary Professional-specific widgets are added to the generic widget package.

**Current status:** In progress. `CollapsibleSection` is integrated into the
Tela 2 profile groups, and their `DragList` order is restored and persisted
through `professional.ui.navigation_order`. The Tela 2 ordering interface was
visually approved on 2026-11-26; navigation, visibility, the remaining
presentation persistence, and the remaining screens are pending.

## Stage 3 — Professional catalogs

**Goal:** Implement specialties, categories, and procedures.

**Implementation**
- Implement catalog entities and repositories.
- Add regional seed catalogs.
- Support create, edit, reorder, and deactivate operations.
- Implement code-system references.
- Implement procedure prices and currencies.

**Tests**
- Catalog CRUD and validation tests.
- Stable identifier tests.
- Seed update and user modification preservation tests.
- Code-system and purpose validation tests.
- Currency consistency tests.

**Completion criteria**
- Catalogs are extensible.
- User changes survive seed updates.
- Invalid procedure and currency data are rejected.

## Stage 4 — Document templates

**Goal:** Implement reusable, versioned document templates.

**Implementation**
- Implement template identity and version entities.
- Implement template categories.
- Implement immutable version storage.
- Implement placeholder validation.
- Integrate document language resolution.
- Integrate Patient Module document generation.

**Tests**
- Template CRUD tests.
- Version immutability tests.
- Placeholder validation tests.
- Language fallback tests.
- Patient data resolution tests.
- Document provenance and persistence integration tests.

**Completion criteria**
- Editing creates a new version.
- Existing versions remain unchanged.
- Generated documents are persisted by the Patient Module.

## Stage 5 — Schedule

**Goal:** Implement appointments, tasks, and schedule management.

**Implementation**
- Implement schedule entities and repositories.
- Implement appointment-type catalog.
- Implement status transitions.
- Implement timezone handling.
- Implement conflict detection.
- Implement all-day events and tasks without end times.

**Tests**
- Date and duration validation tests.
- Timezone tests.
- Conflict detection tests.
- Status transition tests.
- Patient and project reference tests.
- Repository and integration tests.

**Completion criteria**
- Invalid events cannot be saved.
- Conflict behavior is explicit.
- Status transitions follow the defined rules.

## Stage 6 — Budgets

**Goal:** Implement budget creation and management.

**Implementation**
- Implement budget and budget-item entities.
- Implement catalog-based budget creation.
- Implement price snapshots.
- Implement discounts and totals.
- Implement status transitions.
- Implement sequential numbering.
- Implement PDF generation.

**Tests**
- Financial calculation tests.
- Currency consistency tests.
- Snapshot preservation tests.
- Budget status transition tests.
- Expiration and confirmation tests.
- PDF generation and locale tests.

**Completion criteria**
- Calculations are exact.
- Existing budgets do not change when catalog prices change.
- PDF output uses the selected document language.

## Stage 7 — Data transfer and security

**Goal:** Provide reliable backup, export, import, and recovery.

**Implementation**
- Implement automatic and manual backups.
- Implement retention and rotation.
- Implement selective and full exports.
- Implement package validation and import.
- Implement restore operations.
- Apply privacy and filesystem access policies.
- Implement encryption if approved for this delivery.

**Tests**
- Backup and restore round-trip tests.
- Export and import round-trip tests.
- Invalid package tests.
- Conflict resolution tests.
- Retention tests.
- Privacy and access-control tests.

**Completion criteria**
- Data can be recovered from a valid backup.
- Imports validate data before modifying the database.
- Sensitive exports require explicit confirmation.

## Stage 8 — Final integration and validation

**Goal:** Validate the complete Professional Module.

**Implementation**
- Integrate all functional areas.
- Review Patient and Project module contracts.
- Review regional profiles and translations.
- Review migrations and error handling.
- Update architecture and user documentation.

**Tests**
- Full unit test suite.
- Repository and service contract tests.
- Editor and Workspace integration tests.
- Patient Module integration tests.
- Backup and restore tests.
- Regression tests.
- Dark and Light theme checks.
- HiDPI checks.
- Static analysis.

**Completion criteria**
- All defined functional requirements are implemented or explicitly deferred.
- All critical domain invariants are tested.
- No unresolved data-integrity issues remain.
- Full project validation passes.

---

## 10. Implementation Scope and Scheduling

The implementation plan above describes the target Professional Module. It does not mean all stages belong to the current Sprint L.

**Current Sprint L scope:**

| Stage | Deliverable | Status |
|---|---|---|
| L.0 | System form widgets | Complete |
| L.0.2 A/B | Extended widgets — initial deliveries | Complete |
| L.0.2 C/D | Remaining widgets and debug harness consolidation | Deferred |
| L.1 | ProfessionalEditor, profile, SQLite persistence, Workspace composition, settings | Implemented; visually approved 2026-11-26 |
| L.2 | Professional navigation and configuration interactions | In progress; Tela 2 ordering complete |

The immediate implementation must remain limited to:

- Professional Editor.
- Initial professional profile interface.
- SQLite profile persistence.
- EditorRegistry and ModuleUISpec integration.
- `professional.*` settings.
- Required navigation and configuration interactions.

The procedures, templates, schedule, budgets, and data-transfer stages must be scheduled according to the master implementation plan. They must not be silently added to Sprint L.

Phase 4 remains gated by formal Phase 3 closure.

---

## 11. Validation Standards

Every implementation stage must include tests appropriate to its scope.

Required project validation commands:

```powershell
python -m pytest
python -m ruff check .
python -m ruff format --check .
python -m mypy src/
```

Validation rules:

- Do not introduce new Ruff violations.
- Do not introduce new mypy errors.
- Investigate regressions against the recorded baseline.
- Do not reduce test coverage merely to obtain a passing suite.
- Update test counts and validation dates after completed deliveries.
- Preserve existing Editor, Workspace, settings, theme, and translation contracts.

The module is considered complete only when all required functional, persistence, integration, and regression tests pass.

## 12. Related Documents

- `docs/architecture/modules/modules.md`
- `docs/architecture/domain/professional/`
- `docs/architecture/professional_patient_interface.md`
- `docs/architecture/config/cranioz_home.md`
- `docs/architecture/internationalization/internationalization.md`
- `docs/architecture/overview.md`
- `docs/architecture/widgets/widget_catalog.md`
- `next_steps.md`
- `implementation_plan.md`
