# Implementation Plan

**Document type:** Roadmap and execution plan  
**Status:** Living document  
**Scope:** Phased implementation of the CranioZ platform, from foundation to release  
**Last updated:** 2026-11-01

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

---

## 3. External Dependencies & Tech Stack

- **Language:** Python 3.12+
- **UI Framework:** PySide6 / Qt 6
- **Medical Visualization:** VTK
- **DICOM Parsing:** pydicom
- **Scientific Computing:** NumPy, SciPy
- **Image Processing:** ITK (optional, introduced when justified by a concrete requirement)
- **Geometric Modeling:** Open CASCADE (OCCT), CGAL
- **Mesh Processing:** VTK, OpenMesh and other specialized libraries as required
- **Persistence:** JSON for project metadata, scene and layout; SQLite for indexed catalogs and future professional features
- **Testing:** pytest, pytest-qt, pytest-benchmark, hypothesis
- **Tooling:** uv, ruff, mypy

Dependencies must be introduced when required by an implementation task. Their presence in this list does not imply that every library must be integrated during the foundation phases.

---

## 4. Phase Overview

The implementation is divided into 11 phases. The sequence establishes the platform progressively while prioritizing a validated clinical core.

| Phase | Name | Status | Main Pending Work |
|---|---|---|---|
| **Phase 0** | Foundation & Boot | ✅ Implemented | Startup performance improvements |
| **Phase 1** | Contracts & Core Domain | ✅ Core implemented | Remaining context propagation |
| **Phase 2** | Workspace Engine | ✅ Core implemented | Remaining integration and lifecycle issues |
| **Phase 3** | Project & Home Page | ✅ Core implemented | Project index, asynchronous loading, persistence peripherals |
| **Phase 4** | Scene & Visualization | 🚧 In Progress | Imaging infrastructure, rendering, import UI, module integration |
| **Phase 5** | Clinical Flows | ⏳ Planned | WorkflowEngine, layout persistence, module integration |
| **Phase 6** | Clinical Pipeline | ⏳ Planned | Tomography, segmentation, cephalometry, osteotomy and guides |
| **Phase 7** | Scientific Validation | ⏳ Planned | Geometric, clinical and usability validation |
| **Phase 8** | Scientific Product (Release 1.0) | ⏳ Planned | Packaging, recovery, reporting and documentation |
| **Phase 9** | Extensibility (Release 2.0) | ⏳ Planned | Module API and Plugin API |
| **Phase 10** | AI and Nodes (Release 3.0) | ⏳ Planned | Node system, AI assistance and MCP integration |

**Status legend:**

- ✅ **Implemented:** Implemented in the codebase and tested. Known limitations may still exist.
- 🚧 **In Progress:** A contract, partial implementation, or reference implementation exists, but the deliverable is incomplete or not fully integrated.
- ⏳ **Planned:** Not implemented or not yet started.

**Contracts layer:** ADR-0001, ADR-0002 and ADR-0004–0012 are Accepted. ADR-0003 remains Proposed and must be reviewed before dependent widget-library and semantic-color work begins.

**Application layer:** Commands, Tasks, Telemetry, Events and Flows have contracts and reference implementations with contract tests. This does not imply that all production services, module loading, or application workflows are complete.

---

## 5. Current Focus

**Phase 4 — Scene & Visualization** is the active phase.

The foundation, core domain, workspace and project lifecycle are sufficiently established to support implementation of the imaging and visualization infrastructure.

The immediate objective is to complete the integration between the existing Application layer, Scene, imaging infrastructure, rendering adapters and Editors.

### 5.1 Immediate Priorities

#### 1. Complete Command Execution

- Implement `CommandExecutor`.
- Establish the transaction boundary for command execution.
- Publish domain/application events only after successful commit.
- Integrate `CommandBus`, `CommandStack` and `TransactionManager`.
- Correct compensating-command handling for undo/redo.
- Ensure undo and redo use the same transaction and event-publication rules.
- Introduce `CommandDispatcher` as the interface used by Editors and Tools.
- Add integration tests for execution, rollback, undo, redo and event publication.

