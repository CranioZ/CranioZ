# ADR-0009: Project Persistence Format

**Status:** Accepted
**Date:** 2026-10-22
**Deciders:** Architecture team
**Related:** project.md §11-§13, §26, project_serialization.py, ADR-0007

---

## 1. Context

`project.md` §11 establishes that Project Storage is an
infrastructure concern. `project.md` §13 establishes that the
persistence representation is not an architectural authority. But the
format itself — the file layout, the schema version, and the
migration strategy — had not been decided.

Without a decision, `FilesystemProjectRepository` was implemented
with a `project.json` shape (see `project_serialization.py`), but no
ADR records the choice, the invariants, or the migration path. This
ADR fills that gap.

## 2. Decision

### 2.1 Directory layout

Each project is a directory under `projects_root`, named after its
`ProjectId`:

    <projects_root>/
    └── <project_id>/
    ├── project.json (owned by ProjectRepository)
    ├── patient_record.json (owned by Patient persistence layer)
    ├── workflow.json (owned by WorkflowEngine)
    ├── layout.json (owned by Layout persistence, ADR-0010)
    ├── scene.json (owned by Scene persistence, ADR-0008)
    ├── assets/
    │ ├── imaging/
    │ ├── models/
    │ ├── planning/
    │ └── documents/
    └── backups/


**Ownership by file:**

| File | Owner | Scope |
|---|---|---|
| `project.json` | `ProjectRepository` (Peça 7.3) | Metadata + lifecycle. |
| `patient_record.json` | Patient persistence layer | Patient clinical record (ADR-0004). |
| `workflow.json` | WorkflowEngine (Phase 5) | Active workflow state. |
| `layout.json` | Layout persistence (ADR-0010) | `LayoutState` + `OverlayState`. |
| `scene.json` | Scene persistence (ADR-0008) | Scene membership, hierarchy, transforms. |
| `assets/` | Infrastructure (importers) | Binary payloads (DICOM, meshes, etc.). |
| `backups/` | Infrastructure (autosave) | Snapshots for recovery. |

A file in this layout belongs to exactly one owner. No file is
co-written. This separation is enforced by the Application layer,
not by the filesystem.

### 2.2 File format

- JSON, UTF-8, indented with 2 spaces, newline at EOF.
- Timestamps in ISO 8601 with timezone (`+00:00`), matching the
  domain's `datetime` with `tzinfo=UTC`.
- Enums serialized by `.value`, not `.name` (e.g., `"active"`, not
  `"ACTIVE"`).
- The metadata's `project_id` is the canonical key; it must match
  the directory name (`ProjectPathResolver.project_id`).

### 2.3 Schema versioning

Every file that persists a domain structure carries a
`schema_version` field at the root. The current version is `1`.

- A reader rejects files with `schema_version > CURRENT_SCHEMA_VERSION`.
- A reader that encounters `schema_version < CURRENT_SCHEMA_VERSION`
  invokes the corresponding migration before deserializing.
- Migrations are pure functions in the infrastructure layer. They
  never touch the UI or the domain.
- Migration failure aborts the read with `ProjectCorrupted`.

### 2.4 Atomic writes

Writes go to a temporary file (`<file>.tmp`), then to `<file>` via
rename. A crash mid-write leaves the original intact.

- Two consecutive `.tmp` files are never created. A stale `.tmp` is
  removed on the next write.
- Read-modify-write operations are serialized by the
  `ProjectManager`'s single-threaded execution (ADR-0006 §2.5).

### 2.5 Backups

Before overwriting an existing file, the Application layer may copy
it to `backups/<file>.<timestamp>`. Backup policy is per-owner:
`project.json` backups are opt-in, `layout.json` backups are
opt-in, `scene.json` backups are opt-in. The first release may ship
without automatic backups; the mechanism is reserved.

### 2.6 Migration contract

A migration is a function:

    def migrate_v1_to_v2(data: dict) -> dict: ...


