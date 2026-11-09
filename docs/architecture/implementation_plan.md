# Implementation Plan

**Document type:** Roadmap and execution plan
**Status:** Living document
**Scope:** Phased implementation of the CranioZ platform, from foundation to release
**Last updated:** 2026-11-08

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
11. **Centralized Appearance:** Shared visual properties must use design tokens. Component-specific constraints and intrinsic dimensions may be defined locally when they are not part of the shared visual system. See `docs/architecture/appearance/`.

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
| **Phase 1** | Contracts, Core Domain & i18n | 🚧 In Progress | `EditorContext` propagation (Sprint C) |
| **Phase 2** | Workspace Engine & Icons | 🚧 In Progress | `IconProvider`, `AreaLayoutRenderer`, `EditorStack` |
| **Phase 3** | Project, Home Page & Professional Module | 🚧 In Progress | `ProjectIndex`, coordinated deletion, async loading, Professional module |
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

**Contracts layer:** ADR-0001, ADR-0002, ADR-0004–0014 are Accepted. **ADR-0014 (Widget Toolkit Selection)** is Accepted: Qt Widgets + QSS modular + Design Tokens in Python, not QML. The appearance architecture is specified in `docs/architecture/appearance/`.

**Application layer:** Commands, Tasks, Telemetry, Events and Flows have contracts and reference implementations with contract tests. This does not imply that all production services, module loading, or application workflows are complete.

---

## 5. Current Focus

**Phases 1, 2, and 3** are being closed formally before deeper investment in Phase 4. This prevents silent debt from accumulating as the clinical pipeline grows.

Phase 4 remains the next major implementation phase. It begins only after Phases 1–3 are marked `✅ Implemented` in this document.

### 5.1 Immediate Priorities

The sprint order below respects dependencies between Phases 1–3.

| Sprint | Phase | Deliverable | Status | Depends on |
|---|---|---|---|---|
| **B** | 1 | i18n contract and catalogs | ✅ Complete | — |
| **C** | 1 | `EditorContext` propagation | 🚧 Pending | B, E (for `theme_service`), F (for `icon_provider`) |
| **E** | 2 | `ThemeService`, `ThemeCompiler`, tokens | ✅ Complete | — |
| **F** | 2 | `IconProvider`, `UnicodeIconProvider`, glyph migration | 🚧 Pending | E |
| **G** | 2 | `AreaLayoutRenderer` | 🚧 Pending | — |
| **H** | 2 | `EditorStack` | 🚧 Pending | G |
| **I** | 3 | `ProjectIndex` | 🚧 Pending | — |
| **J** | 3 | Coordinated deletion | 🚧 Pending | I |
| **K** | 3 | Async loading | 🚧 Pending | I, J |
| **L** | 3 | Professional module | 🚧 Pending | C, E, F |

**Next sprint:** Sprint F — `IconProvider` + `UnicodeIconProvider` + glyph migration.

**Note on ordering:** Sprint C depends on Sprints E and F because `EditorContext` will carry `theme_service` and `icon_provider`. Sprint E is now complete; Sprint F is the remaining dependency before Sprint C can start. Alternatively, Sprint C can propagate only services that exist at that time, with a follow-up PR adding `theme_service` and `icon_provider`. The first approach is cleaner and is the recommended one.

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

**Tests:** Configuration validation, path resolution, boot dependency construction, startup smoke tests.

**Status:** ✅ Implemented, with startup performance work tracked separately.

---

### Phase 1: Contracts, Core Domain & i18n

**Goal:** Close Phase 1 formally. Blocker: `EditorContext` propagation (Sprint C).

**Deliverables:**

