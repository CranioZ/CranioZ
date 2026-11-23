# Professional Module

**Module ID:** `professional`
**Status:** Proposed
**Scope:** Personal, administrative, and financial management of the surgeon
**Persistence:** Dedicated database outside projects (`~/.cranioz/professional/`)

---

## 1. Purpose

The **Professional Module** manages the surgeon's personal, administrative, and financial information. It is the application's administrative counterpart to the clinical modules.

The module does **not** handle patient clinical data (imaging, planning, osteotomies, Scene). It produces administrative artifacts — documents, budgets, appointments, procedure catalogs — that are **consumed** by clinical modules, particularly the Patient Module.

The module is **self-contained**: it works without any open project, and its data is reused across projects.

---

## 2. Core Principles

- **Outside projects.** Professional data lives in a dedicated database, not inside clinical projects.
- **Reusable across projects.** A procedure catalog, a document template, or a budget is defined once and reused for many patients.
- **Reference, do not contain, patient data.** The module references patients and projects by ID; it never stores clinical content.
- **Translate everything.** Specialties, categories, and procedures are always resolved through the `TranslationService`.
- **Commands for all mutations.** Every persistent change passes through an application Command.
- **Single service owns the database.** A `ProfessionalService` is the only component that reads or writes the professional database.

---

## 3. Ownership and Boundaries

### 3.1 What the Module Owns

- The professional's profile.
- The procedure catalog (specialties, categories, procedures).
- Document templates (orientations, contracts, consent terms, prescriptions, certificates).
- The appointment schedule.
- Budgets and budget items.
- Attachments (logo, signature image).

### 3.2 What the Module References (Does Not Own)

- Patients — referenced by `patient_id`, live in projects.
- Projects — referenced by `project_id`, live in the Project Root.
- Osteotomy patterns — a separate shared catalog (see ADR-0006).
- Scene, imaging, planning — never referenced by this module.

### 3.3 What the Module Does Not Do

- It does not create, modify, or delete patients or projects.
- It does not store clinical data (imaging, planning, Scene).
- It does not implement clinical rules.
- It does not manage the Project lifecycle.

---

## 4. Persistence

### 4.1 Location

```text
~/.cranioz/professional/          (Linux/macOS)
%APPDATA%\CranioZ\Professional\   (Windows)
```

The location is resolved by the same ConfigurationPaths component used for project_root, with an override in config/paths.json and an environment variable CRANIOZ_HOME.

### 4.2 Structure

    professional/
    ├── professional.db          # SQLite
    ├── professional.db.bak      # Automatic backup
    ├── templates/               # Document templates
    │   ├── orientations/
    │   ├── contracts/
    │   ├── consent_terms/
    │   ├── prescriptions/
    │   ├── certificates/
    │   └── declarations/
    ├── attachments/             # Logo, signature
    ├── translations/            # User-supplied translations for custom entities
    │   ├── pt-BR.json
    │   └── en.json
    └── exports/                 # Generated PDFs
        └── budgets/

### 4.3 Technology
SQLite. Chosen for relational integrity, indexed queries (schedule, budgets), ACID transactions, and versioned migrations. A single file simplifies backup and export.

### 4.4 Schema Versioning
A schema_version table tracks the current version. Migrations are applied on database open, following the pattern of ProjectMigrationService. Invalid or future schemas are rejected with a clear error.

## 5. Module Structure
The module is organized into five tabs, presented in a default order that follows the surgeon's natural workflow.

#	Tab	Purpose	Frequency
1	Professional	Personal and professional profile	Rare
2	Procedures	Catalog of procedures and prices	Occasional
3	Budgets	Budget creation from procedure catalog	Frequent
4	Schedule	Appointments, tasks, scheduled surgeries	Daily
5	Document Templates	Reusable document templates	Occasional
Default order rationale: identity → offering → billing → operation → delivery.

Reorganization: the user can reorder tabs, following the pattern of the Patient Module.

## 6. Tab: Professional
6.1 Purpose
The surgeon's identity and presentation data. Used in generated documents (budgets, contracts, prescriptions, orientations).

### 6.2 Fields
    Field	                    Type	                                    Required
    Salutation	                Enum (Dr., Dra., Prof., Profa., —)	        No
    Full name	                Text	                                    Yes
    Registration type	        Enum (CRM, CRO, CREFONO, OTHER)	            No
    Registration number	        Text	                                    No
    Email	                    Text	                                    No
    Phone	                    Text	                                    No
    Address	                    Text	                                    No
    City	                    Text	                                    No
    State	                    Text	                                    No
    Country	                    Text	                                    No
    Clinic logo	                File reference	                            No
    Digital signature	        File reference	                            No
    Date format	                Enum (DD/MM/YYYY, MM/DD/YYYY, YYYY-MM-DD)	Yes