Migrations are registered per (file, from_version, to_version).
Migrations are applied in order if multiple versions must be
crossed. The `ProjectMigrator` is a pure function that never
touches I/O; the repository invokes it after reading and before
deserializing.

### 2.7 Error contracts

- **File missing**: `ProjectNotFound` if the file is required
  (`project.json`). Optional files (e.g., `layout.json`) are
  treated as "not yet written".
- **File corrupted** (invalid JSON, missing required key,
  schema mismatch): `ProjectCorrupted`.
- **File unreadable** (permission denied, I/O error):
  `ProjectStorageError`.
- **Directory unreadable** (permissions): `ProjectStorageError`.

### 2.8 Non-goals

- Encryption at rest is not decided by this ADR. It is a separate
  concern for institutional deployments.
- Versioning of binary assets is not decided here. The `assets/`
  subdirectories are owned by their respective importers.
- A database backend is out of scope. The current design is
  filesystem-based. A future `SQLiteProjectRepository` (or
  equivalent) is an adapter, not a replacement of the domain
  contract.

## 3. Rationale

### 3.1 One owner per file

Co-written files break the single-writer principle. If both
`ProjectRepository` and `LayoutPersistence` wrote to
`project.json`, a race between them could corrupt the file. One
file, one owner, one writer.

### 3.2 Filesystem for Phase 4

A relational database would be premature. The Phase 4 deliverable
is the Scene and its rendering; persistence of the Scene is a JSON
serialization that is tested with `tmp_path`. A database backend
can be added later without changing the contract.

### 3.3 Schema versioning from the start

`overview.md` §15 requires "schema evolution and migration." A
version field costs nothing and prevents silent incompatibility
across releases.

### 3.4 Atomic writes

`project.md` §26 requires "recovery after interrupted writes." The
temporary-file-then-rename pattern is the standard solution and is
already implemented in `FilesystemProjectRepository._write_project_json`.

## 4. Consequences

### 4.1 Positive

- Clear ownership per file, enforced by the layout.
- Atomic writes protect against crashes.
- Schema versioning enables migrations.
- No coupling to a database vendor.

### 4.2 Negative

- Filesystem performance is limited by the OS. On network shares,
  atomic rename may be slow.
- Backup policy is per-owner; forgetting to back up `scene.json`
  could lose planning work if the file is corrupted.

### 4.3 Neutral

- The format is versioned, so the schema can evolve.
- The layout is stable across owners; adding a new file is a new
  entry, not a new structure.

## 5. Rules applied by this ADR

1. Each file has exactly one owner.
2. JSON, UTF-8, 2-space indent, ISO 8601 UTC, enum `.value`.
3. Every persisted structure carries `schema_version`.
4. A reader rejects unknown future versions.
5. A reader migrates known older versions.
6. Writes are atomic (temp + rename).
7. Migration is a pure function registered per file/version.
8. Errors are translated into the `ProjectRepositoryError` family.
9. `project.json` is required; other files are optional.
10. Backup policy is per-owner.

## 6. Rejected alternatives

### 6.1 A single `project.json` with everything

Rejected. Every owner would co-write the same file, producing
races and forcing serialization of unrelated operations. It also
makes partial writes impossible (any schema change forces a
rewrite of the whole file).

### 6.2 SQLite for everything

Rejected for Phase 4. SQLite is a valid adapter choice but not a
domain requirement. The filesystem is the simplest starting point
and the repository contract is agnostic to the backend.

### 6.3 Binary format (MessagePack, Protobuf)

Rejected. JSON is human-readable, diffable, and trivially testable
with `tmp_path`. The volume of data (metadata, layout, scene graph)
is small; binary format is premature optimization.

## 7. Summary

The project persistence format is filesystem-based, one owner per
file, JSON, schema-versioned, atomically written. It supports
migrations and translates errors into the repository family. It is
the prerequisite for `Scene` and `LayoutState` persistence in
Phase 4 and Phase 5.