- ✅ Patient Domain and value objects.
- ✅ Project Domain.
- ✅ UI contracts: `Area`, `Editor`, `EditorRegistry`, `ToolbarSpec`, `ToolSpec`, `LayoutBuilder`, `LayoutRenderer`.
- ✅ `ProjectRepository` and reference implementations.
- ✅ `ProjectContext`, `ProjectAccessPolicy`, `ProjectCatalog`.
- ✅ ADRs 0001, 0002, 0004–0014.
- ✅ **Sprint B (i18n):**
  - `Locale` value object (`pt_BR`, `en_US`).
  - `TranslationService` Protocol (`tr`, `locale`, `set_locale`).
  - `TranslationCatalog` (JSON loader) + `TranslationCatalogRegistry`.
  - Concrete `TranslationService` with `en_US` fallback.
  - `en_US` and `pt_BR` catalogs for existing keys.
  - Injection into `MainWindow`, `Workspace`, `HomePage`, `TomographyEditor`.
  - Removal of `MainWindow._humanize_translation_key`.
  - Contract test: every `name_key` in every `flow.json` resolves in `en_US`.
  - `tests/architecture/test_no_hardcoded_strings_in_shell_widgets.py`: shell widgets must route user-facing strings through `tr(...)`.
- 🚧 **Sprint C (`EditorContext` propagation):**
  - Depends on Sprints E (`theme_service`, complete) and F (`icon_provider`, pending).
  - Propagate `task_manager`, `telemetry`, `correlation_id`, `command_dispatcher`, `scene_query`, `event_subscription`, `translation_service`, `theme_service`, `icon_provider`.
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
- 🚧 `EditorContext` propagation tests (pending Sprint C).

**Status:** 🚧 In Progress. Blocker: Sprint C.

---

### Phase 2: Workspace Engine & Icons

**Goal:** Close Phase 2 formally. Blockers: `IconProvider` + `UnicodeIconProvider`, `AreaLayoutRenderer`, `EditorStack`.

**Deliverables:**

- ✅ `LayoutTree`, `AreaManager`, `LayoutBuilder`, `LayoutRenderer`.
- ✅ `Workspace` facade, `TopOverlay`, `OverlayManager`.
- ✅ Three-segment Top Bar.
- ✅ Area toggles (Left, Right, Bottom).
- ✅ Atomic `Workspace.load_spec()`.
- ✅ **Sprint E (`ThemeService` + `ThemeCompiler` + tokens):**
  - `ThemeMode` (`DARK`, `LIGHT`, `SYSTEM`) and `ThemeName` (`DARK`, `LIGHT`) as `StrEnum`.
  - `ThemeTokens` + 7 dataclasses (Colors, Typography, Spacing, Dimensions, Borders, Effects, Surfaces).
  - 47 tokens as specified in `docs/architecture/appearance/themes-and-design-tokens.md`.
  - `ThemeService`: `mode()`, `set_mode()`, `theme()`, `tokens()`, `color()`, `dimension()`, `surface_color()`, `icon_name()`, `theme_changed` signal, `SYSTEM` resolution via `QStyleHints.colorScheme()`.
  - `ThemeCompiler`: `compile()`, `apply()`, surface composition (toolbar, popover, modal_backdrop), QSS emission. `modal_backdrop` uses a fixed `#000000` base per spec §6.2.
  - `cranioz.infrastructure.settings` package: `SettingsService` protocol, `InMemorySettingsService`, `FilesystemSettingsService`, `SettingsStore`, `SettingsMigrator`, `KNOWN_KEYS`, `SettingsError`, `SettingsMigrationError`.
  - `AppPathResolver.user_settings_path()` and `PathsConfig.settings_root` (default `~/.cranioz/Settings/settings.json`).
  - Boot integration: read `appearance.theme_mode` from `SettingsService` before `MainWindow`; invalid → `DARK` + `WARNING`; apply theme before the first window.
  - Contract tests: `test_no_hardcoded_appearance.py`, `test_tokens_used.py`, `test_tokens_present.py`, `test_theme_completeness.py`, `test_theme_values.py`, `test_contrast.py`.
  - Unit tests: `test_service.py`, `test_tokens.py`, `test_compiler.py`, `test_settings_service.py`.
  - Known debt registered in `_KNOWN_DEBT_FILES` for the widget migration sprint (6 files, 26 literals).
