# Implementation Plan

**Document type:** Roadmap and execution plan  
**Status:** Living document  
**Scope:** Phased implementation of the CranioZ platform, from foundation to release  
**Last updated:** 2026-11-27

---

## 1. Purpose

This document defines the implementation roadmap for CranioZ, translating accepted architectural decisions (ADRs), domain contracts, and clinical requirements into sequenced and testable deliverables.

It serves as a technical and scientific execution plan, distinguishing the doctoral research scope from the long-term evolution of the open-source platform.

Implementation status must reflect the actual codebase. A deliverable is considered complete only when its implementation, relevant tests, and intended integration are verified. Partial implementations and known limitations must remain explicit.

## 2. Guiding Principles

1. **Vertical Slices:** Prefer complete, testable features across Domain, Application, Infrastructure, and UI.
2. **Stable Contracts:** Work may proceed in parallel when dependencies and architectural contracts are stable.
3. **Early Persistence:** Define serialization and persistence contracts before they become architectural bottlenecks.
4. **Continuous Testing:** Include unit, contract, integration, and UI tests as appropriate.
5. **Reversible Decisions:** Validate uncertain technical choices through prototypes, benchmarks, and ADRs.
6. **Clinical Data Integrity:** Never silently modify, reinterpret, or discard source imaging data. Geometry, calibration, and provenance must remain explicit.
7. **CPU-First:** Core clinical functionality must not depend on GPU acceleration.
8. **Complete Integration:** Backend implementation alone does not constitute a completed feature; its intended workflow must be usable.
9. **Prototype Fidelity:** `Prototipagem_UI` is the reference for UI structure and interaction. Deviations must be justified.
10. **Internationalization:** All user-facing strings must use `TranslationService`.
11. **Centralized Appearance:** Shared visual properties must use design tokens and `ThemeService`. See `../../architecture/appearance`.

## 3. Technology Stack

| Area | Technology |
|---|---|
| Language | Python 3.12+ |
| UI | PySide6 / Qt 6 Widgets + QSS |
| Medical visualization | VTK |
| DICOM | pydicom |
| Scientific computing | NumPy, SciPy |
| Image processing | ITK, when justified |
| Geometric modeling | OCCT, CGAL |
| Mesh processing | VTK, OpenMesh |
| Persistence | JSON; SQLite for indexed catalogs |
| Testing | pytest, pytest-qt, pytest-benchmark, hypothesis |
| Tooling | uv, ruff, mypy |

Dependencies must be introduced when required. Their presence in this list does not imply immediate integration.

## 4. Phase Overview

The roadmap contains eleven phases. Phase 4 is divided into two milestones to isolate imaging validation from UI expansion.

| Phase | Name | Status | Main Deliverables |
|---|---|---|---|
| 0 | Foundation & Boot | Complete | Repository, configuration, boot |
| 1 | Contracts, Core Domain & i18n | Complete | Domain contracts, repositories, localization |
| 2 | Workspace Engine & Icons | Complete | Workspace, themes, icon infrastructure |
| 3 | Project, Home Page & Professional Module | Complete | Project lifecycle, Professional module foundation |
| 4A | Imaging Core & Rendering Validation | In progress | DICOM-to-Scene pipeline, validated MPR/3D |
| 4B | Import & Visualization UI | Planned | Import Dialog, layouts, tools, presets |
| 5 | Clinical Flows & Panel Registry | Planned | WorkflowEngine, panels, layout persistence |
| 6 | Clinical Pipeline | Planned | Segmentation, cephalometry, osteotomy, guides |
| 7 | Scientific Validation | Planned | Geometric, clinical, usability validation |
| 8 | Scientific Product (Release 1.0) | Planned | Packaging, persistence, documentation, publication |
| 9 | Extensibility (Release 2.0) | Planned | Module and Plugin APIs |
| 10 | AI and Nodes (Release 3.0) | Planned | Node system, AI assistance, MCP |

**Status definitions**

- **Complete:** Implemented and tested, with known limitations documented.
- **In progress:** Partially implemented or awaiting integration, decisions, or acceptance.
- **Planned:** Not yet implemented.

