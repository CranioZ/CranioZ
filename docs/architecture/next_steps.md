# Next Steps

**Document type:** Action plan and development handoff  
**Status:** Active  
**Scope:** Current development priorities and execution sequence for Phases 2–3  
**Last updated:** 2026-11-16

---

## 1. Context

CranioZ has completed Phases 0, 1, and 2. Phase 3 — Project, Home Page & Professional Module — is currently in progress.

Phase 4 — Scene & Visualization — remains planned and must not formally begin until Phases 2 and 3 are closed.

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

- **1,633 passing tests**
- **0 failed**
- **0 errors**
- **2 skipped**
- `ruff check .` clean
- `ruff format --check .` clean
- `mypy src` clean

This is the baseline recorded on 2026-11-16 in `refactoring_plan.md`. It must be revalidated after subsequent changes.

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

The DICOM import and visualization pipeline has foundational implementations and integration work documented in `implementation_plan.md`.

---

## 2. Completed Work

### 2.1 Phases and Sprints

| Item | Status | Notes |
|---|---|---|
| Phase 0 — Foundation & Boot | Complete | Startup performance improvements remain tracked separately |
| Phase 1 — Contracts, Core Domain & i18n | Complete | Includes Sprints B and C |
| Phase 2 — Workspace Engine & Icons | Complete | Closed after Sprint H |
| Sprint E — ThemeService and ThemeCompiler | Complete | 47 canonical design tokens |
| Sprint F — IconProvider and UnicodeIconProvider | Complete | 70 registered icons |
| Sprint M — Frameless Window and Native Chrome | Complete | Drag, resize, maximize, minimize, and close |
| Blocks 1–6 | Complete | Toolbar, active View, TomographyEditor integration, and visual validation |
| Blocks 5.5–5.6.1 | Complete | Area sizing and window controls |
| Sprint G — AreaLayoutRenderer | Complete | SINGLE, SPLIT, and STACK extension point |
| Sprint H — EditorStack | Complete | LEAF, SPLIT, and STACK composition |

### 2.2 Important architectural decisions

- **ADR-0013:** Editor Layout Tree, View Layout Tree, and Toolbar Placement.
- **ADR-0014:** Qt Widgets + modular QSS + Python Design Tokens.
- `EditorStack` uses `QStackedWidget` and `EditorStackSwitcher`, not `QTabWidget`.
- Workspace composition remains responsible for Areas and Editor placement.
- `AreaLayoutRenderer` handles intra-Area composition.
- Editor identity is independent of Workspace position.
- Modules remain declarative and must not instantiate concrete Editors.

### 2.3 2026-11-13 cleanup

The cleanup removed dead code, duplicated components, obsolete debug scripts, and migrated `QImage.mirrored` to `QImage.flipped`.

The minimum PySide6 version was raised to `>=6.9`.

---

## 3. Current Focus — Phase 3

**Goal:** Complete the Project, Home Page, and Professional Module foundations before formally beginning Phase 4.

Phase 3 contains two coordinated workstreams:

1. **Structural work:** Editor and Module package reorganization and dependency-boundary corrections.
2. **Functional work:** ProjectIndex, coordinated deletion, asynchronous loading, and Professional module integration.

The Editor Architecture Refactoring is a structural activity within Phase 3. It is not a new phase or a replacement for the functional sprints.

### 3.1 Phase 3 work overview

| Work item | Type | Status | Dependencies |
|---|---|---|---|
| Editor Architecture Refactoring | Structural activity | Planned | Phase 2 complete |
| Sprint I — ProjectIndex | Functional sprint | Pending | None within Phase 3 |
| Sprint J — Coordinated deletion | Functional sprint | Pending | Sprint I |
| Sprint K — Async loading | Functional sprint | Pending | Sprints I and J |
| Sprint L — Professional module | Functional sprint | Pending | Refactoring, C, E, F |
| Test stub documentation | Cleanup follow-up | Pending | None |

Sprints I–K may progress independently of the structural refactoring, respecting their own dependencies.

Sprint L must wait for the Editor Architecture Refactoring and its other prerequisites.