- 🚧 **Sprint F (`IconProvider` + `UnicodeIconProvider`):**
  - `IconState` enum.
  - `IconProvider` Protocol.
  - `UnicodeIconProvider` with 60-icon catalog from `icons.md`.
  - Injection into `MainWindow`, `Workspace`, `EditorContext`.
  - Migration of hardcoded glyphs in `TopBar`, `HomeSegment`, `ModulesSegment`, `ExtrasSegment`, `HomePage`, `Toolbar`.
  - Contract tests: `test_icon_catalog.py`, `test_icon_fallback.py`, `test_icon_theme.py`, `test_icon_widget_contract.py`, `test_icon_accessibility.py`.
- 🚧 **Sprint G (`AreaLayoutRenderer`):**
  - Separates inter-Area from intra-Area layout.
  - `AreaWidget` delegates to `AreaLayoutRenderer`.
  - No visible behavior change for the single-Editor case.
  - Regression tests.
- 🚧 **Sprint H (`EditorStack`):**
  - `EditorLayoutSpec.stack([...])`.
  - `EditorStack` widget (tabs per Leaf).
  - Single-Editor case remains unchanged.
  - Tests for tab switching, editor lifecycle, dispose.

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

**Status:** 🚧 In Progress. Blockers: Sprints F, G, H.

---

### Phase 3: Project, Home Page & Professional Module

**Goal:** Close Phase 3 formally. Blockers: `ProjectIndex`, coordinated deletion, async loading, Professional module.

**Deliverables:**

- ✅ `ProjectManager`, `ProjectCatalog`, `HomePage`, `MainWindow`.
- ✅ Project selection lifecycle.
- ✅ `FlowCatalog` and Flow repositories.
- 🚧 **Sprint I (`ProjectIndex`):**
  - `ProjectIndex` interface (`add`, `remove`, `lookup`, `list`).
  - `InMemoryProjectIndex`.
  - `FilesystemProjectIndex`.
  - `ProjectCatalog` consumes `ProjectIndex` instead of scanning the filesystem directly.
  - Contract tests: add/remove/lookup/list, concurrent access, cache invalidation.
- 🚧 **Sprint J (Coordinated deletion):**
  - `ProjectManager.delete_project` coordinates `ProjectCatalog` → `ProjectIndex` → `FilesystemProjectRepository`.
  - Rollback when any step fails.
  - External source data (External Reference mode) is never removed by project deletion.
  - Contract tests.
- 🚧 **Sprint K (Async loading):**
  - `HomePage` loads projects and flows via `TaskManager`.
  - No blocking I/O in `MainWindow.__init__`.
  - `HomePage.refresh()` does not block the GUI thread.
  - Rollback if `Workspace` creation fails after project open.
  - Regression tests.
- 🚧 **Sprint L (Professional module):**
  - `ProfessionalEditor` registered in `EditorRegistry`.
  - `ModuleUISpec` for the Professional module.
  - Settings integration (`professional.*` keys).
  - Tests.

**Deferred to Phase 8:**

- SQLite `ProjectIndex` backend.
- Recent Projects.
- Background disk reconciliation.

**Tests:**

- Project lifecycle tests.
- Filesystem repository integration tests.
- HomePage selection and refresh regression tests.
- Project opening and rollback tests.
- ProjectIndex consistency tests.
- Professional module integration tests.

**Status:** 🚧 In Progress. Blockers: Sprints I, J, K, L.

---

### Phase 4: Scene & Visualization

**Status:** ⏳ Planned. Begins after Phases 1–3 are marked `✅ Implemented`.

**Goal:** Complete the integration between the Application layer, Scene, imaging infrastructure, rendering adapters, and Editors.

#### 4.1 Application Layer

- ✅ `application/commands/`, `tasks/`, `telemetry/`, `events/` contracts and reference implementations.
- 🚧 `CommandDispatcher` integration into all Editors.

#### 4.2 Scene and Domain Integration

