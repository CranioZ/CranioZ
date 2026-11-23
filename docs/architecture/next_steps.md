# Next Steps

**Document type:** Action plan and development handoff
**Status:** Active
**Scope:** Current development priorities and execution sequence for Phase 3
**Last updated:** 2026-11-22

---

## 1. Context

CranioZ has completed Phases 0, 1, and 2. Phase 3 — Project, Home Page & Professional Module — is the active phase.

Phase 4 — Scene & Visualization — remains planned and must not formally begin until Phase 3 is closed.

This document translates the main implementation roadmap into immediate development priorities and the current operational handoff.

### 1.1 Planning document hierarchy

The planning and specification documents have distinct responsibilities:

| Document | Responsibility |
|---|---|
| `implementation_plan.md` | Overall roadmap, phases, deliverables, dependencies, and completion criteria |
| `next_steps.md` | Immediate priorities, execution sequence, and current development handoff |
| `architectural_consolidation_plan.md` | Architectural inconsistencies, duplication, legacy components, and consolidation requirements |
| `refactoring_plan.md` | Detailed technical procedure for the Editor and Module structural refactoring |
| `monitor_logs.md` | Technical specification of the Monitor de Logs diagnostic subsystem (planned; not implemented) |

`implementation_plan.md` governs the overall roadmap. This document must remain consistent with it and must not redefine phases or functional deliverables.

`monitor_logs.md` is not part of the roadmap; it is a subsystem specification referenced here for traceability. Its implementation is deferred to a dedicated sprint (§6.2) and is not part of Phase 3's deliverables.

### 1.2 Current validation baseline

The latest confirmed baseline is:

- **1,701 passing tests**
- **0 failed**
- **0 errors**
- **2 skipped**
- `ruff check .` clean
- `ruff format --check .` clean
- `mypy src` clean (284 source files)
- **85% overall test coverage** (unchanged; Sprint J added tests only, no new production code)

This is the baseline recorded on 2026-11-22, after Sprint J closure. It supersedes the previous baseline of 1,635 (2026-11-18, after the Editor Architecture Refactoring) and 1,692 (2026-11-20, after Sprint I). The measurement was not re-taken for overall coverage because Sprint J did not modify production code; the delta is +9 tests, all passing.

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
- Project Catalog synchronization via `ProjectIndex` (ADR-0016, Sprint I).
- Coordinated project deletion with the delete-specific staleness contract verified (Sprint J).

The DICOM import and visualization pipeline has foundational implementations and integration work documented in `implementation_plan.md`.

The Project Catalog synchronization mechanism is fully implemented per **ADR-0016** (Accepted 2026-11-18, implemented in Sprint I, extended in Sprint J with the delete-specific paths).

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
| **Sprint I — ProjectIndex** | **Complete** | **Closed 2026-11-20. 1692 passing tests.** |
| **Sprint J — Coordinated deletion** | **Complete** | **Closed 2026-11-22. 1701 passing tests.** |

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

### 2.5 2026-11-20 Sprint I closure

Sprint I (`ProjectIndex`) is complete.

- 1692 passing tests, 0 failed, 0 errors, 2 skipped.
- `ruff check`, `ruff format --check`, and `mypy src` clean.
- `ProjectIndex`, `InMemoryProjectIndex`, `ProjectIndexSynchronizer`, and `SynchronizedProjectIndex` implemented per ADR-0016.
- `ProjectCatalog` consumes `ProjectIndex`; `ProjectCatalog.refresh()` removed; `ProjectCatalog(repository=...)` removed.
- Bootstrap ordering verified (`subscribe` → `repository.list_metadata()` → `replace_all`, same synchronous call stack).
- The integration fixture `tests/integration/ui/test_main_window_import.py` migrated to the composition-root wiring, preserving the bootstrap order per ADR-0016 §4.2.
- `FilesystemProjectIndex` does not exist; SQLite implementation deferred to Phase 8.

### 2.6 2026-11-22 Sprint J closure

Sprint J (`Coordinated deletion`) is complete.