#### 2. Complete EditorContext Propagation

- Preserve the existing `shared_context` mechanism.
- Ensure `task_manager`, `telemetry`, `correlation_id` and `command_dispatcher` are propagated consistently.
- Add `SceneQuery` to `EditorContext`.
- Add `EventSubscription` when required by the Editor lifecycle.
- Avoid introducing service dependencies that are not needed by current Editors.

#### 3. Complete Scene Integration

- Instantiate and provide `DomainObjectStore` through the established boot path.
- Ensure `SceneProvider` and `SceneQueryAdapter` expose the required read operations.
- Integrate imported imaging objects with the Scene.
- Preserve the distinction between object ownership and Scene membership.
- Implement Scene serialization according to ADR-0009.
- Add integration tests for object lifecycle, membership, queries and persistence.

#### 4. Complete Medical Imaging Infrastructure

The existing DICOM loader and import command are the starting point. Extend them according to the Medical Imaging Infrastructure architecture document.

Priority work:

- Establish the `Volume` and `VolumeGeometry` contracts.
- Separate voxel data, spatial geometry, metadata and provenance.
- Validate physical slice ordering and volume geometry.
- Establish the internal RAS coordinate convention and the DICOM LPS conversion boundary.
- Define intensity calibration and distinguish HU from uncalibrated CBCT data.
- Make NumPy buffer ownership and VTK interoperability explicit.
- Implement structured import validation and reporting.
- Add VTI export and round-trip validation.
- Complete the import UI and storage-mode selection.

Do not rebuild existing DICOM import functionality without first reviewing the current implementation and identifying specific gaps.

#### 5. Complete Visualization

- Preserve the existing `MPRView` implementation as the current baseline.
- Complete `Viewport3DView` volume rendering.
- Implement the `RenderingAdapter` between Scene and VTK.
- Separate clinical data from renderable representations.
- Implement Window/Level and display controls without modifying source voxel data.
- Validate physical orientation, spacing, origin and coordinate consistency.
- Resolve Windows OpenGL and Qt rendering-context issues through reproducible tests.

The choice between `vtkResliceImageViewer` and a custom `vtkImageReslice` pipeline must be validated through an ADR or documented technical decision. Do not replace the existing implementation solely because another API appears more flexible.

#### 6. Complete Module Loading

- Implement dependency resolution in `InMemoryModuleLoader`.
- Resolve and import module `entry_point` declarations.
- Register Tools, Editors, Services and Flows.
- Populate `BUILTIN_MANIFESTS`.
- Ensure all modules share the application EventBus.
- Implement the first functional built-in module.
- Validate module activation, deactivation, failure and unload behavior.

### 5.2 Phase 4 Completion Dependencies

No architectural contract blocker currently prevents Phase 4 implementation.

The remaining work is primarily implementation and integration:

- Command execution and transaction handling.
- Scene lifecycle and persistence.
- Medical imaging data contracts and validation.
- Rendering and VTK integration.
- Import UI.
- Real module loading and registration.
- End-to-end Editor workflows.

### 5.3 Deferred Work

The following items are intentionally deferred:

- **Recent Projects:** Phase 8.
- **WorkflowEngine execution:** Phase 5.
- **Layout State Persistence:** Phase 5, according to ADR-0010.
- **Module-owned persisted state:** Phase 9.
- **Plugin API:** Phase 9.
- **Node System, AI and MCP:** Phase 10.
- **Custom volume-rendering presets and preset editor:** Phase 8.
- **Curved and panoramic MPR:** Future clinical extension.
- **Additional imaging formats:** Introduce only when supported by a concrete clinical requirement.

---

## 6. Phase Breakdown

### Phase 0: Foundation & Boot

**Goal:** Establish the repository, configuration, logging, minimal persistence and application boot sequence.

**Deliverables:**

