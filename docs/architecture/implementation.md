# Implementation Plan

**Document type:** Roadmap and execution plan
**Status:** Living document
**Scope:** Phased implementation of the CranioZ platform from foundation to release.
**Last updated:** 2026-10-29 (post initial Application layer wiring and Phase 2 debt analysis)

---

## 1. Purpose

This document defines the **execution strategy** for building the CranioZ platform. It translates the architectural decisions (ADRs), the domain contracts, and the clinical requirements into a sequenced, testable, and iterative implementation plan.

Its primary goal is to serve as a scientific, technical, and managerial instrument.

It is also meant to be an **honest status record**: it distinguishes between *contracts that exist*, *reference implementations that exist*, *production implementations that exist*, and *wiring that connects them*. A deliverable marked ✅ means it is implemented and tested; 🚧 means a contract or partial implementation exists but the deliverable is not complete; ⏳ means it has not started.

---

## 2. Guiding Principles

The implementation follows five strict rules:

1. **Vertical Slices over Horizontal Layers:** We do not build "all models first, then all views". We build a feature from the UI down to the Domain and Persistence, and we test it end-to-end.
2. **No Unresolved Contract Dependencies:** A phase may begin before the previous phase is fully completed, **provided** that the architectural contracts (interfaces, Protocols, ADRs) it depends on are defined, documented, and stable.
3. **Early Persistence:** Persistence is not a final feature. Minimum viable persistence (schema, JSON serialization, repository pattern) must be established from the foundation to prevent architectural rework.
4. **Testable at Every Step:** Every phase ships with its own test suite. The `LayoutBuilder` (pure logic) is tested without Qt. The `LayoutRenderer` is tested with `pytest-qt`. The Domain is tested with pure Python.
5. **Reversible Decisions:** If an architectural decision proves wrong during implementation, it must be caught early and changed without rewriting the entire system.

---

## 3. External Dependencies & Tech Stack

- **Language:** Python 3.12+
- **UI Framework:** PySide6 (Qt 6)
- **3D/Medical Visualization:** VTK, ITK
- **DICOM Parsing:** PyDicom
- **Geometric Modeling:** Open CASCADE (OCCT), CGAL
- **Scientific Computing:** NumPy, SciPy, Numba
- **Persistence:** JSON (Project files, Layout, Scene), SQLite (Professional Module)
- **Testing:** `pytest`, `pytest-qt`, `pytest-benchmark`, `hypothesis`
- **Tooling:** `uv`, `ruff`, `mypy`

---

## 4. Phase Overview

The implementation is divided into 11 phases. These phases are designed to build the *platform* progressively.

| Phase | Name | Status | Done / Pending |
|---|---|---|---|
| **Phase 0** | Foundation & Boot | ✅ Implemented | — |
| **Phase 1** | Contracts & Core Domain | ✅ Implemented / 🚧 débito de `EditorContext` | `task_manager`, `telemetry`, `correlation_id` existem no dataclass mas não são propagados |
| **Phase 2** | Workspace | ✅ Implemented / 🚧 débito de lifecycle e geometria | `AreaWidget.refresh`, `compute_region_bounds`, `Editor.dispose`, atomicidade de `load_spec` |
| **Phase 3** | Project & Home Page | ✅ Core / 🚧 periféricos | Recent Projects, WorkflowEngine, Layout persistence |
| **Phase 4** | Scene & Visualization | 🚧 In Progress | Application layer implementada e parcialmente conectada; Scene, rendering e editores clínicos pendentes |
| **Phase 5** | Clinical Flows | ⏳ Planned | Blocked by Phase 4 and real `ModuleLoader` |
| **Phase 6** | Clinical Pipeline (MVP) | ⏳ Planned | — |
| **Phase 7** | Scientific Validation | ⏳ Planned | — |
| **Phase 8** | Scientific Product (Release 1.0) | ⏳ Planned | — |
| **Phase 9** | Extensibility (Release 2.0) | ⏳ Planned | — |
| **Phase 10**| AI and Nodes (Release 3.0) | ⏳ Planned | — |

**Legend:**
- ✅ Implemented — the deliverable is in `src/` and tested. Does not imply absence of known debt; known debt is listed in §10.
- 🚧 In Progress — a contract exists and/or a reference implementation exists, but the deliverable is not complete or not wired.
- ⏳ Planned — the phase is blocked by a prior dependency or has not started.

**Contracts layer.** ADR-0001, 0002, 0004–0012 are Accepted. ADR-0003 is **Proposed** (not Accepted) and must be reviewed before widget-library work depends on it. The contracts for Commands, Scene, Persistence, Layout, Threading, and Telemetry are defined. Phase 4 can be implemented against them.

