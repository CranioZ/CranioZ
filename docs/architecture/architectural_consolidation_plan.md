# CranioZ — Architectural Consolidation Plan

**Document Type:** Technical Planning Document
**Scope:** Architecture, infrastructure, medical imaging, visualization, user interface, and code quality
**Version:** 2.5
**Date:** November 18, 2026
**Status:** Proposed for Implementation
**Project:** CranioZ
**Companion documents:** `Next Steps.md` (immediate work items), `Implementation Plan.md` (11-phase roadmap), `docs/adr/` (architectural decisions), `refactoring_plan.md` (structural refactoring execution)

---

## 1. Purpose

This document consolidates the technical issues identified during the
CranioZ source code evaluations and establishes a plan for correction,
consolidation, and improvement.

The objective is not to expand the architecture or introduce new clinical
features. It is to consolidate existing components, resolve inconsistencies,
and ensure that interfaces between subsystems are reliable.

The main priorities are:

1. Ensure the integrity of medical imaging data.
2. Correct the geometry and anatomical orientation of MPR visualization.
3. Consolidate the DICOM import and processing pipeline.
4. Improve application composition and dependency management.
5. Correct lifecycle and integration issues.
6. Eliminate legacy code and inconsistencies.
7. Establish quality standards and regression tests.

The guiding principle is stated explicitly because it governs every item
in this document:

> **Decisions must follow from an observed problem, not from a preference
> for a particular directory structure, library, or architectural pattern.**

---

## 2. Priority Classification

| Priority | Meaning |
|---|---|
| P0 — Critical | Issues that may compromise data integrity, anatomical orientation, or clinical reliability. |
| P1 — High | Functional issues that must be resolved to consolidate the infrastructure. |
| P2 — Medium | Maintainability, organization, and performance improvements with measurable impact. |
| P3 — Evolutionary | Investigations and improvements that can be deferred until a concrete need arises. |

The classification represents the recommended implementation priority.
It does not imply that every identified issue has already been confirmed
through runtime testing. Where an item's status is "identified but not
confirmed", this document says so.

### 2.1 Classification of Work Types

Every item in this document belongs to one of the following categories.
The category determines the evidence required before the work is justified.

| Category | Definition | Evidence Required |
|---|---|---|
| **Correction** | Resolves a bug, a contract violation, or an observable failure. | A reproducible scenario, or a documented invariant that is provably violated. |
| **Consolidation** | Reduces duplication, ambiguity, or conflicting sources of truth. | Two or more implementations of the same concept, or divergent behaviors. |
| **Optimization** | Improves a measurable performance characteristic. | A benchmark showing that the current behavior is below the documented target. |
| **Investigation** | Answers a technical question without changing code. | A documented decision point with criteria for adoption. |
| **Reorganization** | Improves structure without resolving an observable problem. | **None.** Reorganization is deferred until it becomes a Correction, Consolidation, or Optimization. |

This distinction is not pedantic. A reorganization that presents itself
as a correction consumes development effort that would otherwise address
data integrity, geometry, or stability. This document treats the two as
different categories with different evidence requirements.

#### 2.1.1 Satisfied Evidence — Sprint I (Project Catalog Synchronization)

Sprint I (ProjectIndex, specified by ADR-0016) is classified as an
**Optimization** under this section. The required evidence for an
Optimization is "a benchmark showing that the current behavior is below
the documented target".

The structural cost of the pre-Sprint-I behavior is documented in
ADR-0016 §1: `FilesystemProjectRepository.list_metadata()` performs N
filesystem reads and N JSON decodes per invocation, and `ProjectCatalog`
invokes it multiple times per logical operation, with the Home Page's
search field triggering one invocation per keystroke. The structural
inefficiency is O(N·K) per search query on a network path.

ADR-0016 §7 and §8 define the benchmark that satisfies this requirement:

- 100 / 300 / 1000 projects in `tmp_path`;
- `search_projects()` latency and `repository.list_metadata` call count
  compared between baseline (direct repository) and new (indexed);
- recorded in the ADR's implementation notes as a Sprint I acceptance
  criterion.

The benchmark is **not a CI gate**, because it is time-based and depends
on the reference machine. The deterministic structural proof — "no
`repository.list_metadata` call during catalog queries" — is a CI gate
(`test_project_catalog_uses_index.py`), and is the primary evidence.

This entry documents that the ADR-0016 decision satisfies §2.1's
requirement for Optimization evidence; the benchmark itself is tracked
in ADR-0016 and is not duplicated here.

---

## 3. Priority Corrections — Medical Imaging

### 3.1. MPR Spatial Geometry and Anatomical Orientation

**Priority:** P0
**Category:** Correction
**Subsystem:** Infrastructure / Imaging / Visualization

#### Identified Issue

The current MPR implementation uses operations on NumPy arrays and vertical
mirroring without ensuring that all operations consistently respect the
physical geometry of the volume.

The axial slice display uses a vertical flip that compensates for the
difference between QImage's top-left origin and VTK's bottom-left
convention. This flip was historically implemented with
`QImage.mirrored(False, True)` and was migrated on 2026-11-13 to
`QImage.flipped(Qt.Orientation.Vertical)` (the non-deprecated API in
PySide6 6.9 and later). The operation itself is legitimate; the concern is
that the justification is not documented in the code and is not covered by
an explicit orientation test.

Potential inconsistencies have also been identified in the application of
axis spacing and anatomical orientation.