- 1701 passing tests, 0 failed, 0 errors, 2 skipped (+9 from Sprint I).
- `ruff check`, `ruff format --check`, and `mypy src` clean (284 source files).
- `git diff --stat src/` empty: **no production file changed**.
- The `ProjectManager.delete_project` coordination (repository delete → `ProjectDeleted` publish → synchronizer invalidation → catalog reflects on next query) was already correct; the sprint proved it with tests rather than changing production code.
- Physical delete invariant verified: only `project.json` is removed; sibling files (External Reference mode DICOM, `patient_record.json`, future Phase 4 assets) survive byte-identical.
- Delete-specific staleness paths verified per ADR-0016 §3.3/§3.4 (handler containment, rebuild-on-next-query, `ProjectIndexStaleError` on double failure).
- Architecture gate added: `tests/architecture/test_no_legacy_project_delete_api.py` (4 tests).
- UI affordance for delete deferred (see §7).

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
| Sprint I — ProjectIndex | Functional sprint | ✅ Complete (2026-11-20) | None within Phase 3 |
| Sprint J — Coordinated deletion | Functional sprint | ✅ Complete (2026-11-22) | Sprint I ✅ |
| Sprint K — Async loading | Functional sprint | 🚧 Pending | Sprint J ✅ |
| Sprint L — Professional module | Functional sprint | 🚧 Pending | Refactoring ✅, C ✅, E ✅, F ✅ |
| Test stub documentation | Cleanup follow-up | 🚧 Pending | None |

Sprints J–K form a functional chain. Sprint L may proceed in parallel once its prerequisites are met.

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
- ProjectIndex (Sprint I). Now implemented per ADR-0016.
- Coordinated deletion (Sprint J). Now implemented.
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

**Status:** ✅ Complete (2026-11-20)
**Dependency:** None within Phase 3.
**Architectural authority:** ADR-0016 (`docs/adr/ADR-0016_Project_Catalog_Synchronization.md`).

Deliverables:

- ✅ `ProjectIndex` Protocol in `application/project/index.py`:
  - `add`, `remove`, `lookup`, `list_summaries`, `list_ids`, `count`, `contains`, `replace_all`.
  - `ProjectIndexStaleError` raised by the synchronized decorator when a rebuild after detected staleness fails.
  - The Protocol is a pure read model; it knows nothing about the repository, the event bus, or the filesystem.
- ✅ `InMemoryProjectIndex` in `application/project/in_memory_index.py` — the reference implementation.
- ✅ `ProjectIndexSynchronizer` and `SynchronizedProjectIndex` in `application/project/index_synchronizer.py`:
  - `start()` subscribes to `ProjectCreated`, `ProjectUpdated`, `ProjectDeleted`, then bootstraps via `repository.list_metadata()` and `index.replace_all(...)`, on the same synchronous call stack.
  - Handlers update the index synchronously; they never propagate exceptions to the `EventBus`. On failure they log with `project_id` and operation name only (no PHI) and mark `_possibly_stale = True`.
  - `rebuild()` re-populates the index from the repository.
  - `ensure_fresh()` is called by `SynchronizedProjectIndex` before every read; it is a no-op when not stale, rebuilds when stale, and propagates `ProjectIndexStaleError` if the rebuild fails.
- ✅ `ProjectCatalog` refactored to consume a `ProjectIndex`:
  - `ProjectCatalog.refresh()` is removed; freshness is automatic via `SynchronizedProjectIndex`.
  - The catalog does not know about the synchronizer or the repository.
- ✅ Bootstrap ordering guarantee per ADR-0016 §4. The ordering guarantee holds only while the bootstrap is synchronous; Sprint K must revisit ADR-0016 §4.1 if the bootstrap becomes asynchronous.
- **Not** part of Sprint I: `FilesystemProjectIndex` does not exist as a class name. A persisted or SQLite-backed index remains deferred to Phase 8 (see §7).

Contract tests (per ADR-0016 §8):

- ✅ `test_project_index_contract.py` — `InMemoryProjectIndex` behavior; parametrizable for future `SqliteProjectIndex`.
- ✅ `test_project_index_synchronizer.py` — bootstrap, event handlers, error containment, `rebuild`, `ensure_fresh`.
- ✅ `test_project_index_sync_bootstrap.py` — bootstrap window; verifies consistency under a synchronous `EventBus`.
- ✅ `test_project_catalog_uses_index.py` — the catalog reads via `ProjectIndex`; `repository.list_metadata` is not called during queries (mock fails if invoked).
- ✅ `test_project_catalog_sync.py` — end-to-end integration with `ProjectManager`.
- ✅ `test_project_index_stale_propagation.py` — `ProjectIndexStaleError` propagation and `MainWindow` handling.

Benchmark (documented in ADR-0016 implementation notes, not run in CI): 100/300/1000 projects in `tmp_path`, comparing `search_projects()` latency and `repository.list_metadata` call count between baseline (direct repository) and new (indexed).