- ✅ `pyproject.toml` and CI pipeline.
- ✅ `ConfigurationLoader` and `AppPathResolver`.
- ✅ `EventBus`.
- ✅ JSON serialization for Project Metadata.
- ✅ Boot sequence in `__main__.py`.
- ✅ Error handling for inaccessible application paths.
- ✅ OS username resolution for the initial actor.
- ✅ Flow contracts and repositories.
- 🚧 Lazy imports and startup performance improvements.

**Tests:**

- Configuration validation.
- Application path resolution.
- Boot dependency construction.
- Application startup smoke tests.

**Status:** ✅ Implemented, with startup performance work tracked separately.

### Phase 1: Contracts & Core Domain

**Goal:** Establish the fundamental contracts, initial Domain models and minimum persistence.

**Deliverables:**

- ✅ Patient Domain and its value objects.
- ✅ Project Domain.
- ✅ UI contracts: `Area`, `Editor`, `EditorRegistry`, `ToolbarSpec`, `ToolSpec`, `LayoutBuilder` and `LayoutRenderer`.
- ✅ `ProjectRepository` and reference implementations.
- ✅ `ProjectContext`.
- ✅ `ProjectAccessPolicy`.
- ✅ `ProjectCatalog`.
- ✅ ADRs 0001, 0002 and 0004–0012.
- 🚧 ADR-0003 remains Proposed.
- 🚧 Remaining `EditorContext` propagation.

**Tests:**

- Pure Python Domain tests.
- Repository contract tests.
- Project serialization round-trips.
- Domain invariant and error-case tests.

**Status:** ✅ Core implemented. Remaining context propagation is tracked in Phase 4.

### Phase 2: Workspace Engine

**Goal:** Build the UI layout system that dynamically materializes Editors and Areas.

**Deliverables:**

- ✅ `LayoutTree` and `AreaManager`.
- ✅ `LayoutBuilder` and `LayoutRenderer`.
- ✅ `EditorRegistry` and `EditorContext`.
- ✅ `TopOverlay` and `OverlayManager`.
- ✅ `Workspace` facade.
- ✅ Structural split rendering using `QSplitter`.
- ✅ Editor lifecycle and Workspace cleanup improvements.
- ✅ Atomic `Workspace.load_spec()` behavior.

**Tests:**

- Pure Python layout tests.
- `pytest-qt` rendering tests.
- Editor lifecycle tests.
- Workspace integration tests.
- Geometry and overlay positioning tests.

**Status:** ✅ Core implemented. Remaining integration issues are tracked in §10.

### Phase 3: Project & Home Page

**Goal:** Implement project lifecycle, discovery UI and project persistence.

**Deliverables:**

- ✅ `ProjectManager`.
- ✅ `ProjectCatalog`.
- ✅ `HomePage` and its core UI components.
- ✅ `MainWindow` navigation between Home and Workspace.
- ✅ Project selection lifecycle.
- ✅ `FlowCatalog` and Flow repositories.
- 🚧 Recent Projects deferred to Phase 8.
- ⏳ WorkflowEngine execution deferred to Phase 5.
- ⏳ Layout State Persistence deferred to Phase 5.
- 🚧 Project deletion coordination.
- ⏳ Persistent `ProjectIndex` using SQLite.

**Startup performance requirements:**

- Lazy Editor resolution.
- No blocking I/O in `MainWindow.__init__`.
- Asynchronous project and flow loading.
- Rollback if Workspace creation fails after opening a project.
- Indexed project listing, with disk reconciliation as a background task.

**Tests:**

- Project lifecycle tests.
- Filesystem repository integration tests.
- HomePage selection and refresh regression tests.
- Project opening and rollback tests.
- Project index consistency tests.

**Status:** ✅ Core implemented. Startup performance and persistence peripherals remain.

### Phase 4: Scene & Visualization

**Goal:** Establish the spatial Domain, medical imaging infrastructure and visualization layer required by clinical Editors.

This phase provides the **technical foundation** for imaging. It does not implement the complete clinical tomography and segmentation workflow, which belongs to Phase 6A.

#### 4.1 Application Layer

**Implemented:**

