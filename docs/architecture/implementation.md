# Implementation Plan

**Document type:** Roadmap and execution plan  
**Status:** Living document  
**Scope:** Phased implementation of the CranioZ platform, from foundation to release  
**Last updated:** 2026-11-06

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
| **Phase 2** | Workspace Engine | ✅ Core implemented | Editor Layout Tree configurable (ADR-0013 §2.5, §2.6); IconManager and ThemeManager integration |
| **Phase 3** | Project & Home Page | ✅ Core implemented | Project index, asynchronous loading, persistence peripherals |
| **Phase 4** | Scene & Visualization | ✅ Core implemented | Marching Cubes surface path; RenderingAdapter; import UI; module integration |
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

The immediate objective is to complete the integration between the existing Application layer, Scene, imaging infrastructure, geometry infrastructure, rendering adapters and Editors.

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

The existing DICOM loader, `VtkImageAdapter`, and import command are functional. The DICOM visualization bug was diagnosed and fixed.

**Resolved (2026-11-06):**

- ✅ The DICOM visualization bug was diagnosed and fixed. Root cause: `VtkImageAdapter` combined `transpose(2, 1, 0)` with `ravel(order="C")`, corrupting the memory layout expected by `vtkImageData`. Correct conversion is `data.ravel(order="C")` on the original `(Z, Y, X)` NumPy layout, with `SetDimensions(nx, ny, nz)`.
- ✅ `int16` was validated as the production scalar type. Benchmarks on the reference dataset (400×400×248, 79.4 MB) showed:
  - Conversion: `int16` = 14.9 ms vs `uint8` = 258.3 ms (17× faster).
  - Peak RAM during conversion: `int16` = 0 MB vs `uint8` = 357 MB.
  - Render FPS: `int16` = 3.8 vs `uint8` = 2.1 (81% faster).
  - `uint8` is retained only as a fallback for GPUs with < 2 GB VRAM.

**Priority work (remaining):**

- Consolidate `DicomSeriesReader` to order slices by `ImagePositionPatient` projection onto the `ImageOrientationPatient` normal (not `InstanceNumber` or filename).
- Calculate `spacing_z` from the real distance between consecutive `ImagePositionPatient` values (not `SliceThickness`).
- Preserve `RescaleSlope` and `RescaleIntercept` per slice, and document that CBCT volumes may be uncalibrated (not true HU).
- Apply the LPS→RAS conversion at the infrastructure boundary and document the RAS internal convention.
- Make NumPy buffer ownership explicit in `VtkImageAdapter` (`deep=0` with `Volume` holding the buffer reference).
- Add VTI export and round-trip geometry validation.
- Complete the import UI and storage-mode selection.

Do not rebuild existing DICOM import functionality without first reviewing the current implementation and identifying specific gaps.

#### 5. Establish Geometry Infrastructure (initial subset)

The initial subset of the `Geometry Infrastructure` document (Phase 1 + STL subset of Phase 2) is implemented and validated. It established the canonical `Mesh`, the STL import/export, the VTK adapter, and the `MeshDebugEditor` used to prove the VTK pipeline is healthy independently of the DICOM volume path.

Remaining work is deferred to later phases of the Geometry Infrastructure document:

- Immutable `GeometryRevision` with parent references and provenance.
- Content-hash-based array asset deduplication.
- Persistent asset storage (ADR-0009).
- `ValidationProfile` per operation.
- `GeometryOperation` / `GeometryOperationResult` / TaskManager integration.
- Booleans, welding, advanced processing.
- Benchmarks (1M, 5M triangles).

#### 6. Complete Visualization

- Preserve the existing `MPRView` implementation (manual `vtkImageReslice` pipeline) as the current baseline.
- Preserve the existing `Viewport3DView` volume rendering (`vtkSmartVolumeMapper` + presets, `VTK_SHORT` scalars) as the current baseline.
- Implement the `RenderingAdapter` between Scene and VTK.
- Separate clinical data from renderable representations.
- Implement Window/Level and display controls without modifying source voxel data.
- Validate physical orientation, spacing, origin and coordinate consistency.
- Resolve Windows OpenGL and Qt rendering-context issues through reproducible tests.
- ⏳ Add a Marching Cubes surface path as a complement to volume rendering for orthopedic planning (the initial mesh-based validation was proven viable).

**VTK pipeline validation (confirmed):** The STL validation path (`read_stl` → `Mesh` → `mesh_to_polydata` → `Viewport3DView.set_mesh`) renders correctly. The corrected DICOM path (`Volume` → `VtkImageAdapter` → `Viewport3DView.set_volume`) also renders correctly.