**Application layer status.** The Application layer contracts for Commands, Tasks, Telemetry, and Events are **implemented with reference in-memory implementations and contract tests**. The `application/modules/` layer exists but the `ModuleLoader` is skeletal (no dependency resolution, no `entry_point` import, no registration of Tools/Editors/Services/Flows, ad hoc handler resolution). `BUILTIN_MANIFESTS` is empty and every built-in module is a stub.

---

## 5. Current Focus

**Phase 3 is functionally complete for its core.** The lifecycle core (`ProjectManager`, `ProjectCatalog`), the discovery UI (`HomePage`, `MainWindow`), the boot wiring, the `FlowCatalog`, the `InMemoryFlowRepository`, the `FilesystemFlowRepository` and the flow serialization are implemented and tested. The peripherals (Recent Projects, WorkflowEngine execution, Layout persistence) are deferred and do not block Phase 4.

**Phase 4 is the active phase.** Its contracts are in place, and the Application layer is implemented as contracts + reference in-memory implementations. The `QtTaskManager` is wired into the boot. The real work remaining is to **close the wiring** and **fix the Phase 2 debt** before adding the Scene and the first real Editors.

### 5.1 Immediate priorities (in order)

0. **Refactor the Workspace UI hierarchy (ADR-0013).** ✅ Resolved.
   - `View` abstraction (`ViewLayoutSpec`, `MPRView`, `Viewport3DView`).
   - `TomographyEditor` hosting the 4 Views.
   - `ViewLayoutRenderer` (synchronized 2x2 grid).
   - `AreaWidget` uses `QSplitter` instead of `QTabWidget`.
   - Toolbar inside the Editor (ADR-0002 + ADR-0013).

0.5. **Fix Startup Performance Debt.** ✅/🚧
   - ✅ **Lazy Editor Registry:** `EditorRegistry` registers reference
     strings (`cranioz.ui...:TomographyEditor`), not classes.
     `importlib.import_module` is only called in `create()`.
   - 🚧 **Async Flow Loading:** `MainWindow._populate_flow_list()`
     must be asynchronous (via `QTimer.singleShot(0, ...)` or
     `TaskManager`). The `MainWindow` constructor must not perform I/O.
   - 🚧 **Async Project Refresh:** `ProjectTable.refresh()` must be
     asynchronous. The HomePage must display "Loading..." and populate
     the table when data arrives.
   - 🚧 **Rollback in `_on_project_open_requested`:** If
     `_create_workspace()` fails, call `manager.close_project()`.

0.6. **Persistent Project Index.** ⏳ Next.
   - `infrastructure/project/project_index.py` (SQLite).
   - `ProjectCatalog` reads from the index (O(1)); reconciliation
     (disk scan) is a `Background Initialization` task.

1. **Replace remaining boot placeholders.** ✅ Resolved.
   - `QtTaskManager` (not `NoOpTaskManager`).
   - `LoggingTelemetrySink` (not `NoOpTelemetrySink`).

2. **Fix Phase 2 debt (Workspace lifecycle and geometry).** ✅ Resolved.
   - `AreaWidget.refresh`, `compute_region_bounds`, `Editor.dispose`,
     `load_spec` atomicity, `TopOverlay` following the splitter.

3. **Propagate `EditorContext`.** 🚧 Partial.
   - ✅ `task_manager`, `telemetry`, `correlation_id`,
     `command_dispatcher` propagated via `shared_context`.
   - ✅ `SceneQuery` propagated (Passo 7: `SceneProvider` +
     `SceneQueryAdapter` + `MainWindow` + `Workspace`).
   - ⏳ `EventSubscription` still pending (Passo 9 or 10).
   - ⏳ `SelectionService`, `ViewStateStore`, `EditorServices` still
     do not exist in the dataclass.

4. **Complete the Command mechanism.** 🚧 Partial.
   - ✅ `CommandExecutor` exists and is wired at boot.
   - ✅ `CommandBus`, `CommandStack`, `TransactionManager`
     implemented (in-memory reference).
   - ❌ `CommandExecutor.dispatch()` **does not publish events**
     post-commit (violates ADR-0007 §2.4).
   - ❌ `CommandExecutor` **never sets `command.compensating`**
     (the `Command` is `frozen`; undo/redo is broken in practice).
   - ❌ `undo()`/`redo()` **do not use transaction boundary**
     nor publish events.
   - ❌ No Editor/Module dispatches real Commands yet
     (all are placeholders).

5. **Complete `domain/scene/` wiring.** 🚧 Partial.
   - ✅ `Scene`, `DomainObjectStore`, `Transform`,
     `SpatialRelationship` implemented (Passo 4).
   - ✅ `SceneQueryAdapter` implements `SceneQuery` (Passo 7).
   - ✅ `SceneProvider` + `InMemorySceneProvider` (Passo 7).
   - ❌ `DomainObjectStore` **is not instantiated at boot**.
   - ❌ `ImportDicomSeriesCommand` (or similar) does not exist —
     the `Scene` never receives real objects.
   - ⏳ `FilesystemSceneProvider` deferred (Phase 4,
     Scene serialization).