---

## 4. Structural Workstream — Editor Architecture Refactoring

**Status:** Planned  
**Technical authority:** `refactoring_plan.md`  
**Classification:** Reorganization, according to `architectural_consolidation_plan.md` §2.1.

The refactoring is executed now because the current package organization would introduce Workspace–Editor coupling if `ProfessionalEditor` were implemented before the reorganization.

The objective is to prevent an imminent architectural correction, not to reorganize packages solely for stylistic preference.

### 4.1 Scope

The refactoring covers:

- `modules/` reorganization into `modules/core/` and `modules/builtin/`.
- Migration of `ui/editors/` to the top-level `cranioz/editors/` package.
- Separation of Editor and View contracts.
- Separation of reusable Views and View overlays from concrete Editors.
- Workspace and Editor dependency-boundary corrections.
- Test fixture migration.
- Removal of obsolete production components.
- Consolidation of duplicate `PlaceholderEditor` implementations.
- Relevant application package naming cleanup, subject to inspection.
- Architecture tests, ADRs, and documentation updates.

The following remain outside the refactoring:

- Professional module implementation (Sprint L).
- ProjectIndex (Sprint I).
- Coordinated deletion (Sprint J).
- Async Home Page loading (Sprint K).
- New clinical workflows and Phase 4 visualization features.
- General migration of ThemeService, IconProvider, Toolbar, ToolRegistry, and ToolContext out of `ui/`.
- Unrelated architectural debt already tracked elsewhere.

### 4.2 Confirmed architectural findings

The 2026-11-16 inspection established the following:

- The registry, layout specifications, Workspace, and Workspace specifications already use functional Editor IDs.
- No positional Editor IDs exist.
- `layout_io.py` is empty; no serialized layout exists.
- No Editor identifier migration is required.
- `ViewLayoutRenderer` has a real dependency on the Editor contract for `ACTIVE_ONLY` behavior and activation event filtering.
- `Editor` imports `ToolContext` from `ui.tools`.
- `EditorContext` uses IconProvider, ThemeService, ToolRegistry, and TranslationService.
- MPRView does not import `ui.theme`.
- `EditorStackOrientation` is defined in `ui/workspace/areas/editor_layout_spec.py` and remains there.
- `workspace_spec.py::_PlaceholderEditor` duplicates `PlaceholderEditor` byte-for-byte.
- `ui/main_window.py` imports `MeshDebugEditor` at module level for the `CRANIOZ_DEBUG_MESH=1` path.
- `ui/main_window.py` and `cranioz/__main__.py` register `TomographyEditor` through the composition root.
- `DummyEditor` and `DebugEditor` are currently located in `ui/editors/builtin/test_editor.py`.

These findings should be treated as the current inspection baseline. Recheck them if the relevant code changes before migration.

### 4.3 Immediate execution sequence

The structural workstream follows the sequence defined in `refactoring_plan.md`.

| Step | Activity | Status |
|---|---|---|
| 0 | Pre-refactoring cleanup: remove debug `print()` statements | Pending |
| 1 | Pre-refactoring inspection and open decisions | Partially inspected; decisions pending |
| 2 | Establish architecture tests | Pending |
| 3 | Module system reorganization | Pending |
| 4 | Editor package reorganization | Pending |
| 5 | Remove obsolete components and migrate test-only code | Pending |
| 6 | Application package naming cleanup | Pending; preferably separate PR |
| 7 | ADR and architecture documentation | Pending |
| 8 | Final validation | Pending |

### 4.4 Immediate structural actions

**First: Step 0 — Pre-refactoring cleanup**

- Remove debug `print()` statements from `LayoutBuilder` and `AreaLayoutRenderer`.
- Replace them with `_logger.debug(...)` only where the information remains useful.
- Commit this cleanup separately from structural migration.

**Second: complete Step 1 — Resolve open decisions**

The following decisions must be resolved before their corresponding migrations:

| Decision | Required action |
|---|---|
| `editor_manifest.py` is empty | Decide whether to implement, defer to Sprint L, or remove |
| `editor_catalog.py` is empty | Decide whether to implement, defer, or remove |
| `Workspace.find_viewport_3d()` | Replace with a contract query or document as an approved exception; add regression coverage |
| `MeshDebugEditor` | Keep and migrate to `editors/builtin/mesh_debug/`, or remove the debug feature in a separate commit |

Other findings are already resolved:

- `ViewLayoutRenderer → Editor`: accepted dependency.
- `editors.core.* → infrastructure`: accepted where justified by actual contracts.
- ThemeService is permitted; ThemeCompiler is prohibited in `editors.*`.
- PySide6 is an explicitly approved dependency for relevant Editor and View packages.
- Moving `ui/theme/` out of `ui/` is out of scope.
- `MPRView → ui/theme`: no dependency exists.
- `EditorStackOrientation` remains in Workspace.
- The composition root may import concrete Editors.
- `PlaceholderEditor` implementations should be consolidated.
- `DummyEditor` and `DebugEditor` must move to test fixtures.
- The `EditorLayoutSpec` compatibility shim imports in tests should be updated to the canonical implementation.

Do not begin structural migration while these unresolved decisions affect the target package structure or dependency rules.

### 4.5 Architecture tests

After Step 1, establish executable architecture rules before moving packages.

The tests must enforce:

- Domain isolation.
- Application dependency boundaries.
- Module isolation from concrete Editors and Workspace components.
- Editor core isolation from concrete Editors and Modules.
- View and View Overlay independence.
- Workspace dependence on Editor contracts rather than concrete Editor implementations.
- Prohibition of `ui.theme.compiler` imports in `editors.core.*`.
- Approved presentation dependencies.
- Composition-root exceptions for `cranioz.__main__` and `ui.main_window`.
- Removal of obsolete import paths after migration.

Prefer explicit pytest architecture tests with AST inspection if they provide the required precision.

### 4.6 Migration sequence

The migration must preserve the logical order in `refactoring_plan.md`:

1. Reorganize Module contracts and built-in Modules.
2. Move Editor contracts to `editors/core/editor/`.
3. Move View contracts and View layout components to `editors/core/view/`.
4. Move reusable Views to `editors/views/`.
5. Move reusable View overlays to `editors/view_overlays/`.
6. Move concrete Editors to `editors/builtin/`.
7. Preserve Workspace composition in `ui/workspace/`.
8. Move test-only Editors and Modules into test fixtures.
9. Remove obsolete production components.
10. Consolidate the duplicate PlaceholderEditor.
11. Update `_KNOWN_DEBT_FILES` and `_DEBT_MAX_LITERALS`.
12. Update ADRs and architecture documentation.
13. Run complete validation.

Use `git mv` whenever possible. Each logical migration must be committed independently and leave the project in a valid state.

### 4.7 Workspace components that must remain in `ui/workspace/`

The refactoring must not move:

- Area.
- AreaWidget.
- AreaLayoutRenderer.
- AreaLayoutSpec.
- EditorLayoutSpec.
- EditorStack.
- EditorStackSwitcher.
- EditorStackOrientation.
- LayoutBuilder.
- Workspace layout specifications.
- Workspace-level overlays.
- `workspace_spec.py`.
- `specs/editor_layout_spec.py` compatibility shim.

The `EditorStack` implementation delivered in Sprint H remains a Workspace composition component.

---

## 5. Functional Workstream — Phase 3 Sprints

The functional workstream is independent of the structural refactoring except where explicit dependencies exist.

### 5.1 Sprint I — ProjectIndex

**Status:** Pending  
**Dependency:** None within Phase 3.

Deliverables:

- `ProjectIndex` interface:
  - `add`
  - `remove`
  - `lookup`
  - `list`
- `InMemoryProjectIndex`.
- `FilesystemProjectIndex`.
- `ProjectCatalog` consumes `ProjectIndex` instead of scanning the filesystem directly.
- Contract tests for add/remove/lookup/list, concurrent access, and cache invalidation.

The SQLite implementation remains deferred to Phase 8.

Sprint I can progress while the Editor Architecture Refactoring is underway.

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

