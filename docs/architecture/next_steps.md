# Next Steps

**Document type:** Action plan and development handoff
**Status:** Active
**Scope:** Current development priorities and execution sequence for Phase 3
**Last updated:** 2026-11-18

---

## 1. Context

CranioZ has completed Phases 0, 1, and 2. Phase 3 — Project, Home Page & Professional Module — is the active phase.

Phase 4 — Scene & Visualization — remains planned and must not formally begin until Phase 3 is closed.

This document translates the main implementation roadmap into immediate development priorities and the current operational handoff.

### 1.1 Planning document hierarchy

The four planning documents have distinct responsibilities:

| Document | Responsibility |
|---|---|
| `implementation_plan.md` | Overall roadmap, phases, deliverables, dependencies, and completion criteria |
| `next_steps.md` | Immediate priorities, execution sequence, and current development handoff |
| `architectural_consolidation_plan.md` | Architectural inconsistencies, duplication, legacy components, and consolidation requirements |
| `refactoring_plan.md` | Detailed technical procedure for the Editor and Module structural refactoring |

`implementation_plan.md` governs the overall roadmap. This document must remain consistent with it and must not redefine phases or functional deliverables.

### 1.2 Current validation baseline

The latest confirmed baseline is:

- **1,635 passing tests**
- **0 failed**
- **0 errors**
- **2 skipped**
- `ruff check .` clean
- `ruff format --check .` clean
- `mypy src` clean
- **85% overall test coverage**

This is the baseline recorded on 2026-11-18, after the completion of the Editor Architecture Refactoring. It must be revalidated after subsequent changes. Sprint I is expected to add tests without altering the existing baseline's pass/fail structure; the new baseline will be recorded when Sprint I closes.

### 1.3 Current architectural state

The Workspace foundation is implemented and tested.

Completed capabilities include:

- Area management and Workspace composition.
- Editor lifecycle and context propagation.
- Editor-level and View-level toolbar integration.
- Active View detection and `ACTIVE_ONLY` toolbar behavior.
- Intra-Area layout through `AreaLayoutRenderer`.
- Multiple Editors within an Area through `EditorStack`.
- Lazy materialization and Editor lifecycle management.
- Frameless application window, custom drag support, and native resizing.
- Theme and icon provider foundations.
- Internationalization of the application shell.
- Editor and Module packages reorganized into `cranioz/editors/` and `cranioz/modules/core/`, with dependency boundaries enforced by AST-based architecture tests (ADR-0015).

The DICOM import and visualization pipeline has foundational implementations and integration work documented in `implementation_plan.md`.

The Project Catalog synchronization mechanism is specified by **ADR-0016** (Accepted 2026-11-18). Its implementation is Sprint I.

---

## 2. Completed Work

### 2.1 Phases and Sprints

| Item | Status | Notes |
|---|---|---|
| Phase 0 — Foundation & Boot | Complete | Startup performance improvements remain tracked separately |
| Phase 1 — Contracts, Core Domain & i18n | Complete | Includes Sprints B and C |
| Phase 2 — Workspace Engine & Icons | Complete | Closed after Sprint H |
| Sprint B — i18n contract and catalogs | Complete | |
| Sprint C — EditorContext propagation | Complete | Closed Phase 1 |
| Sprint E — ThemeService and ThemeCompiler | Complete | 47 canonical design tokens |
| Sprint F — IconProvider and UnicodeIconProvider | Complete | 60 registered icons |
| Sprint G — AreaLayoutRenderer | Complete | SINGLE, SPLIT, and STACK extension point |
| Sprint H — EditorStack | Complete | LEAF, SPLIT, and STACK composition |
| Sprint M — Frameless Window and Native Chrome | Complete | Drag, resize, maximize, minimize, and close |
| Blocks 1–6 | Complete | Toolbar, active View, TomographyEditor integration, and visual validation |
| Blocks 5.5–5.6.1 | Complete | Area sizing and window controls |
| **Editor Architecture Refactoring** | **Complete** | **See ADR-0015 and `refactoring_plan.md` §11. Closed on 2026-11-18.** |
| **ADR-0016 — Project Catalog Synchronization** | **Accepted** | **Specifies Sprint I. See `docs/adr/ADR-0016_Project_Catalog_Synchronization.md`.** |