**DICOM visualization bug (resolved):** The root cause was a voxel ordering bug in `VtkImageAdapter`. The fix is documented in §10.5. A regression test prevents reintroduction.

**Sprint 4.2 — Consume `Volume` in Views and Editors (in progress):**

- Refactor `MPRView.set_volume` to accept `Volume` (domain) instead of `vtkImageData`.
- Refactor `Viewport3DView.set_volume` to accept `Volume`.
- Refactor `TomographyEditor` to resolve `Volume` (not `VolumeData`) from the `DomainObjectStore`.
- Use `VtkImageAdapter` as the sole bridge between `Volume` and `vtkImageData`.
- Keep `VolumeData` during this sprint; full removal is Sprint 4.3.
- Update `MPRView`, `Viewport3DView`, and `TomographyEditor` tests.

The MPR pipeline choice (`vtkImageReslice` + `vtkImageMapToWindowLevelColors` + `vtkImageActor`) is settled and is the documented baseline.

#### 7. Complete Module Loading

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
- Rendering and VTK integration (`RenderingAdapter`).
- Import UI.
- Real module loading and registration.
- End-to-end Editor workflows.
- Marching Cubes surface path for bone visualization.

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
- **`uint8` fallback path:** Retain for low-VRAM GPUs only; not a production default.
- **Full Geometry Infrastructure:** Phases 3–4 of the dedicated document (application commands, revisions, persistence, validation profiles, booleans, benchmarks).

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
- ✅ Three-segment Top Bar: `HomeSegment`, `ModulesSegment`, `ExtrasSegment`.
- ✅ Area toggles (Left, Right, Bottom) wired to `Workspace.set_area_visible()`.
- ✅ Minimum `WorkspaceLayoutState` (runtime visibility only, not persisted).
- ✅ `TopOverlay` three-segment content injection (`set_left_content`, `set_center_content`, `set_right_content`).
- ✅ Splitter reflow after Area visibility changes (`LayoutRenderer.refresh_splitter_sizes`).
- ✅ `Area.visible` as the runtime source of truth for the Region computation.
- 🚧 Editor Layout Tree configurable per Area (ADR-0013 §7.3). The `AreaWidget` currently uses a fixed horizontal `QSplitter` for multiple Editors; it does not yet honor `Area.set_editor_layout(EditorLayoutSpec)`.
- 🚧 Editor Stack for stacking multiple Editors in the same Leaf (ADR-0013 §2.5).
- 🚧 `IconManager` and `ThemeService` semantic colors. The Top Bar uses Unicode glyphs as placeholders; `debug_colors=True` (pastel backgrounds by Placement) is the current visual aid during development.

**Tests:**

- Pure Python layout tests.
- `pytest-qt` rendering tests.
- Editor lifecycle tests.
- Workspace integration tests.
- Geometry and overlay positioning tests.
- Top Bar segments injection and toggle tests.
- Region bounds exclusion for hidden Areas.

**Status:** ✅ Core implemented. The remaining items are tracked in §10.9, §10.10, and §10.11.

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

**Goal:** Establish the spatial Domain, medical imaging infrastructure, geometry infrastructure and visualization layer required by clinical Editors.

This phase provides the **technical foundation** for imaging. It does not implement the complete clinical tomography and segmentation workflow, which belongs to Phase 6A.

#### 4.1 Application Layer

**Implemented:**

- ✅ `application/commands/` contracts and reference implementations.
- ✅ `application/tasks/` contracts and reference implementations.
- ✅ `application/telemetry/` contracts and reference implementations.
- ✅ `application/events/` contracts and reference implementations.

**Pending:**

- 🚧 `CommandDispatcher` integration into all Editors (currently propagated through `EditorContext` and `ToolContext` for the Editors that declare it).
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

- ✅ `Volume`, `VolumeGeometry`, `ImageMetadata`, `VolumeProvenance`, `IntensityScale` (Sprint 2).
- ✅ `DicomSeriesReader`, `DicomSorter`, `DicomCalibrator`, `DicomValidator`, `ImportReport` (Sprint 3).
- ✅ `VtkImageAdapter` (`Volume` → `vtkImageData`, sole bridge, Sprint 4.1).
- ✅ DICOM series import command and handler; `ImportDicomSeriesHandler` registered by the MainWindow when a project opens (Sprint 4.2/4.3).
- ✅ Legacy `VolumeData` and `dicom_loader.py` removed. All Views, the Editor, and the MainWindow consume `Volume`.
- ✅ DICOM visualization bug resolved (Sprint 4.2, 2026-11-06). See §10.5.

**Deliverables:**

**Volume model and geometry**