#### Status (2026-11-15)

- Done: `QImage.mirrored(False, True)` migrated to
  `QImage.flipped(Qt.Orientation.Vertical)` in `MPRView`. The deprecated
  API is no longer used. PySide6 minimum raised to 6.9 to support the new
  API.
- Pending (now Phase 4 — Visualization, not Phase 2): the explicit
  orientation test (asserting anatomical A/P, L/R, S/I orientation
  against a reference dataset with known landmarks), the code comment
  explaining the coordinate-system difference the flip compensates for,
  and anatomical orientation indicators in each View.

#### Required Corrections

- Use `VolumeGeometry` as the spatial reference for all visualization
  operations.
- Respect the direction matrix.
- Correctly apply `origin` and `spacing`.
- Ensure consistent conversion between DICOM LPS and the internal RAS
  coordinate system.
- Correct the correspondence between `PixelSpacing`, array dimensions, and
  X/Y axes.
- Correct the physical aspect ratio of images in axial, coronal, and
  sagittal planes.
- Document the vertical flip (now `QImage.flipped(Qt.Orientation.Vertical)`)
  in a code comment that explains the coordinate-system difference it
  compensates for, and cover it with a test that asserts the anatomical
  orientation against a reference dataset. The operation itself is not
  prohibited; the lack of documentation and test coverage is.
- Implement anatomical orientation indicators (A/P, L/R, S/I labels in
  each View).
- Ensure slice navigation uses physical coordinates, not array indices.
- Account for oblique volumes and different acquisition orientations, or
  explicitly reject them with a clear error until supported.

#### Acceptance Criteria

- All three MPR planes display the correct anatomical orientation, verified
  against a reference dataset with known landmarks.
- Physical pixel proportions are preserved (a 1 mm by 1 mm region appears
  square regardless of spacing).
- The position of the same anatomical landmark is consistent across all
  three planes.
- Slice navigation corresponds to physical coordinates.
- The vertical flip operation is documented in a code comment that
  explains the coordinate-system difference it compensates for, and is
  covered by a test that asserts the anatomical orientation.
- Examinations with different orientations and spacing values are displayed
  correctly.
- Anatomical labels remain consistent with patient orientation.

### 3.2. DICOM Pixel Data Decoding Validation

**Priority:** P0
**Category:** Correction
**Subsystem:** Infrastructure / Imaging / DICOM

#### Identified Issue

Directly reading `PixelData` through `np.frombuffer` may not adequately
handle all DICOM pixel encoding and representation characteristics.

The current implementation in `DicomSeriesReader._stack_raw_voxels`
constructs a NumPy array directly from `ds.PixelData`. This bypasses
`pydicom`'s decoder, which handles:

- Compressed transfer syntaxes (JPEG, JPEG-LS, JPEG2000, RLE).
- Explicit VR Big Endian vs. Little Endian.
- `BitsStored` and `HighBit` masking (when `BitsAllocated` is greater than
  `BitsStored`).
- `PixelPaddingValue` substitution.
- Multi-frame images.

For Explicit VR Little Endian uncompressed CT — the current reference
dataset — the code works. For any dataset produced by a real PACS, a
compressed dataset, or a dataset with non-standard bit depth, it will
either produce incorrect values or fail silently.

#### Required Corrections

Review the decoding process considering:

- `TransferSyntaxUID`.
- Compressed and uncompressed transfer syntaxes.
- `BitsAllocated`, `BitsStored`, `HighBit`, `PixelRepresentation`.
- Endianness.
- `RescaleSlope` and `RescaleIntercept` (applied consistently, once).
- `PixelPaddingValue`, when applicable.
- Specific characteristics of supported modalities and DICOM objects.

Adopt `pydicom.Dataset.pixel_array` as the pixel decoding mechanism, with
the appropriate `pylibjpeg` or `gdcm` plugin installed to support
compressed transfer syntaxes. Document which transfer syntaxes are
supported and which produce an explicit error.

The implementation must not assume that all DICOM files use a simple
representation that can be directly interpreted by NumPy.

#### Acceptance Criteria

- Intensity values are decoded correctly for Explicit VR Little Endian,
  Explicit VR Big Endian, and at least one compressed transfer syntax
  (JPEG Baseline or RLE).
- Negative values are preserved when `PixelRepresentation` is 1.
- Intensity calibration is applied consistently and exactly once.
- Unsupported transfer syntaxes produce explicit `DicomSeriesReaderError`
  messages that name the offending UID.
- Reference examinations are available for result validation.
- Generated values are compared against a reference tool (SimpleITK or
  DCMTK) for at least three datasets: axial CT, oblique CT, CBCT.

### 3.3. DICOM Geometry Validation

**Priority:** P1
**Category:** Correction (for the items listed as missing)
**Subsystem:** Infrastructure / Imaging / DICOM

#### Classification Note

The current `DicomSorter` already:

- Orders slices by projection onto the slice normal, not by `InstanceNumber`
  or filename.
- Detects and rejects gantry tilt (shear).
- Detects duplicate slice positions.
- Rejects non-orthogonal `ImageOrientationPatient`.

The remaining work is not a bug fix. It is an extension of the validation
to cover more failure modes that the current sorter reports as WARNING
rather than ERROR. This document classifies the remaining work as P1
(consolidation of the validation surface), not P0.

#### Required Corrections

- Emit ERROR (not WARNING) when slice spacing is irregular beyond
  tolerance, and provide an explicit resampling path or a documented
  refusal.