- ✅ `application/commands/` contracts and reference implementations.
- ✅ `application/tasks/` contracts and reference implementations.
- ✅ `application/telemetry/` contracts and reference implementations.
- ✅ `application/events/` contracts and reference implementations.

**Pending:**

- 🚧 `CommandExecutor`.
- 🚧 `CommandDispatcher` integration.
- 🚧 Transactional command execution and post-commit event publication.
- 🚧 Production module loading and registration.

#### 4.2 Scene and Domain Integration

**Implemented:**

- ✅ `domain/scene/`: `Scene`, `DomainObjectStore`, `Transform` and `SpatialRelationship`.
- ✅ `application/scene/`: `SceneProvider`, `InMemorySceneProvider`, `SceneQueryAdapter`.
- ✅ `ImportDicomSeriesCommand` and its handler.
- ✅ `DomainObjectStore` boot integration.

**Pending:**

- 🚧 Complete `SceneQuery` propagation to Editors.
- ⏳ Scene serialization according to ADR-0009.
- ⏳ Filesystem-backed Scene persistence.
- ⏳ Complete integration between Commands, Scene and imported objects.

#### 4.3 Medical Imaging Infrastructure

**Goal:** Provide a reliable, format-aware foundation for loading, representing, validating, storing and exporting medical image volumes.

**Current implementation:**

- ✅ `infrastructure/imaging/dicom_loader.py` using pydicom and VTK.
- ✅ DICOM series import command and handler.
- 🚧 Current implementation must be evaluated and progressively aligned with the Medical Imaging Infrastructure architecture.

**Deliverables:**

**Volume model and geometry**

- ⏳ `Volume` Domain model.
- ⏳ `VolumeGeometry` with origin, spacing and direction.
- ⏳ Separate image metadata and provenance.
- ⏳ Internal RAS coordinate convention.
- ⏳ Explicit DICOM LPS-to-RAS conversion at the infrastructure boundary.
- ⏳ Consistent mapping between voxel indices and physical coordinates.
- ⏳ Explicit intensity calibration state: HU, UNCALIBRATED or UNKNOWN.

**DICOM import and validation**

- 🚧 Extend the existing DICOM loader rather than replacing it without justification.
- ⏳ Discover and group series using DICOM metadata.
- ⏳ Order slices using physical position, not filenames or `InstanceNumber`.
- ⏳ Validate dimensions, orientation, spacing and slice consistency.
- ⏳ Detect unsupported transfer syntaxes.
- ⏳ Detect irregular spacing and unsupported gantry tilt/shear.
- ⏳ Preserve source metadata and import provenance.
- ⏳ Generate structured validation reports with Error, Warning and Information severities.
- ⏳ Handle patient identity mismatches against the active project record.
- ⏳ Avoid exposing protected health information in logs and telemetry.

**Memory and interoperability**

- ⏳ Define ownership of the voxel buffer.
- ⏳ Define NumPy `[z, y, x]` array convention.
- ⏳ Define explicit NumPy/VTK conversion and buffer lifetime handling.
- ⏳ Avoid assuming zero-copy interoperability.
- ⏳ Keep clinical voxel data in main memory; GPU memory stores renderable representations only.

**Storage and export**

- ⏳ Support External Reference and Managed Copy storage modes.
- ⏳ Preserve source DICOM data as the canonical imaging source.
- ⏳ Implement VTI export as a derived representation.
- ⏳ Validate VTI geometry, dimensions, spacing, origin and scalar values through round-trip tests.
- ⏳ Ensure project deletion never removes externally referenced source data.

**Import UI**

- ⏳ File and directory selection.
- ⏳ Series discovery and grouping.
- ⏳ Metadata preview with minimized PHI exposure.
- ⏳ Patient identity validation and explicit mismatch confirmation.
- ⏳ Storage mode selection.
- ⏳ Validation report presentation.
- ⏳ TaskManager progress, cancellation and error reporting.

#### 4.4 Visualization Infrastructure

**Implemented:**