6. **Implement DICOM import (Passo 8a).** ✅ Resolved.
   - ✅ `infrastructure/imaging/dicom_loader.py` (pydicom + vtkImageData).
   - ✅ `ImportDicomSeriesCommand` + `ImportDicomSeriesHandler`.
   - ✅ `DomainObjectStore` instantiated at boot and wired through
     `MainWindow` → `Workspace` → `EditorContext`.
   - ✅ First real object in the `Scene` (via integration test).
   - ⏳ UI of import (QFileDialog + button) — Passo 8e.

7. **Implement the first real Editor (VTK).** 🚧 Partial.
   - ✅ Real `MPRView` (`vtkResliceImageViewer`, axial/coronal/sagittal) — Passo 8b.
   - ✅ `TomographyEditor` resolves `VolumeData` from `DomainObjectStore` and passes to Views.
   - 🚧 Real `Viewport3DView` with volume rendering (`vtkSmartVolumeMapper`) — Passo 8c (in progress).
   - ⏳ `RenderingAdapter` (observes `Scene`, updates VTK) — Passo 9.
   - ⏳ Window/level controls in the Toolbar — Passo 8d.

8. **Implement `application/modules/` for real.** ⏳ Pending.
   - `InMemoryModuleLoader` resolves dependencies, imports
     `entry_point`, registers Tools/Editors/Services/Flows.
   - `BUILTIN_MANIFESTS` populated (Patient Module first).
   - `ModuleContext` with shared `EventBus` (not one per
     module — current bug).

### 5.2 What blocks Phase 4

No *contract* blockers remain. The ADRs (0007 Commands, 0008 Scene, 0009 Persistence, 0011 Threading, 0012 Telemetry) and the documents (`commands.md`, `scene.md`, `modules.md`) are stable. The remaining prerequisites are implementation and wiring, tracked under §5.1.

### 5.3 Deferred to later phases

- **Recent Projects** (Phase 8): read-only projection, low impact.
- **WorkflowEngine** (Phase 5): the `FlowCatalog` and the flow repository exist; execution is not implemented.
- **Layout State Persistence** (Phase 5): `layout_state.py`, `layout_io.py`, `overlay_state.py` are stubs; implementation follows ADR-0010.
- **Module-owned persisted state** (Phase 9): deferred until the first module needs it (see `modules.md` v10 §15).
- **Plugin API** (Phase 9): deferred.
- **AI/MCP** (Phase 10): deferred.

---

## 6. Phase Breakdown

### Phase 0: Foundation & Boot

**Goal:** Establish the repository, configuration, logging, minimal persistence, and boot sequence.

- **Deliverables:**
  - ✅ `pyproject.toml`, CI pipeline (GitHub Actions).
  - ✅ `ConfigurationLoader`, `AppPathResolver`.
  - ✅ `EventBus`.
  - ✅ JSON serialization for Project Metadata (in `project_serialization.py`).
  - ✅ Boot sequence (`__main__.py`) — initializes config, logging, paths, event bus, project subsystem, UI registries, theme service, and shows the `MainWindow` before entering the Qt event loop.
  - ✅ Error handling for `AppPathInaccessible` with `QMessageBox.critical`.
  - ✅ Actor resolution from the OS username (`getpass.getuser`).
  - ✅ `application/flows/` — `FlowDefinition`, `FlowStep`, `FlowSummary`, `FlowRepository`, `InMemoryFlowRepository`, `FlowCatalog`.
  - ✅ `infrastructure/flows/` — `FilesystemFlowRepository`, `FlowPathResolver`, `flow_serialization`.

- **Performance placeholders (to be resolved in Phase 3/4):**
  - 🚧 `__main__.py` imports `TomographyEditor` and `Workspace` at module level (eager import).
  - 🚧 `MainWindow.__init__` performs synchronous I/O (`_populate_flow_list`).
  - 🚧 `ProjectTable.__init__` performs synchronous I/O (`refresh`).

- **Tests:** Unit tests for config validation and path resolution; smoke test for boot-time dependency construction.

- **Status:** ✅ Implemented with documented boot placeholders.

### Phase 1: Contracts & Core Domain

**Goal:** Define the fundamental contracts and the initial Domain models, plus minimum persistence.