### 5.3 Sprint K — Async loading

**Status:** Pending  
**Dependencies:** Sprints I and J.

Deliverables:

- `HomePage` loads projects and flows through `TaskManager`.
- No blocking I/O in `MainWindow.__init__`.
- `HomePage.refresh()` does not block the GUI thread.
- Rollback if Workspace creation fails after project opening.
- Regression tests for loading, cancellation, failure, and recovery.

### 5.4 Sprint L — Professional module

**Status:** Pending  
**Dependencies:** Editor Architecture Refactoring, Sprint C, Sprint E, and Sprint F.

Deliverables:

- `ProfessionalEditor` registered in `EditorRegistry`.
- `ModuleUISpec` for the Professional module.
- Settings integration through `professional.*` keys.
- Integration and contract tests.

Sprint L must use the final Editor package architecture. Do not introduce temporary dependencies on the legacy `ui/editors/` organization.

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

The structural refactoring and functional sprints are coordinated but independent workstreams.

### 6.1 Dependency overview

| Work item | Can start independently? | Required dependency |
|---|---|---|
| Refactoring Steps 0–2 | Yes | Phase 2 complete |
| Sprint I | Yes | None within Phase 3 |
| Refactoring Steps 3–8 | After structural prerequisites | Previous refactoring steps |
| Sprint J | No | Sprint I |
| Sprint K | No | Sprints I and J |
| Sprint L | No | Refactoring, C, E, F |

### 6.2 Recommended execution sequence

**Immediate cycle:**

1. Execute Refactoring Step 0 and commit the cleanup separately.
2. Complete the remaining Step 1 inspection and resolve the four open decisions.
3. Establish architecture tests in Step 2.
4. Start Sprint I independently, without waiting for the entire refactoring.
5. Proceed with the Module and Editor migrations.
6. Start Sprint J after Sprint I is complete.
7. Start Sprint K after Sprints I and J are complete.
8. Complete the structural refactoring and its final validation.
9. Start Sprint L after the refactoring and its other prerequisites are complete.

The sequence may be adjusted when necessary, but the declared dependencies must be preserved.

**Important:** Do not treat refactoring and Sprint I as mutually exclusive alternatives. They are separate Phase 3 workstreams.

---

## 7. Known Issues and Deferred Items

| Item | Status | Reference |
|---|---|---|
| DICOM visualization bug (voxel ordering) | Resolved 2026-11-06 | `implementation_plan.md` |
| ADR-0003 legacy | Superseded by ADR-0014 | `docs/adr/` |
| `steps_panel` overlay | Removed; replaced by `WorkflowBreadcrumb` in Phase 5 | `implementation_plan.md` |
| `correlation_id` propagation in Workspace | Outstanding | `implementation_plan.md` |
| `event_subscription` propagation test | Dedicated test pending | `tests/integration/ui/workspace/` |
| Hardcoded appearance literals | Tracked in `_KNOWN_DEBT_FILES` | `tests/architecture/` |
| `EditorStackSwitcher` inline QSS | 7 literals; not resolved by refactoring | `_KNOWN_DEBT_FILES` |
| `Editor.icon_name` missing from ABC | Outstanding; not a refactoring blocker | Architectural debt |
| `stl.py` migration from `GetData()` | Deferred to Phase 4.5 / VTK 10 compatibility work | `stl.py` |
| `pyproject.toml` unused `ignore_missing_imports` entries | Cleanup task; no functional impact | `pyproject.toml` |
| Implicit handler resolution in `InMemoryModuleLoader` | Not included in refactoring | `architectural_consolidation_plan.md` §4.4 |
| SQLite `ProjectIndex` backend | Deferred to Phase 8 | `implementation_plan.md` |
| Recent Projects | Deferred to Phase 8 | `implementation_plan.md` |
| Background disk reconciliation | Deferred to Phase 8 | `implementation_plan.md` |

The refactoring must not silently absorb unrelated items from this list.

---

## 8. Validation Requirements

Every structural migration and functional sprint must leave the project in a valid, testable state.

### 8.1 Required commands