### 6.3 Preview
A signature preview panel shows how the professional's identity will appear in generated documents, using the current profile fields.

### 6.4 Behavior
Saving dispatches an UpdateProfessionalProfileCommand.

Cancelling reverts the fields.

The onboarding wizard populates the minimal fields on first run; the tab is used for later edits.

## 7. Tab: Procedures
### 7.1 Purpose
The catalog of procedures offered by the surgeon. Serves as the basis for budgets.

### 7.2 Hierarchy

    Specialty
        └── Category
                └── Procedure

Specialties are built-in or user-created.

Categories group procedures within a specialty.

Procedures are the final entity.

### 7.3 Built-in Specialties
The following are provided as built-in, non-deletable suggestions:

Odontology (area)
Otorhinolaryngology
Oral and Maxillofacial Surgery
Plastic Surgery
Orthodontics
Implantology

The user may add custom specialties. Custom entities are always translatable (see §11).

### 7.4 Procedure Fields
Field	                    Type	                Required
Category	                FK	                    Yes
Name (translation key)	    Text	                Yes
Default price	            Decimal	                Yes
Default duration (minutes)	Integer                 No
TUSS code	                Text	                No
CID code	                Text	                No
Notes	                    Text	                No
Active	                    Boolean	                Yes

### 7.5 Actions
Create, edit, deactivate, and delete procedures, categories, and specialties. Deletion of a specialty or category cascades to its children after confirmation.

### 7.6 Catalog vs. Performed Procedures
The catalog holds definitions. Performed procedures (with a patient, date, and execution) live elsewhere:

Inside a budget, as line items.

Inside the schedule, as scheduled appointments.

Inside the Patient Module, as part of the patient's history.

The catalog never stores instances.

## 8. Tab: Budgets
### 8.1 Purpose
Creation of budgets for a specific patient, composed of procedures from the catalog.

### 8.2 Budget Fields
Field	                            Type	                                        Required
Patient	                            Reference (patient_id)	                        Yes
Project	                            Reference (project_id)	                        No
Status	                            Enum (draft, sent, accepted, rejected, expired)	Yes
Discount	                        Decimal	                                        No
Total	                            Decimal	                                        Computed
Valid until	                        Date	                                        No
Notes	                            Text	                                        No

### 8.3 Budget Item Fields
Field	                            Type	                            Required
Procedure	                        FK	                                Yes
Description	                        Text	                            No
Quantity	                        Integer	                            Yes (default 1)
Unit price	                        Decimal	                            Yes (default from procedure)
Notes	                            Text	                            No


### 8.4 Computation
    subtotal = Σ (quantity × unit_price)
    total    = subtotal − discount

### 8.5 State Machine
    draft ──▶ sent ──▶ accepted
                  ├──▶ rejected
                  └──▶ expired


Transitions are validated. accepted and rejected are terminal except for explicit reopening by the user, which resets the budget to draft.


### 8.6 PDF Export
Budgets can be exported to PDF. The PDF includes:

Header with logo, name, registration, address.

Patient identification.

Line items, subtotal, discount, total.

Validity date.

Signature image.

The PDF is saved in exports/budgets/ and, optionally, attached to the patient in the Patient Module.

### 8.7 Actions
Create, edit, duplicate, delete, export PDF, change status.

## 9. Tab: Schedule
### 9.1 Purpose
The surgeon's personal calendar: appointments, tasks, scheduled surgeries, and administrative notes. Independent of projects.

### 9.2 Views
Weekly (primary).

Monthly (overview).

List (upcoming appointments).

### 9.3 Appointment Types
    Type	        Description
    Consultation	Initial or follow-up visit
    Surgery	        Scheduled surgical procedure
    Follow-up	    Post-operative visit
    Exam	        Imaging or laboratory
    Meeting	        Team, supplier, or institutional
    Task	        Administrative reminder
    Block	        Vacation, congress, unavailability

### 9.4 Appointment Fields
    Field	                Type	                                                    Required
    Type	                Enum	                                                    Yes
    Title	                Text	                                                    Yes
    Patient	                Reference (patient_id)	                                    No
    Project	                Reference (project_id)	                                    No
    Procedure	            FK	                                                        No
    Start / End	            Timestamp	                                                Yes
    Location	            Text	                                                    No
    Status	                Enum (scheduled, confirmed, completed, cancelled, no_show)	Yes
    Notes	                Text	                                                    No

### 9.5 State Machine
text
scheduled ──▶ confirmed ──▶ completed
                        ├──▶ cancelled
                        └──▶ no_show
### 9.6 Actions
Create, edit, cancel, mark completed, navigate (day, week, month, today).

### 9.7 Future Extensions
iCal export and import.

Google Calendar and Outlook synchronization.

Desktop reminders.

Recurring appointments.