- **Deliverables:**
  - ✅ `Patient` Domain (9 section value objects, 6 enums, 2 value objects, aggregate root with cross-section invariants).
  - ✅ `Project` Domain (`Project`, `ProjectId`, `ProjectMetadata`, `ProjectStatus`, `ProjectSummary`).
  - ✅ UI Contracts (`Area`, `Editor`, `EditorRegistry`, `ToolbarSpec`, `ToolSpec`, `LayoutBuilder`, `LayoutRenderer`).
  - ✅ `ProjectRepository` (Protocol), `InMemoryProjectRepository`, `FilesystemProjectRepository`.
  - ✅ `ProjectContext` (frozen, data-only; no service locator).
  - ✅ `ProjectAccessPolicy` (Protocol), `AllowAllProjectAccessPolicy`.
  - ✅ `ProjectCatalog` (read-only projection, no cache).
  - ✅ ADRs 0001, 0002, 0004–0012 written and Accepted.
  - 🚧 ADR-0003 is **Proposed**, not Accepted.
  - 🚧 `EditorContext` fields `task_manager`, `telemetry` and `correlation_id` exist in the dataclass but are not propagated by `LayoutBuilder` or `Workspace`.

- **Tests:** Domain unit tests (pure Python), contract tests for `ProjectRepository`, JSON serialization round-trips for Project.

- **Status:** ✅ Core implemented. 🚧 EditorContext hybrid propagation pending.

### Phase 2: Workspace Engine

**Goal:** Build the UI layout system that dynamically materializes modules.

- **Deliverables:**
  - ✅ `LayoutTree` (N-ary split tree), `AreaManager`.
  - ✅ `LayoutBuilder` (pure Python, no Qt), `LayoutRenderer` (Qt materialization).
  - ✅ `EditorRegistry`, `EditorContext` (hybrid model declared in ADR-0002; propagation pending).
  - ✅ `TopOverlay` (the structural Top Bar, materialized as a floating Overlay, ADR-0005).
  - ✅ `OverlayManager`.
  - ✅ `Workspace` facade coordinating builder, renderer, and overlays.
  - 🚧 Known debt (see §10): `AreaWidget.refresh` can invalidate Editor content; `compute_region_bounds` uses parent-relative geometry; `Workspace.clear` does not call `Editor.dispose()`; `load_spec` is not atomic.

- **Tests:** `pytest-qt` for rendering; unit tests for `LayoutTree`, `Area`, `AreaManager`, `EditorRegistry`; integration tests for `Workspace`.

- **Status:** ✅ Implemented with documented debt.

### Phase 3: Project & Home Page

**Goal:** Implement the project lifecycle, discovery UI, and project persistence.

- **Deliverables:**
  - ✅ `ProjectManager` (single authority for lifecycle, publishes events, honors access policy).
  - ✅ `ProjectCatalog` (read model, delegates to `ProjectRepository`).
  - ✅ `HomePage` UI (`ProjectTable`, `FlowList`, `StartButton`, `CommunitySidebar`, `HomeTopBar`, `HomeBottomBar`).
  - ✅ `MainWindow` (navigation Home ↔ Workspace, ADR-0006).
  - ✅ `ProjectTable` selection lifecycle (emit `None` on deselection, preserve selection on refresh).
  - ✅ `FlowCatalog`, `FlowRepository`, `InMemoryFlowRepository`, `FilesystemFlowRepository`, `flow_serialization`.
  - ✅ `MainWindow` populates the `FlowList` from the `FlowCatalog` at boot (via `_populate_flow_list`).
  - 🚧 Recent Projects — not implemented (deferred to Phase 8).
  - 🚧 `FlowList` real population depends on the `FilesystemFlowRepository` having `flow.json` files on disk; seeding is done by `scripts/seed_flows.py`.
  - ⏳ WorkflowEngine execution (Phase 5).
  - ⏳ Layout State Persistence — `layout_state.py`, `layout_io.py`, `overlay_state.py` are stubs (ADR-0010 defines the contract; implementation in Phase 5).

- **Tests:** Full suite passing, including regression tests for `ProjectTable` and `HomePage` deselection, `FlowCatalog` and `FilesystemFlowRepository`.

- **Status:** ✅ Core implemented. 🚧 Peripherals deferred.

- **Startup Performance (mandatory for Phase 3 "Done"):**
  - 🚧 `EditorRegistry` with lazy resolution (importlib).
  - 🚧 `MainWindow` without I/O in its constructor.
  - 🚧 `ProjectTable` with asynchronous loading.
  - 🚧 Rollback in `_on_project_open_requested`.
  - 🚧 `ProjectIndex` (SQLite) for O(1) project listing.

### Phase 4: Scene & Visualization

**Goal:** Introduce the 3D/2D visualization layer and the spatial domain.

