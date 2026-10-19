# Implementation Plan

**Document type:** Roadmap and execution plan
**Status:** Living document
**Scope:** Phased implementation of the CranioZ platform from foundation to release.

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

| Phase | Name | Status |
|---|---|---|
| **Phase 0** | Foundation & Boot | ✅ Implemented |
| **Phase 1** | Contracts & Core | 🚧 In Progress |
| **Phase 2** | Workspace | ✅ Implemented |
| **Phase 3** | Project & Home Page | ⏳ Next |
| **Phase 4** | Scene & Visualization | ⏳ Planned |
| **Phase 5** | Clinical Flows | ⏳ Planned |
| **Phase 6** | Clinical Pipeline (MVP) | ⏳ Planned |
| **Phase 7** | Scientific Validation | ⏳ Planned |
| **Phase 8** | Scientific Product (Release 1.0) | ⏳ Planned |
| **Phase 9** | Extensibility (Release 2.0) | ⏳ Planned |
| **Phase 10**| AI and Nodes (Release 3.0) | ⏳ Planned |

---

## 5. Phase Breakdown

### Phase 0: Foundation & Boot
**Goal:** Establish the repository, configuration, logging, minimal persistence, and boot sequence.
- **Deliverables:**
  - `pyproject.toml`, CI pipeline (GitHub Actions), `README.md`.
  - `ConfigurationLoader`, `AppPathResolver`.
  - `EventBus`, minimal `Command`/`EventHandler` contracts.
  - JSON Schema for Project Metadata.
- **Tests:** Unit tests for config validation and path resolution.

### Phase 1: Contracts & Core Domain
**Goal:** Define the fundamental contracts and the initial Domain models, plus minimum persistence.
- **Deliverables:**
  - `Patient` Domain (9 value objects).
  - `Project` Domain (ProjectId, Metadata).
  - UI Contracts (`Area`, `Editor`, `LayoutBuilder`, `LayoutRenderer`, `ToolSpec`, `ToolbarSpec`).
  - `ProjectRepository` (Protocol) and `FilesystemProjectRepository` (basic implementation).
- **Tests:** Domain unit tests (pure Python), JSON serialization round-trips for Patient and Project.

### Phase 2: Workspace Engine
**Goal:** Build the UI layout system that dynamically materializes modules.
- **Deliverables:**
  - `LayoutTree` (N-ary split tree), `AreaManager`.
  - `LayoutBuilder` (pure Python), `LayoutRenderer` (Qt materialization).
  - `EditorRegistry`, `EditorContext` (hybrid model).
  - `TopBar` (Structural component of the Workspace).
  - `WorkspaceOverlayManager` (for `steps_panel` and floating elements).
- **Tests:** `pytest-qt` for rendering; benchmarks for tree building.

### Phase 3: Project & Home Page
**Goal:** Implement the project lifecycle, discovery UI, and project persistence.
- **Deliverables:**
  - `ProjectManager` (single authority for lifecycle).
  - `ProjectCatalog` (read model).
  - `HomePage` UI (project cards, recent projects, flow selection).
  - Layout State Persistence (save/load workspace layout per project).
- **Tests:** Project creation/opening/closing flows, JSON serialization round-trips.

### Phase 4: Scene & Visualization
**Goal:** Introduce the 3D/2D visualization layer and the spatial domain.
- **Deliverables:**
  - Domain `Scene` (coordinate system, spatial hierarchy, membership).
  - `RenderingAdapter` (bridges Scene events to VTK).
  - `Viewport3DEditor` and `MPRViewerEditor`.
  - `TaskManager` abstraction for async operations.
  - Scene serialization (JSON).
- **Tests:** Headless VTK tests, spatial transform tests, performance tests (Scene update, upload to GPU, rendering FPS on reference hardware).

### Phase 5: Clinical Flows
**Goal:** Implement the workflow engine and the shared navigation panel.
- **Deliverables:**
  - `WorkflowEngine` (loads JSON, evaluates requirements).
  - `steps_panel` (Workspace Overlay).
  - Flow state persistence.
- **Tests:** State transition tests (pending, active, blocked, completed), requirement evaluation.

### Phase 6: Clinical Pipeline (PhD MVP)
**Goal:** Build the specific clinical tools required for the orthognathic workflow.
This phase is divided into sub-phases to accurately measure scientific progress:

