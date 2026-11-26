# Implementation Plan

**Document type:** Roadmap and execution plan
**Status:** Living document
**Scope:** Phased implementation of the CranioZ platform, from foundation to release
**Last updated:** 2026-11-22

---

## 1. Purpose

This document defines the execution strategy for building the CranioZ platform. It translates architectural decisions (ADRs), domain contracts, and clinical requirements into a sequenced, testable implementation plan.

It serves as a scientific, technical, and managerial instrument, distinguishing the PhD research scope from the long-term evolution of the open-source platform.

It is also an honest implementation record. It distinguishes between contracts, reference implementations, production implementations, and integration work.

A deliverable marked as implemented must exist in the codebase and have passing tests. Partial implementations and known limitations must remain visible.

---

## 2. Guiding Principles

1. **Vertical Slices over Horizontal Layers:** Implement features across UI, Application, Domain, and Infrastructure, validating the complete workflow whenever possible.
2. **Stable Contracts:** A phase may begin before the previous phase is complete if its architectural dependencies are defined and stable.
3. **Early Persistence:** Establish persistence contracts and minimum viable serialization early to avoid architectural rework.
4. **Testable at Every Step:** Each phase must include appropriate unit, contract, integration, and UI tests.
5. **Reversible Decisions:** Validate uncertain technical decisions through prototypes, benchmarks, and ADRs before making them architectural dependencies.
6. **Clinical Data Integrity:** Never silently modify, reinterpret, or discard source imaging data. Geometry, calibration, provenance, and validation must remain explicit.
7. **CPU-First Execution:** The application must remain usable on conventional workstations. GPU acceleration is an optimization, not a prerequisite for core clinical functionality.
8. **No Orphaned Implementations:** A feature is not complete merely because its backend exists. Its intended application workflow must be usable and tested.
9. **UI Fidelity to Prototype:** The Prototipagem_UI documents are the canonical reference for widget layout, interaction models, and clinical affordances. Deviations must be justified in an ADR.
10. **Explicit Internationalization:** User-facing strings must be translatable. UI widgets must never hardcode clinical labels.
11. **Centralized Appearance:** Shared visual properties must use design tokens. Component-specific constraints and intrinsic dimensions may be defined locally when they are not part of the shared visual system. See `../../architecture/appearance`.

---

## 3. External Dependencies & Tech Stack

- **Language:** Python 3.12+
- **UI Framework:** PySide6 / Qt 6 (minimum 6.5.0 for `QStyleHints.colorScheme()`)
- **Medical Visualization:** VTK
- **DICOM Parsing:** pydicom
- **Scientific Computing:** NumPy, SciPy
- **Image Processing:** ITK (optional, introduced when justified by a concrete requirement)
- **Geometric Modeling:** Open CASCADE (OCCT), CGAL
- **Mesh Processing:** VTK, OpenMesh and other specialized libraries as required
- **Persistence:** JSON for project metadata, scene and layout; SQLite for indexed catalogs (deferred to Phase 8); JSON for user settings
- **Testing:** pytest, pytest-qt, pytest-benchmark, hypothesis
- **Tooling:** uv, ruff, mypy

Dependencies must be introduced when required by an implementation task. Their presence in this list does not imply that every library must be integrated during the foundation phases.

---

## 4. Phase Overview

The implementation is divided into 11 phases. The sequence establishes the platform progressively while prioritizing a validated clinical core.

| Phase | Name | Status | Main Pending Work |
|---|---|---|---|
| **Phase 0** | Foundation & Boot | ✅ Implemented | Startup performance improvements |
| **Phase 1** | Contracts, Core Domain & i18n | ✅ Implemented | — |
| **Phase 2** | Workspace Engine & Icons | ✅ Implemented | — |
| **Phase 3** | Project, Home Page & Professional Module | 🚧 In Progress | Professional module (Sprint L) |
| **Phase 4** | Scene & Visualization | ⏳ Planned | Import Dialog, RenderingAdapter, Viewer Layout Manager, 2D/3D Tools, LUTs |
| **Phase 5** | Clinical Flows & Panel Widget Registry | ⏳ Planned | WorkflowEngine, WorkflowBreadcrumb, Panel Registry |
| **Phase 6** | Clinical Pipeline | ⏳ Planned | Tomography, Segmentation, Cephalometry, Osteotomy, Guides, Animation |
| **Phase 7** | Scientific Validation | ⏳ Planned | Geometric, clinical and usability validation |
| **Phase 8** | Scientific Product (Release 1.0) | ⏳ Planned | SvgIconProvider, SQLite ProjectIndex, Recent Projects, PDF reports, locale selector |
| **Phase 9** | Extensibility (Release 2.0) | ⏳ Planned | Module API and Plugin API |
| **Phase 10** | AI and Nodes (Release 3.0) | ⏳ Planned | Node system, AI assistance and MCP integration |

**Status legend:**

- ✅ **Implemented:** Implemented in the codebase and tested. Known limitations may still exist.
- 🚧 **In Progress:** A contract, partial implementation, or reference implementation exists, but the deliverable is incomplete or not fully integrated.
- ⏳ **Planned:** Not implemented or not yet started.

**Contracts layer:** ADR-0001, ADR-0002, ADR-0004–0016 are Accepted. **ADR-0014 (Widget Toolkit Selection)** is Accepted: Qt Widgets + QSS modular + Design Tokens in Python, not QML. **ADR-0015 (Editor and Module Package Reorganization)** is Accepted and records the structural refactoring that closed in Phase 3. **ADR-0016 (Project Catalog Synchronization)** is Accepted and specifies the synchronization mechanism between the Project subsystem and the Project Catalog. **ADR-0018 (Professional Module SQLite Persistence)** is Accepted and authorizes the dedicated Professional database without creating a generic module-persistence mechanism. The appearance architecture is specified in `../../architecture/appearance`.

The **Monitor de Logs** is a developer-facing diagnostic subsystem specified in `monitor_logs.md`. It is not an ADR and it is not part of any Phase's closure criteria. Its implementation is deferred to a dedicated sprint (§5.1) and does not block Phase 3 or Phase 4.

**Application layer:** Commands, Tasks, Telemetry, Events and Flows have contracts and reference implementations with contract tests. This does not imply that all production services, module loading, or application workflows are complete.

---

## 5. Current Focus

**Phases 1 and 2 are closed.** The **Editor Architecture Refactoring** (ADR-0015, `refactoring_plan.md`) is complete. Sprints I and J are complete.