- ✅ `Volume` Domain model.
- ✅ `VolumeGeometry` with origin, spacing and direction.
- ✅ Separate image metadata and provenance.
- ✅ Internal RAS coordinate convention.
- ✅ Explicit DICOM LPS-to-RAS conversion at the infrastructure boundary.
- ✅ Consistent mapping between voxel indices and physical coordinates.
- ✅ Explicit intensity calibration state: HU, UNCALIBRATED or UNKNOWN.

**DICOM import and validation**

- ✅ `DicomSorter` orders slices by physical position (`ImagePositionPatient`), not filenames or `InstanceNumber`. The projection is onto the normal computed from `ImageOrientationPatient` (`np.cross(iop[:3], iop[3:])`).
- ✅ `DicomValidator` validates dimensions, orientation, spacing and slice consistency.
- ✅ `DicomValidator` detects unsupported transfer syntaxes.
- ✅ `DicomValidator` detects irregular spacing and unsupported gantry tilt/shear.
- ✅ `DicomSeriesReader` preserves source metadata and import provenance.
- ✅ `ImportReport` generates structured validation reports with Error, Warning and Information severities.
- ✅ `spacing_z` is computed from the real distance between consecutive `ImagePositionPatient` values (`np.linalg.norm(pos_second - pos_first)`), not from `SliceThickness`.
- ✅ `RescaleSlope` and `RescaleIntercept` are applied per slice. CBCT volumes that fall outside the expected HU range are flagged as `UNCALIBRATED`.
- ⏳ Handle patient identity mismatches against the active project record.
- ⏳ Avoid exposing protected health information in logs and telemetry.

**Memory and interoperability**

- ✅ Define ownership of the voxel buffer. `Volume` owns the NumPy buffer; `VtkImageAdapter` shares it (`deep=0`); Views retain a strong reference to `Volume` while the VTK pipeline is active.
- ✅ NumPy `[z, y, x]` array convention.
- ✅ Explicit NumPy/VTK conversion and buffer lifetime handling (`VtkImageAdapter`).
- ✅ **Voxel ordering contract:** `Volume.data.shape == (Z, Y, X)`. Conversion to `vtkImageData` uses `data.ravel(order="C")` **without transposition**. `image.SetDimensions(nx, ny, nz)` matches the NumPy axes. Combining `transpose(2,1,0)` with `ravel(order="C")` corrupts the spatial layout and produces stripe artifacts (regression test required).
- ✅ **Production scalar type:** `VTK_SHORT` (`int16`). Benchmarks confirmed it is both faster and more faithful than `VTK_UNSIGNED_CHAR` on the reference dataset. `uint8` remains available as a low-VRAM fallback only.
- ✅ Keep clinical voxel data in main memory; GPU memory stores renderable representations only.

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

#### 4.4 Geometry Infrastructure

**Goal:** Provide the canonical representation, validation and persistence foundations for geometric data (triangular meshes).

**Architecture:** See the `Geometry Infrastructure` document. Distributed across Domain, Application and Infrastructure layers. This sub-phase implements only the initial subset (Phase 1 + STL subset of Phase 2 of that document), to validate the VTK rendering pipeline independently of the DICOM volume path.

**Implemented:**

- ✅ `domain/geometry/`: `Mesh`, `CoordinateFrame`, `ValidationIssue`, `ValidationResult`, `ValidationSeverity`.
- ✅ `infrastructure/geometry/io/stl.py`: STL import and export with explicit unit scale and coordinate frame.
- ✅ `infrastructure/geometry/adapters/vtk/`: `Mesh` → `vtkPolyData` conversion.
- ✅ `Viewport3DView.set_mesh(mesh: Mesh)` — VTK pipeline validated independently of the DICOM volume path (see `docs/known_issues/dicom_visualization_bug.md`).
- ✅ `MeshDebugEditor` — minimal Editor hosting a single `Viewport3DView`, activated via `CRANIOZ_DEBUG_MESH=1`, used for manual STL validation.
- ✅ `MeshAttribute` remains deferred (not required for the initial subset).

**Initial scope (completed):**

- Canonical triangular `Mesh` with explicit `CoordinateFrame`.
- Structural validation (shape, dtype, indices, finite coordinates).
- STL import with explicit unit scale and coordinate frame (no silent assumptions — §4.5 of the Geometry Infrastructure document).
- `Mesh` → `vtkPolyData` conversion.
- `Viewport3DView.set_mesh(mesh: Mesh)` to validate the VTK pipeline independently of the DICOM volume path.

**Deferred to later phases of the Geometry Infrastructure document:**