- **Contracts ready:**
  - ✅ ADR-0007 (Commands, Transactions, Undo/Redo).
  - ✅ ADR-0008 (Scene and DomainObjectStore).
  - ✅ ADR-0009 (Project Persistence Format).
  - ✅ ADR-0011 (Threading and Task Execution).
  - ✅ ADR-0012 (Telemetry and Observability).
  - ✅ `commands.md`, `scene.md`, `modules.md` v10.

- **Application layer (implemented, with reference in-memory implementations and contract tests):**
  - ✅ `application/commands/` — `Command`, `CommandHandler`, `CommandBus`, `InMemoryCommandBus`, `CommandStack`, `InMemoryCommandStack`.
  - ✅ `application/tasks/` — `Task`, `TaskHandle`, `TaskManager`, `CancelToken`, `TaskState`, `NoOpTaskManager`.
  - ✅ `application/telemetry/` — `TelemetrySink`, `Severity`, `MeasurementUnit`, `NoOpTelemetrySink`, `RecordingTelemetrySink`.
  - ✅ `application/events/` — `EventSubscription`, `EventPublisher`, `SubscriptionHandle`, `EventBusAdapter`, `SubscriptionClosed`.

- **Application layer (partial or pending):**
  - 🚧 `application/modules/` — `Module`, `ModuleBase`, `ModuleManifest`, `ModuleContext`, `ModuleRegistry`, `ModuleLoader` exist, but `InMemoryModuleLoader` does not resolve dependencies, does not import `entry_point`, does not register Tools/Editors/Services/Flows, and resolves handlers via an ad hoc `_handler` attribute. `BUILTIN_MANIFESTS` is empty; every built-in module is a stub.
  - ⏳ `CommandExecutor` — ties transaction boundary, post-commit event publication, `CommandStack` and `CommandBus`. Not implemented.
  - ⏳ `CommandDispatcher` — the interface used by Editors/Tools to dispatch Commands. Not wired.

- **Domain / infrastructure / UI (partial):**
  - ✅ `domain/scene/` — `Scene`, `DomainObjectStore`, `Transform`, `SpatialRelationship`.
  - ✅ `infrastructure/imaging/` — `dicom_loader.py` (pydicom + vtkImageData).
  - ✅ `application/scene/` — `SceneProvider`, `InMemorySceneProvider`, `SceneQueryAdapter`, `ImportDicomSeriesCommand` + handler.
  - ✅ `ui/editors/mpr_viewer/` — real `MPRView` (`vtkResliceImageViewer`).
  - 🚧 `ui/editors/viewport_3d/` — `Viewport3DView` com `vtkOutlineFilter` (volume rendering em 8c).
  - ⏳ `infrastructure/rendering/` — `RenderingAdapter` (observes `Scene`, updates VTK).
  - ⏳ Scene serialization (JSON).

- **Boot wiring (partial):**
  - ✅ `QtTaskManager` substituiu `NoOpTaskManager`.
  - ✅ `LoggingTelemetrySink` substituiu `NoOpTelemetrySink`.
  - ✅ `SceneProvider` + `InMemorySceneProvider` no boot (Passo 7).
  - ✅ `DomainObjectStore` no boot (Passo 8a).
  - ⏳ Propagate `SceneQuery` and `EventSubscription` to `EditorContext` — `SceneQuery` ✅, `EventSubscription` ⏳ (Passo 9).
  - ⏳ `BUILTIN_MANIFESTS` + `InMemoryModuleLoader` real (Passo 10).

- **Blockers:** No contract blockers. Implementation and wiring blockers tracked in §5.1.

- **Tests:** Headless VTK tests, spatial transform tests, performance tests (Scene update, upload to GPU, rendering FPS on reference hardware).

- **Status:** 🚧 In Progress. Application layer implemented; Scene, rendering, editors and real boot wiring pending.

### Phase 5: Clinical Flows

**Goal:** Implement the workflow engine and the shared navigation panel.

- **Deliverables:**
  - ⏳ `WorkflowEngine` (loads JSON, evaluates requirements, computes step states).
  - ⏳ `steps_panel` (Workspace Overlay).
  - ⏳ Flow state persistence.
  - ✅ Flow Catalog (`FlowCatalog`, `FlowRepository`, `InMemoryFlowRepository`, `FilesystemFlowRepository`) — the loader exists and populates the `FlowList`.
  - ⏳ Layout State Persistence (`layout_state.py`, `layout_io.py`, `overlay_state.py`) — per ADR-0010.
  - ⏳ Real `ModuleRegistry`/`ModuleLoader` wire-up of `application/modules/` into `__main__`.

- **Blockers:** Depends on Phase 4 (Scene is a requirement of most flows) and on the real module loader.

- **Tests:** State transition tests (pending, active, blocked, completed), requirement evaluation.

- **Status:** ⏳ Planned (Flow Catalog portion ✅).