- ✅ `MPRView` using `vtkResliceImageViewer`.
- ✅ Axial, coronal and sagittal orientations.
- ✅ `TomographyEditor` resolves imported volume data and provides it to Views.

**Pending:**

- 🚧 `Viewport3DView` volume rendering using `vtkSmartVolumeMapper`.
- ⏳ Volume rendering presets.
- ⏳ `RenderingAdapter` observing Scene changes and updating VTK representations.
- ⏳ Window/Level controls and display-state integration.
- ⏳ Consistent physical orientation and coordinate handling.
- ⏳ VTK resource lifecycle and cleanup.
- ⏳ Headless and Windows rendering tests.

**Architectural constraints:**

- Domain data must not depend on VTK.
- VTK actors, mappers and render windows are presentation objects.
- Rendering adapters translate semantic Scene objects into renderable representations.
- Rendering updates must not mutate clinical source data.
- All VTK render-window and actor lifecycle operations remain on the GUI thread, according to ADR-0011.

#### 4.5 Module Integration

- 🚧 Implement dependency resolution in `InMemoryModuleLoader`.
- 🚧 Resolve module entry points.
- 🚧 Register Tools, Editors, Services and Flows.
- 🚧 Populate `BUILTIN_MANIFESTS`.
- 🚧 Share the application EventBus across ModuleContexts.
- ⏳ Implement the first functional built-in module.

#### 4.6 Tests

- DICOM import tests using anonymized or synthetic datasets.
- Physical geometry and coordinate conversion tests.
- Slice ordering and spacing validation tests.
- Intensity calibration tests.
- NumPy/VTK interoperability and buffer-lifetime tests.
- VTI export round-trip tests.
- Scene lifecycle and persistence tests.
- Headless VTK tests where supported.
- Qt/VTK integration tests on reference Windows hardware.
- Performance tests for import, Scene updates, GPU upload and rendering.

**Status:** 🚧 In Progress. The existing import path and MPR implementation provide a starting point. The remaining work is to consolidate imaging data contracts, validation, rendering and end-to-end integration.

### Phase 5: Clinical Flows

**Goal:** Implement workflow execution and shared clinical navigation.

**Deliverables:**

- ⏳ `WorkflowEngine`.
- ⏳ JSON flow loading and requirement evaluation.
- ⏳ Step-state computation.
- ⏳ `steps_panel` Workspace Overlay.
- ⏳ Flow state persistence.
- ⏳ Layout State Persistence according to ADR-0010.
- ⏳ Real ModuleRegistry and ModuleLoader integration.
- ✅ Flow Catalog and repositories.

**Tests:**

- Step-state transitions: pending, active, blocked and completed.
- Requirement evaluation.
- Flow loading and serialization.
- Flow state persistence.
- Module activation through clinical flows.

**Dependencies:** Phase 4 Scene integration and functional module loading.

**Status:** ⏳ Planned.

### Phase 6: Clinical Pipeline

**Goal:** Implement the clinical tools required for the initial orthognathic surgery workflow.

This phase is divided into sub-phases to distinguish clinical functionality and scientific validation.

#### Phase 6A — Tomography & Segmentation

**Goal:** Deliver the clinical tomography workflow on top of Phase 4 imaging infrastructure.

**Deliverables:**

- ⏳ Tomography Editor clinical workflow.
- ⏳ Synchronized axial, coronal and sagittal navigation.
- ⏳ Physical-coordinate crosshair and slice positioning.
- ⏳ Configurable slice distance and number of displayed slices.
- ⏳ Independent and synchronized slice navigation.
- ⏳ Window/Level and intensity display controls.
- ⏳ Intensity probing at physical coordinates.
- ⏳ ROI tools, distinguishing display ROI from processing ROI.
- ⏳ Threshold-based segmentation.
- ⏳ Mask creation and editing.
- ⏳ Segmentation persistence and Scene integration.
- ⏳ Surface generation from segmentation masks.
- ⏳ Clinical workflow integration.

Curved and panoramic MPR are deferred to a later extension unless required by a validated clinical use case.

#### Phase 6B — Registration & Cephalometry