- ✅ `domain/scene/`, `application/scene/`.
- ✅ `ImportDicomSeriesCommand` and handler.
- 🚧 Complete `SceneQuery` propagation.
- ⏳ Scene serialization (ADR-0009).
- ⏳ Filesystem-backed Scene persistence.
- ⏳ Complete integration between Commands, Scene and imported objects.

#### 4.3 Medical Imaging Infrastructure

**4.3.1 Volume and geometry**

- ✅ `Volume`, `VolumeGeometry`, `ImageMetadata`, `VolumeProvenance`, `IntensityScale`.
- ✅ Internal RAS convention.
- ✅ LPS-to-RAS conversion.
- ✅ Explicit intensity calibration state.

**4.3.2 DICOM import and validation**

- ✅ `DicomSorter`, `DicomValidator`, `DicomSeriesReader`, `ImportReport`.
- ✅ `spacing_z` from `ImagePositionPatient` distance.
- ✅ `RescaleSlope`/`RescaleIntercept` per slice.
- ⏳ Patient identity mismatch handling.
- ⏳ PHI-aware logging.

**4.3.3 Memory and interoperability**

- ✅ Voxel buffer ownership: `Volume` owns; `VtkImageAdapter` shares.
- ✅ NumPy `[z, y, x]` convention.
- ✅ Voxel ordering contract: `data.ravel(order="C")` without transposition. Regression test enforced.
- ✅ Production scalar type: `VTK_SHORT`.
- ✅ Direction matrix applied in `VtkImageAdapter`.

**4.3.4 Unified Import Dialog (required)**

- `ImportManager` with categories (Volume, Radiographs, Scans, Photographs, Meshes, Dental Implants, Facial Implants), sources (project, file, sample data), preview, auto-tagging.
- `ImportDialog` with tab bar, source selector, asset grid/list, preview panel, add/remove/select actions.
- Per-category importers.
- Scene and DomainObjectStore integration.
- TaskManager progress, cancellation, error reporting.

**4.3.5 Storage and export**

- ⏳ External Reference and Managed Copy storage modes.
- ⏳ Preserve source DICOM as canonical.
- ⏳ VTI export with round-trip validation.
- ⏳ Project deletion never removes external source data.

#### 4.4 Geometry Infrastructure

**Implemented:** `Mesh`, `CoordinateFrame`, STL I/O, VTK adapter, `MeshDebugEditor`.

**Deferred:** `GeometryRevision`, content-hash deduplication, persistent asset storage, `ValidationProfile`, `GeometryOperation`, booleans, welding, benchmarks.

#### 4.5 Visualization Infrastructure

**Implemented:**

- ✅ `MPRView` (manual `vtkImageReslice` pipeline).
- ✅ `Viewport3DView` (`vtkSmartVolumeMapper`, `VTK_SHORT`).
- ✅ Axial, coronal, sagittal, 3D orientations.
- ✅ Volume rendering presets.
- ✅ `set_volume(Volume)`, `set_mesh(Mesh)`.
- ✅ DICOM volume path validated in MPR and 3D.

**Pending:**

- ⏳ `RenderingAdapter` between Scene and VTK.
- ⏳ **ViewerLayoutManager** (dynamic grids: 1×1, 2×2, 3×3, editable up to 6×4, panoramic, ATM).
- ⏳ **2D Tools** (brightness/contrast, pan, zoom, HU probe, ROI, nerve drawing, distance/angle, crosshair, ruler, LUT selection, LUT inversion, background color, animation, thumbnail).
- ⏳ **3D Tools** (ROI, cut, paint, annotations, distance/angle, preset selection, orthographic/perspective, background color, lock rotation, thumbnail).
- ⏳ **Clinical transfer functions** (HU-based presets: `bone_cortical`, `bone_trabecular`, `soft_tissue`, `air`, `metal`, `cbct_percentile`).
- ⏳ **Viewer status indicators** (active view badge, orientation badge, inactive state).
- ⏳ Remove the debug bounding box from `Viewport3DView`.
- ⏳ VTK resource lifecycle under repeated open/close.
- ⏳ Headless and Windows rendering tests.