**Architectural references:** ADR-0001 through ADR-0016 and ADR-0018 are accepted. ADR-0014 establishes Qt Widgets, QSS, and Python design tokens. ADR-0015 governs Editor and Module package organization. ADR-0016 governs ProjectIndex synchronization. ADR-0018 governs Professional module SQLite persistence.

The appearance architecture is documented in `../../architecture/appearance`.

## 5. Current Status and Immediate Priorities

Phases 0, 1, 2, and 3 are closed. The Editor Architecture Refactoring (ADR-0015) is complete.

Phase 4A is the active implementation phase. The remaining Professional screens are deferred and do not block any phase.

### 5.1 Completed Work

| Sprint | Phase | Deliverable | Status |
|---|---|---|---|
| B | 1 | i18n contracts and catalogs | Complete |
| C | 1 | EditorContext propagation | Complete |
| E | 2 | ThemeService, ThemeCompiler, tokens | Complete |
| F | 2 | IconProvider, UnicodeIconProvider | Complete |
| G | 2 | AreaLayoutRenderer | Complete |
| H | 2 | EditorStack | Complete |
| Editor Refactoring | 3 | Editor/Module package reorganization | Complete |
| I | 3 | ProjectIndex (ADR-0016) | Complete |
| J | 3 | Coordinated project deletion | Complete |
| K | 3 | Asynchronous flow loading | Complete |
| Icon Foundation | 2 | SVG provider, fallback, recolor, cache, HiDPI, and six Professional assets | Complete |
| Home Page Refinement | 3 | SVG action icons, collapsible search, StartButton sizing, and project management with selection/removal | Complete |
| Phase 3 Closure | 3 | Project lifecycle, Home Page, Professional profile and navigation; remaining Professional screens deferred | Complete |

### 5.2 Sprint L — Professional Module

**Status:** Complete for the accepted Phase 3 scope.

- **L.0:** System form widgets — complete.
- **L.0.2 A:** Qt-native widgets — complete.
- **L.0.2 B:** CollapsibleSection, DragList, IconSidebar — complete.
- **L.0.2 C/D:** TimelineSlider, ColorPicker, Histogram, final harness consolidation, HiDPI validation, and catalog closure — deferred.
- **L.1:** Professional domain, SQLite profile persistence, repository/service, command/query flow, ProfessionalEditor, Tela 2, central-Area composition, and `professional.*` settings — complete.
- **L.2:** Navigation, section organization, drag ordering, and persistence for the delivered profile workflow — complete for the accepted Phase 3 scope. `IconSidebar` provides the six Professional tabs; the active tab is restored and persisted through `professional.ui.last_section`, and unimplemented tabs show localized placeholder pages. `CollapsibleSection` is integrated into the Tela 2 profile groups. Their `DragList` order and expanded/collapsed state are restored and persisted through `professional.ui.navigation_order` and `professional.ui.collapsed_sections`. The Tela 2 ordering interface was visually approved on 2026-11-26.

The `ModuleUISpec` ownership decision and the visual approval of Tela 2
were completed on 2026-11-26.

Tela 2 does not expose visibility controls in its profile sections. Per the
UI prototype, top-level module tab visibility and ordering belong to the
Tela 7 reorganization dialog.

On 2026-11-27, the developer determined that the remaining Professional pages neither block nor unlock any phase. Phase 3 is therefore closed with Telas 3–7 and the remaining Professional capabilities deferred to future module work. Their progress, owner, and target dates are recorded in `next_steps.md`.

### 5.3 Phase 3 UI Scope

| Feature | Assigned phase |
|---|---|
| Project search, sorting, selection, and removal UI | Phase 3 |
| Project import/export | Phase 8 |
| Resource preview and resource management | Phase 4B |
| Flow management UI | Phase 5 |
| Recent Projects and SQLite ProjectIndex | Phase 8 |
| Professional Telas 3–7 and remaining module capabilities | Future Professional backlog |

The coordinated deletion API and the Phase 3 project-management UI are implemented, including search, selection, confirmation, error handling, and catalog refresh. Project import/export remains a Phase 8 deliverable.

### 5.4 Deferred Diagnostic Subsystem

The **Monitor de Logs** is specified in `monitor_logs.md`, but is not implemented. It is a developer-facing diagnostic subsystem, distinct from the clinical Console, History, and Telemetry.