**Deliverables:**

- ⏳ Image and surface registration.
- ⏳ Reference-based alignment.
- ⏳ Cephalometric template system.
- ⏳ Automatic and AI-assisted landmark detection.
- ⏳ Landmark refinement and verification.
- ⏳ Cephalometric measurements and reports.
- ⏳ Registration and landmark validation.

Manual acquisition remains available for refinement and fallback, not as the primary automation strategy.

#### Phase 6C — Osteotomy

**Deliverables:**

- ⏳ Le Fort I osteotomy.
- ⏳ BSSO and relevant sagittal split variants.
- ⏳ Genioplasty.
- ⏳ Boolean operations and fragment separation.
- ⏳ Fragment movement and transform management.
- ⏳ Surgical plan persistence.

#### Phase 6D — Surgical Guides

**Deliverables:**

- ⏳ Parametric guide generation.
- ⏳ Guide-to-anatomy fit validation.
- ⏳ Manufacturing constraints.
- ⏳ Export for additive manufacturing.

#### Phase 6E — Integrated Validation

**Deliverables:**

- ⏳ End-to-end orthognathic workflow.
- ⏳ Data integrity and reproducibility tests.
- ⏳ Geometric validation.
- ⏳ Clinical workflow usability tests.

**Tests:**

- Geometric validation with defined reference datasets.
- Registration error metrics.
- Mesh topology checks, including non-manifold edges.
- Segmentation reproducibility.
- End-to-end workflow tests.

**Status:** ⏳ Planned.

### Phase 7: Scientific Validation

**Goal:** Execute the scientific validation protocols defined in the doctoral research project.

**Deliverables:**

- Geometric validation reports using phantoms and ground-truth datasets.
- Reproducibility studies.
- Inter- and intra-examiner reliability.
- ICC and measurement error analysis.
- Usability evaluation.
- Performance evaluation on reference hardware.
- Documentation of validation methodology.

**Tests and metrics:**

- Metrics must be defined before evaluation.
- Thresholds must be justified by the clinical task and relevant literature.
- Validation datasets must be independent of development datasets.
- Results must include uncertainty and limitations.

**Status:** ⏳ Planned.

### Phase 8: Scientific Product (Release 1.0)

**Goal:** Consolidate the validated clinical core into a stable, distributable scientific product.

**Deliverables:**

- Windows installer.
- Autosave and crash recovery.
- PDF report generation.
- Final user documentation.
- Developer documentation.
- Recent Projects on the Home Page.
- Performance profiling and optimization.
- Release packaging and versioning.
- Scientific publication.
- DOI registration and public release.

**Tests:**

- Full regression suite.
- Installation and upgrade tests.
- Project recovery tests.
- Performance profiling on reference hardware.
- Release acceptance tests.

**Status:** ⏳ Planned.

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

**Tests:**

- Plugin compatibility tests.
- Module lifecycle tests.
- API stability tests.
- Persistence migration tests.

**Status:** ⏳ Planned.

### Phase 10: AI and Nodes (Release 3.0)

**Goal:** Introduce advanced automation and procedural workflows.

**Deliverables:**

- Non-destructive Node System.
- Graph evaluation and execution.
- AI Assistant Editor.
- AI-assisted clinical operations.
- MCP Server integration.
- Command parity between UI and automated execution.

**Tests:**

- Graph evaluation tests.
- Deterministic execution tests where applicable.
- AI command execution parity with human UI.
- Validation of automated outputs against clinical constraints.

**Status:** ⏳ Planned.

---

## 7. Testing Strategy & Metrics

Testing is a clinical requirement. Metrics must be reproducible and contextualized to avoid misleading results.

### 7.1 Coverage

- **Domain:** Critical invariants and error cases must be tested.
- **Application:** Command execution, transaction rollback, event publication and task lifecycle.
- **Infrastructure:** DICOM parsing, geometry, calibration, persistence and interoperability.
- **UI:** Widget behavior, Editor lifecycle and Workspace integration.
- **End-to-End:** Complete clinical workflows using synthetic, anonymized or approved datasets.