**Architectural constraints:**

- Domain data must not depend on VTK.
- VTK actors, mappers, and render windows are presentation objects.
- Rendering adapters translate semantic Scene objects into renderable representations.
- Rendering updates must not mutate clinical source data.
- VTK render-window and actor lifecycle operations remain on the GUI thread (ADR-0011).

#### 4.6 Module Integration

- 🚧 `InMemoryModuleLoader` with dependency resolution.
- 🚧 Entry-point imports.
- 🚧 Tools, Editors, Services, Flows registration.
- 🚧 `BUILTIN_MANIFESTS`.
- 🚧 Shared EventBus across ModuleContexts.
- ⏳ First functional built-in module.

#### 4.7 Tests

- DICOM import tests.
- Geometry and coordinate conversion tests.
- Slice ordering and spacing validation.
- Intensity calibration tests.
- NumPy/VTK interoperability tests.
- Geometry Infrastructure tests.
- VTI round-trip tests.
- Scene lifecycle and persistence tests.
- ✅ Voxel ordering regression tests.
- ✅ `int16` fidelity test.
- ✅ `spacing_z` test.
- ⏳ Import Dialog end-to-end tests.
- ⏳ ViewerLayoutManager tests.
- ⏳ Tool behavior tests.
- ⏳ LUT selection and inversion tests.
- ⏳ Preset selection tests.
- ⏳ Performance tests.

---

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
- **SQLite ProjectIndex** (backend for the Phase 3 contract).
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
- **Application:** Command execution, transaction rollback, event publication, task lifecycle, i18n contract, settings round-trip.
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

### 7.5 Telemetry

Long-running operations must emit telemetry events through `TelemetrySink`, using correlation IDs (ADR-0012). Telemetry must not contain PHI.

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
11. Every user-facing string resolves through `TranslationService`.
12. Every shared visual property resolves through `ThemeService`; no hardcoded color, size, spacing, radius, opacity or font weight in the Qt presentation layer, except for the files explicitly listed in `_KNOWN_DEBT_FILES` (widget migration sprint).

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

The foundation, core domain, workspace, project lifecycle, imaging pipeline, and DICOM visualization are implemented. The voxel-ordering bug that blocked Phase 4 was resolved on 2026-11-06. The appearance architecture is decided (ADR-0014, `docs/architecture/appearance/`).

Sprint B (i18n) is complete: the shell — `MainWindow`, the Home Page tree, the three Top Bar segments, and the Workspace placeholder editor — resolves user-facing strings through the `TranslationService`. The architecture guard `tests/architecture/test_no_hardcoded_strings_in_shell_widgets.py` prevents regressions.

Sprint E (appearance foundation) is complete: `ThemeService` and `ThemeCompiler` are implemented, the 47 canonical design tokens are defined for `DARK` and `LIGHT`, the `cranioz.infrastructure.settings` package provides typed, versioned, and atomically written user settings, and `AppPathResolver.user_settings_path()` resolves the user settings file. The theme is applied at boot before the first window. The test suite grew by 177 tests; total is 1510 passing with 0 failures and 88% coverage. `tests/architecture/test_no_hardcoded_appearance.py` guards against new hardcoded colors and freezes the existing debt for the widget migration sprint.

The immediate focus is closing Phases 1, 2, and 3 formally through Sprints C, F, G, H, I, J, K, L. Sprints B and E are closed; Sprint C is the remaining Phase 1 blocker, and Sprint F is the next Phase 2 deliverable.

Phase 4 begins after Phases 1–3 are marked `✅ Implemented`. Its first deliverables are the Unified Import Dialog, the `RenderingAdapter`, the `ViewerLayoutManager`, the 2D/3D tools, and the clinical transfer function presets.

The geometry infrastructure initial subset is validated. Full geometry infrastructure is deferred.

---

## 10. Known Issues and Resolutions

### 10.1 ADR-0014 (Widget Toolkit Selection) — Accepted