Its implementation belongs to a dedicated, unscheduled sprint. It is not a Phase 3, 4, or Release 1.0 requirement.

## 6. Phase Breakdown

### Phase 0 — Foundation & Boot

**Goal:** Establish repository structure, configuration, logging, minimal persistence, and application startup.

**Deliverables:**

- Repository and CI configuration.
- `ConfigurationLoader` and `AppPathResolver`.
- `EventBus`.
- JSON serialization for Project Metadata.
- Boot sequence in `__main__.py`.
- Error handling for inaccessible application paths.
- OS username resolution for the initial actor.
- Flow contracts and repositories.

**Tests:** Configuration, path resolution, boot dependency construction, and startup smoke tests.

**Status:** Complete.

Startup performance optimization and lazy-loading improvements are separate future work and do not affect Phase 0 closure.

### Phase 1 — Contracts, Core Domain & i18n

**Goal:** Establish core domain contracts, repositories, UI contracts, and localization.

**Deliverables:**

- Patient and Project domains.
- Value objects and domain invariants.
- UI contracts: `Area`, `Editor`, `EditorRegistry`, `ToolbarSpec`, `ToolSpec`, `LayoutBuilder`, `LayoutRenderer`.
- `ProjectRepository` and reference implementations.
- `ProjectContext`, `ProjectAccessPolicy`, and `ProjectCatalog`.
- `TranslationService` Protocol and catalogs (`pt_BR`, `en_US`).
- Translation injection into the application shell and existing Editors.
- `EditorContext` propagation, including TaskManager, Telemetry, CommandDispatcher, SceneQuery, EventBus subscription, ThemeService, and IconProvider.

**Tests:** Domain invariants, repository contracts, serialization round-trips, localization completeness, hardcoded-string architecture tests, and EditorContext propagation.

**Status:** Complete, formally closed on 2026-11-18.

### Phase 2 — Workspace Engine & Icons

**Goal:** Establish the Workspace architecture, layout engine, visual theme infrastructure, and centralized icon management.

**Deliverables:**

- `LayoutTree`, `AreaManager`, `LayoutBuilder`, `LayoutRenderer`.
- Workspace facade, TopOverlay, and OverlayManager.
- Three-segment Top Bar and Area toggles.
- Atomic `Workspace.load_spec()`.
- `ThemeService`, `ThemeCompiler`, and canonical design tokens.
- Settings infrastructure and persistence.
- `IconProvider` Protocol and `UnicodeIconProvider`.
- Centralized `IconManager` and icon catalog.
- Icon provider injection into the application shell and shared components.
- `AreaLayoutRenderer` and `EditorStack`.

The existing icon management infrastructure is complete. `SvgIconProvider` and the first six Professional assets were introduced early with Unicode fallback; the remaining bulk asset migration is a Phase 8 integration task.

**Tests:** Layout, Editor lifecycle, rendering, theme resolution, token completeness, icon catalog, fallback, theme integration, accessibility, and settings persistence.

**Status:** Complete, formally closed on 2026-11-18.

### Phase 3 — Project, Home Page & Professional Module

**Goal:** Complete project lifecycle management and the first fully integrated built-in module.

**Deliverables:**

- `ProjectManager`, `ProjectCatalog`, `HomePage`, and `MainWindow`.
- Project selection and opening lifecycle.
- Project search, sorting, selection, and deletion UI.
- `FlowCatalog` and Flow repositories.
- Editor and Module package reorganization (ADR-0015).
- In-memory `ProjectIndex` and synchronization (ADR-0016).
- Coordinated deletion through `ProjectManager`.
- Asynchronous Flow definition loading through `TaskManager`.
- Professional domain, persistence, services, commands, and Editor.
- Professional module navigation, sections, and configuration interactions.

**ProjectIndex architecture:**

The repository remains authoritative. `InMemoryProjectIndex` is a read-optimized projection maintained by `ProjectIndexSynchronizer` and domain events. The index does not own project data or filesystem operations.

SQLite persistence and background disk reconciliation are deferred to Phase 8.

**Tests:**

- Project lifecycle and repository integration.
- ProjectIndex contract and synchronization.
- Bootstrap ordering and stale-index handling.
- Coordinated deletion and failure paths.
- Project management page selection, removal, confirmation, and catalog refresh.
- External Reference data preservation.
- Async loading and Workspace rollback.
- Professional module integration and UI tests.