### Phase 6: Clinical Pipeline

**Goal:** Build the specific clinical tools required for the orthognathic workflow.

This phase is divided into sub-phases to accurately measure scientific progress:

- **Phase 6A — Tomography & Segmentation:** DICOM import, MPR, thresholding, mask painting.
- **Phase 6B — Registration & Cephalometry:** Alignment, cephalometric landmark acquisition.
- **Phase 6C — Osteotomy:** Le Fort I, BSSO, boolean operations.
- **Phase 6D — Surgical Guides:** Parametric guide generation.
- **Phase 6E — Integrated Validation:** End-to-end flow testing.

- **Tests:** Geometric validation (RMSE < 0.3 mm), topological validation (0 non-manifold edges).

- **Status:** ⏳ Planned.

### Phase 7: Scientific Validation

**Goal:** Execute the validation protocols defined in the project.

- **Deliverables:**
  - Geometric validation reports (phantoms, ground-truth).
  - Reproducibility studies (ICC > 0.85).
  - Usability reports (SUS > 70).
  - Documentation of the validation methodology.

- **Tests:** Automated scripts generating validation datasets and metrics.

- **Status:** ⏳ Planned.

### Phase 8: Scientific Product (Release 1.0)

**Goal:** Consolidate the platform as a stable, distributable scientific product.

- **Deliverables:**
  - Windows 11 Installer.
  - Autosave and crash recovery.
  - PDF Report generation.
  - Final user documentation and developer SDK documentation.
  - Scientific publication and DOI registration.
  - Recent Projects on the Home Page (§11 of `home_page.md`).

- **Tests:** Full regression suite, performance profiling on reference hardware.

- **Status:** ⏳ Planned.

### Phase 9: Extensibility (Release 2.0)

**Goal:** Open the platform for community contribution.

- **Deliverables:**
  - Module API and Plugin API.
  - Plugin loader and sandbox.
  - External plugin catalog.
  - Module-owned persisted state and its migration contract (per `modules.md` v10 §15).

- **Tests:** Plugin compatibility tests.

- **Status:** ⏳ Planned.

### Phase 10: AI and Nodes (Release 3.0)

**Goal:** Advanced automation and procedural workflows.

- **Deliverables:**
  - Node System (non-destructive graph).
  - AI Assistant (`AIAssistantEditor`).
  - MCP Server integration.

- **Tests:** AI command execution parity with human UI, graph evaluation tests.

- **Status:** ⏳ Planned.

---

## 7. Testing Strategy & Metrics

Testing is a clinical requirement. Metrics must be contextualized to avoid false positives or hardware dependencies.

### 7.1 Coverage Metrics

- **Domain Layer:** High coverage of critical business rules, with 100% of invariants and relevant error cases tested.
- **Application Layer:** Critical command paths and transaction rollbacks tested; contract tests for every Protocol (`ProjectRepository`, `CommandBus`, `TaskManager`, `TelemetrySink`, `ModuleRegistry`, `ModuleLoader`). Contract tests for `CommandBus`, `CommandStack`, `EventSubscription`/`EventPublisher`, `TaskManager`, `TelemetrySink`, `ModuleRegistry` and `ModuleLoader` are implemented against reference in-memory implementations.
- **UI Layer:** 80% coverage of `ui/workspace/`.

### 7.2 Performance Metrics (Reference Hardware)
All performance metrics must be measured against a defined **Reference Dataset** and **Reference Hardware**.


- **DICOM Import:** Load a reference dataset of 500 slices in < 10 seconds (including indexing and readiness for first visualization).
- **Rendering:** 30+ FPS for a mesh of 1,000,000 polygons.
  - *Metrics separated into:* Scene update time, GPU upload time, render time.
- **Memory:** < 4 GB RAM during standard facial CT processing.

### 7.3 GPU vs. CPU

- **Correction:** Semantic clinical data belongs to main memory (RAM) and the Domain `Scene`.
- The GPU should only hold **renderable representations** (VTK actors, shaders).
- Use caches and incremental transfer to reduce copies. Do not keep the entire clinical dataset on the GPU.

### 7.4 Concurrency

- **Correction:** `QTimer` is for UI scheduling, not asynchronous execution.
- **TaskManager:** Application layer abstraction for tasks (ADR-0011). `NoOpTaskManager` is a reference synchronous implementation for tests; `QtTaskManager` is the production implementation and is pending.
- **Execution:** Heavy CPU-bound tasks must use `QThreadPool`/`QtConcurrent` or `ProcessPool` (for GIL-independent execution), coordinated by the `TaskManager`.
- **Telemetry:** Every long operation must emit `task.dispatch`, `task.complete`, `task.cancel`, or `task.failure` through the `TelemetrySink` with a correlation id (ADR-0012). `NoOpTelemetrySink` is the test sink; `LoggingTelemetrySink` is the production sink and is pending.

