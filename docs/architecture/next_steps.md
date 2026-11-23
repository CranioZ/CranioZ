# Next Steps

**Document type:** Action plan and development handoff[cite: 2]
**Status:** Active[cite: 2]
**Scope:** Current development priorities and execution sequence for Phase 3[cite: 2]
**Last updated:** 2026-11-22[cite: 2]

---

## 1. Context

CranioZ has completed Phases 0, 1, and 2[cite: 2]. Phase 3 — Project, Home Page & Professional Module — is the active phase[cite: 2].

Phase 4 — Scene & Visualization — remains planned and must not formally begin until Phase 3 is closed[cite: 2].

This document translates the main implementation roadmap into immediate development priorities and the current operational handoff[cite: 2].

### 1.1 Planning document hierarchy

The planning and specification documents have distinct responsibilities[cite: 2]:

| Document | Responsibility |
|---|---|
| `implementation_plan.md` | Overall roadmap, phases, deliverables, dependencies, and completion criteria[cite: 2] |
| `next_steps.md` | Immediate priorities, execution sequence, and current development handoff[cite: 2] |
| `architectural_consolidation_plan.md` | Architectural inconsistencies, duplication, legacy components, and consolidation requirements[cite: 2] |
| `refactoring_plan.md` | Detailed technical procedure for the Editor and Module structural refactoring[cite: 2] |
| `monitor_logs.md` | Technical specification of the Monitor de Logs diagnostic subsystem (planned; not implemented)[cite: 2] |

`implementation_plan.md` governs the overall roadmap[cite: 2]. This document must remain consistent with it and must not redefine phases or functional deliverables[cite: 2].

`monitor_logs.md` is not part of the roadmap; it is a subsystem specification referenced here for traceability[cite: 2]. Its implementation is deferred to a dedicated sprint (§6.2) and is not part of Phase 3's deliverables[cite: 2].

### 1.2 Current validation baseline

The latest confirmed baseline is:

- **1,713 passing tests**[cite: 2]
- **0 failed**[cite: 2]
- **0 errors**[cite: 2]
- **2 skipped**[cite: 2]
- `ruff check .` clean[cite: 2]
- `ruff format --check .` clean (570 files)[cite: 2]
- `mypy src` clean (284 source files)[cite: 2]

This is the baseline recorded on 2026-11-22, after Sprint K closure[cite: 2]. It supersedes the previous baselines of 1,635 (2026-11-18, after the Editor Architecture Refactoring), 1,692 (2026-11-20, after Sprint I), and 1,701 (2026-11-22, after Sprint J), with a delta of **+12 tests** over Sprint J (`test_home_page_flows_async.py`, `test_main_window_workspace_rollback.py`, and `test_main_window_bootstrap_ordering.py`)[cite: 2].

### 1.3 Current architectural state

The Workspace foundation is implemented and tested[cite: 2].

Completed capabilities include:

- Area management and Workspace composition[cite: 2].
- Editor lifecycle and context propagation[cite: 2].
- Editor-level and View-level toolbar integration[cite: 2].
- Active View detection and `ACTIVE_ONLY` toolbar behavior[cite: 2].
- Intra-Area layout through `AreaLayoutRenderer`[cite: 2].
- Multiple Editors within an Area through `EditorStack`[cite: 2].
- Lazy materialization and Editor lifecycle management[cite: 2].
- Frameless application window, custom drag support, and native resizing[cite: 2].
- Theme and icon provider foundations[cite: 2].
- Internationalization of the application shell[cite: 2].
- Editor and Module packages reorganized into `cranioz/editors/` and `cranioz/modules/core/`, with dependency boundaries enforced by AST-based architecture tests (ADR-0015)[cite: 2].
- Project Catalog synchronization via `ProjectIndex` (ADR-0016, Sprint I)[cite: 2].
- Coordinated project deletion with the delete-specific staleness contract verified (Sprint J)[cite: 2].
- Asynchronous clinical flow loading via `_LoadFlowsTask` and `TaskManager` while keeping project catalog reads and `synchronizer.start()` synchronous (Sprint K)[cite: 2].

The DICOM import and visualization pipeline has foundational implementations and integration work documented in `implementation_plan.md`[cite: 2].

The Project Catalog synchronization mechanism is fully implemented per **ADR-0016** (Accepted 2026-11-18, implemented in Sprint I, extended in Sprint J with the delete-specific paths, and preserved with synchronous bootstrap in Sprint K)[cite: 2].

---

## 2. Completed Work

### 2.1 Phases and Sprints