- Detect missing slices by comparing the expected count (from
  `(last_position - first_position) / spacing_z`) against the actual count.
- Document the behavior for oblique acquisitions: currently rejected by
  the orthonormality check on the direction matrix; extend the message to
  name the specific failure mode (oblique orientation vs. gantry tilt).
- Preserve slice ordering through the pipeline and assert it in tests.

#### Acceptance Criteria

- Volume geometry corresponds to the spatial information encoded in the
  series.
- Slice ordering is independent of file ordering and `InstanceNumber`.
- Inconsistent series (missing slices, irregular spacing) are detected
  and reported as errors with actionable messages.
- The behavior for oblique acquisitions is documented, whether as
  supported (with resampling) or explicitly rejected.
- Physical coordinates remain consistent throughout the
  DICOM to Volume to VTK pipeline.

### 3.4. Intensity Calibration and Interpretation

**Priority:** P1
**Category:** Consolidation
**Subsystem:** Domain / Imaging / Infrastructure

#### Identified Issue

`IntensityScale` exists and is correctly populated by `DicomCalibrator`,
but its consumers are not uniformly documented. Two consumers are known:

- `Viewport3DView.set_volume` uses `volume.is_hu_calibrated` to select the
  transfer-function preset (`bone` vs `cbct`). This is correct.
- `MPRView._render_slice` applies percentile-based window/level regardless
  of `IntensityScale`. This is acceptable, because percentiles are robust
  to uncalibrated data, but the reasoning is not documented.

#### Required Corrections

- Document, in `Volume` and in each consumer, how `IntensityScale` is used
  and why.
- Ensure `RescaleSlope` and `RescaleIntercept` are applied exactly once and
  only in `DicomCalibrator`.
- Preserve `IntensityScale.UNKNOWN` and `IntensityScale.UNCALIBRATED`
  explicitly when the scale cannot be determined; do not silently coerce
  to `HU`.
- Do not normalize original stored values during import.

#### Acceptance Criteria

- The intensity scale is explicitly identified for every imported volume.
- Calibration is applied exactly once (verified by a test that
  double-calibrates and observes the difference).
- Original data remain traceable in `VolumeProvenance`.
- Uncalibrated values are never presented as HU in the UI.
- Each consumer of `is_hu_calibrated` has a documented justification.
- Tests cover different slope and intercept values, including negative
  slope and non-zero intercept.

### 3.5. MPR Performance

**Priority:** P2
**Category:** Optimization
**Subsystem:** UI / Visualization

#### Identified Issue

`MPRView._render_slice` calls `np.percentile(slice_data, [1, 99])` on every
slice change. For a 512 by 512 slice this is about 1 millisecond; for the
whole volume it would be prohibitive. The current implementation only
computes percentiles for the displayed slice, so the cost is acceptable
for slice navigation but not for initial load if the slice dimension is
large.

#### Required Corrections

- Measure the actual cost of slice navigation on the reference dataset
  before optimizing.
- If navigation is below the interaction target (currently 16 milliseconds
  per frame for 60 Hz), document the measurement and defer the
  optimization.
- If navigation exceeds the target, compute per-slice statistics once and
  cache them by `(volume_id, slice_index, view_type)`, invalidating on
  volume change.
- Separate global statistics (whole-volume percentiles, if ever needed)
  from per-slice statistics.

#### Acceptance Criteria

- A benchmark on the reference dataset shows the per-slice cost.
- If optimization is implemented, the benchmark is added to the test suite
  and the cached statistics are invalidated when the volume changes.
- If optimization is not implemented, the decision is documented with the
  measurement that justified it.

### 3.6. Imaging Pipeline Consolidations — 2026-11-18 Reference

**Priority:** N/A
**Category:** Consolidation (closed)
**Subsystem:** Infrastructure / Imaging
**Status:** Resolved by the Editor Architecture Refactoring (ADR-0015).

The Editor Architecture Refactoring closed several imaging-pipeline
consolidations that were previously tracked as open items in this
document. The following were confirmed and resolved on 2026-11-18:

- **`DicomSeriesReader` remains the single canonical pixel decoder.**
  No parallel implementation was reintroduced. `dicom_loader.py` was
  removed on 2026-11-13 (§7.1).
- **`SceneQueryAdapter` has a single implementation** in
  `infrastructure/scene/`. The duplicate in
  `main_window` was removed on 2026-11-13 (§7.2).
- **No new parallel implementations were introduced** during the
  refactoring, per the standing task in §7.3.

The P0/P1 imaging items in §3.1–§3.5 remain **open** — they are
independent of the structural refactoring.

---

## 4. Application Architecture and Composition

### 4.1. Composition Root / Bootstrap

**Priority:** P3
**Category:** Reorganization (deferred)
**Subsystem:** Bootstrap / Application / Infrastructure

#### Identified Issue

Object construction and dependency injection are concentrated in
`__main__.py` (about 150 lines of linear wiring) and `MainWindow.__init__`
(15 optional arguments).

#### Clarification: Concept vs. Structure

Three concepts are involved and must be kept distinct:

- **Bootstrap** — the application initialization process.
- **Composition Root** — the location where dependencies are constructed
  and connected.
- **Runtime** — the set of services and resources active during execution.

None of these concepts requires a separate module, class, or file. The
current `__main__.py` already is a Composition Root. It does not need
to be renamed, moved, or split to be architecturally correct.