### 2.2 Important architectural decisions

- **ADR-0013:** Editor Layout Tree, View Layout Tree, and Toolbar Placement.
- **ADR-0014:** Qt Widgets + modular QSS + Python Design Tokens.
- **ADR-0015:** Editor and Module Package Reorganization. Editors are now a top-level package (`cranioz/editors/`) independent of `ui/`. Modules are split into `modules/core/` and `modules/builtin/`. Dependency boundaries are enforced by `tests/architecture/test_dependency_boundaries.py`.
- **ADR-0016:** Project Catalog Synchronization. The `ProjectCatalog` consumes a `ProjectIndex` populated by a `ProjectIndexSynchronizer` and invalidated by `ProjectCreated`, `ProjectUpdated`, and `ProjectDeleted`. The repository remains the authoritative source. The strategy is fixed by the ADR and is not open for independent redefinition by the Home Page or the Catalog.
- `EditorStack` uses `QStackedWidget` and `EditorStackSwitcher`, not `QTabWidget`.
- Workspace composition remains responsible for Areas and Editor placement.
- `AreaLayoutRenderer` handles intra-Area composition.
- Editor identity is independent of Workspace position.
- Modules remain declarative and must not instantiate concrete Editors.

### 2.3 2026-11-13 cleanup

The cleanup removed dead code, duplicated components, obsolete debug scripts, and migrated `QImage.mirrored` to `QImage.flipped`.

The minimum PySide6 version was raised to `>=6.9`.

### 2.4 2026-11-18 refactoring closure

The Editor Architecture Refactoring is complete.

- 1635 passing tests, 0 failed, 0 errors, 2 skipped.
- `ruff check`, `ruff format --check`, and `mypy src` clean.
- 85% overall test coverage.
- ADR-0015 records the final architecture.
- The structural prerequisites for Sprint L (Professional module) are met.

---

## 3. Current Focus — Phase 3

**Goal:** Complete the Project, Home Page, and Professional Module foundations before formally beginning Phase 4.

Phase 3 contains two coordinated workstreams:

1. **Structural work:** Editor and Module package reorganization and dependency-boundary corrections. **Completed on 2026-11-18.**
2. **Functional work:** ProjectIndex, coordinated deletion, asynchronous loading, and Professional module integration. **In progress.**

The Editor Architecture Refactoring is a structural activity within Phase 3. It is now closed.

### 3.1 Phase 3 work overview

| Work item | Type | Status | Dependencies |
|---|---|---|---|
| Editor Architecture Refactoring | Structural activity | ✅ Complete | Phase 2 complete |
| Sprint I — ProjectIndex | Functional sprint | 🚧 In Progress | None within Phase 3 |
| Sprint J — Coordinated deletion | Functional sprint | Pending | Sprint I |
| Sprint K — Async loading | Functional sprint | Pending | Sprints I and J |
| Sprint L — Professional module | Functional sprint | Pending | Refactoring ✅, C ✅, E ✅, F ✅ |
| Test stub documentation | Cleanup follow-up | Pending | None |

Sprints I–K form a functional chain. Sprint L may proceed in parallel once its prerequisites are met.

Sprint L is unblocked by the completed Editor Architecture Refactoring and its other prerequisites.

---

## 4. Structural Workstream — Editor Architecture Refactoring

**Status:** ✅ Complete (2026-11-18)
**Technical authority:** `refactoring_plan.md` (now marked Completed)
**Architectural record:** ADR-0015.

The refactoring is recorded in `refactoring_plan.md` §11 (Post-Refactoring Notes). The final validation confirms:

- 1635 passing tests, 0 failed, 0 errors, 2 skipped.
- `ruff check`, `ruff format --check`, and `mypy src` clean.
- 85% overall test coverage.
- No obsolete imports of `cranioz.ui.editors.*` (except the approved composition root).
- No obsolete imports of `cranioz.modules.base`.
- `_KNOWN_DEBT_FILES` and `_DEBT_MAX_LITERALS` consistent with the post-migration file set.

### 4.1 Scope (closed)

The refactoring covered:

- `modules/` reorganization into `modules/core/` and `modules/builtin/`.
- Migration of `ui/editors/` to the top-level `cranioz/editors/` package.
- Separation of Editor and View contracts.
- Separation of reusable Views and View overlays from concrete Editors.
- Workspace and Editor dependency-boundary corrections.
- Test fixture migration.
- Removal of obsolete production components.
- Consolidation of duplicate `PlaceholderEditor` implementations.
- Relevant application package naming cleanup (Step 6.2 complete; Step 6.1 deferred).
- Architecture tests, ADRs, and documentation updates.

The following were explicitly outside the refactoring and remain out of scope:

- Professional module implementation (Sprint L).
- ProjectIndex (Sprint I). Now specified by ADR-0016.
- Coordinated deletion (Sprint J).
- Async Home Page loading (Sprint K).
- New clinical workflows and Phase 4 visualization features.
- General migration of ThemeService, IconProvider, Toolbar, ToolRegistry, and ToolContext out of `ui/`.

### 4.2 Resolved open decisions

| Decision | Resolution |
|---|---|
| `editor_manifest.py` empty | Removed. If a contract is needed for Sprint L, it will be introduced with a real implementation. |
| `editor_catalog.py` empty | Removed. Same rationale. |
| `Workspace.find_viewport_3d()` | Kept as a documented exception to §4.1 rule 8. Regression test tracked as follow-up. |
| `MeshDebugEditor` | Kept and migrated to `editors/builtin/mesh_debug/editor.py`. |
| Duplicate `PlaceholderEditor` | Consolidated into the canonical implementation. `_KNOWN_DEBT_FILES` reduced from 8 to 5 files. |

### 4.3 Deferred to a future PR

- `application/event_bus.py` → `application/events/bus.py` (Step 6.1 of `refactoring_plan.md`). Deferred per §5.10 of that document.
- `editors/view_overlays/` (Step 4.4 of `refactoring_plan.md`). Skipped because the current `ui/editors/overlays/gizmos/` and `ui/editors/overlays/rulers/` directories contain only empty `__init__.py` files.

---

## 5. Functional Workstream — Phase 3 Sprints

The functional workstream is independent of the structural refactoring except where explicit dependencies exist.

### 5.1 Sprint I — ProjectIndex

**Status:** 🚧 In Progress
**Dependency:** None within Phase 3.
**Architectural authority:** ADR-0016 (`docs/adr/ADR-0016_Project_Catalog_Synchronization.md`).

Deliverables:

- `ProjectIndex` Protocol in `application/project/index.py`:
  - `add`, `remove`, `lookup`, `list_summaries`, `list_ids`, `count`, `contains`, `replace_all`.
  - `ProjectIndexStaleError` raised by the synchronized decorator when a rebuild after detected staleness fails.
  - The Protocol is a pure read model; it knows nothing about the repository, the event bus, or the filesystem.
- `InMemoryProjectIndex` in `application/project/in_memory_index.py` — the reference implementation.
- `ProjectIndexSynchronizer` and `SynchronizedProjectIndex` in `application/project/index_synchronizer.py`:
  - `start()` subscribes to `ProjectCreated`, `ProjectUpdated`, `ProjectDeleted`, then bootstraps via `repository.list_metadata()` and `index.replace_all(...)`, on the same synchronous call stack.
  - Handlers update the index synchronously; they never propagate exceptions to the `EventBus`. On failure they log with `project_id` and operation name only (no PHI) and mark `_possibly_stale = True`.
  - `rebuild()` re-populates the index from the repository.
  - `ensure_fresh()` is called by `SynchronizedProjectIndex` before every read; it is a no-op when not stale, rebuilds when stale, and propagates `ProjectIndexStaleError` if the rebuild fails.