**Phase 3** remains the active phase. Its remaining functional deliverable is
**Sprint L (Professional module)**. Sprints I and J closed on 2026-11-20 and
2026-11-22; Sprint K closed on 2026-11-22.

Phase 4 remains the next major implementation phase. It begins only after Phase 3 is marked `✅ Implemented` in this document.

### 5.1 Immediate Priorities

The sprint order below respects dependencies within Phase 3.

| Sprint | Phase | Deliverable | Status | Depends on |
|---|---|---|---|---|
| **B** | 1 | i18n contract and catalogs | ✅ Complete | — |
| **C** | 1 | `EditorContext` propagation | ✅ Complete | B, E, F |
| **E** | 2 | `ThemeService`, `ThemeCompiler`, tokens | ✅ Complete | — |
| **F** | 2 | `IconProvider`, `UnicodeIconProvider`, glyph migration | ✅ Complete | E |
| **G** | 2 | `AreaLayoutRenderer` | ✅ Complete | — |
| **H** | 2 | `EditorStack` | ✅ Complete | G |
| **Editor Refactoring** | 3 | Editor/Module package reorganization (ADR-0015) | ✅ Complete | — |
| **I** | 3 | `ProjectIndex` (ADR-0016) | ✅ Complete (2026-11-20) | — |
| **J** | 3 | Coordinated deletion | ✅ Complete (2026-11-22) | I ✅ |
| **K** | 3 | Async loading | ✅ Complete (2026-11-22) | I ✅, J ✅ |
| **L** | 3 | Professional module | 🚧 In Progress — next focus is L.1 | Editor Refactoring ✅, C ✅, E ✅, F ✅ |
| **Monitor de Logs** | — | Diagnostic subsystem | ⏳ Planned (not scheduled; not a Phase 3 deliverable) | Sprint K (to inform tab mapping) |

**Current focus:** Sprint L. L.0 is complete; L.0.2 Deliveries A and B are
complete. L.1 is in progress with the Professional domain, SQLite profile
persistence, repository/service boundary, and command/query flow complete.
L.0.2 Deliveries C and D are deferred and do not block L.1. The next
implementation task is `ProfessionalEditor`, `ModuleUISpec`, and settings
integration.

**Note on ordering:** Sprint L is unblocked by the completed Editor Refactoring (ADR-0015) and by the completed Sprints C, E, and F. The functional dependency chain for Phase 3 is **J → K**, with **L** independent and able to proceed in parallel (`next_steps.md` §6.1).

**Note on ADR-0016 and Sprint K:** ADR-0016 §4.1 records that the bootstrap-ordering guarantee holds only while the `ProjectIndex` bootstrap is synchronous. Sprint K (Async loading) makes `HomePage` load projects via `TaskManager`; if the bootstrap becomes asynchronous, ADR-0016 §4.1 must be revisited before Sprint K is closed.

**Note on the Monitor de Logs:** the diagnostic subsystem is specified in `monitor_logs.md`. It is **not** part of Sprint K, Sprint L, or Phase 3 closure. Sprint K may emit additional `logging` records as a by-product of async work (e.g. Task lifecycle), but it does not introduce the `QtLogHandler`, the `LogsDialog`, the 📋 button wiring, or the `Areas` snapshot contract. Those belong to a dedicated, currently unscheduled sprint, deliberately sequenced after Sprint K.

---

## 6. Phase Breakdown

### Phase 0: Foundation & Boot

**Goal:** Establish the repository, configuration, logging, minimal persistence and application boot sequence.

**Deliverables:**

- ✅ `../../../pyproject.toml` and CI pipeline.
- ✅ `ConfigurationLoader` and `AppPathResolver`.
- ✅ `EventBus`.
- ✅ JSON serialization for Project Metadata.
- ✅ Boot sequence in `__main__.py`.
- ✅ Error handling for inaccessible application paths.
- ✅ OS username resolution for the initial actor.
- ✅ Flow contracts and repositories.
- 🚧 Lazy imports and startup performance improvements.

**Tests:** Configuration validation, path resolution, boot dependency construction, startup smoke tests.

**Status:** ✅ Implemented, with startup performance work tracked separately.

---

### Phase 1: Contracts, Core Domain & i18n

**Goal:** Formally closed on 2026-11-18.

**Deliverables:**

- ✅ Patient Domain and value objects.
- ✅ Project Domain.
- ✅ UI contracts: `Area`, `Editor`, `EditorRegistry`, `ToolbarSpec`, `ToolSpec`, `LayoutBuilder`, `LayoutRenderer`.
- ✅ `ProjectRepository` and reference implementations.
- ✅ `ProjectContext`, `ProjectAccessPolicy`, `ProjectCatalog`.
- ✅ ADRs 0001, 0002, 0004–0016.
- ✅ **Sprint B (i18n):**
  - `Locale` value object (`pt_BR`, `en_US`).
  - `TranslationService` Protocol (`tr`, `locale`, `set_locale`).
  - `TranslationCatalog` (JSON loader) + `TranslationCatalogRegistry`.
  - Concrete `TranslationService` with `en_US` fallback.
  - `en_US` and `pt_BR` catalogs for existing keys.
  - Injection into `MainWindow`, `Workspace`, `HomePage`, `TomographyEditor`.
  - Removal of `MainWindow._humanize_translation_key`.
  - Contract test: every `name_key` in every `flow.json` resolves in `en_US`.
  - `../../../tests/architecture/test_no_hardcoded_strings_in_shell_widgets.py`: shell widgets must route user-facing strings through `tr(...)`.
- ✅ **Sprint C (`EditorContext` propagation):**
  - `task_manager`, `telemetry`, `correlation_id`, `command_dispatcher`, `scene_query`, `event_subscription`, `translation_service`, `theme_service`, `icon_provider` propagated to every Editor.
  - `Workspace._create_editor` and `MainWindow._create_workspace` pass the complete set.
  - `TomographyEditor.initialize` and `MeshDebugEditor.initialize` accept the complete set.
  - Contract test: every Editor registered in `EditorRegistry` receives all required fields.

**Tests:**

- Pure Python Domain tests.
- Repository contract tests.
- Project serialization round-trips.
- Domain invariant and error-case tests.
- ✅ i18n contract tests.
- ✅ `test_no_hardcoded_strings_in_shell_widgets.py`.
- ✅ `EditorContext` propagation tests.

**Status:** ✅ Implemented.

---

### Phase 2: Workspace Engine & Icons

**Goal:** Formally closed on 2026-11-18.

**Deliverables:**