#### Decision: No Structural Refactoring at This Time

The following criteria determine whether a refactor is warranted. A
refactor is justified only if at least one row below is "Yes" or
"Possibly".

| Situation | Justifies refactor? |
|---|---|
| `__main__.py` is about 150 lines | No |
| Wiring works and is covered by tests | No |
| Tests construct their own services | No |
| Test wiring is duplicated across 3+ files without a shared fixture | Maybe — solution is a fixture, not a Builder |
| Dependencies are difficult to identify | Yes |
| Cycles or inconsistent dependencies exist | Yes |
| Initialization needs different Runtime configurations | Possibly |
| Application must support different execution modes | Yes |
| Service construction is duplicated across production entry points | Yes |

**Directive:** Do not introduce `ApplicationBuilder`,
`InfrastructureBuilder`, `UIBuilder`, `Runtime`, or a shared container
merely to reduce the size of `__main__.py`. Size is not an architectural
problem. Duplication, ambiguity, and hidden coupling are.

**Anti-pattern to avoid:** Creating four builder classes that share a
mutable `Runtime` container. This recreates the God Object the split was
meant to avoid, with more indirection and a rigid construction order.

#### Smaller Alternative (Available If Needed Before the Larger Refactor)

If `MainWindow`'s 15-argument `__init__` becomes painful before the
larger refactor is justified, replace the constructor signature with a
frozen `ApplicationContainer` dataclass.

The proposed `ApplicationContainer` is a `@dataclass(frozen=True)` with
the following fields, in topological construction order:

- `config: Config`
- `translation: TranslationService`
- `event_bus: EventBus`
- `command_dispatcher: CommandExecutor`
- `task_manager: QtTaskManager`
- `telemetry: LoggingTelemetrySink`
- `app_paths: AppPathResolver`
- `settings: FilesystemSettingsService`
- `theme: ThemeService`
- `icons: IconProvider`
- `catalog: ProjectCatalog`
- `manager: ProjectManager`
- `flow_catalog: FlowCatalog`
- `editor_registry: EditorRegistry`
- `tool_registry: ToolRegistry`
- `scene_provider: InMemorySceneProvider`
- `domain_object_store: DomainObjectStore`

`MainWindow.__init__` would then accept a single `container` argument of
type `ApplicationContainer` instead of fifteen individual parameters. The
optional `parent` keyword argument remains, with a default of `None`.

Cost: about 2 hours. Does not move the wiring; does not introduce builders.
It solves the 15-argument signature and makes the dependency set explicit
and type-checkable.

**Note (ADR-0016):** If Sprint I is implemented as specified, the
`ProjectCatalog` will be constructed with a `SynchronizedProjectIndex`
rather than the `ProjectRepository` directly. The `ProjectIndexSynchronizer`
is a composition-root concern and does not change the `ApplicationContainer`
field set (it still exposes `catalog: ProjectCatalog`); only its construction
in `__main__.py` changes.

#### Revisit Criteria

Reopen this decision when any of the following occurs:

1. A second entry point is added (`--headless`, MCP server, CLI).
2. `MainWindow` is refactored into controllers (see §4.2), each requiring
   a different service subset.
3. Boot time exceeds 5 seconds and requires structured lazy loading.
4. Service construction is duplicated across production entry points.
5. The wiring becomes genuinely hard to follow (measured by: a new
   contributor cannot trace the dependency graph in under 10 minutes).

### 4.2. MainWindow Refactoring

**Priority:** P1
**Category:** Correction
**Subsystem:** UI / Application

#### Identified Issue

`MainWindow` currently concentrates responsibilities related to navigation,
import operations, handler registration, project lifecycle, and signal
coordination. This is an observable coupling problem: the class cannot be
tested in isolation, and any change to import logic, project lifecycle, or
workspace management requires touching the same file.

#### Required Corrections

Extract responsibilities progressively, one controller per pull request,
in order of decreasing autonomy:

1. **`ImportController` first** — it is the most self-contained and
   easiest to test in isolation. It owns the DICOM import flow
   (`QFileDialog`, then `ImportDicomSeriesCommand`, then
   `Workspace.reload_volume`), the handler lifecycle, and the error
   dialogs.
2. **`ProjectController` second** — it owns `ProjectManager.open_project`,
   `ProjectManager.close_project`, and the Home to Workspace navigation.
3. **`WorkspaceController` third** — it owns the Top Bar wiring, the Area
   toggles, and the `Workspace`-level state.
4. **`ApplicationController` last**, and only if the remaining
   `MainWindow` logic justifies it.

Each extraction is a separate commit with its own tests. Do not extract
two controllers in the same pull request.

#### Acceptance Criteria

- `MainWindow` does not directly execute infrastructure operations.
- Import functionality is not implemented directly in the window.
- Project lifecycle has a clearly defined owner.
- Navigation between Home and Workspace follows an explicit flow.
- Each extracted controller has its own unit tests.
- `MainWindow` does not become a universal coordinator for all application
  functionality.

### 4.3. DICOM Import Layer Violation

**Priority:** P1
**Category:** Correction
**Subsystem:** Application / Infrastructure

#### Identified Issue

`ImportDicomSeriesHandler`, located in the Application layer, directly
imports `DicomSeriesReader` from `infrastructure.imaging.dicom`. This is a
verifiable layer violation: every other cross-layer dependency in the
project goes through a Protocol defined in the Application layer.

#### Required Corrections