- `ProjectCatalog` refactored to consume a `ProjectIndex`:
  - `ProjectCatalog.refresh()` is removed; freshness is automatic via `SynchronizedProjectIndex`.
  - The catalog does not know about the synchronizer or the repository.
- Bootstrap ordering guarantee per ADR-0016 §4. The ordering guarantee holds only while the bootstrap is synchronous; Sprint K must revisit ADR-0016 §4.1 if the bootstrap becomes asynchronous.
- **Not** part of Sprint I: `FilesystemProjectIndex` does not exist as a class name. A persisted or SQLite-backed index remains deferred to Phase 8 (see §7).

Contract tests (per ADR-0016 §8):

- `test_project_index_contract.py` — `InMemoryProjectIndex` behavior; parametrizable for future `SqliteProjectIndex`.
- `test_project_index_synchronizer.py` — bootstrap, event handlers, error containment, `rebuild`, `ensure_fresh`.
- `test_project_index_sync_bootstrap.py` — bootstrap window; verifies consistency under a synchronous `EventBus`.
- `test_project_catalog_uses_index.py` — the catalog reads via `ProjectIndex`; `repository.list_metadata` is not called during queries (mock fails if invoked).
- `test_project_catalog_sync.py` — end-to-end integration with `ProjectManager`.
- `test_project_index_stale_propagation.py` — `ProjectIndexStaleError` propagation and `MainWindow` handling.

Benchmark (documented in ADR-0016 implementation notes, not run in CI): 100/300/1000 projects in `tmp_path`, comparing `search_projects()` latency and `repository.list_metadata` call count between baseline (direct repository) and new (indexed).

The SQLite implementation remains deferred to Phase 8.

### 5.2 Sprint J — Coordinated deletion

**Status:** Pending
**Dependency:** Sprint I.

Deliverables:

- `ProjectManager.delete_project` coordinates:
  - `ProjectCatalog`
  - `ProjectIndex`
  - `FilesystemProjectRepository`
- Rollback when any deletion step fails.
- External source data in External Reference mode must never be removed by project deletion.
- Contract and failure-path tests.

Sprint J must preserve the single-lifecycle-writer invariant (`project.md` §25). Deletion reflects into the catalog through the `ProjectDeleted` event; the `ProjectManager` does not call the catalog directly.

### 5.3 Sprint K — Async loading

**Status:** Pending
**Dependencies:** Sprints I and J.

Deliverables:

- `HomePage` loads projects and flows through `TaskManager`.
- No blocking I/O in `MainWindow.__init__`.
- `HomePage.refresh()` does not block the GUI thread.
- Rollback if Workspace creation fails after project opening.
- Regression tests for loading, cancellation, failure, and recovery.
- **Bootstrap-ordering re-evaluation:** if the `ProjectIndexSynchronizer` bootstrap becomes asynchronous in Sprint K, ADR-0016 §4.1 must be revisited before Sprint K is closed. The options at that time include a bootstrap-time event queue or a transactional `replace_all` that preserves concurrent `add` operations. The ADR does not pre-commit to a solution; it records that the decision must be reopened.

### 5.4 Sprint L — Professional module

**Status:** Pending (unblocked by the completed refactoring)
**Dependencies:** Editor Architecture Refactoring ✅, Sprint C ✅, Sprint E ✅, Sprint F ✅.

Deliverables:

- `ProfessionalEditor` registered in `EditorRegistry`.
- `ModuleUISpec` for the Professional module.
- Settings integration through `professional.*` keys.
- Integration and contract tests.

Sprint L must use the final Editor package architecture (`cranioz/editors/builtin/`). The legacy `ui/editors/` organization no longer exists.

### 5.5 Test stub documentation

**Status:** Pending.

The following files reserve contracts for missing granular unit tests:

- `tests/infrastructure/i18n/` — four stubs.
- `tests/infrastructure/scene/test_scene_query_adapter.py`.

Required actions:

- Add a `README.md` to `tests/infrastructure/i18n/`.
- Add a `README.md` to `tests/infrastructure/scene/`.
- Add explicit TODO markers to relevant stubs.

Do not interpret these empty files as completed unit-test coverage.

---

## 6. Execution Strategy and Parallelism

The structural refactoring is complete. The remaining work is the functional chain I → J → K, with L proceeding in parallel subject to its prerequisites.

### 6.1 Dependency overview

| Work item | Can start independently? | Required dependency |
|---|---|---|
| Sprint I | Yes | None within Phase 3 |
| Sprint J | No | Sprint I |
| Sprint K | No | Sprints I and J |
| Sprint L | Yes (structurally) | Refactoring ✅, C ✅, E ✅, F ✅ |

### 6.2 Recommended execution sequence

**Current cycle:**

1. Sprint I is in progress (specified by ADR-0016).
2. Start Sprint J after Sprint I is complete.
3. Start Sprint K after Sprints I and J are complete. Before closing Sprint K, revisit ADR-0016 §4.1 if the index bootstrap becomes asynchronous.
4. Sprint L may begin in parallel with Sprints I–K, but its integration tests may benefit from the ProjectIndex contract delivered by Sprint I.

The sequence may be adjusted when necessary, but the declared dependencies must be preserved.

---

## 7. Known Issues and Deferred Items

| Item | Status | Reference |
|---|---|---|
| DICOM visualization bug (voxel ordering) | Resolved 2026-11-06 | `implementation_plan.md` |
| ADR-0003 legacy | Superseded by ADR-0014 | `docs/adr/` |
| `steps_panel` overlay | Removed; replaced by `WorkflowBreadcrumb` in Phase 5 | `implementation_plan.md` |
| `correlation_id` propagation in Workspace | Outstanding | `implementation_plan.md` |
| `event_subscription` propagation test | Dedicated test pending | `tests/integration/ui/workspace/` |
| Hardcoded appearance literals | Tracked in `_KNOWN_DEBT_FILES` (now 5 files) | `tests/architecture/` |
| `EditorStackSwitcher` inline QSS | 7 literals; not resolved by refactoring | `_KNOWN_DEBT_FILES` |
| `Editor.icon_name` missing from ABC | Outstanding; not a refactoring blocker | Architectural debt |
| `Workspace.find_viewport_3d()` regression test | Tracked as follow-up (Step 1 decision #9) | ADR-0015 |
| `stl.py` migration from `GetData()` | Deferred to Phase 4.5 / VTK 10 compatibility work | `stl.py` |
| `pyproject.toml` unused `ignore_missing_imports` entries | Cleanup task; no functional impact | `pyproject.toml` |
| Implicit handler resolution in `InMemoryModuleLoader` | Not included in refactoring | `architectural_consolidation_plan.md` §4.4 |
| `application/event_bus.py` → `application/events/bus.py` | Deferred to a separate PR | `refactoring_plan.md` §5.10 |
| SQLite `ProjectIndex` backend | Deferred to Phase 8 | `implementation_plan.md`, ADR-0016 §2.1 |
| Persisted filesystem index (`index.json`) | Deferred to Phase 8; rejected for Sprint I per ADR-0016 §5 | ADR-0016 §5 |
| External mutation detection / background disk reconciliation | Deferred to Phase 8 | ADR-0016 §3.2, `implementation_plan.md` |
| Recent Projects | Deferred to Phase 8 | `implementation_plan.md` |

The project must not silently absorb unrelated items from this list into future sprints.

---

## 8. Validation Requirements

Every functional sprint must leave the project in a valid, testable state.

### 8.1 Required commands

```powershell
.venv\Scripts\python.exe -m pytest
.venv\Scripts\python.exe -m ruff check .
.venv\Scripts\python.exe -m ruff format --check .
.venv\Scripts\python.exe -m mypy src