Coverage percentages are secondary to testing critical behavior and failure paths.

### 7.2 Performance Metrics

All performance targets must be measured using a defined Reference Dataset and Reference Hardware.

Initial targets:

- **DICOM Import:** 500-slice reference dataset in under 10 seconds, including indexing and readiness for first visualization.
- **Surface Rendering:** 30+ FPS for a mesh of 1,000,000 polygons on reference hardware.
- **Memory:** Target below 4 GB RAM during standard facial CT processing.

Performance measurements must distinguish:

- File reading and DICOM parsing.
- Volume construction and geometry validation.
- NumPy/VTK conversion.
- GPU upload.
- Scene update.
- Rendering.

Targets must be reviewed against actual datasets and hardware. They are not universal guarantees.

### 7.3 CPU and GPU Responsibilities

- Clinical data and semantic objects remain in main memory and the Domain Scene.
- GPU memory stores renderable representations and rendering resources.
- Avoid unnecessary copies and maintain explicit ownership of large buffers.
- GPU acceleration is optional for core clinical workflows.
- CPU-based fallback must remain available for essential operations.

### 7.4 Concurrency

- `TaskManager` is the only application mechanism for off-thread work, according to ADR-0011.
- Long-running DICOM parsing, segmentation, registration and mesh processing must execute as Tasks.
- GUI and VTK render-window operations remain on the GUI thread.
- Cancellation is cooperative.
- Progress, cancellation and errors must be propagated through TaskManager callbacks.
- Do not use `QTimer` as a substitute for background execution.
- Do not create unmanaged threads, event loops or call `QApplication.processEvents()`.

### 7.5 Telemetry

Long-running operations must emit the appropriate telemetry events through `TelemetrySink`, using correlation IDs according to ADR-0012.

Telemetry must not contain protected health information or unnecessary patient-identifying metadata.

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
9. Known debt affecting the phase is fixed or explicitly tracked with a linked issue.
10. Data integrity, failure handling and recovery behavior are tested where relevant.

### 8.1 Release 1.0 Scope

Release 1.0 delivers the validated clinical core defined by the doctoral research scope.

It does not include:

- External Plugins.
- Node System.
- AI/MCP platform integration.
- Multi-monitor support as a required feature.

These capabilities belong to Releases 2.0 and 3.0 and must not compromise the initial clinical delivery.

---

## 9. Implementation Summary

The foundation, core Domain, Workspace and project lifecycle are implemented sufficiently to support the next development stage.

Phase 4 is the active phase. Its existing DICOM import path, Scene integration and MPR implementation provide a functional starting point, but they do not yet constitute a complete medical imaging infrastructure.

The immediate priorities are:

1. Complete transactional Command execution.
2. Complete `EditorContext` propagation.
3. Consolidate Scene lifecycle and persistence.
4. Formalize `Volume` and `VolumeGeometry`.
5. Strengthen DICOM geometry validation and provenance.
6. Implement explicit NumPy/VTK interoperability and buffer ownership.
7. Complete VTI export and round-trip validation.
8. Complete volume rendering and `RenderingAdapter`.
9. Complete the import UI.
10. Implement real module loading and registration.

The implementation sequence preserves the distinction between infrastructure and clinical functionality:

- **Phase 4:** Data representation, import, validation, storage, geometry and visualization foundations.
- **Phase 5:** Workflow execution and clinical navigation.
- **Phase 6A:** Clinical tomography interaction and segmentation.
- **Phase 6B–6E:** Registration, cephalometry, osteotomy, guides and integrated validation.

This separation avoids placing clinical behavior inside infrastructure components and allows the imaging foundation to be tested independently.

---

## 10. Known Debt

This section records known issues that must be resolved or explicitly deferred before the affected phase can be declared complete.

### 10.1 Phase 1 / Phase 4 — EditorContext

- `SceneQuery` is not yet available as a field on `EditorContext`.
- `EventSubscription` propagation remains pending.
- Additional services must be introduced only when required by concrete Editor workflows.