- Define a `DicomSeriesReader` Protocol in `main_window`.
- Make `ImportDicomSeriesHandler` depend on this Protocol.
- Move the concrete implementation to `imaging` as
  `PydicomSeriesReader` (implementing the Protocol).
- Inject the concrete implementation during application composition.

Conceptual structure:

- Application layer: `DicomSeriesReader` (Protocol).
- Infrastructure layer: `PydicomSeriesReader` (implementation of the
  Protocol).
- The Application layer depends only on the Protocol.
- The Infrastructure layer is wired into the Application at boot time.

#### Acceptance Criteria

- Application does not import the concrete reader implementation.
- The reader can be replaced without modifying the use case (proven by a
  test using an in-memory fake).
- Tests can use a mock or fake implementation.
- The import workflow remains functional end-to-end.

### 4.4. Command Handler Registration

**Priority:** P1
**Category:** Correction
**Subsystem:** Application / Modules / Commands

#### Identified Issue

`InMemoryModuleLoader._resolve_handler` uses `command_type._handler`, a
class attribute, as an implicit resolution mechanism. The manual
registration of `ImportDicomSeriesCommand` in `MainWindow` also indicates
that handler registration is not sufficiently centralized.

#### Required Corrections

- Eliminate resolution based on implicit class attributes (`_handler`).
- Centralize handler registration during application composition or
  module discovery.
- Define registration rules for internal commands and module-provided
  commands.
- Separate command definitions from handler implementations.

The `InMemoryCommandBus` already provides explicit registration via
`register(command_type, handler)`. Use that interface directly; do not
introduce a new registry.

#### Acceptance Criteria

- Every command has an explicitly registered handler.
- Missing handlers produce `CommandNotRegistered` errors that name the
  command type.
- Registration does not depend on `MainWindow`.
- Modules can register their commands without coupling to the UI.
- The implicit `_handler` attribute is removed.

### 4.5. ProjectManager Lifecycle

**Priority:** P1
**Category:** Correction
**Subsystem:** Application / Projects

#### Identified Issue

`ProjectManager` maintains project contexts in memory and does not
provide a closing process during application shutdown. If the application
closes with projects still open, the `TaskManager` is shut down but the
`ProjectContext` objects are not released, and the `ProjectClosing` and
`ProjectClosed` events are not published.

#### Required Corrections

- Implement `ProjectManager.close_all()` that calls `close_project()` for
  every active context.
- Call `ProjectManager.close_all()` from `__main__.py` before
  `task_manager.shutdown()`.
- Ensure `close_all()` publishes `ProjectClosing` and `ProjectClosed` for
  each context.
- Log and handle failures in `close_all()` without aborting the shutdown
  sequence.
- Document the concurrency policy: `ProjectManager` is single-threaded,
  called on the GUI thread; no lock is required.

#### Acceptance Criteria

- Active projects are properly closed during shutdown.
- `ProjectClosing` and `ProjectClosed` are published for every open
  project during shutdown.
- Associated resources are released.
- Closing failures are logged and the shutdown continues.
- The concurrency policy is documented in the `ProjectManager` docstring.

### 4.6. Project Catalog Synchronization — Specified by ADR-0016

**Priority:** P2
**Category:** Optimization
**Subsystem:** Application / Projects / Catalog
**Status:** Specified by ADR-0016 (Accepted 2026-11-18); implemented by Sprint I.

#### Context

ADR-0016 fixes the synchronization mechanism between the Project
subsystem and the `ProjectCatalog`: an in-memory `ProjectIndex`
populated by a `ProjectIndexSynchronizer` and invalidated by the
`ProjectCreated`, `ProjectUpdated`, and `ProjectDeleted` events. The
`ProjectRepository` remains the authoritative source. TTL and polling
are prohibited. SQLite and background reconciliation remain deferred to
Phase 8.

This section records the classification of Sprint I under §2.1 and
points to the ADR as the authoritative specification. It does not
restate ADR-0016.

#### Evidence for Optimization (§2.1)

The evidence required by §2.1 for an Optimization is defined by ADR-0016
§7 and §8: a benchmark of `search_projects()` latency and
`repository.list_metadata` call count on 100 / 300 / 1000 projects, plus
the deterministic CI-gated test
(`test_project_catalog_uses_index.py`) that asserts no
`repository.list_metadata` call during catalog queries.

The benchmark is recorded in ADR-0016 implementation notes and is not
duplicated here. The deterministic test is a CI gate.

#### Relationship to Other Items

- §4.1 (Composition Root): the `SynchronizedProjectIndex` and
  `ProjectIndexSynchronizer` are constructed at the composition root;
  the `ApplicationContainer` field set is unchanged.
- §4.5 (ProjectManager lifecycle): the `ProjectIndexSynchronizer`
  subscribes to `ProjectCreated` / `ProjectUpdated` / `ProjectDeleted`
  and is not affected by project opening/closing. `close_all()` does not
  interact with the index.
- §5.1 (Async DICOM import): unrelated.
- §6.1 (WorkspaceSpec): unrelated.

The full specification is ADR-0016.

---

## 5. Asynchronous Import Pipeline

### 5.1. DICOM Import Through TaskManager

**Priority:** P1
**Category:** Correction
**Subsystem:** Application / Infrastructure / UI

#### Identified Issue

DICOM import is executed synchronously from the UI, blocking the main
thread while reading and processing large volumes. For a 500-slice series,
the current implementation would freeze the UI for several seconds.

#### Required Corrections