```powershell
.venv\Scripts\python.exe -m pytest
.venv\Scripts\python.exe -m ruff check .
.venv\Scripts\python.exe -m ruff format --check .
.venv\Scripts\python.exe -m mypy src
```

If the development environment needs to be restored:

```powershell
uv sync --extra dev
```

Plain `uv sync` removes development tools from the active environment.

### 8.2 Structural validation

The Editor Architecture Refactoring must verify:

- No circular imports.
- No Module-to-concrete-Editor dependency.
- No Workspace dependency on concrete Editor implementations where approved registry contracts should be used.
- No regression in Editor lifecycle or context propagation.
- No regression in Area and EditorStack composition.
- No broken dynamic imports or saved-layout identifiers.
- No regression in appearance-token enforcement.
- All relevant architecture tests pass.
- No obsolete production imports from `ui/editors/` remain.
- `_KNOWN_DEBT_FILES` and `_DEBT_MAX_LITERALS` match the post-migration file set.

### 8.3 Functional validation

Each sprint must include its relevant unit, contract, integration, and regression tests.

The full test suite must be executed at major migration boundaries and before declaring Phase 3 complete.

---

## 9. Phase 3 Completion Criteria

Phase 3 is complete when:

- [ ] Editor Architecture Refactoring is complete and validated.
- [ ] Module and Editor package boundaries are enforced by architecture tests.
- [ ] `ProjectIndex` is implemented and integrated into `ProjectCatalog`.
- [ ] Coordinated project deletion is implemented with rollback.
- [ ] External Reference source data is protected from project deletion.
- [ ] Async project and Flow loading is integrated through `TaskManager`.
- [ ] `MainWindow` initialization does not perform blocking project or Flow I/O.
- [ ] Professional module is registered and integrated using the final Editor architecture.
- [ ] Test stub documentation is complete.
- [ ] Relevant ADRs and architecture documentation are updated.
- [ ] All functional and architectural regression tests pass.
- [ ] `ruff check`, `ruff format --check`, and `mypy src` pass.
- [ ] All changes are committed and the final repository state is validated.

Only after these criteria are satisfied should Phase 3 be marked complete in `implementation_plan.md`.

---

## 10. Current Handoff Summary

**Completed:** Phases 0, 1, and 2. Sprint H closed Phase 2.

**Current phase:** Phase 3 — Project, Home Page & Professional Module.

**Structural workstream:** Editor Architecture Refactoring.

**Next structural action:** Step 0 — remove debug `print()` statements from `LayoutBuilder` and `AreaLayoutRenderer`, then commit separately.

**Next structural decision point:** Complete Step 1 and resolve the open decisions concerning `editor_manifest.py`, `editor_catalog.py`, `Workspace.find_viewport_3d()`, and `MeshDebugEditor`.

**Next functional sprint:** Sprint I — ProjectIndex.

**Functional dependency sequence:** I → J → K.

**Professional module:** Sprint L, after the Editor Architecture Refactoring and prerequisites C, E, and F.

**Phase 4:** Planned; formal start is gated by completion of Phase 3.

The next development cycle should maintain the two coordinated workstreams. The structural refactoring establishes the final architecture; Sprints I–K complete independent functional requirements; Sprint L integrates the Professional module into the resulting architecture.

---

## 11. Relationship with Other Planning Documents

### `implementation_plan.md`

The authoritative roadmap for phases, deliverables, dependencies, and completion criteria.

### `refactoring_plan.md`

The technical execution plan for Editor Architecture Refactoring. It defines package boundaries, migration steps, open decisions, commit strategy, risks, and acceptance criteria.

### `architectural_consolidation_plan.md`

The architectural findings and consolidation context. It must not be treated as an unrestricted backlog for the refactoring.

### Document authority

When a conflict exists:

1. `implementation_plan.md` governs the overall roadmap.
2. `next_steps.md` governs immediate execution priorities and handoff.
3. `architectural_consolidation_plan.md` records architectural consolidation findings.
4. `refactoring_plan.md` governs the technical execution of the approved structural refactoring.

The four documents must remain consistent while preserving their distinct purposes.