- **Phase 6A — Tomography & Segmentation:** DICOM import, MPR, thresholding, mask painting.
- **Phase 6B — Registration & Cephalometry:** Alignment, cephalometric landmark acquisition.
- **Phase 6C — Osteotomy:** Le Fort I, BSSO, boolean operations.
- **Phase 6D — Surgical Guides:** Parametric guide generation.
- **Phase 6E — Integrated Validation:** End-to-end flow testing.
- **Tests:** Geometric validation (RMSE < 0.3mm), topological validation (0 non-manifold edges).

### Phase 7: Scientific Validation
**Goal:** Execute the validation protocols defined in the PhD project.
- **Deliverables:**
  - Geometric validation reports (phantoms, ground-truth).
  - Reproducibility studies (ICC > 0.85).
  - Usability reports (SUS > 70).
  - Documentation of the validation methodology.
- **Tests:** Automated scripts generating validation datasets and metrics.

### Phase 8: Scientific Product (Release 1.0)
**Goal:** Consolidate the platform as a stable, distributable scientific product.
- **Deliverables:**
  - Windows 11 Installer.
  - Autosave and crash recovery.
  - PDF Report generation.
  - Final user documentation and developer SDK documentation.
  - Scientific publication and DOI registration.
- **Tests:** Full regression suite, performance profiling on reference hardware.

### Phase 9: Extensibility (Release 2.0)
**Goal:** Open the platform for community contribution.
- **Deliverables:**
  - Module API and Plugin API.
  - Plugin loader and sandbox.
  - External plugin catalog.
- **Tests:** Plugin compatibility tests.

### Phase 10: AI and Nodes (Release 3.0)
**Goal:** Advanced automation and procedural workflows.
- **Deliverables:**
  - Node System (non-destructive graph).
  - AI Assistant (`AIAssistantEditor`).
  - MCP Server integration.
- **Tests:** AI command execution parity with human UI, graph evaluation tests.

---

## 6. Testing Strategy & Metrics

Testing is a clinical requirement. Metrics must be contextualized to avoid false positives or hardware dependencies.

### 6.1 Coverage Metrics
- **Domain Layer:** High coverage of critical business rules, with 100% of invariants and relevant error cases tested.
- **Application Layer:** Critical command paths and transaction rollbacks tested.
- **UI Layer:** 80% coverage of `ui/workspace/`.

### 6.2 Performance Metrics (Reference Hardware)
All performance metrics must be measured against a defined **Reference Dataset** and **Reference Hardware** (e.g., the workstations specified in the PhD infrastructure plan).

- **DICOM Import:** Load a reference dataset of 500 slices in < 10 seconds (including indexing and readiness for first visualization).
- **Rendering:** 30+ FPS for a mesh of 1,000,000 polygons.
  - *Metrics separated into:* Scene update time, GPU upload time, render time.
- **Memory:** < 4 GB RAM during standard facial CT processing.

### 6.3 GPU vs. CPU
- **Correction:** Semantic clinical data belongs to main memory (RAM) and the Domain `Scene`.
- The GPU should only hold **renderable representations** (VTK actors, shaders).
- Use caches and incremental transfer to reduce copies. Do not keep the entire clinical dataset on the GPU.

### 6.4 Concurrency
- **Correction:** `QTimer` is for UI scheduling, not asynchronous execution.
- **TaskManager:** Application layer abstraction for tasks.
- **Execution:** Heavy CPU-bound tasks must use `QThreadPool`/`QtConcurrent` or `ProcessPool` (for GIL-independent execution), coordinated by the `TaskManager`.

---

## 7. Release Criteria (Definition of Done)

A phase is "Done" when:
1. Code is implemented according to the architecture documents.
2. Unit, Widget, and Integration tests are written and passing.
3. The CI pipeline is green.
4. Documentation is updated (including ADRs if a new decision was made).
5. The feature is usable end-to-end by the UI (no orphaned backend code).
6. No `TODO` comments are left without a linked GitHub Issue.

### 7.1 The PhD Deliverable (Release 1.0)
The PhD concludes with the delivery of the validated clinical core. It **does not** include Plugins, Nodes, AI/MCP, or multi-monitor support. These are explicitly deferred to Releases 2.0 and 3.0, demonstrating the platform's long-term vision and extensibility without compromising the thesis deadline.

---

## 8. Summary

By following this roadmap, the CranioZ project ensures that the architectural foundation (Workspace, Commands, Scene) is built correctly before the heavy clinical lifting begins. It respects the scientific validation timelines, protects the PhD scope from feature creep, and establishes a clear path for post-doctoral open-source evolution.