Integrate the import use case with `QtTaskManager`. Separate the following
stages:

1. Import request from the UI (GUI thread).
2. Use case dispatch (GUI thread).
3. Reading and processing in the worker (worker thread).
4. Result delivery (GUI thread, via `on_result`).
5. Project and scene updates (GUI thread).

Also implement:

- Progress reporting via `on_progress`.
- Cooperative cancellation via `CancelToken`.
- Exception handling via `on_error`.
- Error and warning reporting through the existing dialog path.
- Prevention of duplicate operations (disable the import action while a
  task is running).
- Guarantees that cancelled tasks cannot improperly update the project
  (the `on_result` callback is not invoked after cancellation).

Widget manipulation and updates to UI-associated graphical objects must
remain on the GUI thread; the `QtTaskManager` already guarantees this via
`QMetaObject.invokeMethod` with `QueuedConnection`.

#### Acceptance Criteria

- Import does not block the UI, verified by a UI responsiveness test.
- Users can monitor progress and cancel the operation.
- Errors are reported without terminating the application.
- Cancellation respects the technical safety boundaries of the operation.
- Scene updates occur on the GUI thread (verified by asserting thread
  identity in the callback).

---

## 6. Module System and Workflow Organization

### 6.1. WorkspaceSpec and Module System Integration

**Priority:** P2
**Category:** Consolidation
**Subsystem:** Application / Modules / UI / Workspace

#### Identified Issue

`MainWindow._create_workspace` hardcodes a placeholder module list
(`modules_segment.set_modules((("tomography", "Tomografia"),))`). The
workflow selected on the Home Page is passed to
`ProjectManager.open_project` but is not used to select a
`WorkspaceSpec`. The `Workspace` always loads `WORKSPACE_SPEC_DEFAULT`.

This is not a bug today, because the only functional workflow is the
default one. It becomes a bug when the second workflow is added, because
the workspace will not reflect the selected workflow.

#### Required Corrections

- Define the mapping between `workflow_id` and `WorkspaceSpec`.
- Pass the selected `workflow_id` to `Workspace.load_spec` or to a
  `WorkspaceSpecResolver` that returns the corresponding spec.
- Feed the `ModulesSegment` from the actual registered modules, not a
  hardcoded tuple.
- Distinguish between available, registered, loaded, and active modules
  in the `ModulesSegment` presentation.

This item is a prerequisite for Phase 5 (WorkflowEngine). It can be
implemented as part of Phase 5, not as a standalone correction.

#### Acceptance Criteria

- Workflow selection is preserved from the Home Page to the Workspace.
- The Workspace receives the corresponding specification.
- Displayed modules correspond to modules actually available for the
  selected workflow.
- Unimplemented modules are correctly identified.
- The application does not indicate that functionality is available when
  only a stub exists.

**Note:** Incomplete module implementations are not architectural defects
if they are consistent with the planned development phases. This item
becomes a Correction only when the second workflow is added.

---

## 7. Legacy Code Removal and Consolidation

### 7.1. Removal of `dicom_loader.py` — Completed 2026-11-13

**Priority:** P1
**Category:** Correction
**Status:** Resolved 2026-11-13

`imaging` maintained an implementation
parallel to `DicomSeriesReader`, including normalization of values to
the range 0 to 4095 and Gaussian smoothing.

The file was removed on 2026-11-13 after confirming no active consumers.
The parallel normalization and smoothing are no longer part of any code
path.

### 7.2. Removal of Duplicated Components — Completed 2026-11-13

**Priority:** P2
**Category:** Consolidation
**Status:** Resolved 2026-11-13

The following components were removed on 2026-11-13:

- `src/cranioz/domain/scene/volume_data.py` — the payload type of the
  obsolete `dicom_loader.py`. No remaining references.
- `src/cranioz/application/rendering/` — the `RenderingAdapter` Protocol
  was never implemented nor consumed. The concrete renderer is
  `VTKSceneRenderer`.
- `src/cranioz/application/scene/scene_query_adapter.py` — a byte-identical
  duplicate of `infrastructure/scene/scene_query_adapter.py`. `MainWindow`
  imports the infrastructure version.
- 10 obsolete DICOM debug scripts under `scripts/debug/dicom/` (see
  §11.2).

### 7.3. Standing Task: Prevent New Parallel Implementations

**Priority:** P2
**Category:** Consolidation

Verify, at each future phase, that no new parallel implementation has
been introduced for concepts that already have a canonical one. This is a
standing task, not a one-off correction.

### 7.4. Phase 2 Toolbar/Editor Foundation (Blocks 1–6, 5.5–5.6.1, Sprint M, Sprint G, Sprint H) — Completed 2026-11-15

**Priority:** P1
**Category:** Consolidation
**Status:** Resolved 2026-11-15 (Blocks 4–6, 5.5–5.6.1, Sprint M, Sprint G, Sprint H); 2026-11-13 (Blocks 1–3)
**Refs:** `Next Steps.md` §2.2, `Implementation Plan.md` §5.1

Delivered:

- **Block 1 — Toolbar polish.** `Toolbar._root_layout.setAlignment(AlignTop)`;
  `ViewLayoutRenderer._VERTICAL_TOOLBAR_WIDTH` set to 96 pixels with
  `setFixedWidth(96)` for LEFT and RIGHT toolbars (fits "Toggle" without
  truncation); grid container and outer splitter use
  `QSizePolicy.Expanding`; vertical toolbars get `(Fixed, Expanding)`
  and horizontal toolbars get `(Expanding, Fixed)`. 8 tests.