- Immutable `GeometryRevision` with parent references and provenance.
- Content-hash-based array asset deduplication.
- Persistent asset storage (ADR-0009).
- `ValidationProfile` per operation.
- `GeometryOperation` / `GeometryOperationResult` / TaskManager integration.
- Booleans, welding, advanced processing.
- Benchmarks (1M, 5M triangles).

#### 4.5 Visualization Infrastructure

**Implemented:**

- ✅ `MPRView` using a manual `vtkImageReslice` + `vtkImageMapToWindowLevelColors` + `vtkImageActor` pipeline.
  - Chosen over `vtkResliceImageViewer` because the latter caused `wglMakeCurrent` failures on Windows drivers (see §10.6).
- ✅ Axial, coronal and sagittal orientations.
- ✅ `Viewport3DView` volume rendering using `vtkSmartVolumeMapper` with `VTK_SHORT` scalars.
- ✅ Volume rendering presets (Bone, Soft Tissue, Skin, CT Angio, CBCT).
- ✅ `TomographyEditor` resolves imported volume data and provides it to Views.
- ✅ STL validation path (`Mesh` → `vtkPolyData` → `Viewport3DView.set_mesh`) confirmed working. The VTK pipeline (renderer, camera, mapper, OpenGL context) is healthy.
- ✅ **DICOM volume path validated:** The corrected `VtkImageAdapter` (no transpose, `int16`) renders the imported DICOM volume correctly in both MPR and 3D views. The previous stripe artifacts were caused by voxel ordering, not by the renderer, camera, mapper, or OpenGL context.
- ✅ `Viewport3DView.set_volume(volume: Volume)` consumes the domain `Volume` directly via `VtkImageAdapter`.

**Pending:**

- ⏳ `RenderingAdapter` observing Scene changes and updating VTK representations.
- ⏳ Window/Level controls and display-state integration across the pipeline (the MPR pipeline applies a fixed W/L; the 3D viewport W/L is deferred to Passo 8d).
- ⏳ Consistent physical orientation and coordinate handling validated against reference datasets.
- ⏳ VTK resource lifecycle and cleanup validated under repeated open/close.
- ⏳ Headless and Windows rendering tests (see §10.6).
- ⏳ **Marching Cubes surface path** for bone visualization (recommended as a complement to volume rendering for orthopedic planning; the initial mesh-based validation was proven viable).

**Architectural constraints:**

- Domain data must not depend on VTK.
- VTK actors, mappers and render windows are presentation objects.
- Rendering adapters translate semantic Scene objects into renderable representations.
- Rendering updates must not mutate clinical source data.
- All VTK render-window and actor lifecycle operations remain on the GUI thread, according to ADR-0011.

#### 4.6 Module Integration

- 🚧 Implement dependency resolution in `InMemoryModuleLoader`.
- 🚧 Resolve module entry points.
- 🚧 Register Tools, Editors, Services and Flows.
- 🚧 Populate `BUILTIN_MANIFESTS`.
- 🚧 Share the application EventBus across ModuleContexts.
- ⏳ Implement the first functional built-in module.

#### 4.7 Tests

- DICOM import tests using anonymized or synthetic datasets.
- Physical geometry and coordinate conversion tests.
- Slice ordering and spacing validation tests.
- Intensity calibration tests.
- NumPy/VTK interoperability and buffer-lifetime tests.
- Geometry Infrastructure tests (Mesh invariants, STL round-trip, VTK conversion).
- VTI export round-trip tests.
- Scene lifecycle and persistence tests.
- ✅ **Voxel ordering regression test:** build a synthetic `Volume` with a known asymmetric pattern, convert to `vtkImageData`, and assert that `vtkImageData.GetScalarComponentAsFloat` matches `Volume.data` at every corner and at the center.
- ✅ **`int16` fidelity test:** verify the `vtkImageData` scalar range equals `Volume.data.min()`/`max()`.
- ✅ **`spacing_z` test:** construct a synthetic DICOM series with known `ImagePositionPatient` and assert the computed spacing.
- ⏳ Import performance test: 500-slice reference dataset < 10 s.
- ⏳ `uint8` fallback test: verify that the normalization preserves the spatial ordering (only the scalar values change).
- ⏳ Headless VTK tests where supported.
- ⏳ Qt/VTK integration tests on reference Windows hardware.
- ⏳ Performance tests for import, Scene updates, GPU upload and rendering.

**Status:** ✅ Core implemented. The existing import path, MPR implementation and 3D viewport render the imported DICOM volume correctly. The Geometry Infrastructure initial subset is validated. The remaining work is to consolidate imaging data contracts, complete the rendering adapter, and build the clinical workflows.

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
- **Application:** Command execution, transaction rollback, event publication and task