| Item | Status | Notes |
|---|---|---|
| Phase 0 — Foundation & Boot | Complete[cite: 2] | Startup performance improvements remain tracked separately[cite: 2] |
| Phase 1 — Contracts, Core Domain & i18n | Complete[cite: 2] | Includes Sprints B and C[cite: 2] |
| Phase 2 — Workspace Engine & Icons | Complete[cite: 2] | Closed after Sprint H[cite: 2] |
| Sprint B — i18n contract and catalogs | Complete[cite: 2] |[cite: 2] |
| Sprint C — EditorContext propagation | Complete[cite: 2] | Closed Phase 1[cite: 2] |
| Sprint E — ThemeService and ThemeCompiler | Complete[cite: 2] | 47 canonical design tokens[cite: 2] |
| Sprint F — IconProvider and UnicodeIconProvider | Complete[cite: 2] | 60 registered icons[cite: 2] |
| Sprint G — AreaLayoutRenderer | Complete[cite: 2] | SINGLE, SPLIT, and STACK extension point[cite: 2] |
| Sprint H — EditorStack | Complete[cite: 2] | LEAF, SPLIT, and STACK composition[cite: 2] |
| Sprint M — Frameless Window and Native Chrome | Complete[cite: 2] | Drag, resize, maximize, minimize, and close[cite: 2] |
| Blocks 1–6 | Complete[cite: 2] | Toolbar, active View, TomographyEditor integration, and visual validation[cite: 2] |
| Blocks 5.5–5.6.1 | Complete[cite: 2] | Area sizing and window controls[cite: 2] |
| **Editor Architecture Refactoring** | **Complete**[cite: 2] | **See ADR-0015 and `refactoring_plan.md` §11. Closed on 2026-11-18.**[cite: 2] |
| **ADR-0016 — Project Catalog Synchronization** | **Accepted**[cite: 2] | **Specifies Sprint I. See `docs/adr/ADR-0016_Project_Catalog_Synchronization.md`.**[cite: 2] |
| **Sprint I — ProjectIndex** | **Complete**[cite: 2] | **Closed 2026-11-20. 1692 passing tests.**[cite: 2] |
| **Sprint J — Coordinated deletion** | **Complete**[cite: 2] | **Closed 2026-11-22. 1701 passing tests.**[cite: 2] |
| **Sprint K — Async loading** | **Complete**[cite: 2] | **Closed 2026-11-22. K-minimal (flows async, projects sync); 1713 passing tests.**[cite: 2] |

### 2.2 Important architectural decisions

- **ADR-0013:** Editor Layout Tree, View Layout Tree, and Toolbar Placement[cite: 2].
- **ADR-0014:** Qt Widgets + modular QSS + Python Design Tokens[cite: 2].
- **ADR-0015:** Editor and Module Package Reorganization. Editors are now a top-level package (`cranioz/editors/`) independent of `ui/`. Modules are split into `modules/core/` and `modules/builtin/`. Dependency boundaries are enforced by `tests/architecture/test_dependency_boundaries.py`[cite: 2].
- **ADR-0016:** Project Catalog Synchronization. The `ProjectCatalog` consumes a `ProjectIndex` populated by a `ProjectIndexSynchronizer` and invalidated by `ProjectCreated`, `ProjectUpdated`, and `ProjectDeleted`. The repository remains the authoritative source. The strategy is fixed by the ADR and is not open for independent redefinition by the Home Page or the Catalog[cite: 2].
- `EditorStack` uses `QStackedWidget` and `EditorStackSwitcher`, not `QTabWidget`[cite: 2].
- Workspace composition remains responsible for Areas and Editor placement[cite: 2].
- `AreaLayoutRenderer` handles intra-Area composition[cite: 2].
- Editor identity is independent of Workspace position[cite: 2].
- Modules remain declarative and must not instantiate concrete Editors[cite: 2].

### 2.3 2026-11-13 cleanup

The cleanup removed dead code, duplicated components, obsolete debug scripts, and migrated `QImage.mirrored` to `QImage.flipped`[cite: 2].

The minimum PySide6 version was raised to `>=6.9`[cite: 2].

### 2.4 2026-11-18 refactoring closure

The Editor Architecture Refactoring is complete[cite: 2].

- 1635 passing tests, 0 failed, 0 errors, 2 skipped[cite: 2].
- `ruff check`, `ruff format --check`, and `mypy src` clean[cite: 2].
- 85% overall test coverage[cite: 2].
- ADR-0015 records the final architecture[cite: 2].
- The structural prerequisites for Sprint L (Professional module) are met[cite: 2].

### 2.5 2026-11-20 Sprint I closure

Sprint I (`ProjectIndex`) is complete[cite: 2].

- 1692 passing tests, 0 failed, 0 errors, 2 skipped[cite: 2].
- `ruff check`, `ruff format --check`, and `mypy src` clean[cite: 2].
- `ProjectIndex`, `InMemoryProjectIndex`, `ProjectIndexSynchronizer`, and `SynchronizedProjectIndex` implemented per ADR-0016[cite: 2].
- `ProjectCatalog` consumes `ProjectIndex`; `ProjectCatalog.refresh()` removed; `ProjectCatalog(repository=...)` removed[cite: 2].
- Bootstrap ordering verified (`subscribe` → `repository.list_metadata()` → `replace_all`, same synchronous call stack)[cite: 2].
- The integration fixture `tests/integration/ui/test_main_window_import.py` migrated to the composition-root wiring, preserving the bootstrap order per ADR-0016 §4.2[cite: 2].
- `FilesystemProjectIndex` does not exist; SQLite implementation deferred to Phase 8[cite: 2].