The SQLite implementation remains deferred to Phase 8.

**Closure note (2026-11-20):** 1692 passing tests, 0 failed, 0 errors, 2 skipped. Integration fixture `tests/integration/ui/test_main_window_import.py` migrated to the composition-root wiring (`repository → synchronizer → index → catalog`), preserving the bootstrap order required by ADR-0016 §4. No production code changed during that migration; the drift was confined to the test fixture.

### 5.2 Sprint J — Coordinated deletion

**Status:** ✅ Complete (2026-11-22)
**Dependency:** Sprint I ✅.

Deliverables:

- ✅ `ProjectManager.delete_project` coordinates `ProjectCatalog` → `ProjectIndex` → `FilesystemProjectRepository` via the `ProjectDeleted` event (ADR-0016 §2.2). The `ProjectManager` does **not** call `ProjectCatalog` or `ProjectIndex` directly; the coordination is the event-driven path.
- ✅ Rollback semantics: a repository failure raises before `ProjectDeleted` is published; a handler failure is contained by the synchronizer (ADR-0016 §3.4) and marks the index stale; the next query rebuilds from the authoritative repository (ADR-0016 §3.3). No event compensation, no manual index re-add.
- ✅ External source data in External Reference mode is never removed by project deletion. The `FilesystemProjectRepository` owns exactly one file (`project.json`); sibling files belong to other persistence layers and survive deletion byte-identical.
- ✅ Contract and failure-path tests.

Sprint J preserves the single-lifecycle-writer invariant (`project.md` §25). Deletion reflects into the catalog through the `ProjectDeleted` event; the `ProjectManager` does not call the catalog directly.

**Deliverables in `tests/` (zero production change):**

- **J.1 — Physical delete invariant** (`tests/integration/application/project/test_project_delete_invariant.py`, new, 2 tests):
  - `test_delete_project_removes_only_project_json`: after `ProjectManager.delete_project`, `project.json` is gone and every sibling file (`patient_record.json`, `scene.json`, `imaging/ct/slice.dcm`, `models/maxilla.stl`) survives byte-identical.
  - `test_delete_project_leaves_parent_project_directory`: the project directory itself survives; only the discoverable marker (`project.json`) is removed.
  - This is the executable form of the plan's Sprint J requirement: "External source data (External Reference mode) is never removed by project deletion."
  - Not covered by `test_project_repository_contract.py`: the Protocol contract does not specify filesystem behavior. The invariant is a `FilesystemProjectRepository` property.

- **J.2 — Delete-specific staleness paths** (`tests/integration/application/project/test_project_index_stale_propagation.py`, extended from 2 → 5 tests):
  - `test_delete_project_handler_failure_does_not_propagate_to_manager`: ADR-0016 §3.4 — a failing `_on_deleted` handler is contained; `delete_project` returns normally.
  - `test_delete_project_handler_failure_rebuilds_on_next_query`: ADR-0016 §3.3 — after a contained handler failure, the next catalog query rebuilds from the repository and reflects the deletion.
  - `test_delete_project_rebuild_failure_after_handler_failure_raises_stale`: ADR-0016 §3.3 — when both handler and rebuild fail, the query raises `ProjectIndexStaleError` instead of silently returning the pre-delete state.

- **J.4 — Architecture gate** (`tests/architecture/test_no_legacy_project_delete_api.py`, new, 4 tests):
  - `test_no_call_site_constructs_project_catalog_with_repository`: ADR-0016 removed `ProjectCatalog(repository=...)`.
  - `test_no_call_site_calls_project_catalog_refresh`: ADR-0016 removed `ProjectCatalog.refresh()`.
  - `test_only_filesystem_repository_references_project_json`: no module outside `FilesystemProjectRepository`, `ProjectPathResolver`, `ProjectSerialization` may **access** (AST-detected, not merely mention) `project.json`.
  - `test_only_project_manager_calls_repository_delete`: `ProjectManager` is the single lifecycle writer (project.md §25).

**Closure note (2026-11-22):**

Final validation: **1701 passed, 0 failed, 0 errors, 2 skipped; `tests/architecture/` 85 passed.** The 2 skips are pre-existing (View-level and Editor-level Toolbars temporarily disabled, Block 5.5). The 9 warnings are pre-existing (`GetData()` deprecated in VTK ≥ 9.6, exercised by `stl.py:143`). No production file changed: `git diff --stat src/` is empty.