**Phase closure criteria:**

1. Resolve `ModuleUISpec` ownership within the accepted architecture (approved 2026-11-26).
2. Approve Tela 2 visually (completed 2026-11-26).
3. Complete the accepted L.2 scope and its tests.
4. Verify the delivered Professional profile and navigation workflow.
5. Update documentation and `next_steps.md`.
6. Defer Professional Telas 3–7 as independent future work (approved 2026-11-27).

**Status:** Complete, formally closed on 2026-11-27 with the remaining Professional screens deferred.

### Phase 4A — Imaging Core & Rendering Validation

**Goal:** Validate the complete imaging path from DICOM import to Scene persistence and correct MPR/3D visualization.

This milestone is the principal technical gate for the imaging subsystem. UI expansion must not conceal unresolved rendering or geometry problems.

#### 4A.1 Reference Dataset

Create a controlled **Imaging Reference Dataset** before declaring the rendering pipeline validated.

The initial dataset should include a synthetic asymmetric phantom with:

- Known dimensions and voxel spacing.
- Known orientation and physical origin.
- Known slice positions.
- Distinct, controlled intensity regions.
- Asymmetric structures that reveal axis inversion, transposition, or displacement.
- Expected reference results for axial, coronal, sagittal, and 3D views.

The dataset must be reproducible and independent of patient data.

#### 4A.2 Imaging and Scene Integration

- Complete `CommandDispatcher` integration into Editors.
- Complete `SceneQuery` propagation.
- Integrate `ImportDicomSeriesCommand` with the Scene.
- Validate `Volume`, `VolumeGeometry`, `ImageMetadata`, `VolumeProvenance`, and `IntensityScale`.
- Preserve internal RAS and DICOM LPS-to-RAS conversion.
- Validate DICOM sorting, orientation, spacing, calibration, and intensity handling.
- Handle patient identity mismatches.
- Ensure PHI-safe logging.
- Implement Scene serialization (ADR-0009).
- Implement filesystem-backed Scene persistence.
- Preserve source DICOM as canonical data.
- Define External Reference and Managed Copy behavior.
- Implement VTI export with round-trip validation.

Existing implementations of `DicomSorter`, `DicomValidator`, `DicomSeriesReader`, `ImportReport`, and `VtkImageAdapter` must be validated through the complete pipeline rather than treated as proof of end-to-end correctness.

#### 4A.3 Rendering Integration

- Implement the minimal `RenderingAdapter` between Scene objects and VTK.
- Validate MPR using the existing `vtkImageReslice` pipeline.
- Validate 3D volume rendering using `vtkSmartVolumeMapper`.
- Verify voxel ordering, scalar type, origin, spacing, direction matrix, physical coordinates, and camera bounds.
- Validate resource ownership and repeated open/close behavior.
- Ensure rendering does not mutate clinical source data.
- Keep VTK render-window operations on the GUI thread (ADR-0011).

#### 4A.4 Rendering Acceptance Criteria

The pipeline is considered validated only when:

1. Physical dimensions, spacing, orientation, and origin match the reference dataset.
2. Axial, coronal, and sagittal views display the expected anatomical orientation.
3. Asymmetric phantom structures appear in the correct positions.
4. Crosshair and slice navigation correspond to the same physical coordinates across views.
5. Intensity values and Window/Level behavior match the reference.
6. 3D rendering displays the expected volume bounds and orientation.
7. No unexplained transposition, inversion, displacement, or geometry distortion remains.
8. Scene serialization and reload preserve the expected geometry and visualization state.
9. Tests pass on the supported Windows environment, including rendering lifecycle checks.

The reference dataset and acceptance tests must be retained for Phase 7.

#### 4A.5 Module Infrastructure

Complete module discovery and registration for:

- Built-in module manifests.
- Dependency resolution.
- Entry-point imports.
- Editors, Tools, Services, and Flow definition registration.
- Shared EventBus across ModuleContexts.

This milestone provides module infrastructure and discovery only. It does not execute clinical workflows.

**Tests:** DICOM import, geometry, calibration, NumPy/VTK interoperability, Scene lifecycle, persistence, reference dataset, MPR/3D rendering, and module registration.

