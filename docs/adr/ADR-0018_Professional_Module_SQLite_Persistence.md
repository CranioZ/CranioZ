# ADR-0018 — Professional Module SQLite Persistence

**Status:** Accepted
**Date:** 2026-11-24
**Supersedes:** —
**Related:** `modules.md` §§6–7, 10, 15; `professional.md` §§2, 5, 7, 9;
ADR-0007 (Commands and Transactions), ADR-0009 (Project Persistence Format),
ADR-0011 (Threading and Task Execution)
**Sprint:** L.1

---

## 1. Context

The Professional Module stores application-level professional and
administrative data that is independent of any clinical project. Its
data must remain available across projects and must not be copied into
project storage or application settings.

`modules.md` previously prohibited Module-owned persisted files and
migration unless an accepted ADR defined their ownership, access,
schema, and migration. `professional.md` specifies a dedicated SQLite
database, but the module contract did not yet authorize that persistence
boundary.

This ADR resolves that conflict for the Professional Module. It does not
create a general persistence mechanism for arbitrary modules.

## 2. Decision

The Professional Module uses one dedicated SQLite database outside
clinical projects.

### 2.1 Ownership

| Component | Layer | Responsibility |
|---|---|---|
| `ProfessionalService` | Application | Sole owner of the database lifecycle and transaction boundary. Exposes validated operations to command handlers and query consumers. |
| `ProfessionalRepository` | Application port | Defines persistence operations using domain values and identifiers. It has no SQLite-specific types. |
| `SqliteProfessionalRepository` | Infrastructure | Implements the repository port using SQLite. It does not decide domain validity or transaction policy. |
| `ProfessionalMigrationService` | Application/Infrastructure boundary | Applies the Professional Module’s explicit schema migrations before normal data access. |
| `ProfessionalDatabase` | Infrastructure | Owns the SQLite connection, connection configuration, and low-level database errors. |
| `ProfessionalModule` | Module | Declares the Editor, services, commands, and UI specification. It does not open the database directly. |
| `ProfessionalEditor` | UI/Editor | Requests reads and persistent changes through application contracts; it never imports SQLite or the repository implementation. |

The database belongs to the Professional capability, not to an
individual project. The Application composition root constructs the
repository and migration service and supplies them to
`ProfessionalService`.

Persistent changes must be executed through Commands and the shared
command/transaction mechanism. The Editor must not write to the database
directly.

### 2.2 Location and configuration

The database lives under a dedicated application data root:

```text
<professional_root>/
    professional.db
    templates/
    attachments/
    exports/
```

The default location follows `professional.md`:

```text
~/.cranioz/professional/
```

`AppPathResolver` must expose the resolved `professional_root`. The path
must be configurable through the existing application-path
configuration and initialized once during bootstrap. The module must not
derive or construct physical paths independently.

The database path is:

```text
<professional_root>/professional.db
```

No database, template, attachment, or export data may be stored inside
clinical project directories.

### 2.3 Schema ownership and versioning

The Professional Module owns its database schema. Schema changes are
defined only by ordered migrations maintained with the Professional
Module.

The installed schema version is stored with SQLite `PRAGMA user_version`.
Migration version `1` is the initial supported schema and must be
created by an explicit migration. No schema is created implicitly from
ad-hoc SQL in repositories or Editors.

Rules:

- each migration has a stable, monotonically increasing version;
- migrations run in order inside an explicit transaction;
- a migration either completes fully or leaves the previous schema
  version intact;
- opening a database with a newer schema version fails with an explicit
  incompatibility error;
- migration errors preserve the original database and never fall back to
  JSON or an in-memory replacement;
- foreign keys are enabled for every connection;
- timestamps are stored in UTC with an unambiguous format;
- domain values and identifiers are validated before reaching SQLite;
- the database schema is not duplicated in Editor visual state or
  `professional.*` settings.

Before migrating a non-empty database, the implementation must preserve
a recoverable backup. The backup location and retention policy must not
overwrite the only recoverable copy.