Lint/type gate: `ruff check .` → `All checks passed!`; `ruff format --check .` → `566 files already formatted`; `mypy src` → `Success: no issues found in 284 source files`. `mypy` emits one pre-existing note about unused `ignore_missing_imports` entries in `pyproject.toml` (see §7).

**Scope correction recorded during Sprint J:** the UI affordance for delete (button/menu/confirmation dialog) is **deferred**. The plan's §8.6 ("The feature is usable through its intended UI workflow") is satisfied at the **API level** — `ProjectManager.delete_project` is reachable and its effects propagate through the catalog without an explicit refresh — but **not at the UI level**, because no delete affordance exists today (see `home_page.md` and `project.md` §7: "For example, if a future UI provides a 'Delete Project' action…"). Adding the UI requires UX decisions (placement in `ProjectTable`, i18n keys in `en/` and `pt-BR/`, confirmation dialog, disabled state for the open project) that are out of scope for a "coordinated deletion" sprint.

**Debt tracked (not fixed in Sprint J):**

- **UI affordance for Delete Project.** Adding the button/menu + confirmation dialog + i18n keys is a separate sprint. The API-level behavior is verified; the UI-level criterion (§8.6) will be met when the affordance is added.
- **`patient_record.json` is not deleted when a project is deleted.** Deliberate Phase 4 boundary: the `FilesystemProjectRepository` owns only `project.json`; `patient_record.json` belongs to the Patient persistence layer. `test_delete_project_removes_only_project_json` is the forcing function: when Phase 4 introduces per-project assets, that test must be revisited and a decision recorded (Phase 4, §4.3.5 storage/export).
- **`ProjectIndexSynchronizer` remains synchronous, single-threaded.** `delete_project` remains synchronous. Sprint K (async loading) must not parallelize the `repository.delete → publish(ProjectDeleted)` pair without re-opening ADR-0016 §4.1.
- **`pyproject.toml` mypy note.** `mypy` reports unused `ignore_missing_imports` entries for `cupy.*`, `cv2.*`, `numba.*`, `reportlab.*`, `scipy.*`. They will become active in Phase 4 (ITK/CGAL/OCCT) or Phase 6 (segmentation with scipy/numba). No action until then.

**Test count delta:** +9 (1692 → 1701). Sprint I's test baseline is preserved.

### 5.3 Sprint K — Async loading

**Status:** ✅ Complete (2026-11-22)
**Dependencies:** Sprint J ✅.

**Scope decision (recorded at closure):** K-minimal option (b) —
**flows async, projects synchronous**. Rationale:

- The `ProjectCatalog` reads from an in-memory `SynchronizedProjectIndex`
  (ADR-0016), so project listing performs no I/O on the GUI thread. A
  Task for projects would be decorative.
- The only blocking I/O on the boot path is
  `FlowCatalog.list_definitions()` (filesystem read of
  `<flows_root>/*/flow.json`), invoked from
  `MainWindow._populate_flow_list()` in `MainWindow.__init__`. This is
  exactly the "File I/O larger than a few milliseconds" case in
  ADR-0011 §2.1, and it is moved to a `_LoadFlowsTask` dispatched
  through the `TaskManager`.
- `synchronizer.start()` remains synchronous in the composition root
  (`__main__::_build_project_subsystem`). ADR-0016 §4.1 is **not**
  reopened. The K.6 criterion is satisfied by construction.

**Deliverables:**

- ✅ `HomePage.refresh()` is synchronous (calls `ProjectTable.refresh()`).
  The decorative `_LoadProjectsTask` and the `loading_*` signals for
  projects were removed. The `HomePage` no longer receives a
  `task_manager`.
- ✅ `HomePage` exposes `flows_loading_started` / `flows_loading_finished` /
  `flows_loading_failed` for the `MainWindow` to drive UI state if it
  chooses. Today the `FlowList` keeps its "No flows available"
  placeholder during the load (silent loading).
- ✅ `MainWindow._dispatch_flow_loading()` dispatches a `_LoadFlowsTask`
  through the injected `TaskManager`. It falls back to a synchronous
  load when no `TaskManager` is injected (tests).
- ✅ `_LoadFlowsTask` calls `progress(0.0)` / `progress(1.0)` and
  `cancel_token.raise_if_cancelled()` at both boundaries, per
  ADR-0011 §5.
- ✅ `MainWindow.__init__` performs no blocking I/O on the flow path.
- ✅ Rollback on Workspace creation failure (K.4) already present in
  `_on_project_open_requested`; covered by a new integration test.