---

## 8. Release Criteria (Definition of Done)

A phase is "Done" when:

1. Code is implemented according to the architecture documents.
2. Unit, Widget, and Integration tests are written and passing.
3. Contract tests for every new Protocol exist (a reference in-memory implementation + the same suite for the concrete adapter).
4. The CI pipeline is green.
5. Documentation is updated (including ADRs if a new decision was made).
6. **The feature is usable end-to-end by the UI (no orphaned backend code).**
7. No `TODO` comments are left without a linked GitHub Issue.
8. **No production `NoOp*` placeholders remain in the boot path for a service that the phase claims to deliver.**
9. **Known debt that affects the phase is either fixed or recorded in §10 with a linked issue.**

### 8.1 The Deliverable (Release 1.0)

The concludes with the delivery of the validated clinical core. It **does not** include Plugins, Nodes, AI/MCP, or multi-monitor support. These are explicitly deferred to Releases 2.0 and 3.0, demonstrating the platform's long-term vision and extensibility without compromising the thesis deadline.

---

## 9. Summary

The architectural foundation is in place, and the Application layer is now **implemented as contracts plus reference in-memory implementations**, with contract tests. The next milestone is not "implement the Application layer"; it is **to close the wiring** — replace boot placeholders with real services, propagate `EditorContext` to Editors, implement `CommandExecutor`, and fix the Phase 2 debt — before adding `Scene`, rendering, and clinical Editors.

Phases 0, 1, 2 and 3 are functionally complete for their core, with documented debt. Phase 4 is in progress: the Application layer is done; `domain/scene/`, `infrastructure/rendering/`, `ui/editors/`, the real `ModuleLoader`, and the real boot wiring remain. Phase 5 (Clinical Flows) depends on Phase 4 and on the real module loader. Phases 6–10 are planned.

**Post Application layer:** The contracts for Commands, Tasks, Telemetry, Events and Flows are implemented and tested. The contracts for Scene, Persistence, Layout, Threading and Telemetry (behavioral) are in place. The next implementation steps are: real boot services, `EditorContext` propagation, `CommandExecutor`, `domain/scene/`, `infrastructure/rendering/`, and the first concrete Editors.

---

## 10. Known Debt

This section records debt that is known, accepted for now, and must be resolved (or explicitly deferred with a linked issue) before the phase that depends on it can be declared "done". Each item is a candidate for a GitHub Issue.

### 10.1 Phase 2 — Workspace lifecycle and geometry

- ✅ **`AreaWidget.refresh()` no longer invalidates Editor content.**
- ✅ **`LayoutRenderer.compute_region_bounds()` now maps to Workspace coordinates.**
- ✅ **`Workspace.clear()` now calls `Editor.dispose()` and `clear_cache()`.**
- ✅ **`Workspace.load_spec()` is now atomic.**
- ✅ **`TopOverlay` follows the splitter when moved manually.**
- ✅ **`QTabBar` is centered via stylesheet.**
- ✅ **Debug visual is clean** (no Log/Toggle buttons, editor_ids visible).

### 10.2 Phase 1 / Phase 4 — `EditorContext` propagation

- ✅ **`LayoutBuilder` propagates `shared_context`.** ADR-0002 §2.3 defines `shared_context` as the extension point for shared services. The builder now propagates `task_manager`, `telemetry`, `correlation_id` and `command_dispatcher` by reference into each `EditorContext`.
- ✅ **`EditorContext` fields `task_manager`, `telemetry`, `correlation_id` and `command_dispatcher` are populated.** The `Workspace` provides them via `shared_context`; the `LayoutBuilder` propagates them; the `Editor` consumes them.
- **`EditorContext` has no `SceneQuery` or `EventSubscription`.** These are defined in ADR-0002 and `editors.md` §15 but are not yet fields on the dataclass. `SceneQuery` is the next prerequisite for the VTK/MPR Views.

### 10.3 Phase 4 — Module system

- **`InMemoryModuleLoader` is skeletal.** (unchanged)
- **`BUILTIN_MANIFESTS` is empty.** (unchanged)
- **`InMemoryModuleLoader` creates a new `EventBus` per `ModuleContext`.** (unchanged)
- **No `CommandExecutor`.** (unchanged — this is the next priority, §5.1 item 4).

### 10.4 Phase 3 — Project deletion

- **`FilesystemProjectRepository.delete()` removes only `project.json`.** Other files (`patient_record.json`, `assets/`, `scene.json`, `layout.json`, `backups/`) belong to other owners and are left orphaned. Deleting a project must coordinate with the owners of each file (ADR-0009 §2.1), or the repository must document that it only deletes its own file and that higher layers coordinate the rest. Today neither is documented in code.