These are not part of the initial release.

## 10. Tab: Document Templates
### 10.1 Purpose
A list of pre-configured documents that can be applied to a patient in the Patient Module. Templates are reusable, translatable, and versioned independently of any project.

###10.2 Categories

    Category	    Built-in	Examples
    Orientations	Yes	        Post-operative care
    Contracts	    Yes	        Service agreement
    Consent terms	Yes	        Surgical consent
    Prescriptions	Yes	        Post-operative prescription
    Certificates	No	        Attendance certificate
    Declarations	No	        Procedure declaration

The first four are built-in and non-deletable. Others can be added by the user.

### 10.3 Template Fields
    Field	                Type	                            Required
    Kind	                Enum (category)	                    Yes
    Name (translation key)	Text	                            Yes
    File path	            Text (relative to templates/)	    Yes
    Created / Updated	    Timestamp	                        Auto

### 10.4 Format
Templates are plain text files (.txt) with placeholders using the syntax {{variable_name}}.

    Dear {{patient_name}},
    
    You underwent {{procedure_name}} on {{procedure_date}}.
    Please follow the post-operative instructions below.
    
    Sincerely,
    {{professional_salutation}} {{professional_name}}
    {{professional_registration_type}} {{professional_registration}}
    10.5 Placeholders
    Available variables include (non-exhaustive):
    
    Patient: patient_name, patient_social_name, patient_birth_date, patient_cpf.
    
    Procedure: procedure_name, procedure_date.
    
    Professional: professional_salutation, professional_name, professional_registration_type, professional_registration, clinic_name, clinic_address.
    
    System: today.

### 10.6 Actions
Create, import, edit, delete, and create a new category.

### 10.7 Use in the Patient Module
The Patient Module displays the list of templates and allows the user to apply one to a patient. Variables are filled from the patient record, the active procedure, and the professional profile. The rendered document is saved as a patient document.

This is the primary interface between the Professional Module and the Patient Module.

## 11. Internationalization
All specialties, categories, and procedures are always translated.

Built-in entities have translation keys in translations/<lang>/professional.json, provided by CranioZ.

Custom entities have translation keys of the form user.<kind>.<uuid>, provided by the user.

Custom translations live in ~/.cranioz/professional/translations/<lang>.json.

When a translation is missing in the active language, the fallback sequence is:

* The entity's source_language (the language at creation time).
* 
* The translation key itself.
* 
* A neutral placeholder.

The TranslationCatalogRegistry loads catalog sources in this precedence order (highest to lowest):

* Professional (user-created entities).
* 
* Settings (user overrides).
* 
* System (built-in).

12. Application Service
12.1 ProfessionalService
The ProfessionalService is the sole owner of the professional database. It exposes commands, reads the repository, and validates inputs.

Conceptual interface:

    class ProfessionalService(Protocol):
        # Profile
        def get_profile(self) -> ProfessionalProfile: ...
        def update_profile(self, command: UpdateProfessionalProfileCommand) -> None: ...
    
        # Catalog
        def list_specialties(self) -> list[Specialty]: ...
        def list_categories(self, specialty_id: str) -> list[Category]: ...
        def list_procedures(self, category_id: str | None = None) -> list[Procedure]: ...
        def create_procedure(self, command: CreateProcedureCommand) -> None: ...
        def update_procedure(self, command: UpdateProcedureCommand) -> None: ...
        def delete_procedure(self, command: DeleteProcedureCommand) -> None: ...
    
        # Templates
        def list_templates(self, kind: str) -> list[DocumentTemplate]: ...
        def create_template(self, command: CreateDocumentTemplateCommand) -> None: ...
        def update_template(self, command: UpdateDocumentTemplateCommand) -> None: ...
        def delete_template(self, command: DeleteDocumentTemplateCommand) -> None: ...
    
        # Schedule
        def list_appointments(self, start: date, end: date) -> list[Appointment]: ...
        def create_appointment(self, command: CreateAppointmentCommand) -> None: ...
        def update_appointment(self, command: UpdateAppointmentCommand) -> None: ...
        def cancel_appointment(self, command: CancelAppointmentCommand) -> None: ...
    
        # Budgets
        def list_budgets(self, patient_id: str | None = None) -> list[Budget]: ...
        def get_budget(self, budget_id: str) -> Budget: ...
        def create_budget(self, command: CreateBudgetCommand) -> None: ...
        def update_budget(self, command: UpdateBudgetCommand) -> None: ...
        def delete_budget(self, command: DeleteBudgetCommand) -> None: ...
    
        # Lifecycle
        def export_data(self) -> Path: ...
        def import_data(self, archive: Path) -> None: ...
        def backup(self) -> Path: ...

### 12.2 Repository
A ProfessionalRepository port abstracts SQLite access. The concrete adapter lives in infrastructure/persistence/professional/.