Qt Widgets + QSS modular + Design Tokens in Python. QML rejected as shell foundation. Appearance architecture lives in `docs/architecture/appearance/`. The legacy ADR-0003 is superseded.

### 10.2 Internationalization — Shell migrated (Sprint B complete)

- `TranslationService`, `TranslationCatalog`, `TranslationCatalogRegistry` are implemented and injected.
- `MainWindow._humanize_translation_key` was removed; every shell widget resolves user-facing strings via `tr(...)`.
- `tests/architecture/test_no_hardcoded_strings_in_shell_widgets.py` guards against regressions: it scans the AST of each shell file and fails if a user-facing literal is passed directly to a Qt widget constructor or setter without going through `tr(...)`. The whitelist documents every exception (glyphs, `objectName`, QSS selectors, composite file-dialog filters).
- Pending: `EditorContext` propagation (Sprint C) and full `pt_BR` / `en_US` catalog coverage (Phase 8).

### 10.3 `IconProvider` — Contract defined in Sprint F; product in Phase 8

- Sprint F: `IconProvider` Protocol, `UnicodeIconProvider`, migration of hardcoded glyphs.
- Phase 8: `SvgIconProvider`, cache, SVG assets, full migration of every widget.

### 10.4 `steps_panel` overlay — Removed

The previous `steps_panel` overlay is **removed from the roadmap**.

Rationale:

- The prototype defines a rich Top Bar with module tabs (Tomography, Registration, Cephalometry, Segmentation, Osteotomy) that already communicates the workflow.
- A dedicated steps panel duplicates that information and consumes clinical image space.
- Navigation between steps is served by module tabs and panel widgets.

Replacement: `WorkflowBreadcrumb` in the Top Bar (Phase 5) shows step state without an overlay.

The `steps_panel` design remains archived in `docs/proposals/steps_panel.md` in case clinical validation in Phase 7 reopens the question.

### 10.5 DICOM visualization bug — Resolved (2026-11-06)

**Root cause:** `VtkImageAdapter` combined `transpose(2, 1, 0)` with `ravel(order="C")`, corrupting the memory layout expected by `vtkImageData`.

**Fix:** `data.ravel(order="C")` on the original `(Z, Y, X)` layout with `SetDimensions(nx, ny, nz)`. Direction matrix applied. `int16` (`VTK_SHORT`) as the production scalar type.

**Regression test:** `test_voxel_ordering_matches_numpy` and `_everywhere` cover every voxel.

**Lessons learned:** The 2D slice extraction is a valuable diagnostic; if the 2D slice is correct but the 3D volume shows artifacts, the bug is in the 3D conversion path.

### 10.6 Windows OpenGL / Qt context issues

Documented for reproducibility. Not a blocker. The `wglMakeCurrent failed ... code 6` messages emitted during pytest teardown are VTK reporting OpenGL context destruction after the test window is gone; they do not affect test outcomes.

### 10.7 Editor Layout Tree and Editor Stack — Sprint H

- `AreaLayoutRenderer` (Sprint G) separates inter-Area from intra-Area layout.
- `EditorLayoutSpec.stack([...])` (Sprint H) enables multiple Editors per Leaf, rendered as tabs.
- Regression: existing single-Editor behaviour must remain unchanged.

### 10.8 Panel Registry — Phase 5

Left, Right, and Bottom Areas must support zero or more registered panels. The current hardcoded widget compositions are replaced by a `PanelRegistry` and per-Area panel managers.

### 10.9 Unified Import Dialog scope — Phase 4.3.4

The prototype (§97–114) defines a full import manager, not a "DICOM import UI" only. Phase 4.3.4 must deliver categories, sources, preview, auto-tagging, per-category importers, grid/list toggle, and add/remove/select actions.

### 10.10 Clinical transfer functions — Phase 4.5

The prototype defines preset categories (Bone, Soft Tissue, etc.) and LUT selection in the Right Area panel. The presets must be HU-based clinical presets (§5.1.4), not percentiles, for calibrated volumes. The CBCT fallback remains for uncalibrated volumes.