### 2.6 2026-11-22 Sprint J closure

Sprint J (`Coordinated deletion`) is complete[cite: 2].

- 1701 passing tests, 0 failed, 0 errors, 2 skipped (+9 from Sprint I)[cite: 2].
- `ruff check`, `ruff format --check`, and `mypy src` clean (284 source files)[cite: 2].
- `git diff --stat src/` empty: **no production file changed**[cite: 2].
- The `ProjectManager.delete_project` coordination (repository delete → `ProjectDeleted` publish → synchronizer invalidation → catalog reflects on next query) was already correct; the sprint proved it with tests rather than changing production code[cite: 2].
- Physical delete invariant verified: only `project.json` is removed; sibling files (External Reference mode DICOM, `patient_record.json`, future Phase 4 assets) survive byte-identical[cite: 2].
- Delete-specific staleness paths verified per ADR-0016 §3.3/§3.4 (handler containment, rebuild-on-next-query, `ProjectIndexStaleError` on double failure)[cite: 2].
- Architecture gate added: `tests/architecture/test_no_legacy_project_delete_api.py` (4 tests)[cite: 2].
- UI affordance for delete deferred (see §7)[cite: 2].

### 2.7 2026-11-22 Sprint K closure

Sprint K (`Async loading`) is complete using K-minimal option (b): **flows async, projects synchronous**[cite: 2].

- 1713 passing tests, 0 failed, 0 errors, 2 skipped (+12 from Sprint J)[cite: 2].
- `ruff check .`, `ruff format --check .` (570 files), and `mypy src` (284 source files) clean[cite: 2].
- `HomePage.refresh()` is synchronous; `FlowCatalog.list_definitions()` runs off-thread via `_LoadFlowsTask` through `TaskManager`[cite: 2].
- `synchronizer.start()` remains synchronous in the composition root; ADR-0016 §4.1 was not reopened[cite: 2].

---

## 3. Current Focus — Phase 3

**Goal:** Complete the Project, Home Page, and Professional Module foundations before formally beginning Phase 4[cite: 2].

Phase 3 contains two coordinated workstreams[cite: 2]:

1. **Structural work:** Editor and Module package reorganization and dependency-boundary corrections[cite: 2]. **Completed on 2026-11-18.**[cite: 2]
2. **Functional work:** ProjectIndex, coordinated deletion, asynchronous loading, and Professional module integration[cite: 2]. **In progress (Sprints I, J, and K complete; Sprint L remaining).**[cite: 2]

The Editor Architecture Refactoring is a structural activity within Phase 3[cite: 2]. It is now closed[cite: 2].

### 3.1 Phase 3 work overview

| Work item | Type | Status | Dependencies |
|---|---|---|---|
| Editor Architecture Refactoring | Structural activity | ✅ Complete[cite: 2] | Phase 2 complete[cite: 2] |
| Sprint I — ProjectIndex | Functional sprint | ✅ Complete (2026-11-20)[cite: 2] | None within Phase 3[cite: 2] |
| Sprint J — Coordinated deletion | Functional sprint | ✅ Complete (2026-11-22)[cite: 2] | Sprint I ✅[cite: 2] |
| Sprint K — Async loading | Functional sprint | ✅ Complete (2026-11-22)[cite: 2] | Sprint J ✅[cite: 2] |
| Sprint L — Professional module | Functional sprint | 🚧 Pending[cite: 2] | Refactoring ✅, C ✅, E ✅, F ✅[cite: 2] |
| Test stub documentation | Cleanup follow-up | 🚧 Pending[cite: 2] | None[cite: 2] |

Sprints I–K are complete[cite: 2]. Sprint L is unblocked by the completed Editor Architecture Refactoring and its other prerequisites and is the remaining functional deliverable of Phase 3[cite: 2].

---

## 4. Structural Workstream — Editor Architecture Refactoring

**Status:** ✅ Complete (2026-11-18)[cite: 2]
**Technical authority:** `refactoring_plan.md` (now marked Completed)[cite: 2]
**Architectural record:** ADR-0015[cite: 2].

The refactoring is recorded in `refactoring_plan.md` §11 (Post-Refactoring Notes)[cite: 2]. The final validation confirms[cite: 2]:

- 1635 passing tests, 0 failed, 0 errors, 2 skipped[cite: 2].
- `ruff check`, `ruff format --check`, and `mypy src` clean[cite: 2].
- 85% overall test coverage[cite: 2].
- No obsolete imports of `cranioz.ui.editors.*` (except the approved composition root)[cite: 2].
- No obsolete imports of `cranioz.modules.base`[cite: 2].
- `_KNOWN_DEBT_FILES` and `_DEBT_MAX_LITERALS` consistent with the post-migration file set[cite: 2].

### 4.1 Scope (closed)

The refactoring covered[cite: 2]:

- `modules/` reorganization into `modules/core/` and `modules/builtin/`[cite: 2].
- Migration of `ui/editors/` to the top-level `cranioz/editors/` package[cite: 2].
- Separation of Editor and View contracts[cite: 2].
- Separation of reusable Views and View overlays from concrete Editors[cite: 2].
- Workspace and Editor dependency-boundary corrections[cite: 2].
- Test fixture migration[cite: 2].
- Removal of obsolete production components[cite: 2].
- Consolidation of duplicate `PlaceholderEditor` implementations[cite: 2].
- Relevant application package naming cleanup (Step 6.2 complete; Step 6.1 deferred)[cite: 2].
- Architecture tests, ADRs, and documentation updates[cite: 2].

The following were explicitly outside the refactoring and remain out of scope[cite: 2]:

- Professional module implementation (Sprint L)[cite: 2].
- ProjectIndex (Sprint I). Now implemented per ADR-0016[cite: 2].
- Coordinated deletion (Sprint J). Now implemented[cite: 2].
- Async Home Page loading (Sprint K). Now implemented[cite: 2].
- New clinical workflows and Phase 4 visualization features[cite: 2].
- General migration of ThemeService, IconProvider, Toolbar, ToolRegistry, and ToolContext out of `ui/`[cite: 2].

### 4.2 Resolved open decisions

| Decision | Resolution |
|---|---|
| `editor_manifest.py` empty | Removed. If a contract is needed for Sprint L, it will be introduced with a real implementation[cite: 2]. |
| `editor_catalog.py` empty | Removed. Same rationale[cite: 2]. |
| `Workspace.find_viewport_3d()` | Kept as a documented exception to §4.1 rule 8. Regression test tracked as follow-up[cite: 2]. |
| `MeshDebugEditor` | Kept and migrated to `editors/builtin/mesh_debug/editor.py`[cite: 2]. |
| Duplicate `PlaceholderEditor` | Consolidated into the canonical implementation. `_KNOWN_DEBT_FILES` reduced from 8 to 5 files[cite: 2]. |

### 4.3 Deferred to a future PR

- `application/event_bus.py` → `application/events/bus.py` (Step 6.1 of `refactoring_plan.md`). Deferred per §5.10 of that document[cite: 2].
- `editors/view_overlays/` (Step 4.4 of `refactoring_plan.md`). Skipped because the current `ui/editors/overlays/gizmos/` and `ui/editors/overlays/rulers/` directories contain only empty `__init__.py` files[cite: 2].

---

## 5. Functional Workstream — Phase 3 Sprints

The functional workstream is independent of the structural refactoring except where explicit dependencies exist[cite: 2].

### 5.1 Sprint I — ProjectIndex

**Status:** ✅ Complete (2026-11-20)[cite: 2]
**Dependency:** None within Phase 3[cite: 2].
**Architectural authority:** ADR-0016 (`docs/adr/ADR-0016_Project_Catalog_Synchronization.md`)[cite: 2].

Deliverables[cite: 2]:

- ✅ `ProjectIndex` Protocol in `application/project/index.py`[cite: 2]:
  - `add`, `remove`, `lookup`, `list_summaries`, `list_ids`, `count`, `contains`, `replace_all`[cite: 2].
  - `ProjectIndexStaleError` raised by the synchronized decorator when a rebuild after detected staleness fails[cite: 2].
  - The Protocol is a pure read model; it knows nothing about the repository, the event bus, or the filesystem[cite: 2].
- ✅ `InMemoryProjectIndex` in `application/project/in_memory_index.py` — the reference implementation[cite: 2].
- ✅ `ProjectIndexSynchronizer` and `SynchronizedProjectIndex` in `application/project/index_synchronizer.py`[cite: 2]:
  - `start()` subscribes to `ProjectCreated`, `ProjectUpdated`, `ProjectDeleted`, then bootstraps via `repository.list_metadata()` and `index.replace_all(...)`, on the same synchronous call stack[cite: 2].
  - Handlers update the index synchronously; they never propagate exceptions to the `EventBus`. On failure they log with `project_id` and operation name only (no PHI) and mark `_possibly_stale = True`[cite: 2].
  - `rebuild()` re-populates the index from the repository[cite: 2].
  - `ensure_fresh()` is called by `SynchronizedProjectIndex` before every read; it is a no-op when not stale, rebuilds when stale, and propagates `ProjectIndexStaleError` if the rebuild fails[cite: 2].
- ✅ `ProjectCatalog` refactored to consume a `ProjectIndex`[cite: 2]:
  - `ProjectCatalog.refresh()` is removed; freshness is automatic via `SynchronizedProjectIndex`[cite: 2].
  - The catalog does not know about the synchronizer or the repository[cite: 2].
- ✅ Bootstrap ordering guarantee per ADR-0016 §4. The ordering guarantee holds only while the bootstrap is synchronous; ADR-0016 §4.1 was not reopened in Sprint K[cite: 2].
- **Not** part of Sprint I: `FilesystemProjectIndex` does not exist as a class name. A persisted or SQLite-backed index remains deferred to Phase 8 (see §7)[cite: 2].

Contract tests (per ADR-0016 §8)[cite: 2]:

- ✅ `test_project_index_contract.py` — `InMemoryProjectIndex` behavior; parametrizable for future `SqliteProjectIndex`[cite: 2].
- ✅ `test_project_index_synchronizer.py` — bootstrap, event handlers, error containment, `rebuild`, `ensure_fresh`[cite: 2].
- ✅ `test_project_index_sync_bootstrap.py` — bootstrap window; verifies consistency under a synchronous `EventBus`[cite: 2].
- ✅ `test_project_catalog_uses_index.py` — the catalog reads via `ProjectIndex`; `repository.list_metadata` is not called during queries (mock fails if invoked)[cite: 2].
- ✅ `test_project_catalog_sync.py` — end-to-end integration with `ProjectManager`[cite: 2].
- ✅ `test_project_index_stale_propagation.py` — `ProjectIndexStaleError` propagation and `MainWindow` handling[cite: 2].

Benchmark (documented in ADR-0016 implementation notes, not run in CI): 100/300/1000 projects in `tmp_path`, comparing `search_projects()` latency and `repository.list_metadata` call count between baseline (direct repository) and new (indexed)[cite: 2].

The SQLite implementation remains deferred to Phase 8[cite: 2].

**Closure note (2026-11-20):** 1692 passing tests, 0 failed, 0 errors, 2 skipped[cite: 2]. Integration fixture `tests/integration/ui/test_main_window_import.py` migrated to the composition-root wiring (`repository → synchronizer → index → catalog`), preserving the bootstrap order required by ADR-0016 §4[cite: 2]. No production code changed during that migration; the drift was confined to the test fixture[cite: 2].

### 5.2 Sprint J — Coordinated deletion

**Status:** ✅ Complete (2026-11-22)[cite: 2]
**Dependency:** Sprint I ✅[cite: 2].

Deliverables[cite: 2]:

- ✅ `ProjectManager.delete_project` coordinates `ProjectCatalog` → `ProjectIndex` → `FilesystemProjectRepository` via the `ProjectDeleted` event (ADR-0016 §2.2)[cite: 2]. The `ProjectManager` does **not** call `ProjectCatalog` or `ProjectIndex` directly; the coordination is the event-driven path[cite: 2].
- ✅ Rollback semantics: a repository failure raises before `ProjectDeleted` is published; a handler failure is contained by the synchronizer (ADR-0016 §3.4) and marks the index stale; the next query rebuilds from the authoritative repository (ADR-0016 §3.3)[cite: 2]. No event compensation, no manual index re-add[cite: 2].
- ✅ External source data in External Reference mode is never removed by project deletion[cite: 2]. The `FilesystemProjectRepository` owns exactly one file (`project.json`); sibling files belong to other persistence layers and survive deletion byte-identical[cite: 2].
- ✅ Contract and failure-path tests[cite: 2].

Sprint J preserves the single-lifecycle-writer invariant (`project.md` §25)[cite: 2]. Deletion reflects into the catalog through the `ProjectDeleted` event; the `ProjectManager` does not call the catalog directly[cite: 2].

**Deliverables in `tests/` (zero production change):**

- **J.1 — Physical delete invariant** (`tests/integration/application/project/test_project_delete_invariant.py`, new, 2 tests)[cite: 2]:
  - `test_delete_project_removes_only_project_json`: after `ProjectManager.delete_project`, `project.json` is gone and every sibling file (`patient_record.json`, `scene.json`, `imaging/ct/slice.dcm`, `models/maxilla.stl`) survives byte-identical[cite: 2].
  - `test_delete_project_leaves_parent_project_directory`: the project directory itself survives; only the discoverable marker (`project.json`) is removed[cite: 2].
  - This is the executable form of the plan's Sprint J requirement: "External source data (External Reference mode) is never removed by project deletion."[cite: 2]
  - Not covered by `test_project_repository_contract.py`: the Protocol contract does not specify filesystem behavior[cite: 2]. The invariant is a `FilesystemProjectRepository` property[cite: 2].

- **J.2 — Delete-specific staleness paths** (`tests/integration/application/project/test_project_index_stale_propagation.py`, extended from 2 → 5 tests)[cite: 2]:
  - `test_delete_project_handler_failure_does_not_propagate_to_manager`: ADR-0016 §3.4 — a failing `_on_deleted` handler is contained; `delete_project` returns normally[cite: 2].
  - `test_delete_project_handler_failure_rebuilds_on_next_query`: ADR-0016 §3.3 — after a contained handler failure, the next catalog query rebuilds from the repository and reflects the deletion[cite: 2].
  - `test_delete_project_rebuild_failure_after_handler_failure_raises_stale`: ADR-0016 §3.3 — when both handler and rebuild fail, the query raises `ProjectIndexStaleError` instead of silently returning the pre-delete state[cite: 2].