- ✅ `LayoutTree`, `AreaManager`, `LayoutBuilder`, `LayoutRenderer`.
- ✅ `Workspace` facade, `TopOverlay`, `OverlayManager`.
- ✅ Three-segment Top Bar.
- ✅ Area toggles (Left, Right, Bottom).
- ✅ Atomic `Workspace.load_spec()`.
- ✅ **Sprint E (`ThemeService` + `ThemeCompiler` + tokens):** 47 canonical tokens; `ThemeService`; `ThemeCompiler`; `cranioz.infrastructure.settings` package; boot integration; expanded `_build_qss`; `StartButton` and `FlowRow` migrated to `setProperty` + global QSS; contract and unit tests.
- ✅ **Sprint F (`IconProvider` + `UnicodeIconProvider`):** 60-icon catalog; injected into `MainWindow`, `Workspace`, `HomePage`, `TopBar` segments, `Toolbar`, `StartButton`, `FlowRow`; hardcoded glyphs migrated; `_WHITELIST` emptied; 5 contract tests.
- ✅ **Sprint G (`AreaLayoutRenderer`):** separates inter-Area from intra-Area layout; `AreaWidget` delegates; no visible behavior change; regression tests.
- ✅ **Sprint H (`EditorStack`):** `EditorLayoutSpec.stack([...])`; `EditorStack` widget; single-Editor case unchanged; tests for tab switching, editor lifecycle, dispose.

**Tests:**

- Pure Python layout tests.
- `pytest-qt` rendering tests.
- Editor lifecycle tests.
- Editor Stack behavior tests.
- Theme color resolution tests.
- Icon provider determinism tests.
- Contrast tests.
- ✅ Token and theme completeness tests (Sprint E).
- ✅ Settings persistence round-trip and fallback tests (Sprint E).
- ✅ Icon catalog, fallback, theme integration, widget contract, and accessibility tests (Sprint F).

**Status:** ✅ Implemented.

---

### Phase 3: Project, Home Page & Professional Module

**Goal:** Close Phase 3 formally. Remaining functional blocker: the **Professional module (Sprint L)**[cite: 1].

**Deliverables:**

- ✅ `ProjectManager`, `ProjectCatalog`, `HomePage`, `MainWindow`[cite: 1].
- ✅ Project selection lifecycle[cite: 1].
- ✅ `FlowCatalog` and Flow repositories[cite: 1].
- ✅ **Editor Architecture Refactoring:** see ADR-0015 and `refactoring_plan.md` §11. Completed on 2026-11-18[cite: 1].
- ✅ **Sprint I (`ProjectIndex`):** implemented per ADR-0016. Closed on 2026-11-20[cite: 1].
  - `ProjectIndex` Protocol in `application/project/index.py`: `add`, `remove`, `lookup`, `list_summaries`, `list_ids`, `count`, `contains`, `replace_all`. Includes `ProjectIndexStaleError`. The Protocol is a pure read model and does not know about the repository, the event bus, or the filesystem[cite: 1].
  - `InMemoryProjectIndex` in `application/project/in_memory_index.py`[cite: 1].
  - `ProjectIndexSynchronizer` and `SynchronizedProjectIndex` in `application/project/index_synchronizer.py`[cite: 1].
  - `ProjectCatalog` consumes a `ProjectIndex` instead of querying the `ProjectRepository` directly; `ProjectCatalog.refresh()` is removed (freshness is automatic)[cite: 1].
  - Event-driven invalidation via `ProjectCreated`, `ProjectUpdated`, `ProjectDeleted`[cite: 1].
  - Bootstrap ordering guarantee per ADR-0016 §4: `subscribe` → `repository.list_metadata()` → `replace_all`, on the same synchronous call stack. No event queue while the bootstrap is synchronous (see §5.1 note on Sprint K)[cite: 1].
  - Staleness rule per ADR-0016 §3.3: a query never silently returns data from a stale index; `ProjectIndexStaleError` is raised when a rebuild after a detected staleness fails[cite: 1].
  - Handler error containment per ADR-0016 §3.4: handlers never propagate to the `EventBus`; failures log with `project_id` and operation name only (no PHI) and mark the index as possibly stale[cite: 1].
  - Contract tests: `add`/`remove`/`lookup`/`list`/`count`/`contains`/`replace_all`; bootstrap ordering; handler error containment; staleness propagation; catalog reads via `ProjectIndex` only; end-to-end integration with `ProjectManager`[cite: 1].
  - Benchmark documented in ADR-0016's implementation notes (not a CI gate): 100/300/1000 projects in `tmp_path`, comparing `search_projects()` latency and `repository.list_metadata` call count between baseline (direct repository) and new (indexed)[cite: 1].
  - **Not** part of Sprint I: `FilesystemProjectIndex` does not exist. A persisted index and a SQLite implementation remain deferred to Phase 8[cite: 1].
  - **Final validation (2026-11-20):** 1692 passing tests, 0 failed, 0 errors, 2 skipped; `ruff check`, `ruff format --check`, and `mypy src` clean. The integration fixture `../../../tests/integration/ui/test_main_window_import.py` was migrated to the composition-root wiring; the bootstrap order (`synchronizer.start()` before `manager.create_project(...)`) is preserved and documented in ADR-0016 §4.2[cite: 1].
- ✅ **Sprint J (Coordinated deletion):** complete on 2026-11-22[cite: 1].
  - `ProjectManager.delete_project` coordinates `ProjectCatalog` → `ProjectIndex` → `FilesystemProjectRepository` via the `ProjectDeleted` event (ADR-0016 §2.2). The `ProjectManager` does not call `ProjectCatalog` or `ProjectIndex` directly[cite: 1].
  - Rollback semantics verified: repository failure raises before `ProjectDeleted` is published; handler failure is contained by the synchronizer (ADR-0016 §3.4) and marks the index stale; the next query rebuilds from the authoritative repository (ADR-0016 §3.3). No event compensation, no manual index re-add[cite: 1].
  - External source data (External Reference mode) is never removed by project deletion. `FilesystemProjectRepository` owns exactly one file (`project.json`); sibling files survive byte-identical[cite: 1].
  - Contract and failure-path tests[cite: 1].
  - **Final validation (2026-11-22):** 1701 passing tests, 0 failed, 0 errors, 2 skipped (+9 vs Sprint I); `../../../tests/architecture` 85 passed; `ruff check`, `ruff format --check`, `mypy src` clean (284 source files); `git diff --stat src/` empty (**no production code changed**; the coordination was already correct and the sprint proved it with tests)[cite: 1].
  - **Scope correction:** the UI affordance for delete is deferred. The API-level behavior is verified and propagates through the catalog. The UI affordance requires UX decisions that are out of scope for a "coordinated deletion" sprint. Tracked in `next_steps.md` §5.2 and §7[cite: 1].