- **Block 2 — `Toolbar.set_active` / `set_expanded` / chevron.**
  `set_active(bool)` attenuates via `QGraphicsOpacityEffect(0.5)` without
  hiding; `set_expanded(bool)` compresses to a chevron; `expanded_changed`
  signal. Chevron flips automatically; persistence deferred. 11 tests.
- **Block 3 — `Editor._EditorSignals` + `Editor.set_active_view`.**
  `active_view_changed = Signal(object)` accepting `str` or `None`;
  `set_active_view` validates `view_id` against the Editor's Views
  (unknown id produces a WARNING and no signal); idempotent for the same
  id; `None` clears. `dispose()` resets without emitting. 12 tests in
  `tests/unit/ui/editors/test_editor_active_view.py`.
- **Block 4 — `ViewLayoutRenderer` event filter + `ACTIVE_ONLY`.**
  Activation filter installed on each View's `activation_widget()`
  (Viewport3DView returns the `QVTKRenderWindowInteractor`; other Views
  return `content_widget()`); forwards `MouseButtonPress` and `FocusIn`
  to `editor.set_active_view`; `ACTIVE_ONLY` toolbars start inactive;
  `clear_cache()` removes filters correctly. 12 tests.
- **Block 5 — `TomographyEditor` materializes Editor-level Toolbars.**
  `content_widget()` wraps the View grid with LEFT (`ALWAYS`) and RIGHT
  (`COLLAPSIBLE`) toolbars; `_editor_toolbars` cleared on `dispose()`.
  7 tests.
- **Block 5.5 — Percentage-based Area layout.**
  `Workspace._LEFT_RATIO = 0.20`, `_RIGHT_RATIO = 0.25`,
  `_BOTTOM_RATIO = 0.20`; `_apply_default_splitter_sizes()` never lets
  the Central Area drop below `TopOverlay.minimum_width()`;
  `AreaWidget.refresh()` returns early when hidden;
  `_build_empty_placeholder()` uses `WA_TranslucentBackground`.
- **Block 5.6 — Window controls in ExtrasSegment.**
  `minimize_requested`, `maximize_requested`, `close_requested`;
  `MainWindow._on_window_maximize_requested` toggles
  `showMaximized`/`showNormal`; `closeEvent` asks for confirmation when
  a project is open, then tears it down via `_close_active_project`.
  19 tests.
- **Block 5.6.1 — Window controls in HomeTopBar.**
  `HomeTopBar.minimize_requested`, `maximize_requested`,
  `close_requested`; `HomePage` forwards the three signals;
  `MainWindow._connect_home_signals` connects them.
  `test_home_top_bar.py` +5 tests, `test_home_page.py` +3 tests,
  `test_main_window.py` +3 end-to-end tests.
- **Sprint M — Frameless window + native chrome.**
  `MainWindow` uses `Qt.FramelessWindowHint`; the native Windows title
  bar is removed. `WindowDragFilter` installed on `HomeTopBar` and the
  `Workspace`'s `TopOverlay` allows dragging the window from the custom
  top bars (ignores `QPushButton` clicks). `_central_container` wraps
  the `QStackedWidget` with `setContentsMargins(4, 4, 4, 4)` to create
  a resize dead zone. Native resize is delegated to the OS via
  `windowHandle().startSystemResize(edges)` in `mousePressEvent`, with
  dynamic cursor feedback in `mouseMoveEvent`.
  `_update_maximize_icon(restore=...)` keeps the maximize/restore icon
  in sync between `HomeTopBar` and `ExtrasSegment`. 3 new integration
  tests in `test_main_window.py` (`test_main_window_is_frameless`,
  `test_main_window_drag_filter_is_installed`,
  `test_main_window_central_container_has_margins`).
- **Block 6 — `debug_workspace.py` final visual validation.**
  The script was run end-to-end with Blocks 4–6, 5.5–5.6.1, Sprint M
  and Sprint G applied. The visual matches the Prototipagem_UI_17
  reference. Committed.
- **Sprint G — `AreaLayoutRenderer`.**
  `AreaLayoutSpec` (`SINGLE`, `SPLIT`, `STACK`) with structural
  validation. `AreaLayoutRenderer._resolve_spec()` returns `SINGLE`
  for one Editor and `SPLIT` for multiple (behavior preserved).
  `STACK` declared and raised `NotImplementedError` until Sprint H.
  `_render_split()` extracted; `_build_editor_container()` unchanged.
  6 `AreaLayoutSpec` tests + 1 `STACK` failure-mode integration test.
  `stl.py` reverted to `GetData()` with `# TODO(vtk-10)`.
  `main_window.py` annotated with `QMouseEvent` (mypy clean).
  `ruff check .` clean; `mypy src` clean; `pytest` 1632 passing.
