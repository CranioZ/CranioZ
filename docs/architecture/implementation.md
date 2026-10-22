# Implementation Plan

**Document type:** Roadmap and execution plan
**Status:** Living document
**Scope:** Phased implementation of the CranioZ platform from foundation to release.
**Last updated:** 2026-10-22

---

## 1. Purpose

This document defines the **execution strategy** for building the CranioZ platform. It translates the architectural decisions (ADRs), the domain contracts, and the clinical requirements into a sequenced, testable, and iterative implementation plan.

Its primary goal is to serve as a scientific, technical, and managerial instrument, distinguishing between the strict scope of the PhD research and the long-term evolution of the open-source platform.

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

The implementation is divided into 11 phases. These phases are designed to build the *platform* progressively, ensuring the PhD delivers a validated clinical core.

| Phase | Name | Status | Done / Pending |
|---|---|---|---|
| **Phase 0** | Foundation & Boot | ✅ Implemented | Boot wiring to MainWindow pending (Phase 3 dependency) |
| **Phase 1** | Contracts & Core | ✅ Implemented | — |
| **Phase 2** | Workspace | ✅ Implemented | — |
| **Phase 3** | Project & Home Page | 🚧 In Progress | Core done; Recent Projects, Flow Catalog, Layout persistence pending |
| **Phase 4** | Scene & Visualization | ⏳ Next | Blocked by: Commands, Scene domain, ADRs |
| **Phase 5** | Clinical Flows | ⏳ Planned | Blocked by: Phase 4, `modules.md`, Flow Catalog |
| **Phase 6** | Clinical Pipeline (MVP) | ⏳ Planned | — |
| **Phase 7** | Scientific Validation | ⏳ Planned | — |
| **Phase 8** | Scientific Product (Release 1.0) | ⏳ Planned | — |
| **Phase 9** | Extensibility (Release 2.0) | ⏳ Planned | — |
| **Phase 10**| AI and Nodes (Release 3.0) | ⏳ Planned | — |

**Legend:**
- ✅ Implemented — all deliverables of the phase are in `src/` and tested.
- 🚧 In Progress — the core of the phase is in `src/`, but documented deliverables are still missing.
- ⏳ Next — the phase is unblocked and is the next to start.
- ⏳ Planned — the phase is blocked by a prior dependency or by an ADR that has not been written.

---

## 5. Current Focus

**Phase 3 is the active phase.** The lifecycle core (`ProjectManager`, `ProjectCatalog`) and the discovery UI (`HomePage`, `MainWindow`) are implemented and tested. The remaining work is peripheral and does not block Phase 4.

### 5.1 Immediate priorities (in order)

1. **Boot wiring.** Connect `__main__.py` to `MainWindow`. Today the application initializes configuration, logging, paths and the `EventBus`, but calls `app.exec()` without showing a window. This is the highest-value missing piece — it makes the application usable end-to-end.
2. **Documentation synchronization.** Update `implementation.md` (this document), `home_page.md` §25, `project.md` §17, and `startup_project_opening_workflow.md` §9 to match the code. Several documents still describe `service_locator` in `ProjectContext`, `EditorHost`, and `Main Toolbar`, all of which were rejected by ADRs.
3. **Missing ADRs.** Write the ADRs that block Phase 4: `project-persistence-format`, `project-catalog-synchronization`, `commands`, `scene`, `layout-persistence`.
4. **Flow Catalog (Bloco 9).** Implement the flow definition loader and populate the `HomePage`'s `FlowList`. Depends on `modules.md` (currently empty).
5. **Layout State Persistence.** Persist `LayoutState` and `OverlayState` per `(project_id, module_id)`. Depends on the `layout-persistence` ADR.
6. **Recent Projects (§11 of `home_page.md`).** Add a recent-projects section to the `HomePage`. Low priority; can be deferred to Phase 8.

### 5.2 What blocks Phase 4

Before Phase 4 (Scene & Visualization) can begin, three prerequisites must exist:

1. **Command mechanism** (`application/commands/`) — `commands.md` specifies the contract, but no code exists. The Scene cannot be mutated without Commands.
2. **Scene domain** (`domain/scene/`) — `scene.md` specifies the contract, but no code exists.
3. **ADRs** for `commands`, `scene`, and `project-persistence-format` — these decisions are cited in `project.md` and `scene.md` but have not been written.

---

## 6. Phase Breakdown

### Phase 0: Foundation & Boot

**Goal:** Establish the repository, configuration, logging, minimal persistence, and boot sequence.

- **Deliverables:**
  - ✅ `pyproject.toml`, CI pipeline (GitHub Actions), `README.md`.
  - ✅ `ConfigurationLoader`, `AppPathResolver`.
  - ✅ `EventBus`.
  - ✅ JSON serialization for Project Metadata (in `project_serialization.py`).
  - 🚧 Boot sequence (`__main__.py`) — initializes config, logging, paths, and the event bus, but does not yet create or show the `MainWindow`. **Pending.**
  - ⏳ Minimal `Command`/`EventHandler` contracts — referenced in `commands.md` but not implemented.

- **Tests:** Unit tests for config validation and path resolution.

- **Status:** ✅ Implemented for all deliverables except the boot-to-window wiring, which is tracked under Phase 3.

### Phase 1: Contracts & Core Domain

**Goal:** Define the fundamental contracts and the initial Domain models, plus minimum persistence.

- **Deliverables:**
  - ✅ `Patient` Domain (9 section value objects, 6 enums, 2 value objects, aggregate root with cross-section invariants).
  - ✅ `Project` Domain (`Project`, `ProjectId`, `ProjectMetadata`, `ProjectStatus`, `ProjectSummary`).
  - ✅ UI Contracts (`Area`, `Editor`, `EditorRegistry`, `EditorContext`, `ToolbarSpec`, `ToolSpec`, `LayoutBuilder`, `LayoutRenderer`).
  - ✅ `ProjectRepository` (Protocol), `InMemoryProjectRepository`, `FilesystemProjectRepository`.
  - ✅ `ProjectContext` (frozen, data-only; no service locator).
  - ✅ `ProjectAccessPolicy` (Protocol), `AllowAllProjectAccessPolicy`.
  - ✅ `ProjectCatalog` (read-only projection, no cache).

- **Tests:** Domain unit tests (pure Python), contract tests for `ProjectRepository`, JSON serialization round-trips for Project.

- **Status:** ✅ Implemented.

### Phase 2: Workspace Engine

**Goal:** Build the UI layout system that dynamically materializes modules.

- **Deliverables:**
  - ✅ `LayoutTree` (N-ary split tree), `AreaManager`.
  - ✅ `LayoutBuilder` (pure Python, no Qt), `LayoutRenderer` (Qt materialization).
  - ✅ `EditorRegistry`, `EditorContext` (hybrid model, ADR-0002).
  - ✅ `TopOverlay` (the structural Top Bar, materialized as a floating Overlay, ADR-0005).
  - ✅ `OverlayManager`.
  - ✅ `Workspace` facade coordinating builder, renderer, and overlays.

- **Tests:** `pytest-qt` for rendering; unit tests for `LayoutTree`, `Area`, `AreaManager`, `EditorRegistry`; integration tests for `Workspace`.

- **Status:** ✅ Implemented.

### Phase 3: Project & Home Page

**Goal:** Implement the project lifecycle, discovery UI, and project persistence.

- **Deliverables:**
  - ✅ `ProjectManager` (single authority for lifecycle, publishes events, honors access policy).
  - ✅ `ProjectCatalog` (read model, delegates to `ProjectRepository`).
  - ✅ `HomePage` UI (`ProjectTable`, `FlowList`, `StartButton`, `CommunitySidebar`, `HomeTopBar`, `HomeBottomBar`).
  - ✅ `MainWindow` (navigation Home ↔ Workspace, ADR-0006).
  - 🚧 Recent Projects — not implemented.
  - 🚧 Flow Catalog — `FlowList` exists but is populated only by tests and debug scripts; the real catalog depends on Bloco 9.
  - ⏳ Layout State Persistence — `layout_state.py`, `layout_io.py`, `overlay_state.py` are stubs.