- **J.4 — Architecture gate** (`tests/architecture/test_no_legacy_project_delete_api.py`, new, 4 tests)[cite: 2]:
  - `test_no_call_site_constructs_project_catalog_with_repository`: ADR-0016 removed `ProjectCatalog(repository=...)`[cite: 2].
  - `test_no_call_site_calls_project_catalog_refresh`: ADR-0016 removed `ProjectCatalog.refresh()`[cite: 2].
  - `test_only_filesystem_repository_references_project_json`: no module outside `FilesystemProjectRepository`, `ProjectPathResolver`, `ProjectSerialization` may **access** (AST-detected, not merely mention) `project.json`[cite: 2].
  - `test_only_project_manager_calls_repository_delete`: `ProjectManager` is the single lifecycle writer (project.md §25)[cite: 2].

**Closure note (2026-11-22):**

Final validation: **1701 passed, 0 failed, 0 errors, 2 skipped; `tests/architecture/` 85 passed[cite: 2].** The 2 skips are pre-existing (View-level and Editor-level Toolbars temporarily disabled, Block 5.5)[cite: 2]. The 9 warnings are pre-existing (`GetData()` deprecated in VTK ≥ 9.6, exercised by `stl.py:143`)[cite: 2]. No production file changed: `git diff --stat src/` is empty[cite: 2].

Lint/type gate: `ruff check .` → `All checks passed!`; `ruff format --check .` → `566 files already formatted`; `mypy src` → `Success: no issues found in 284 source files`[cite: 2]. `mypy` emits one pre-existing note about unused `ignore_missing_imports` entries in `pyproject.toml` (see §7)[cite: 2].

**Scope correction recorded during Sprint J:** the UI affordance for delete (button/menu/confirmation dialog) is **deferred**[cite: 2]. The plan's §8.6 ("The feature is usable through its intended UI workflow") is satisfied at the **API level** — `ProjectManager.delete_project` is reachable and its effects propagate through the catalog without an explicit refresh — but **not at the UI level**, because no delete affordance exists today (see `home_page.md` and `project.md` §7: "For example, if a future UI provides a 'Delete Project' action…")[cite: 2]. Adding the UI requires UX decisions (placement in `ProjectTable`, i18n keys in `en/` and `pt-BR/`, confirmation dialog, disabled state for the open project) that are out of scope for a "coordinated deletion" sprint[cite: 2].

**Debt tracked (not fixed in Sprint J):**

- **UI affordance for Delete Project[cite: 2].** Adding the button/menu + confirmation dialog + i18n keys is a separate sprint[cite: 2]. The API-level behavior is verified; the UI-level criterion (§8.6) will be met when the affordance is added[cite: 2].
- **`patient_record.json` is not deleted when a project is deleted[cite: 2].** Deliberate Phase 4 boundary: the `FilesystemProjectRepository` owns only `project.json`; `patient_record.json` belongs to the Patient persistence layer[cite: 2]. `test_delete_project_removes_only_project_json` is the forcing function: when Phase 4 introduces per-project assets, that test must be revisited and a decision recorded (Phase 4, §4.3.5 storage/export)[cite: 2].
- **`ProjectIndexSynchronizer` remains synchronous, single-threaded[cite: 2].** `delete_project` remains synchronous[cite: 2]. The `repository.delete → publish(ProjectDeleted)` pair remains synchronous and was not parallelized in Sprint K[cite: 2].
- **`pyproject.toml` mypy note[cite: 2].** `mypy` reports unused `ignore_missing_imports` entries for `cupy.*`, `cv2.*`, `numba.*`, `reportlab.*`, `scipy.*`[cite: 2]. They will become active in Phase 4 (ITK/CGAL/OCCT) or Phase 6 (segmentation with scipy/numba)[cite: 2]. No action until then[cite: 2].

**Test count delta:** +9 (1692 → 1701)[cite: 2]. Sprint I's test baseline is preserved[cite: 2].

### 5.3 Sprint K — Async loading

**Status:** ✅ Complete (2026-11-22)[cite: 2]
**Dependencies:** Sprint J ✅[cite: 2].

**Scope decision (recorded at closure):** K-minimal option (b) —
**flows async, projects synchronous**[cite: 2]. Rationale[cite: 2]:

- The `ProjectCatalog` reads from an in-memory `SynchronizedProjectIndex`
  (ADR-0016), so project listing performs no I/O on the GUI thread[cite: 2]. A
  Task for projects would be decorative[cite: 2].
- The only blocking I/O on the boot path is
  `FlowCatalog.list_definitions()` (filesystem read of
  `<flows_root>/*/flow.json`), invoked from
  `MainWindow._populate_flow_list()` in `MainWindow.__init__`[cite: 2]. This is
  exactly the "File I/O larger than a few milliseconds" case in
  ADR-0011 §2.1, and it is moved to a `_LoadFlowsTask` dispatched
  through the `TaskManager`[cite: 2].
- `synchronizer.start()` remains synchronous in the composition root
  (`__main__::_build_project_subsystem`)[cite: 2]. ADR-0016 §4.1 is **not**
  reopened[cite: 2]. The K.6 criterion is satisfied by construction[cite: 2].

Deliverables[cite: 2]:

- ✅ `HomePage.refresh()` is synchronous (calls `ProjectTable.refresh()`)[cite: 2].
  The decorative `_LoadProjectsTask` and the `loading_*` signals for
  projects were removed[cite: 2]. The `HomePage` no longer receives a
  `task_manager`[cite: 2].