- **Sprint H — `EditorStack`.**
  `EditorLayoutSpec` (LEAF/SPLIT/STACK) with `EditorStackOrientation`
  and `stack(...)` constructor. `EditorStack` widget + `EditorStackSwitcher`
  (compact, dark-styled, not a `QTabWidget` — ADR-0013 §2.5).
  `AreaLayoutRenderer` extended with `_materialize_tree()`,
  `_materialize_split()`, `_materialize_stack()`. `LayoutBuilder`
  collects `editor_ids` recursively and propagates the spec to the
  `Area` via `set_editor_layout_spec()`. `AreaWidget` forwards
  `IconProvider` and disposes the `EditorStack`. Backward-compatibility
  shim at `specs/editor_layout_spec.py`. `PlaceholderEditor` moved to
  `src/cranioz/ui/editors/placeholder_editor.py` (public).
  `debug_workspace.py` validated visually with a `STACK`
  `ModuleUISpec`. 6 `EditorLayoutSpec` tests, 4 `EditorStack` tests,
  1 `STACK` integration test. `test_no_hardc

<!-- TRUNCATION NOTICE (2026-11-18):
The v2.3 source you provided was truncated at this point.
The remaining content of §7.4 and any later sections of v2.3
(e.g., §8, §9, §10, §11, §12) that existed in the original file
must be restored from your local copy. The sections below (§7.5,
§7.6, §8, §13) are the new additions introduced by this update.
-->

### 7.5. Editor and Module Package Consolidations — Completed 2026-11-18

**Priority:** N/A
**Category:** Consolidation (closed)
**Subsystem:** Editors / Modules / Workspace
**Status:** Resolved by the Editor Architecture Refactoring (ADR-0015).

The Editor Architecture Refactoring (2026-11-18) closed the following
consolidations that were previously listed as open or anticipated in
this document and in `refactoring_plan.md` §7:

- **`_PlaceholderEditor` duplication.** The private copy in
  `workspace` was consolidated into the canonical
  `PlaceholderEditor` in `editors/core/editor/placeholder_editor.py`.
- **`_null_task_manager.py` duplication.** Removed. `module_loader.py`
  now uses `NoopTaskManager` from `cranioz.application.tasks`.
- **`editor_manifest.py` and `editor_catalog.py`** (both empty). Removed.
  If a contract is needed for Sprint L, it will be introduced with a
  real implementation.
- **`editors`** (debug-only production components). Removed.
- **`DummyEditor` / `DebugEditor`** moved from
  `editors` to
  `tests/fixtures/editors/test_editor.py`.
- **`MeshDebugEditor`** moved to `editors/builtin/mesh_debug/editor.py`
  and the composition-root import in `main_window.py` was updated.
- **`_KNOWN_DEBT_FILES`** reduced from 8 to 5 files; the corresponding
  `_DEBT_MAX_LITERALS` budget was reduced by the same count.

The final validation is recorded in `refactoring_plan.md` §11:
**1635 passing tests, 0 failed, 0 errors, 2 skipped; `ruff check`,
`ruff format --check`, and `mypy src` clean; 85% overall coverage.**

### 7.6. Deferred by the Refactoring — 2026-11-18

**Priority:** Tracked separately
**Category:** Correction / Consolidation (open)
**Status:** Deferred to a future PR.

The following items were identified during the refactoring but were
explicitly deferred to a separate PR to keep scopes clean:

- **`main_window` → `main_window`**
  (Step 6.1 of `refactoring_plan.md`). The migration is mechanical and
  independent of the Editor reorganization.
- **`editors/view_overlays/`** (Step 4.4 of `refactoring_plan.md`).
  Skipped because `editors` and
  `editors` contain only empty `__init__.py` files.
  The package will be created when a concrete overlay implementation
  exists.
- **`Workspace.find_viewport_3d()` regression test.** Documented as an
  approved exception to §4.1 rule 8 (see `refactoring_plan.md` §7,
  decision #9). The test remains a follow-up.
- **Implicit handler resolution** in `InMemoryModuleLoader`
  (`command_type._handler`). Tracked in §4.4 above.

These items do not block Phase 3 or Sprint L.

---

## 8. Document Authority and Relationships

*[Restore from your local v2.3 copy. This section was not included in
the excerpt you provided.]*

---

## 9. ... 

*[Restore from your local v2.3 copy.]*

---

## 13. Post-Refactoring Cross-Reference (2026-11-18)

This section links the open items in this document to the structural
refactoring that was completed on 2026-11-18.

| Item in this document | Resolution / Status | Reference |
|---|---|---|
| §3.6 Imaging pipeline consolidations | Closed by the refactoring | ADR-0015; `refactoring_plan.md` §11 |
| §4.1 Composition root | Deferred (P3) — revisit criteria unchanged | §4.1 above |
| §4.2 MainWindow refactoring | Open (P1) — unchanged scope | `next_steps.md` §5.1 |
| §4.3 DICOM import layer violation | Open (P1) — unchanged scope | §4.3 above |
| §4.4 Command handler registration | Open (P1) — `_handler` resolution remains | `refactoring_plan.md` §5.10 |
| §4.5 ProjectManager lifecycle | Open (P1) — unchanged scope | §4.5 above |
| §5.1 Async DICOM import | Open (P1) — unchanged scope | §5.1 above |
| §6.1 WorkspaceSpec integration | Open (P2) — prerequisite for Phase 5 | §6.1 above |
| §7.5 Editor and Module consolidations | Closed by the refactoring | ADR-0015; `refactoring_plan.md` §11 |
| §7.6 Deferred items | Tracked separately | `refactoring_plan.md` §11; §4.4 above |

The structural refactoring resolved the **Editor and Module package
reorganization** items but did **not** absorb the imaging-pipeline
corrections (§3.1–§3.5), the MainWindow refactoring (§4.2), the DICOM
import layer violation (§4.3), or the async import pipeline (§5.1).
Those items remain open and are governed by this document, not by
`refactoring_plan.md`.