- **Tests:** Project lifecycle tests (77 tests across `test_project_manager.py`, `test_project_catalog.py`, `test_home_page.py`, `test_project_table.py`, `test_main_window.py`).

- **Status:** 🚧 In Progress. Core is done; peripherals are pending.

### Phase 4: Scene & Visualization

**Goal:** Introduce the 3D/2D visualization layer and the spatial domain.

- **Deliverables:**
  - ⏳ Domain `Scene` (coordinate system, spatial hierarchy, membership).
  - ⏳ `DomainObjectStore`.
  - ⏳ Command mechanism (`Command`, `CommandBus`, `CommandHandler`, `CommandStack`).
  - ⏳ `RenderingAdapter` (bridges Scene events to VTK).
  - ⏳ `Viewport3DEditor` and `MPRViewerEditor`.
  - ⏳ `TaskManager` abstraction for async operations.
  - ⏳ Scene serialization (JSON).

- **Blockers:** No code exists. Requires ADRs for `commands` and `scene`, and the `project-persistence-format` ADR for serialization.

- **Tests:** Headless VTK tests, spatial transform tests, performance tests (Scene update, upload to GPU, rendering FPS on reference hardware).

- **Status:** ⏳ Next (blocked).

### Phase 5: Clinical Flows

**Goal:** Implement the workflow engine and the shared navigation panel.

- **Deliverables:**
  - ⏳ `WorkflowEngine` (loads JSON, evaluates requirements, computes step states).
  - ⏳ `steps_panel` (Workspace Overlay).
  - ⏳ Flow state persistence.
  - ⏳ `modules.md` — the Module contract (currently empty).
  - ⏳ `ModuleRegistry`, `ModuleLoader` (currently stubs in `src/cranioz/modules/`).

- **Blockers:** Depends on Phase 4 (Scene is a requirement of most flows) and on `modules.md`.

- **Tests:** State transition tests (pending, active, blocked, completed), requirement evaluation.

- **Status:** ⏳ Planned (blocked).

### Phase 6: Clinical Pipeline (PhD MVP)

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

**Goal:** Execute the validation protocols defined in the PhD project.

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

- **Tests:** Full regression suite, performance profiling on reference hardware.

- **Status:** ⏳ Planned.

### Phase 9: Extensibility (Release 2.0)

**Goal:** Open the platform for community contribution.

- **Deliverables:**
  - Module API and Plugin API.
  - Plugin loader and sandbox.
  - External plugin catalog.

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
- **Application Layer:** Critical command paths and transaction rollbacks tested.
- **UI Layer:** 80% coverage of `ui/workspace/`.

### 7.2 Performance Metrics (Reference Hardware)

All performance metrics must be measured against a defined **Reference Dataset** and **Reference Hardware** (e.g., the workstations specified in the PhD infrastructure plan).

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
- **TaskManager:** Application layer abstraction for tasks.
- **Execution:** Heavy CPU-bound tasks must use `QThreadPool`/`QtConcurrent` or `ProcessPool` (for GIL-independent execution), coordinated by the `TaskManager`.

---

## 8. Release Criteria (Definition of Done)

A phase is "Done" when:

1. Code is implemented according to the architecture documents.
2. Unit, Widget, and Integration tests are written and passing.
3. The CI pipeline is green.
4. Documentation is updated (including ADRs if a new decision was made).
5. The feature is usable end-to-end by the UI (no orphaned backend code).
6. No `TODO` comments are left without a linked GitHub Issue.

### 8.1 The PhD Deliverable (Release 1.0)

The PhD concludes with the delivery of the validated clinical core. It **does not** include Plugins, Nodes, AI/MCP, or multi-monitor support. These are explicitly deferred to Releases 2.0 and 3.0, demonstrating the platform's long-term vision and extensibility without compromising the thesis deadline.

---

## 9. Summary

By following this roadmap, the CranioZ project ensures that the architectural foundation (Workspace, Commands, Scene) is built correctly before the heavy clinical lifting begins. It respects the scientific validation timelines, protects the PhD scope from feature creep, and establishes a clear path for post-doctoral open-source evolution.