**Status:** In progress.

### Phase 4B — Import & Visualization UI

**Goal:** Expand the validated imaging core into the complete import and visualization interface.

#### 4B.1 Unified Import Dialog

- `ImportManager` with categories:
  - Volumes
  - Radiographs
  - Scans
  - Photographs
  - Meshes
  - Dental Implants
  - Facial Implants
- Sources: Project, File, Sample Data.
- `ImportDialog` with category navigation, source selector, asset grid/list, preview, and selection actions.
- Per-category importers.
- Auto-tagging and resource metadata.
- Scene and DomainObjectStore integration.
- TaskManager progress, cancellation, and error reporting.

#### 4B.2 Resource Management

- Resource preview.
- Resource selection and management.
- Asset metadata and contextual actions.
- Integration with Scene and project ownership rules.

#### 4B.3 Viewer Layouts

Implement `ViewerLayoutManager` supporting:

- 1×1, 2×2, and 3×3 layouts.
- Editable layouts up to 6×4.
- Panoramic and ATM-specific layouts.
- Active and inactive view states.
- Viewer maximization and restoration.

#### 4B.4 Visualization Tools

**2D tools:**

- Brightness and contrast.
- Pan and zoom.
- HU/intensity probe.
- ROI.
- Nerve drawing.
- Distance and angle.
- Crosshair and ruler.
- LUT selection and inversion.
- Background color.
- Animation and thumbnails.

**3D tools:**

- ROI, cut, and paint.
- Annotations.
- Distance and angle.
- Rendering preset selection.
- Orthographic and perspective projection.
- Background color.
- Rotation lock and thumbnails.

#### 4B.5 Clinical Visualization

- HU-based transfer functions: `bone_cortical`, `bone_trabecular`, `soft_tissue`, `air`, `metal`, and `cbct_percentile`.
- Viewer status indicators and orientation badges.
- Remove debug bounding geometry.
- Validate VTK resource lifecycle.

**Tests:** Import Dialog integration, resource management, ViewerLayoutManager, tool behavior, LUT selection, presets, UI rendering, and performance.

**Status:** Planned.

### Phase 5 — Clinical Flows & Panel Widget Registry

**Goal:** Implement workflow execution, panel composition, and layout persistence.

**Deliverables:**

- `WorkflowEngine` for requirements, transitions, and execution state.
- JSON Flow loading and requirement evaluation.
- Step-state computation.
- `WorkflowBreadcrumb` in the Top Bar.
- Flow state persistence.
- `PanelRegistry` with ID-based registration and Area assignment.
- Multiple registered panels per Area.
- Panel visibility, ordering, and layout integration.
- Layout State Persistence (ADR-0010).
- Integration with the production ModuleRegistry and ModuleLoader.
- Flow management UI: create, select, remove, import, export, inspect module sequence, and add modules.

**Built-in panel groups:**

| Area | Panels |
|---|---|
| Left | Objects, Volumes, Cephalometric Points, Masks, Measurements |
| Right | Registry, Scene, History, Material, Osteotomy Patterns, Object Properties, Tomography, Segmentation |
| Bottom | Console, History, Animation, AI Assistant, Nodes |

The Console remains a clinical/application notification channel, distinct from the developer-facing Monitor de Logs.

**Tests:** Workflow transitions, requirement evaluation, Flow persistence, PanelRegistry contracts, Area composition, and layout round-trips.

**Status:** Planned.

### Phase 6 — Clinical Pipeline

**Goal:** Implement the clinical capabilities required for the initial orthognathic surgery workflow.

The subprojects are independently scoped and must have their own implementation and validation criteria.

#### 6A — Tomography & Segmentation

- Clinical Tomography Editor workflow.
- Synchronized axial, coronal, and sagittal navigation.
- Physical-coordinate crosshair and slice positioning.
- Slice distance, count, and range controls.
- Window/Level and intensity controls.
- Intensity probing.
- Display ROI and processing ROI.
- Threshold-based segmentation.
- Mask creation and editing.
- Paint, erase, hole closing, and small-segment removal.
- Surface generation from segmentation masks.
- Curved MPR and panoramic reconstruction.
- Clinical workflow integration.