- ✅ `HomePage` exposes `flows_loading_started` / `flows_loading_finished` /
  `flows_loading_failed` for the `MainWindow` to drive UI state if it
  chooses[cite: 2]. Today the `FlowList` keeps its "No flows available"
  placeholder during the load (silent loading)[cite: 2].
- ✅ `MainWindow._dispatch_flow_loading()` dispatches a `_LoadFlowsTask`
  through the injected `TaskManager`[cite: 2]. It falls back to a synchronous
  load when no `TaskManager` is injected (tests)[cite: 2].
- ✅ `_LoadFlowsTask` calls `progress(0.0)` / `progress(1.0)` and
  `cancel_token.raise_if_cancelled()` at both boundaries, per
  ADR-0011 §5[cite: 2].
- ✅ `MainWindow.__init__` performs no blocking I/O on the flow path[cite: 2].
- ✅ Rollback on Workspace creation failure (K.4) already present in
  `_on_project_open_requested`; covered by a new integration test[cite: 2].
- ✅ Bootstrap-ordering guarantee (K.6) covered by a new integration
  test that mirrors `__main__::_build_project_subsystem`[cite: 2].

**Explicitly out of Sprint K scope (unchanged):**

- Monitor de Logs subsystem (dedicated sprint, after K)[cite: 2].
- Separation Console / History / Monitor de Logs (project invariant)[cite: 2].

**Explicitly not re-opened:**

- ADR-0016 §4.1 — the bootstrap remains synchronous[cite: 2].

### 5.4 Sprint L — Professional module

**Status:** 🚧 Pending (unblocked by the completed refactoring and by Sprints C, E, F)[cite: 2]
**Dependencies:** Editor Architecture Refactoring ✅, Sprint C ✅, Sprint E ✅, Sprint F ✅[cite: 2].

Deliverables[cite: 2]:

- `ProfessionalEditor` registered in `EditorRegistry`[cite: 2].
- `ModuleUISpec` for the Professional module[cite: 2].
- Settings integration through `professional.*` keys[cite: 2].
- Integration and contract tests[cite: 2].

Sprint L must use the final Editor package architecture (`cranioz/editors/builtin/`)[cite: 2]. The legacy `ui/editors/` organization no longer exists[cite: 2].

Sprint L is independent of Sprints J–K functionally and may proceed in parallel[cite: 2]. Its integration tests may benefit from the ProjectIndex contract delivered by Sprint I[cite: 2].

### 5.5 Test stub documentation

**Status:** 🚧 Pending[cite: 2].

The following files reserve contracts for missing granular unit tests[cite: 2]:

- `tests/infrastructure/i18n/` — four stubs[cite: 2].
- `tests/infrastructure/scene/test_scene_query_adapter.py`[cite: 2].

Required actions[cite: 2]:

- Add a `README.md` to `tests/infrastructure/i18n/`[cite: 2].
- Add a `README.md` to `tests/infrastructure/scene/`[cite: 2].
- Add explicit TODO markers to relevant stubs[cite: 2].

Do not interpret these empty files as completed unit-test coverage[cite: 2].

---

## 6. Execution Strategy and Parallelism

The structural refactoring is complete[cite: 2]. Sprints I, J, and K are complete[cite: 2]. The remaining functional deliverable in Phase 3 is Sprint L[cite: 2].

### 6.1 Dependency overview

| Work item | Can start independently? | Required dependency |
|---|---|---|
| Sprint I | ✅ Complete (2026-11-20)[cite: 2] | —[cite: 2] |
| Sprint J | ✅ Complete (2026-11-22)[cite: 2] | Sprint I ✅[cite: 2] |
| Sprint K | ✅ Complete (2026-11-22)[cite: 2] | Sprint J ✅[cite: 2] |
| Sprint L | Yes (structurally)[cite: 2] | Refactoring ✅, C ✅, E ✅, F ✅[cite: 2] |
| Monitor de Logs (dedicated sprint) | Yes (documentation)[cite: 2] | `monitor_logs.md` (specification)[cite: 2] |
| Monitor de Logs (implementation) | No[cite: 2] | Sprint K ✅ (to inform tab mapping)[cite: 2] |

### 6.2 Recommended execution sequence

**Current cycle:**

1. Sprints I, J, and K are complete (ADR-0016 §4.1 was not reopened; bootstrap remains synchronous)[cite: 2].
2. Execute and close **Sprint L** (`ProfessionalEditor` in `EditorRegistry`, `ModuleUISpec`, `professional.*` settings keys, and contract/integration tests)[cite: 2].
3. Complete the test stub documentation follow-up (§5.5) if desired before closing Phase 3[cite: 2].
4. Mark Phase 3 `✅ Implemented` in `implementation_plan.md` once Sprint L is closed[cite: 2].

**Deferred (not part of the current cycle, not part of Phase 3):**