### 10.11 ViewerLayoutManager — Phase 4.5

The prototype defines a dynamic grid system (1×1, 2×2, 3×3, up to 6×4 editable, panoramic, ATM). This is a Phase 4 deliverable; deferring it to Phase 5 would leave the Editor unable to reproduce the prototype layout.

### 10.12 Real background blur — Not supported by design

Frosted glass in CranioZ is **simulated glass** (translucency + gradient + border), not real background blur. `QGraphicsBlurEffect` cannot sample VTK-rendered content. Platform APIs require separate windows. See `docs/architecture/appearance/themes-and-design-tokens.md` §6.3.

### 10.13 Sprint E (appearance foundation) — Complete (2026-11-08)

**Delivered:**

- `cranioz.infrastructure.settings` package with `SettingsService` protocol, `InMemorySettingsService`, `FilesystemSettingsService`, `SettingsStore`, `SettingsMigrator`, `KNOWN_KEYS`, `SettingsError`, `SettingsMigrationError`.
- `AppPathResolver.user_settings_path()` and `PathsConfig.settings_root` (default `~/.cranioz/Settings/settings.json`).
- `src/cranioz/ui/theme/tokens.py`: `ThemeMode`, `ThemeName` (`StrEnum`), 8 token dataclasses, 47 canonical tokens for `DARK` and `LIGHT`, `validate_tokens`, `validate_all_themes`, `count_tokens`.
- `src/cranioz/ui/theme/service.py`: `ThemeService` with mode resolution (`DARK`/`LIGHT`/`SYSTEM` via `QStyleHints`), `theme_changed` signal, token accessors, `surface_color()` delegating to the compiler, and `icon_name()` kept for Sprint F.
- `src/cranioz/ui/theme/compiler.py`: `ThemeCompiler` + `CompiledStyles` with surface composition (toolbar, popover, modal_backdrop), typed elevations, and QSS emission. `modal_backdrop` uses a fixed `#000000` base per spec §6.2.
- `src/cranioz/__main__.py`: boot order is now `SettingsService` → `ThemeService` → `apply theme` → `MainWindow`.

**Tests added (177):**

- `tests/unit/ui/theme/test_service.py` (27)
- `tests/unit/ui/theme/test_tokens.py` (37)
- `tests/unit/ui/theme/test_compiler.py` (25)
- `tests/unit/infrastructure/settings/test_settings_service.py` (27)
- `tests/architecture/test_no_hardcoded_appearance.py` (10)
- `tests/architecture/test_tokens_used.py` (8)
- `tests/architecture/test_tokens_present.py` (2)
- `tests/architecture/test_theme_completeness.py` (12)
- `tests/architecture/test_theme_values.py` (9)
- `tests/architecture/test_contrast.py` (20)

**Known debt:**

`_KNOWN_DEBT_FILES` in `tests/architecture/test_no_hardcoded_appearance.py` freezes 26 pre-existing hardcoded color/opacity literals across 6 files:

- `ui/home/widgets/flow_row.py` (9)
- `ui/home/widgets/start_button.py` (5)
- `ui/workspace/areas/area_widget.py` (5)
- `ui/workspace/workspace.py` (3)
- `ui/workspace/workspace_spec.py` (1)
- `ui/editors/viewport_3d/presets.py` (3)

These are the target of the widget migration sprint. The guard prevents new literals from being added and the frozen count is the upper bound for each file.

---

## 11. References

- `docs/architecture/appearance/` — canonical appearance architecture.
- `docs/adr/ADR-0013_Editor_Layout_Tree_View_Layout_Tree_and_Toolbar_Placement.md` — accepted.
- `docs/adr/ADR-0014-widget-toolkit-selection.md` — accepted.
- `docs/architecture/application/startup.md` — boot sequence.
- `docs/architecture/settings/configs_and_settings.md` — settings scopes.
- `docs/known_issues/dicom_visualization_bug.md` — resolved 2026-11-06.
- `docs/architecture/next_steps.md` — Sprint B / C guidance.