AI-assisted segmentation is not a prerequisite for this milestone. Advanced AI platform integration belongs to Phase 10.

#### 6B — Registration & Cephalometry

**Technical deliverables:**

- Image and surface registration.
- Reference-based alignment.
- Cephalometric template system.
- Automatic, AI-assisted, and reference-based landmark localization.
- Primary and secondary landmark classification.
- Point connectivity.
- Landmark refinement and verification.
- Cephalometric measurements and reports.
- Registration and landmark validation.

Manual localization is a refinement and fallback strategy, not the primary system architecture.

**AI scope:** AI-assisted landmark localization is a specific, reviewable clinical algorithm within this subproject. It is distinct from the general AI Assistant, Node System, and MCP infrastructure planned for Phase 10.

**Scientific data protocol:**

The target of at least 30 CBCT cases requires a data acquisition and validation plan before implementation is considered scientifically complete.

The protocol must define:

- Data source and case eligibility.
- Inclusion and exclusion criteria.
- Ethics Committee/CEP approval or formal determination, as applicable.
- Anonymization and secure storage.
- Data access and governance.
- Landmark annotation protocol.
- Reference standard and examiner qualification.
- Intra- and inter-examiner reliability.
- Separation of development and validation datasets.

Data availability and ethical approval must not be assumed. These are independent prerequisites that may require more time than software implementation.

#### 6C — Osteotomy

- Le Fort I, BSSO, and genioplasty.
- Osteotomy pattern library.
- Boolean operations and fragment separation.
- Fragment movement and transform management.
- Preoperative and postoperative comparison.
- Animation.
- Soft-tissue thickness and color maps.
- Surgical plan persistence.

#### 6D — Surgical Guides

- Parametric guide generation.
- Guide-to-anatomy fit validation.
- Manufacturing constraints.
- Export for additive manufacturing.

#### 6E — Integrated Clinical Workflow

- End-to-end orthognathic workflow.
- Data integrity and reproducibility.
- Geometric validation.
- Clinical workflow usability.
- Integration of segmentation, registration, osteotomy, and guide generation.

**Status:** Planned.

### Phase 7 — Scientific Validation

**Goal:** Execute the scientific validation protocols defined in the doctoral research project.

**Deliverables:**

- Imaging geometry validation using the Phase 4A reference dataset.
- DICOM and rendering reproducibility.
- Geometric validation reports.
- Clinical accuracy evaluation.
- Inter- and intra-examiner reliability.
- ICC and measurement error analysis.
- Usability evaluation.
- Performance evaluation on reference hardware.
- Documentation of methods, results, and limitations.

Clinical validation must use the approved dataset and protocol established in Phase 6B, as applicable.

**Status:** Planned.

### Phase 8 — Scientific Product (Release 1.0)

**Goal:** Consolidate the validated clinical core into a stable and distributable scientific product.

**Deliverables:**

**Distribution and reliability**
- Windows installer.
- Autosave and crash recovery.
- Performance profiling and optimization.
- Release packaging and versioning.
- Final user and developer documentation.

**Project management**
- Recent Projects on the Home Page.
- `SqliteProjectIndex`, implementing the existing `ProjectIndex` Protocol.
- Background disk reconciliation (ADR-0016).
- Project import/export with compatibility, versioning, and integrity validation.

**Appearance and localization**
- Complete the SVG asset catalog for the remaining logical icon names.
- Continue progressive migration of UI icons from Unicode to SVG.
- Close the final icon visual style, licensing, and provenance review.
- Complete shared-widget migration to `ThemeService` and the existing icon management infrastructure.
- Locale selector UI.
- Complete `pt_BR` and `en_US` catalogs.
- Locale-aware formatting.
- High-contrast theme (`ThemeName.HIGH_CONTRAST`).

**Medical visualization**
- Custom volume-rendering preset editor.

**Scientific dissemination**
- Scientific publication.
- DOI registration.
- Public release.

**Status:** Planned.

### Phase 9 — Extensibility (Release 2.0)

**Goal:** Enable external development and community contributions.

**Deliverables:**

- Stable Module API.
- Plugin API.
- Plugin loader and permission boundaries.
- External plugin catalog.
- Module-owned persisted state.
- State migration contract.
- Compatibility and versioning policies.