- ✅ **Sprint K (Async loading):** complete on 2026-11-22. K-minimal
  option (b): flows async, projects synchronous. `HomePage.refresh()`
  is synchronous (in-memory `SynchronizedProjectIndex`, ADR-0016);
  the `MainWindow` dispatches a `_LoadFlowsTask` through the
  `TaskManager` because `FlowCatalog.list_definitions()` performs
  filesystem I/O. `synchronizer.start()` remains synchronous in the
  composition root; ADR-0016 §4.1 is not reopened. New tests:
  `test_home_page_flows_async.py`, `test_main_window_workspace_rollback.py`,
  `test_main_window_bootstrap_ordering.py`[cite: 1].
- ⏳ **Sprint L.0.2 Deliveries C and D:** deferred at the current planning
  decision. They do not block L.1.
  - Deferred: `TimelineSlider`, `ColorPicker`, `Histogram`, final debug-harness
    consolidation, HiDPI validation and catalog closure.
- 🚧 **Sprint L (Professional module):**
  - **L.0:** complete. System form widgets delivered.
  - **L.0.2 Delivery A:** complete. Simple Qt-native widgets delivered.
  - **L.0.2 Delivery B:** complete. `CollapsibleSection`, stable-key `DragList`
    and `IconSidebar` delivered.
  - **L.1 (in progress):** domain, SQLite profile persistence,
    repository/service, and command/query flow complete; `ProfessionalEditor`,
    `ModuleUISpec`, and settings integration remain.
  - **L.2:** navigation, sections and configuration interactions.
  - `ProfessionalEditor` registered in `EditorRegistry`[cite: 1].
  - `ModuleUISpec` for the Professional module[cite: 1].
  - Settings integration (`professional.*` keys)[cite: 1].
  - Tests[cite: 1].
  - **Sprint L is unblocked** by the completed Editor Architecture Refactoring, Sprint C, Sprint E, and Sprint F[cite: 1].

**Deferred to Phase 8:**

- SQLite `ProjectIndex` backend (`SqliteProjectIndex`, same `ProjectIndex` Protocol)[cite: 1].
- Recent Projects[cite: 1].
- Background disk reconciliation[cite: 1].

**Not part of Phase 3, not deferred to Phase 8 — deferred to a dedicated unscheduled sprint:**

- Monitor de Logs (`monitor_logs.md`): `QtLogHandler`, `LogsDialog`, 📋 button wiring, `Areas` snapshot contract. Documented and awaiting a dedicated sprint[cite: 1].

**Tests:**

- Project lifecycle tests[cite: 1].
- Filesystem repository integration tests[cite: 1].
- HomePage selection and refresh regression tests[cite: 1].
- Project opening and rollback tests[cite: 1].
- ProjectIndex contract tests (index), synchronizer tests (bootstrap, events, error containment, `rebuild`, `ensure_fresh`), catalog-via-index tests, and end-to-end `ProjectManager` sync tests (Sprint I, ADR-0016)[cite: 1].
- `ProjectIndexStaleError` propagation and `MainWindow` handling tests (Sprint I, ADR-0016)[cite: 1].
- Delete-specific staleness paths and the physical delete invariant (Sprint J, ADR-0016 §3.3/§3.4 and §2.2)[cite: 1].
- Architecture gate: `../../../tests/architecture/test_no_legacy_project_delete_api.py` (Sprint J)[cite: 1].
- Async flow loading, workspace rollback, and bootstrap ordering integration tests (Sprint K)[cite: 1].
- Professional module integration tests[cite: 1].

**Status:** 🚧 In Progress. Remaining functional blocker: **Sprint L**. L.1 is
in progress with domain, SQLite profile persistence, repository/service, and
command/query flow complete; `ProfessionalEditor`, `ModuleUISpec`, and settings
integration remain. L.0.2 Deliveries C and D are deferred.

---

### Phase 4: Scene & Visualization

**Status:** ⏳ Planned. Begins after Phase 3 is marked `✅ Implemented`[cite: 1].

**Goal:** Complete the integration between the Application layer, Scene, imaging infrastructure, rendering adapters, and Editors[cite: 1].

#### 4.1 Application Layer

- ✅ `main_window`, `tasks/`, `telemetry/`, `events/` contracts and reference implementations[cite: 1].
- 🚧 `CommandDispatcher` integration into all Editors[cite: 1].

#### 4.2 Scene and Domain Integration

- ✅ `domain/scene/`, `application/scene/`[cite: 1].
- ✅ `ImportDicomSeriesCommand` and handler[cite: 1].
- 🚧 Complete `SceneQuery` propagation[cite: 1].
- ⏳ Scene serialization (ADR-0009)[cite: 1].
- ⏳ Filesystem-backed Scene persistence[cite: 1].
- ⏳ Complete integration between Commands, Scene and imported objects[cite: 1].

#### 4.3 Medical Imaging Infrastructure

**4.3.1 Volume and geometry**

- ✅ `Volume`, `VolumeGeometry`, `ImageMetadata`, `VolumeProvenance`, `IntensityScale`[cite: 1].
- ✅ Internal RAS convention[cite: 1].
- ✅ LPS-to-RAS conversion[cite: 1].
- ✅ Explicit intensity calibration state[cite: 1].

**4.3.2 DICOM import and validation**

- ✅ `DicomSorter`, `DicomValidator`, `DicomSeriesReader`, `ImportReport`[cite: 1].
- ✅ `spacing_z` from `ImagePositionPatient` distance[cite: 1].
- ✅ `RescaleSlope`/`RescaleIntercept` per slice[cite: 1].
- ⏳ Patient identity mismatch handling[cite: 1].
- ⏳ PHI-aware logging[cite: 1].

**4.3.3 Memory and interoperability**

- ✅ Voxel buffer ownership: `Volume` owns; `VtkImageAdapter` shares[cite: 1].
- ✅ NumPy `[z, y, x]` convention[cite: 1].
- ✅ Voxel ordering contract: `data.ravel(order="C")` without transposition. Regression test enforced[cite: 1].
- ✅ Production scalar type: `VTK_SHORT`[cite: 1].
- ✅ Direction matrix applied in `VtkImageAdapter`[cite: 1].

**4.3.4 Unified Import Dialog (required)**