### 12.3 Ownership
The ProfessionalService is the only component that accesses the professional database. The onboarding wizard and the Professional Module both use the service; neither accesses the database directly.

## 13. Onboarding
### 13.1 First Run
On first boot, if no professional profile exists, an onboarding wizard collects the minimal fields:

* Salutation
* Full name
* Registration type
* Registration number

The wizard dispatches an UpdateProfessionalProfileCommand and closes. The remaining fields (email, address, logo, signature) are filled later via the Professional tab.

### 13.2 Skipping
The wizard can be skipped. In that case, generated documents will contain placeholders for the missing fields, and the user is warned.

### 13.3 Re-entry
There is no separate "onboarding" after the first run. All edits happen through the Professional tab.

## 14. Commands
The module introduces the following application Commands:

    Profile
    
    UpdateProfessionalProfileCommand
    
    Catalog
    
    CreateSpecialtyCommand, UpdateSpecialtyCommand, DeleteSpecialtyCommand
    
    CreateCategoryCommand, UpdateCategoryCommand, DeleteCategoryCommand
    
    CreateProcedureCommand, UpdateProcedureCommand, DeleteProcedureCommand
    
    Templates
    
    CreateDocumentTemplateCommand, UpdateDocumentTemplateCommand, DeleteDocumentTemplateCommand, ImportDocumentTemplateCommand
    
    Schedule
    
    CreateAppointmentCommand, UpdateAppointmentCommand, CancelAppointmentCommand, CompleteAppointmentCommand
    
    Budgets
    
    CreateBudgetCommand, UpdateBudgetCommand, DeleteBudgetCommand, ChangeBudgetStatusCommand, ExportBudgetPdfCommand
    
    Maintenance
    
    ExportProfessionalDataCommand
    
    ImportProfessionalDataCommand
    
    BackupProfessionalDataCommand

15. Interfaces with Other Modules
### 15.1 Patient Module
    Direction	            Data
    Professional → Patient	Document templates (applied to a patient)
    Professional → Patient	Budgets (created for a patient)
    Professional → Patient	Procedure catalog (referenced in patient history)
    Professional → Patient	Schedule (appointments linked to a patient)
    Patient → Professional	Patient identity (name, birth date, contact) for rendering templates and budgets

The interface is documented in docs/architecture/professional_patient_interface.md.

### 15.2 Project Module
The Professional Module references projects by project_id when a budget or appointment is linked to a project. It never reads or writes project files directly.

### 15.3 Osteotomy Module
Osteotomy patterns are not part of the Professional Module. They live in a separate shared catalog (see ADR-0006).

## 16. Security and Privacy
### 16.1 Sensitive Data
The professional database may contain patient-identifying information (names, contact details) in budgets and appointments. Although it does not hold clinical data, it falls under the same privacy considerations.

### 16.2 File Permissions
The ~/.cranioz/professional/ directory is created with permissions restricted to the operating system user.

### 16.3 Encryption
SQLCipher is available as an optional encryption layer. When enabled, the database and its backups are encrypted with a user-provided key. When disabled, the database is plaintext but access-restricted.

### 16.4 Audit
A professional_audit_log table records creation, modification, and deletion of budgets and appointments, including actor, timestamp, and affected entity. Audit logging is optional in the first release.

### 16.5 Export and Import
Exported archives contain patient-identifying information. The user is warned before exporting, and the archive may be encrypted.

## 17. Backup, Export, and Import
### 17.1 Automatic Backup
On application close (or at a configurable interval), the database is copied to professional.db.bak and to ~/.cranioz/backups/professional/. The last five backups are retained by default.

### 17.2 Manual Export
The user can export the entire professional database as a .cranioz-professional archive (a zip containing professional.db, templates/, attachments/, and a manifest.json with version metadata).

### 17.3 Import
Importing an archive replaces the current database after confirmation. Conflict resolution policies (merge, replace, rename) are defined in ADR-0009.

18. Out of Scope
The following are explicitly out of scope for the initial release:

* Multiple professionals on the same installation.
* 
* Integration with external ERP, billing, or insurance systems.
* 
* Advanced financial analytics and reports.
* 
* Cryptographic digital signature (ICP-Brasil).
* 
* Conditional and loop constructs in document templates.
* 
* Recurring appointments.
* 
* Bidirectional calendar synchronization.
* 
* These may be added in future versions if demand justifies them.

## 19. Related Documents
    docs/architecture/domain/professional/ — domain entities.
    
    docs/architecture/professional_patient_interface.md — interface with the Patient Module.
    
    docs/architecture/config/cranioz_home.md — structure of ~/.cranioz/.
    
    docs/architecture/internationalization/internationalization.md — translation system.
    
    docs/architecture/overview.md — overall architecture.