**Status:** Planned.

### Phase 10 — AI and Nodes (Release 3.0)

**Goal:** Introduce advanced automation and procedural workflows.

**Deliverables:**

- Non-destructive Node System.
- Graph evaluation and execution.
- AI Assistant Editor.
- General AI-assisted clinical operations.
- MCP Server integration.
- Command parity between UI and automated execution.

This phase covers platform-level AI and automation capabilities. It does not replace the specific AI-assisted landmark localization planned in Phase 6B.

**Status:** Planned.

## 7. Testing Strategy & Metrics

Testing is a clinical requirement. Performance and accuracy claims must be reproducible and contextualized.

### 7.1 Test Coverage

| Layer | Required validation |
|---|---|
| Domain | Invariants, value objects, error cases |
| Application | Commands, transactions, events, tasks, workflows |
| Infrastructure | DICOM, geometry, calibration, persistence |
| UI | Widget behavior, Editor lifecycle, Workspace integration |
| Appearance | Tokens, themes, contrast, icon catalog |
| Integration | Scene, import, rendering, persistence |
| End-to-End | Clinical workflows using synthetic or approved datasets |

### 7.2 Performance Targets

All targets require a defined Reference Dataset and Reference Hardware.

Initial targets:

- **DICOM Import:** 500-slice reference dataset in under 10 seconds, including indexing and readiness for first visualization.
- **Surface Rendering:** 30+ FPS for a mesh of 1,000,000 polygons on reference hardware.
- **Memory:** Below 4 GB RAM during standard facial CT processing.
- **Project Catalog:** No filesystem I/O per keystroke after index bootstrap; verify through call-count tests and benchmarks.

These are targets, not verified performance claims.

### 7.3 CPU and GPU

- Clinical data and semantic objects remain in main memory and the Domain Scene.
- GPU memory stores rendering representations and resources.
- GPU acceleration is optional for core clinical workflows.
- CPU fallback must remain available for essential operations.

### 7.4 Concurrency

- `TaskManager` is the application mechanism for off-thread work (ADR-0011).
- Long-running DICOM parsing, segmentation, registration, and mesh processing execute as Tasks.
- GUI and VTK render-window operations remain on the GUI thread.
- Cancellation is cooperative.
- `QTimer` must not be used as a substitute for background execution.

### 7.5 Telemetry and Privacy

- Long-running operations emit telemetry through `TelemetrySink`, using correlation IDs (ADR-0012).
- Telemetry and logs must not contain PHI.
- Project synchronization failures log only `project_id` and operation name.
- The Monitor de Logs is a logging view, not a telemetry channel.

## 8. Definition of Done

A phase is complete when:

1. Implementation follows accepted architecture and relevant ADRs.
2. Applicable unit, contract, integration, and UI tests pass.
3. New Protocols have contract tests.
4. CI is green.
5. Documentation is updated.
6. The intended UI workflow is usable.
7. Unresolved TODOs are linked to tracked work.
8. No production `NoOp*` placeholder remains for a service claimed as delivered.
9. Deprecated APIs are removed from call sites or have an explicitly accepted compatibility layer.
10. Known technical debt is fixed or tracked.
11. Data integrity, failure handling, and recovery are tested where relevant.
12. User-facing strings use `TranslationService`.
13. Shared visual properties use the appearance architecture, with any remaining migration debt explicitly tracked.

### 8.1 Release 1.0 Scope

Release 1.0 delivers the validated clinical core defined by the doctoral research scope.

It does not require:

- External Plugins.
- Node System.
- General AI/MCP platform integration.
- Multi-monitor support.

These capabilities belong to Releases 2.0 and 3.0.

## 9. Implementation Record

This section records the current implementation baseline and major completed architectural work. Detailed implementation procedures belong in their respective ADRs and sprint documentation.

### 9.1 Foundation and Workspace

Phases 0–2 are closed.

- Configuration, logging, application paths, EventBus, and boot sequence are implemented.
- Domain and UI contracts are established.
- Localization contracts and catalogs are implemented.
- ThemeService, ThemeCompiler, and canonical design tokens are implemented.
- IconManager, IconProvider, UnicodeIconProvider, and the initial icon catalog are implemented.
- Workspace layout, overlays, Area rendering, and EditorStack are implemented.