- `ImportManager` with categories (Volume, Radiographs, Scans, Photographs, Meshes, Dental Implants, Facial Implants), sources (project, file, sample data), preview, auto-tagging[cite: 1].
- `ImportDialog` with tab bar, source selector, asset grid/list, preview panel, add/remove/select actions[cite: 1].
- Per-category importers[cite: 1].
- Scene and DomainObjectStore integration[cite: 1].
- TaskManager progress, cancellation, error reporting[cite: 1].

**4.3.5 Storage and export**

- ⏳ External Reference and Managed Copy storage modes[cite: 1].
- ⏳ Preserve source DICOM as canonical[cite: 1].
- ⏳ VTI export with round-trip validation[cite: 1].
- ⏳ Project deletion never removes external source data[cite: 1].

#### 4.4 Geometry Infrastructure

**Implemented:** `Mesh`, `CoordinateFrame`, STL I/O, VTK adapter, `MeshDebugEditor`[cite: 1].

**Deferred:** `GeometryRevision`, content-hash deduplication, persistent asset storage, `ValidationProfile`, `GeometryOperation`, booleans, welding, benchmarks[cite: 1].

#### 4.5 Visualization Infrastructure

**Implemented:**

- ✅ `MPRView` (manual `vtkImageReslice` pipeline)[cite: 1].
- ✅ `Viewport3DView` (`vtkSmartVolumeMapper`, `VTK_SHORT`)[cite: 1].
- ✅ Axial, coronal, sagittal, 3D orientations[cite: 1].
- ✅ Volume rendering presets[cite: 1].
- ✅ `set_volume(Volume)`, `set_mesh(Mesh)`[cite: 1].
- ✅ DICOM volume path validated in MPR and 3D[cite: 1].

**Pending:**

- ⏳ `RenderingAdapter` between Scene and VTK[cite: 1].
- ⏳ **ViewerLayoutManager** (dynamic grids: 1×1, 2×2, 3×3, editable up to 6×4, panoramic, ATM)[cite: 1].
- ⏳ **2D Tools** (brightness/contrast, pan, zoom, HU probe, ROI, nerve drawing, distance/angle, crosshair, ruler, LUT selection, LUT inversion, background color, animation, thumbnail)[cite: 1].
- ⏳ **3D Tools** (ROI, cut, paint, annotations, distance/angle, preset selection, orthographic/perspective, background color, lock rotation, thumbnail)[cite: 1].
- ⏳ **Clinical transfer functions** (HU-based presets: `bone_cortical`, `bone_trabecular`, `soft_tissue`, `air`, `metal`, `cbct_percentile`)[cite: 1].
- ⏳ **Viewer status indicators** (active view badge, orientation badge, inactive state)[cite: 1].
- ⏳ Remove the debug bounding box from `Viewport3DView`[cite: 1].
- ⏳ VTK resource lifecycle under repeated open/close[cite: 1].
- ⏳ Headless and Windows rendering tests[cite: 1].

**Architectural constraints:**

- Domain data must not depend on VTK[cite: 1].
- VTK actors, mappers, and render windows are presentation objects[cite: 1].
- Rendering adapters translate semantic Scene objects into renderable representations[cite: 1].
- Rendering updates must not mutate clinical source data[cite: 1].
- VTK render-window and actor lifecycle operations remain on the GUI thread (ADR-0011)[cite: 1].

#### 4.6 Module Integration

- 🚧 `InMemoryModuleLoader` with dependency resolution[cite: 1].
- 🚧 Entry-point imports[cite: 1].
- 🚧 Tools, Editors, Services, Flows registration[cite: 1].
- 🚧 `BUILTIN_MANIFESTS`[cite: 1].
- 🚧 Shared EventBus across ModuleContexts[cite: 1].
- ⏳ First functional built-in module[cite: 1].

#### 4.7 Tests

- DICOM import tests[cite: 1].
- Geometry and coordinate conversion tests[cite: 1].
- Slice ordering and spacing validation[cite: 1].
- Intensity calibration tests[cite: 1].
- NumPy/VTK interoperability tests[cite: 1].
- Geometry Infrastructure tests[cite: 1].
- VTI round-trip tests[cite: 1].
- Scene lifecycle and persistence tests[cite: 1].
- ✅ Voxel ordering regression tests[cite: 1].
- ✅ `int16` fidelity test[cite: 1].
- ✅ `spacing_z` test[cite: 1].
- ⏳ Import Dialog end-to-end tests[cite: 1].
- ⏳ ViewerLayoutManager tests[cite: 1].
- ⏳ Tool behavior tests[cite: 1].
- ⏳ LUT selection and inversion tests[cite: 1].
- ⏳ Preset selection tests[cite: 1].
- ⏳ Performance tests[cite: 1].

### Phase 5: Clinical Flows & Panel Widget Registry

**Goal:** Implement workflow execution, panel composition per Area, and layout persistence.

**Deliverables:**

- ⏳ `WorkflowEngine` (evaluates requirements, transitions).
- ⏳ JSON flow loading and requirement evaluation.
- ⏳ Step-state computation.
- ⏳ **`WorkflowBreadcrumb` in the Top Bar** (replaces the removed `steps_panel`).
- ⏳ Flow state persistence.
- ⏳ **`PanelRegistry`:** panels registered by ID, addressable by Area.
- ⏳ Area panel management: Left, Right, Bottom support zero or more registered panels.
- ⏳ Built-in panels:
  - **Left:** Objects, Volumes, Cephalometric Points, Masks, Measurements.
  - **Right:** Registry, Scene, History, Material, Osteotomy Patterns, Object Properties, Tomography, Segmentation.
  - **Bottom:** Console, History, Animation, AI Assistant, Nodes.
- ⏳ Layout State Persistence (ADR-0010).
- ⏳ Real ModuleRegistry and ModuleLoader integration.
- ✅ Flow Catalog and repositories.

**Status:** ⏳ Planned.

---

### Phase 6: Clinical Pipeline

**Goal:** Implement the clinical tools required for the initial orthognathic surgery workflow.

#### Phase 6A — Tomography & Segmentation

- ⏳ Tomography Editor clinical workflow.
- ⏳ Synchronized axial, coronal, sagittal navigation.
- ⏳ Physical-coordinate crosshair and slice positioning.
- ⏳ Slice distance, count, range controls.
- ⏳ Window/Level and intensity display controls.
- ⏳ Intensity probing.
- ⏳ ROI tools (display ROI vs processing ROI).
- ⏳ Threshold-based segmentation.
- ⏳ Mask creation and editing.
- ⏳ Segmentation paint/erase/close holes/small-segment removal.
- ⏳ AI-assisted segmentation (deferred to Phase 10 if not ready).
- ⏳ Curved MPR and panoramic reconstruction.
- ⏳ Surface generation from segmentation masks.
- ⏳ Clinical workflow integration.