- **Monitor de Logs — dedicated sprint (unscheduled).** Implements `monitor_logs.md`: `QtLogHandler`, `LogsDialog`, the 📋 button wiring on the HomePage top bar, and the `Workspace._apply_default_splitter_sizes` snapshot contract for the `Areas` tab[cite: 2]. It is deliberately sequenced **after** Sprint K, so that the logging emitted by the async-loading work informs the tab mapping and the format[cite: 2]. It does not block Sprint L[cite: 2]. It is not required to close Phase 3[cite: 2].

The sequence may be adjusted when necessary, but the declared dependencies must be preserved[cite: 2].

---

## 7. Known Issues and Deferred Items

| Item | Status | Reference |
|---|---|---|
| DICOM visualization bug (voxel ordering) | Resolved 2026-11-06[cite: 2] | `implementation_plan.md`[cite: 2] |
| ADR-0003 legacy | Superseded by ADR-0014[cite: 2] | `docs/adr/`[cite: 2] |
| `steps_panel` overlay | Removed; replaced by `WorkflowBreadcrumb` in Phase 5[cite: 2] | `implementation_plan.md`[cite: 2] |
| `correlation_id` propagation in Workspace | Outstanding[cite: 2] | `implementation_plan.md`[cite: 2] |
| `event_subscription` propagation test | Dedicated test pending[cite: 2] | `tests/integration/ui/workspace/`[cite: 2] |
| Hardcoded appearance literals | Tracked in `_KNOWN_DEBT_FILES` (now 5 files)[cite: 2] | `tests/architecture/`[cite: 2] |
| `EditorStackSwitcher` inline QSS | 7 literals; not resolved by refactoring[cite: 2] | `_KNOWN_DEBT_FILES`[cite: 2] |
| `Editor.icon_name` missing from ABC | Outstanding; not a refactoring blocker[cite: 2] | Architectural debt[cite: 2] |
| `Workspace.find_viewport_3d()` regression test | Tracked as follow-up (Step 1 decision #9)[cite: 2] | ADR-0015[cite: 2] |
| `stl.py` migration from `GetData()` | Deferred to Phase 4.5 / VTK 10 compatibility work[cite: 2] | `stl.py`[cite: 2] |
| `pyproject.toml` unused `ignore_missing_imports` entries | Cleanup task; no functional impact[cite: 2] | `pyproject.toml`[cite: 2] |
| Implicit handler resolution in `InMemoryModuleLoader` | Not included in refactoring[cite: 2] | `architectural_consolidation_plan.md` §4.4[cite: 2] |
| `application/event_bus.py` → `application/events/bus.py` | Deferred to a separate PR[cite: 2] | `refactoring_plan.md` §5.10[cite: 2] |
| SQLite `ProjectIndex` backend | Deferred to Phase 8[cite: 2] | `implementation_plan.md`, ADR-0016 §2.1[cite: 2] |
| Persisted filesystem index (`index.json`) | Deferred to Phase 8; rejected for Sprint I per ADR-0016 §5[cite: 2] | ADR-0016 §5[cite: 2] |
| External mutation detection / background disk reconciliation | Deferred to Phase 8[cite: 2] | ADR-0016 §3.2, `implementation_plan.md`[cite: 2] |
| Recent Projects | Deferred to Phase 8[cite: 2] | `implementation_plan.md`[cite: 2] |
| **UI affordance for Delete Project** | **Deferred from Sprint J (2026-11-22)**[cite: 2] | **`next_steps.md` §5.2 "Debt tracked"**[cite: 2] |
| **`patient_record.json` deletion on project delete** | **Deferred to Phase 4 §4.3.5 (storage/export)**[cite: 2] | **`next_steps.md` §5.2 "Debt tracked"**[cite: 2] |
| **`ProjectIndexSynchronizer` sync-only (no parallel delete)** | **Constraint preserved in Sprint K**[cite: 2] | **`next_steps.md` §5.3 "Constraints inherited from Sprint J"**[cite: 2] |
| **Monitor de Logs — `LogsDialog` + `QtLogHandler` + 📋 wiring + `Areas` snapshot contract** | **Planned. Not implemented. Dedicated sprint, sequenced after Sprint K. Not part of Phase 3's closure criteria.**[cite: 2] | **`monitor_logs.md` (technical authority); `home_page.md` §25 (`logs_requested` reserved) and §26 (pointer); `workspace.md` §5.5 (pointer)**[cite: 2] |
| **Separation Console / History / Monitor de Logs** | **Project invariant, recorded 2026-11-22. The `ConsoleEditor` must not be fed by `logging`; it must be fed by an application-level notification service (to be defined).**[cite: 2] | **`monitor_logs.md` §2**[cite: 2] |

The project must not silently absorb unrelated items from this list into future sprints[cite: 2].

---

## 8. Validation Requirements

Every functional sprint must leave the project in a valid, testable state[cite: 2].

### 8.1 Required commands

```powershell
.venv\Scripts\python.exe -m pytest
.venv\Scripts\python.exe -m ruff check .
.venv\Scripts\python.exe -m ruff format --check .
.venv\Scripts\python.exe -m mypy src