### 10.2 Phase 3 — Project Lifecycle and Persistence

- Project deletion must coordinate files owned by Patient, Scene, Layout and other persistence components.
- `FilesystemProjectRepository.delete()` must not silently leave orphaned project data.
- `ProjectIndex` remains pending.
- Filesystem repositories require stronger integration tests for permissions, atomic writes and path traversal.

### 10.3 Phase 4 — Module System

- `InMemoryModuleLoader` requires dependency resolution.
- Module entry points are not fully loaded and registered.
- `BUILTIN_MANIFESTS` requires functional built-in module definitions.
- `ModuleContext` must use the shared application EventBus.
- `CommandExecutor` and `CommandDispatcher` integration remain prerequisites for real Editor operations.

### 10.4 Phase 4 — Medical Imaging

- The current DICOM loader requires a review against the Medical Imaging Infrastructure contracts.
- The `Volume` and `VolumeGeometry` models must become the authoritative representation of imported image data.
- Physical slice ordering and geometry validation must be explicit.
- LPS-to-RAS conversion must be centralized at the infrastructure boundary.
- Intensity calibration must distinguish HU from uncalibrated CBCT values.
- NumPy/VTK buffer ownership and lifetime must be explicit.
- Import validation and provenance reporting remain incomplete.
- External Reference and Managed Copy storage modes require implementation and tests.
- VTI export and round-trip validation remain pending.
- Import UI remains pending.

### 10.5 Phase 4 — Visualization

- `Viewport3DView` still uses `vtkOutlineFilter` as a placeholder.
- Volume rendering using `vtkSmartVolumeMapper` remains pending.
- `RenderingAdapter` is not yet implemented.
- Window/Level controls are not fully integrated across the visualization pipeline.
- The MPR implementation currently uses `vtkResliceImageViewer`. Its suitability must be evaluated before deciding whether to retain or replace it.
- VTK resource lifecycle and rendering-context stability require further testing.

### 10.6 Phase 4 — Windows OpenGL and Qt Integration

- `QVTKRenderWindowInteractor` may fail to obtain a valid OpenGL context in CI or server environments.
- `wglMakeCurrent` errors must be reproduced and isolated.
- Headless tests must distinguish failures in data processing from failures in rendering-context initialization.
- Do not treat `vtkFixedPointVolumeRayCastMapper` or `QT_QPA_PLATFORM=offscreen` as universal solutions. Validate the selected strategy on supported environments.

### 10.7 Cross-Cutting — Internationalization and Theme

- UI strings and colors remain partially hardcoded.
- `TranslationService` must be wired into the UI.
- `ThemeService` must expose semantic colors according to ADR-0003.
- Temporary translation-key helpers must be removed after proper localization integration.
- ADR-0003 must be reviewed and accepted before dependent widget-library work is considered complete.

### 10.8 Documentation and Testing

- `docs/architecture/README.md` requires cleanup of accidental shell commands.
- `docs/architecture/domain/project/project.md` requires cleanup of accidental code snippets.
- References to removed abstractions such as `EditorHost` must be reviewed.
- The main `README.md` requires content.
- i18n tests require implementation.
- Filesystem repository integration tests require expansion.

### 10.9 Startup Performance

- `__main__.py` must avoid unnecessary eager imports of Editors and Workspace components.
- `MainWindow.__init__` must not perform blocking I/O.
- Project and flow loading must not block initial window display.
- Project opening must roll back correctly if Workspace creation fails.
- `ProjectIndex` must avoid scanning the entire project directory on every startup.

---

## 11. Change Management

This plan is a living document and must remain synchronized with the implementation.

- Update status only after implementation and tests provide evidence.
- Record architectural changes through ADRs.
- Do not mark a phase complete because its interfaces or placeholder classes exist.
- Do not duplicate existing implementations without a documented technical reason.
- When a task reveals a dependency outside its current phase, update the plan rather than introducing an undocumented shortcut.
- Keep deferred capabilities visible without allowing them to expand the scope of Release 1.0.