#### Phase 6B — Registration & Cephalometry

- ⏳ Image and surface registration.
- ⏳ Reference-based alignment.
- ⏳ Cephalometric template system.
- ⏳ Cephalometric capture strategies (manual, thirds cube, facial fifths, dental cusps, AI-assisted).
- ⏳ Primary vs secondary point distinction.
- ⏳ Point connectivity.
- ⏳ Landmark refinement and verification.
- ⏳ Cephalometric measurements and reports.
- ⏳ Registration and landmark validation.

#### Phase 6C — Osteotomy

- ⏳ Le Fort I, BSSO, genioplasty.
- ⏳ Osteotomy pattern library.
- ⏳ Boolean operations and fragment separation.
- ⏳ Fragment movement and transform management.
- ⏳ Pre-op vs post-op comparison and animation.
- ⏳ Soft-tissue thickness map and color map.
- ⏳ Surgical plan persistence.

#### Phase 6D — Surgical Guides

- ⏳ Parametric guide generation.
- ⏳ Guide-to-anatomy fit validation.
- ⏳ Manufacturing constraints.
- ⏳ Export for additive manufacturing.

#### Phase 6E — Integrated Validation

- ⏳ End-to-end orthognathic workflow.
- ⏳ Data integrity and reproducibility tests.
- ⏳ Geometric validation.
- ⏳ Clinical workflow usability tests.

**Status:** ⏳ Planned.

---

### Phase 7: Scientific Validation

**Goal:** Execute the scientific validation protocols defined in the doctoral research project.

**Deliverables:**

- Geometric validation reports.
- Reproducibility studies.
- Inter- and intra-examiner reliability.
- ICC and measurement error analysis.
- Usability evaluation.
- Performance evaluation on reference hardware.
- Documentation of validation methodology.

**Status:** ⏳ Planned.

---

### Phase 8: Scientific Product (Release 1.0)

**Goal:** Consolidate the validated clinical core into a stable, distributable scientific product.

**Deliverables:**

- Windows installer.
- Autosave and crash recovery.
- PDF report generation (localized).
- Final user and developer documentation.
- **Recent Projects** on the Home Page.
- **SQLite ProjectIndex** (`SqliteProjectIndex`, same `ProjectIndex` Protocol as ADR-0016).
- **Background disk reconciliation** for the Project Catalog (ADR-0016 §3.2).
- **IconManager complete:** `SvgIconProvider`, SVG assets, cache by (name, size, theme), SVG recoloring.
- **Complete migration of every widget** to `ThemeService.color(...)` + `IconProvider.icon(...)`.
- **Locale selector UI.**
- **Complete `pt_BR` and `en_US` catalogs.**
- **Locale-aware formatting.**
- **Custom volume-rendering preset editor.**
- **High-contrast theme** (as `ThemeName.HIGH_CONTRAST`).
- Performance profiling and optimization.
- Release packaging and versioning.
- Scientific publication.
- DOI registration and public release.

**Status:** ⏳ Planned.

---

### Phase 9: Extensibility (Release 2.0)

**Goal:** Open the platform to external development and community contributions.

**Deliverables:**

- Stable Module API.
- Plugin API.
- Plugin loader and permission boundaries.
- External plugin catalog.
- Module-owned persisted state.
- State migration contract.
- Compatibility and versioning policies.

**Status:** ⏳ Planned.

---

### Phase 10: AI and Nodes (Release 3.0)

**Goal:** Introduce advanced automation and procedural workflows.

**Deliverables:**

- Non-destructive Node System.
- Graph evaluation and execution.
- AI Assistant Editor.
- AI-assisted clinical operations.
- MCP Server integration.
- Command parity between UI and automated execution.

**Status:** ⏳ Planned.

---

## 7. Testing Strategy & Metrics

Testing is a clinical requirement. Metrics must be reproducible and contextualized.

### 7.1 Coverage

- **Domain:** Critical invariants and error cases.
- **Application:** Command execution, transaction rollback, event publication, task lifecycle, i18n contract, settings round-trip, project catalog synchronization (ADR-0016), coordinated deletion (ADR-0016 §2.2/§3.3/§3.4).
- **Infrastructure:** DICOM parsing, geometry, calibration, persistence, interoperability, settings persistence and migration.
- **UI:** Widget behavior, Editor lifecycle, Workspace integration, tool behavior, import dialog.
- **Appearance:** Token completeness, theme completeness, contrast, no hardcoded values, icon catalog, surface composition.
- **End-to-End:** Complete clinical workflows using synthetic or approved datasets.

### 7.2 Performance Metrics

All performance targets must be measured using a defined Reference Dataset and Reference Hardware.

Initial targets:

- **DICOM Import:** 500-slice reference dataset in under 10 seconds, including indexing and readiness for first visualization.
- **Surface Rendering:** 30+ FPS for a mesh of 1,000,000 polygons on reference hardware.
- **Memory:** Below 4 GB RAM during standard facial CT processing.
- **Project Catalog Queries (ADR-0016):** after bootstrap, `search_projects()` must not perform filesystem I/O per keystroke. Verified by call-count test; latency benchmark documented in ADR-0016 implementation notes.

### 7.3 CPU and GPU Responsibilities

- Clinical data and semantic objects remain in main memory and the Domain Scene.
- GPU memory stores renderable representations and rendering resources.
- GPU acceleration is optional for core clinical workflows.
- CPU-based fallback must remain available for essential operations.

### 7.4 Concurrency

- `TaskManager` is the only application mechanism for off-thread work (ADR-0011).
- Long-running DICOM parsing, segmentation, registration, and mesh processing execute as Tasks.
- GUI and VTK render-window operations remain on the GUI thread.
- Cancellation is cooperative.
- Do not use `QTimer` as a substitute for background execution.
- The `ProjectIndexSynchronizer` (ADR-0016) assumes single-threaded execution on the main thread, consistent with the `EventBus` and `ProjectManager`. If the bootstrap becomes asynchronous (Sprint K), ADR-0016 §4.1 must be revisited.
- The `QtLogHandler` (when implemented, see `monitor_logs.md` §6.3) does **not** spawn threads. It marshals `LogRecord`s from any thread to the GUI thread through a `Qt.ConnectionType.QueuedConnection`. This is a marshalling mechanism, not a work-execution mechanism; it does not conflict with the "TaskManager as the only application mechanism for off-thread work" rule.

### 7.5 Telemetry