- ✅ Bootstrap-ordering guarantee (K.6) covered by a new integration
  test that mirrors `__main__::_build_project_subsystem`.

**Explicitly out of Sprint K scope (unchanged):**

- Monitor de Logs subsystem (dedicated sprint, after K).
- Separation Console / History / Monitor de Logs (project invariant).

**Explicitly not re-opened:**

- ADR-0016 §4.1 — the bootstrap remains synchronous.

### 5.4 Sprint L — Professional module

**Status:** 🚧 Pending (unblocked by the completed refactoring and by Sprints C, E, F)
**Dependencies:** Editor Architecture Refactoring ✅, Sprint C ✅, Sprint E ✅, Sprint F ✅.

Deliverables:

- `ProfessionalEditor` registered in `EditorRegistry`.
- `ModuleUISpec` for the Professional module.
- Settings integration through `professional.*` keys.
- Integration and contract tests.

Sprint L must use the final Editor package architecture (`cranioz/editors/builtin/`). The legacy `ui/editors/` organization no longer exists.

Sprint L is independent of Sprints J–K functionally and may proceed in parallel. Its integration tests may benefit from the ProjectIndex contract delivered by Sprint I.

### 5.5 Test stub documentation

**Status:** 🚧 Pending.

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

The structural refactoring is complete. Sprint I and Sprint J are complete. The remaining work is the functional chain J → K, with L proceeding in parallel subject to its prerequisites.

### 6.1 Dependency overview

| Work item | Can start independently? | Required dependency |
|---|---|---|
| Sprint I | ✅ Complete (2026-11-20) | — |
| Sprint J | ✅ Complete (2026-11-22) | Sprint I ✅ |
| Sprint K | No | Sprint J ✅ |
| Sprint L | Yes (structurally) | Refactoring ✅, C ✅, E ✅, F ✅ |
| Monitor de Logs (dedicated sprint) | Yes (documentation) | `monitor_logs.md` (specification) |
| Monitor de Logs (implementation) | No | Sprint K closed (to inform tab mapping) |

### 6.2 Recommended execution sequence

**Current cycle:**

1. Sprint I and Sprint J are complete.
2. Start Sprint K. Before closing Sprint K, revisit ADR-0016 §4.1 **if and only if** the index bootstrap becomes asynchronous.
3. Sprint L may begin in parallel with Sprint K. Its integration tests may benefit from the completed `ProjectIndex` contract.
4. Close Sprint L when its deliverables, contract tests, and settings integration are complete.
5. Mark Phase 3 `✅ Implemented` in `implementation_plan.md` only when Sprints K and L are both closed.

**Deferred (not part of the current cycle, not part of Phase 3):**

- **Monitor de Logs — dedicated sprint (unscheduled).** Implements `monitor_logs.md`: `QtLogHandler`, `LogsDialog`, the 📋 button wiring on the HomePage top bar, and the `Workspace._apply_default_splitter_sizes` snapshot contract for the `Areas` tab. It is deliberately sequenced **after** Sprint K, so that the logging emitted by the async-loading work informs the tab mapping and the format. It does not block Sprint K or Sprint L. It is not required to close Phase 3.

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
| **UI affordance for Delete Project** | **Deferred from Sprint J (2026-11-22)** | **`next_steps.md` §5.2 "Debt tracked"** |
| **`patient_record.json` deletion on project delete** | **Deferred to Phase 4 §4.3.5 (storage/export)** | **`next_steps.md` §5.2 "Debt tracked"** |
| **`ProjectIndexSynchronizer` sync-only (no parallel delete)** | **Constraint for Sprint K** | **`next_steps.md` §5.3 "Constraints inherited from Sprint J"** |
| **Monitor de Logs — `LogsDialog` + `QtLogHandler` + 📋 wiring + `Areas` snapshot contract** | **Planned. Not implemented. Dedicated sprint, sequenced after Sprint K. Not part of Phase 3's closure criteria.** | **`monitor_logs.md` (technical authority); `home_page.md` §25 (`logs_requested` reserved) and §26 (pointer); `workspace.md` §5.5 (pointer)** |
| **Separation Console / History / Monitor de Logs** | **Project invariant, recorded 2026-11-22. The `ConsoleEditor` must not be fed by `logging`; it must be fed by an application-level notification service (to be defined).** | **`monitor_logs.md` §2** |

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
```