The SVG provider foundation, theme recoloring, HiDPI rendering, fallback, cache, and six Professional navigation assets are implemented. The remaining SVG asset migration is a Phase 8 deliverable.

### 9.2 Editor Architecture

ADR-0015 was completed on 2026-11-18.

The refactoring separated Editor contracts from implementations, moved concrete Editors into the appropriate package, separated reusable Views from Editors, and added architecture tests for dependency boundaries.

See ADR-0015 and `refactoring_plan.md`.

### 9.3 Project Catalog

ADR-0016 was accepted on 2026-11-18.

The repository remains authoritative. `InMemoryProjectIndex` is a read-optimized projection maintained by `ProjectIndexSynchronizer` and domain events.

Sprint I completed on 2026-11-20. Sprint J completed on 2026-11-22. Sprint K completed on 2026-11-22.

The SQLite index and background disk reconciliation remain Phase 8 deliverables.

### 9.4 Professional Module

Phase 3 closed on 2026-11-27 with Sprint L's accepted scope complete.

The Professional domain, SQLite profile persistence, service/repository boundary, command/query flow, ProfessionalEditor, Tela 2, and settings integration have been implemented. `ModuleUISpec` ownership and Tela 2 visual approval were completed on 2026-11-26. `IconSidebar` now provides the six-item internal navigation and persists the active tab through `professional.ui.last_section`. Tela 2 section ordering and expansion state are persisted through `professional.ui.navigation_order` and `professional.ui.collapsed_sections`.

The remaining Professional pages and capabilities are future backlog work. They are independent of the active clinical-imaging sequence.

### 9.5 Imaging

The imaging foundation includes:

- `Volume`, `VolumeGeometry`, `ImageMetadata`, `VolumeProvenance`, and `IntensityScale`.
- Internal RAS convention and DICOM LPS-to-RAS conversion.
- DICOM sorting, validation, and series reading.
- NumPy `[z, y, x]` convention.
- `Volume` ownership of the voxel buffer.
- `VtkImageAdapter` sharing the buffer.
- Explicit intensity calibration state.
- MPR and 3D view implementations.

The complete DICOM-to-Scene-to-rendering path must still pass the Phase 4A reference dataset and acceptance criteria. Existing implementations must not be interpreted as proof of end-to-end validation.

### 9.6 Validation Baseline

The last recorded full validation baseline, rerun on 2026-11-27 after the Home Page refinement and project-management UI delivery, is:

- 1935 passed.
- 0 failed.
- 0 errors.
- 2 skipped.
- `ruff check` clean.
- `ruff format --check` clean (649 files).
- `mypy src` clean (328 source files).

Each subsequent sprint must record its own validation results.

## 10. Deferred Work and Architectural References

This section consolidates deferred items to avoid repeating them throughout the roadmap.

| Item | Destination | Reference |
|---|---|---|
| Startup optimization and lazy imports | Future backlog | Boot architecture |
| TimelineSlider, ColorPicker, Histogram, final harness and HiDPI closure | Future Professional backlog | `next_steps.md` |
| Professional Telas 3–7 and remaining module capabilities | Future Professional backlog | `professional.md`, `next_steps.md` |
| Monitor de Logs | Dedicated unscheduled sprint | `monitor_logs.md` |
| SQLite ProjectIndex and disk reconciliation | Phase 8 | ADR-0016 |
| Project import/export | Phase 8 | Project persistence and compatibility design |
| Remaining SVG UI asset migration | Phase 8 | Appearance and icon architecture |
| GeometryRevision, content-hash deduplication, persistent asset storage, ValidationProfile, GeometryOperation, booleans, welding, and benchmarks | Future geometry work | Geometry architecture |
| General AI and Node infrastructure | Phase 10 | AI and Nodes architecture |

The following refactoring items remain deferred to future PRs:

- `application/event_bus.py` → `application/events/bus.py`, per `refactoring_plan.md`.
- `editors/view_overlays/`, pending a concrete implementation need.

Detailed specifications and architectural rationale belong in the referenced documents. This roadmap defines sequencing, scope, and completion criteria; it does not replace ADRs, `next_steps.md`, or feature-specific specifications.