Long-running operations must emit telemetry events through `TelemetrySink`, using correlation IDs (ADR-0012). Telemetry must not contain PHI.

The `ProjectIndexSynchronizer` (ADR-0016) must log failures using `project_id` and operation name only, never `project_name` or `patient_display_name`.

The Monitor de Logs (`monitor_logs.md`) is a `logging` view, not a telemetry channel. It does not go through `TelemetrySink`, and it does not emit telemetry of its own.

---

## 8. Release Criteria (Definition of Done)

A phase is complete when:

1. Code follows the accepted architecture and relevant ADRs.
2. Unit, contract, integration and UI tests are passing as applicable.
3. New Protocols have contract tests.
4. CI is green.
5. Documentation is updated.
6. The feature is usable through its intended UI workflow.
7. No unresolved `TODO` remains without a linked issue.
8. No production `NoOp*` placeholder remains for a service the phase claims to deliver.
9. No call site uses a pre-ADR API that the accepted ADR removed without a shim (e.g., no `ProjectCatalog(repository=...)` remains after ADR-0016). Verified by grep in the sprint close review.
10. Known debt affecting the phase is fixed or explicitly tracked with a linked issue.
11. Data integrity, failure handling and recovery behavior are tested where relevant.
12. Every user-facing string resolves through `TranslationService`.
13. Every shared visual property resolves through `ThemeService`; no hardcoded color, size, spacing, radius, opacity or font weight in the Qt presentation layer, except for the files explicitly listed in `_KNOWN_DEBT_FILES` (widget migration sprint).

### 8.1 Release 1.0 Scope

Release 1.0 delivers the validated clinical core defined by the doctoral research scope.

It does not include:

- External Plugins.
- Node System.
- AI/MCP platform integration.
- Multi-monitor support as a required feature.

These capabilities belong to Releases 2.0 and 3.0.

---

## 9. Implementation Summary

The foundation, core domain, workspace, project lifecycle, imaging pipeline, and DICOM visualization are implemented. The voxel-ordering bug that blocked Phase 4 was resolved on 2026-11-06. The appearance architecture is decided (ADR-0014, `../../architecture/appearance`).

**The Editor Architecture Refactoring closed on 2026-11-18.** It moved Editor implementations out of `ui/` into a top-level `cranioz/editors/` package, separated Editor contracts from concrete implementations, separated reusable Views from concrete Editors, and enforced the dependency boundaries through AST-based architecture tests. See ADR-0015 (`../../adr/ADR-0015_Editor_and_Module_Package_Reorganization.md`) and `refactoring_plan.md` §11. Final validation: **1635 passing tests, 0 failed, 0 errors, 2 skipped, ruff check clean, ruff format --check clean, mypy src clean (281 files), 85% overall coverage.**

Sprint B (i18n) is complete: the shell — `MainWindow`, the Home Page tree, the three Top Bar segments, and the Workspace placeholder editor — resolves user-facing strings through the `TranslationService`. The architecture guard `../../../tests/architecture/test_no_hardcoded_strings_in_shell_widgets.py` prevents regressions.

Sprint E (appearance foundation) is complete: `ThemeService` and `ThemeCompiler` are implemented, the 47 canonical design tokens are defined for `DARK` and `LIGHT`, the `cranioz.infrastructure.settings` package provides typed, versioned, and atomically written user settings, and `AppPathResolver.user_settings_path()` resolves the user settings file. The Modern Dark palette is applied, the QSS covers tables, headers, scrollbars, buttons, inputs, labels, cards, `StartButton`, and `FlowRow`, and the two Home Page widgets (`StartButton`, `FlowRow`) are migrated from inline `setStyleSheet` to `setProperty` + the global QSS.

Sprint F (icons) is complete: `IconState`, `IconProvider` Protocol and `UnicodeIconProvider` are implemented with the closed 60-icon catalog; the provider is injected into `MainWindow`, `Workspace`, `HomePage`, the three Top Bar segments, `Toolbar`, `StartButton`, and `FlowRow`; the hardcoded glyphs in those widgets are migrated to `provider.icon(...)`; and the `_WHITELIST` in `test_no_hardcoded_strings_in_shell_widgets.py` is empty, meaning the Sprint B debt is paid. The five contract tests (`test_icon_catalog.py`, `test_icon_fallback.py`, `test_icon_theme.py`, `test_icon_widget_contract.py`, `test_icon_accessibility.py`) pass.

Sprint G (`AreaLayoutRenderer`) and Sprint H (`EditorStack`) are complete. Phase 2 is closed.

Sprint C (`EditorContext` propagation) is complete. Phase 1 is closed.

**ADR-0016 (Project Catalog Synchronization) is Accepted on 2026-11-18.** It specifies the mechanism by which the `ProjectCatalog` remains consistent with the `ProjectManager`: an in-memory `ProjectIndex` populated by a `ProjectIndexSynchronizer` and invalidated by `ProjectCreated`, `ProjectUpdated`, and `ProjectDeleted`. The repository remains the authoritative source; the index is a read-optimized projection. External mutations are not detected automatically and require an explicit rebuild or restart. SQLite and background reconciliation remain deferred to Phase 8.

**Sprint I (ProjectIndex) is complete on 2026-11-20.** The `ProjectIndex` Protocol, `InMemoryProjectIndex`, `ProjectIndexSynchronizer`, and `SynchronizedProjectIndex` are implemented and tested under ADR-0016. `ProjectCatalog` consumes a `ProjectIndex` and no longer calls `repository.list_metadata()`; `refresh()` is removed. Final validation: **1692 passing tests, 0 failed, 0 errors, 2 skipped; `ruff check`, `ruff format --check`, `mypy src` clean.** The integration fixture `../../../tests/integration/ui/test_main_window_import.py` was migrated to the composition-root wiring (`repository → synchronizer → index → catalog`), preserving the bootstrap order required by ADR-0016 §4. No production code changed during that migration; the drift was confined to the test fixture.

**Sprint J (Coordinated deletion) is complete on 2026-11-22.** `ProjectManager.delete_project` coordinates `ProjectCatalog` → `ProjectIndex` → `FilesystemProjectRepository` via the `ProjectDeleted` event. The delete-specific staleness paths (handler containment, rebuild-on-next-query, `ProjectIndexStaleError` on double failure) and the physical delete invariant (only `project.json` is removed; sibling files survive byte-identical) are verified. Final validation: **1701 passing tests, 0 failed, 0 errors, 2 skipped; `../../../tests/architecture` 85 passed; `ruff check`, `ruff format --check`, `mypy src` clean (284 source files); `git diff --stat src/` empty.** The UI affordance for delete remains deferred (`next_steps.md` §5.2, §7).