The initial profile schema may contain the profile, registrations, and
supporting reference data required by Stage 0 of `professional.md`.
Later stages add their tables through new migrations; they must not
silently alter migration `1`.

### 2.4 Connections and transactions

The SQLite connection is owned by `ProfessionalDatabase` and exposed only
through the repository/service boundary.

Required connection configuration:

- foreign-key enforcement enabled;
- explicit transaction boundaries;
- a bounded busy timeout;
- write-ahead logging where supported, with fallback behavior documented
  by the adapter;
- no shared connection leaked to UI components or Editor instances.

Long-running database work follows ADR-0011 and runs through the
Application `TaskManager`. Short reads and writes may remain on the
application thread only when their duration is demonstrably small.

### 2.5 Lifecycle

`ProfessionalService` is a session-scoped application service. It:

- initializes and migrates the database before serving persistent
  operations;
- remains independent of `ProjectContext`;
- is disposed when the Professional Module unloads;
- does not retain a Module instance;
- reports database failures as application errors while preserving the
  last committed transaction.

The service may be available before a clinical project is open. Access
to the Professional Editor from the shell is a separate navigation
decision and is not implied by this ADR.

### 2.6 Settings and Editor state boundary

Profile and administrative data belong only in SQLite.

The `professional.*` settings namespace stores presentation preferences,
such as section order, visibility, and the last section. Editor
`persistent_state()` and `restore_state()` store visual Editor state.
Neither mechanism may become a second source of truth for professional
profile data.

Sensitive patient data must not be persisted in the Professional
database beyond the minimal display label and explicit provenance
permitted by `professional.md`. Logs and telemetry must not contain
patient identifiers or sensitive document content.

### 2.7 Error handling

Database and migration errors must be translated at the application
boundary. Infrastructure exceptions may be chained for diagnostics but
must not leak as the public UI contract.

Failed commands leave the previous committed database state intact.
Migration failures preserve the original database and report the
incompatible version and failing migration.

## 3. Rejected alternatives

### 3.1 Store professional data in each project

Rejected: professional and administrative data must be reusable across
projects and is not project-owned.

### 3.2 Store profile data in `professional.*` settings

Rejected: settings are presentation preferences and are not a relational
database or a domain source of truth.

### 3.3 Temporary JSON persistence

Rejected by `professional.md`. It would create a second format, weaken
transactional integrity, and require an unnecessary migration later.

### 3.4 Let Editors or the Module access SQLite directly

Rejected: this bypasses Commands, validation, transaction ownership, and
the Module isolation contract.

### 3.5 Create a generic module-database framework

Deferred: this ADR authorizes only the Professional database. A reusable
module-persistence mechanism would require a separate architectural
decision.

## 4. Consequences

### Positive

- Professional data survives independently of clinical projects.
- Relational integrity, transactions, indexes, and migrations use one
  supported mechanism.
- The persistence boundary is explicit and testable.
- The Module remains declarative and does not own technical adapters.

### Costs

- Bootstrap must resolve and configure the Professional data root.
- The implementation needs migration and backup tests.
- `ProfessionalService` lifecycle must be integrated with the Module and
  Application composition root.
- Database access cannot begin until the application path and migration
  infrastructure are available.

## 5. Testing requirements

At minimum:

- create a database in a temporary directory;
- migrate an empty database to version `1`;
- reopen and verify the schema version;
- reject a database with a newer schema version;
- roll back a failed migration and preserve the previous database;
- enforce foreign keys and transaction rollback;
- save, reload, and validate profile data;
- verify profile data is absent from settings and Editor visual state;
- verify the Editor has no direct SQLite access;
- preserve the database across application restart;
- prevent database files from being created inside project directories.

Tests must not depend on the user’s real `~/.cranioz` directory.

## 6. Compliance

This ADR provides the ownership, access, schema-versioning, and migration
decision required by `modules.md` §7 for a Module-owned persisted
resource.

It does not authorize:

- persistence for other Modules;
- direct SQLite access from Modules or Editors;
- changes to the clinical Project persistence format;
- module picker or Flow activation behavior.