### 10.5 Phase 1 / Phase 4 — ADR-0003

- **ADR-0003 is `Proposed`, not `Accepted`.** The document `implementation.md` previously stated that ADRs 0001–0012 were all stable. They are not: ADR-0003 (widgets, overlays, icon actions, semantic colors) is still Proposed. Widget-library work and semantic-color work depend on it; it must be reviewed and accepted (or revised) before those deliverables start.

### 10.6 Cross-cutting — i18n and theme

- **UI strings and colors are hardcoded.** `HomePage`, `ProjectTable`, `FlowList`, `StartButton`, `FlowRow` use Portuguese strings and hardcoded colors, contrary to the i18n documentation and ADR-0003 §2.4 (semantic colors via `ThemeService.color()`). `TranslationService` exists but is not wired into the UI; `ThemeService` does not yet expose semantic colors. This is not a Phase 4 blocker, but it must be resolved before Release 1.0 (§8.1).

### 10.7 Documentation

- **`docs/architecture/README.md` contains an accidental PowerShell command** instead of Markdown.
- **`docs/architecture/domain/project/project.md` ends with an accidental Python file-write snippet.**
- **Some documents still reference `EditorHost`**, which ADR-0001 removed.
- **The main `README.md` is empty.**
- **i18n test files are empty** (`tests/infrastructure/i18n/`).

### 10.8 New debt discovered during analysis (2026-10-29)

- **UI Modules and Widgets are Stubs.** The directories `ui/widgets/` (except for empty subfolders), `ui/editors/overlays/`, and most of `modules/builtin/` contain only empty or placeholder files. They represent the *intent* to build these components but do not contain functional code.
- **`TranslationService` not wired to UI.** The `TranslationService` and its catalogs exist, but the UI layer (e.g., `HomePage`, `FlowRow`) uses hardcoded strings. The i18n infrastructure is not actually in use.
- **`ThemeService` lacks semantic colors.** The `ThemeService` resolves icon names but does not yet expose the semantic colors (`color("active")`, `color("disabled")`, etc.) required by ADR-0003. The UI uses hardcoded hex values.
- **`Project deletion` not coordinated.** As noted in §10.4, deleting a project only removes `project.json`. The `ProjectManager` must coordinate with other persistence layers (Patient, Scene, Layout) to perform a full, atomic deletion.
- **`Filesystem repositories` need integration tests.** The `FilesystemProjectRepository` and `FilesystemFlowRepository` have unit tests, but their integration with the real filesystem (permissions, atomic writes, directory traversal) needs more thorough testing.
- **`HomePage` uses `_humanize_translation_key`.** `MainWindow` uses a temporary helper function `_humanize_translation_key` to make flow names readable. This is a placeholder for the `TranslationService` and should be removed once i18n is wired.
- ✅ **`MPRView` is now backed by `vtkResliceImageViewer`.** (Passo 8b)   Axial, coronal, and sagittal orientations are supported. The View
  receives a `vtkImageData` via `set_volume()` from the   `TomographyEditor`.
- 🚧 **`Viewport3DView` uses `vtkOutlineFilter`.** (Passo 8b)   Volume rendering (`vtkSmartVolumeMapper` + presets) is planned for
  Passo 8c. Window/level controls are planned for Passo 8d.
- 
### 10.9 Phase 0 / Phase 3 — Startup Performance Debt

- **Eager import of `TomographyEditor` and `Workspace` in `__main__.py`.**
  The `EditorRegistry` must use reference strings (see §5.1 item 0.5).
- **Synchronous I/O in `MainWindow.__init__`.** `_populate_flow_list`
  must be asynchronous.
- **Synchronous I/O in `ProjectTable.__init__`.** `refresh` must be
  asynchronous or use `ProjectIndex`.
- **Missing rollback in `_on_project_open_requested`.** If the
  `Workspace` fails, the project remains open in the `ProjectManager`.
- **Missing `ProjectIndex`.** The HomePage scans the entire disk
  on every launch.

### 10.10 Phase 4 — Volume rendering and window/level

- **Volume rendering is not implemented.** `Viewport3DView` uses   `vtkOutlineFilter` (bounding box) as a placeholder. The real
  rendering (`vtkSmartVolumeMapper` + presets) is Passo 8c.
- **Window/level controls are not exposed.** `set_window_level()` in   `Viewport3DView` stores the values but does not apply them to the
  transfer function; the MPR `set_window_level` is applied directly.
  UI controls are Passo 8d.
- **Preset editor and import/export are deferred.** The 4 built-in   presets (`bone`, `soft_tissue`, `skin`, `ct_angio`) are hardcoded
  in `presets.py`. Custom presets, editor, and serialization are   Phase 8.