The immediate focus is **Sprint L.1 (Professional Module)**. The ADR-0018 SQLite
persistence foundation, profile repository/service boundary, and command/query
flow were completed on 2026-11-24. Validation:
**1854 passed, 0 failed, 3 skipped; `ruff check`, `ruff format --check`, and
`mypy src` clean.** Sprint K is complete. L.0.2 Deliveries C and D are deferred
and do not block Phase 3.

Phase 4 begins after Phase 3 is marked `✅ Implemented`. Its first deliverables are the Unified Import Dialog, the `RenderingAdapter`, the `ViewerLayoutManager`, the 2D/3D tools, and the clinical transfer function presets.

The geometry infrastructure initial subset is validated. Full geometry infrastructure is deferred.

The **Monitor de Logs** (`monitor_logs.md`) is a developer-facing diagnostic subsystem. Its specification is complete, but no implementation exists. It is deferred to a dedicated, currently unscheduled sprint, sequenced after Sprint K so that the async-loading logging informs the tab mapping. It is **not** part of Phase 3's closure criteria, **not** part of Phase 4's deliverables, and **not** a Release 1.0 requirement. The `logs_requested` signal is reserved in `home_page.md` §25; the `Areas` snapshot contract with the `Workspace` is specified in `monitor_logs.md` §7.

---

## 10. Known Issues and Resolutions

### 10.1 ADR-0014 (Widget Toolkit Selection)

...

### 10.2 Editor and Module Package Reorganization (ADR-0015)

Completed 2026-11-18. Resolved items:

- The duplicated `_PlaceholderEditor` was consolidated into the canonical `PlaceholderEditor`.
- The duplicate `_null_task_manager.py` was removed; `module_loader.py` uses `NoopTaskManager` from `cranioz.application.tasks`.
- `cranioz.ui.editors` was removed.
- `DummyEditor` and `DebugEditor` moved to `../../../tests/fixtures/editors/test_editor.py`.
- `editor_manifest.py` and `editor_catalog.py` were removed (deferred to Sprint L if a contract is needed).
- `MeshDebugEditor` moved to `editors/builtin/mesh_debug/editor.py`.
- `_KNOWN_DEBT_FILES` reduced from 8 to 5 files.
- `Workspace.find_viewport_3d()` is documented as an approved exception to §4.1 rule 8. A regression test is tracked as follow-up.

### 10.3 Project Catalog Synchronization (ADR-0016)

Accepted 2026-11-18. Recorded decisions:

- The `ProjectIndex` Protocol is a pure read model; `InMemoryProjectIndex` is the reference implementation.
- `ProjectIndexSynchronizer` and `SynchronizedProjectIndex` maintain and decorate the index.
- `ProjectCatalog.refresh()` is removed; freshness is automatic via `SynchronizedProjectIndex`.
- Bootstrap uses direct ordering (`subscribe` → `repository.list_metadata()` → `replace_all`) on the same synchronous call stack; no event queue while the bootstrap is synchronous.
- `FilesystemProjectIndex` does not exist as a class name; a persisted or SQLite-backed index is deferred to Phase 8.
- Handler failures are logged with `project_id` and operation name only (no PHI), and mark the index as possibly stale.
- A query never silently returns data from a stale index; `ProjectIndexStaleError` is raised when a rebuild after a detected staleness fails.
- External mutations are not detected automatically; explicit rebuild or restart is required, and background reconciliation is deferred to Phase 8.
- Sprint K (Async loading) must revisit the bootstrap-ordering decision if the index bootstrap becomes asynchronous.
- **Integration fixture drift (Sprint I/02, 2026-11-20):** `../../../tests/integration/ui/test_main_window_import.py` was still constructing `ProjectCatalog(repository=...)` after ADR-0016 removed that parameter. The fixture was rewritten to mirror `__main__.py::_build_project_subsystem` line-for-line, preserving the `synchronizer.start()` → `manager.create_project(...)` order. No compatibility shim was added; the `TypeError` from the removed parameter is the intended forcing function. Recorded in ADR-0016 §6.3.
- **Coordinated deletion closure (Sprint J, 2026-11-22):** the coordination is event-driven and already correct; the sprint added the failure-path tests and the physical delete invariant, and an architecture gate (`test_no_legacy_project_delete_api.py`). The UI affordance for delete is deferred. The `repository.delete → publish(ProjectDeleted)` pair remains synchronous and must not be parallelized without re-opening ADR-0016 §4.1.

### 10.4 Deferred to a Future PR

- `application/event_bus.py` → `application/events/bus.py` (Step 6.1 of `refactoring_plan.md`). Deferred per `refactoring_plan.md` §5.10.
- `editors/view_overlays/` (Step 4.4 of `refactoring_plan.md`). Skipped because the current `ui/editors/overlays/gizmos/` and `ui/editors/overlays/rulers/` directories contain only empty `__init__.py` files.

### 10.5 Monitor de Logs (planned)

The **Monitor de Logs** (`monitor_logs.md`) is a developer-facing diagnostic subsystem, distinct from the Console and History Editors (see `monitor_logs.md` §2). It is specified but not implemented. Recorded decisions:

- The `logs_requested` signal is reserved in `home_page.md` §25; the 📋 button is not wired.
- The `LogsDialog` is non-modal (`Qt.WindowType.Tool`), single-instance per `MainWindow`, with tabs `Boot / Home Page / Workspace / Areas / Scene / Project / Tomography / Segmentation`.
- The `QtLogHandler` is a `logging.Handler` that marshals records to the GUI thread via a `QueuedConnection`; it is installed by the bootstrap after `_configure_logging`.
- The `Areas` tab is fed by `cranioz.ui.workspace` records tagged with `area_snapshot=True`. The aggregated INFO line is emitted once per applied layout (already debounced by 50 ms in `Workspace._apply_default_splitter_sizes`); per-Area DEBUG lines are emitted per Area. The existing `_logger.info("DEBUG: Vertical splitter ...")` in `Workspace._compute_vertical_sizes` will be lowered to `debug` when the contract is implemented.
- The Console Editor is **not** fed by `logging`. It is a clinical channel, fed by an application-level notification service (to be defined). This separation is a project invariant.
- The Monitor de Logs is not a telemetry channel; it does not use `TelemetrySink` and does not emit telemetry.

Implementation is deferred to a dedicated, currently unscheduled sprint, sequenced after Sprint K. It does not block Sprint K, Sprint L, Phase 3 closure, or Phase 4.
