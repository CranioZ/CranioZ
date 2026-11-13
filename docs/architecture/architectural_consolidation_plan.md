# CranioZ — Architectural Consolidation Plan

**Document Type:** Technical Planning Document  
**Scope:** Architecture, infrastructure, medical imaging, visualization, user interface, and code quality  
**Version:** 2.1  
**Date:** November 13, 2026  
**Status:** Proposed for Implementation  
**Project:** CranioZ  
**Companion documents:** `Next Steps.md` (immediate work items), `Implementation Plan.md` (11-phase roadmap), `docs/adr/` (architectural decisions)

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

#### Status (2026-11-13)

- Done: `QImage.mirrored(False, True)` migrated to
  `QImage.flipped(Qt.Orientation.Vertical)` in `MPRView`. The deprecated
  API is no longer used. PySide6 minimum raised to 6.9 to support the new
  API.
- Pending: the explicit orientation test (asserting anatomical A/P, L/R,
  S/I orientation against a reference dataset with known landmarks), the
  code comment explaining the coordinate-system difference the flip
  compensates for, and anatomical orientation indicators in each View.

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

- Define a `DicomSeriesReader` Protocol in `application/imaging/`.
- Make `ImportDicomSeriesHandler` depend on this Protocol.
- Move the concrete implementation to `infrastructure/imaging/dicom/` as
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

`infrastructure/imaging/dicom_loader.py` maintained an implementation
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

### 7.4. Phase 2 Toolbar/Editor Foundation (Blocks 1-3) — Completed 2026-11-13

**Priority:** P1  
**Category:** Consolidation  
**Status:** Resolved 2026-11-13  
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

Not yet delivered (Block 4, next work item): `ViewLayoutRenderer` event
filter and `ACTIVE_ONLY` wiring. See `Next Steps.md` §8.6.

---

## 8. OpenGL and Runtime Environment

### 8.1. OpenGL Configuration Consolidation

**Priority:** P1  
**Category:** Consolidation  
**Subsystem:** Bootstrap / UI / Visualization / Tests

#### Identified Issue

Different OpenGL configurations have been identified:

- `__main__.py`: Compatibility Profile 2.1.
- `conftest.py`: Core Profile 3.2.
- Debug scripts: Core Profile 3.2.
- `qt_opengl_config.py`: possible duplicate configuration.

Tests may not reproduce the same graphical environment used by the
application.

#### Required Corrections

- Identify the actual OpenGL configuration required by VTK and Qt.
- If the Application (Compatibility 2.1) and the test suite (Core 3.2)
  intentionally differ, document the reason in a code comment and in
  `docs/architecture/rendering/`.
- If they differ accidentally, consolidate on a single configuration in
  `qt_opengl_config.py` and import it from both `__main__.py` and
  `conftest.py`.
- Review the use of `qt_opengl_config.py`.
- Eliminate duplicated configuration blocks.

#### Acceptance Criteria

- OpenGL configuration is explicit and centralized.
- Application and tests use configurations appropriate to their
  respective purposes, documented.
- No duplicated configuration blocks remain.
- Visualization tests are reproducible.
- Behavior in environments without graphical support is defined and
  tested (skip with a clear reason, not a silent failure).

---

## 9. Privacy and Clinical Data Protection

### 9.1. PHI Handling Policy

**Priority:** P1  
**Category:** Correction  
**Subsystem:** Domain / Imaging / Projects / Infrastructure / Telemetry

#### Identified Issue

`ImageMetadata` stores identifiable information obtained from DICOM files,
while `ProjectMetadata` may store `patient_display_name` as plain text in
`project.json`. Without a system-wide policy, personal information may be
exposed through files, logs, telemetry, and exports.

#### Required Corrections

Define a clinical data handling policy covering:

- Patient identity.
- Clinical metadata.
- Imaging metadata.
- Project persistence.
- Logs and error messages.
- Telemetry.
- Temporary files.
- Backups.
- Export and sharing.
- Anonymization and pseudonymization.

Separate the following concepts in the policy:

- **Patient Identity** — name, birth date, medical record number.
- **Clinical Metadata** — clinical procedure, status, workflow.
- **Imaging Metadata** — series UID, orientation, spacing.
- **Project Metadata** — project name, display name, timestamps.

The policy is a document (`docs/architecture/privacy/phi-policy.md`) that
every future pull request can be checked against. Implementation follows
the policy; the policy itself is P1 and can be written before any code
change.

#### Acceptance Criteria

- The PHI handling policy is documented.
- Logs do not expose identifiable information (verified by a
  `test_no_phi_in_logs.py` that greps the log output of a full import).
- Telemetry does not transmit PII.
- Export privacy behavior is defined and tested.
- Anonymization is verifiable.
- Data required for image geometry and interpretation are preserved.

---

## 10. Performance and Visualization

### 10.1. VTK Image Adapter Review

**Priority:** P1  
**Category:** Consolidation  
**Subsystem:** Infrastructure / Visualization

#### Required Corrections

Review consistency between:

- NumPy array `[z, y, x]` and VTK dimensions `[x, y, z]`.
- Spacing.
- Origin.
- Direction matrix.
- Memory sharing (`deep=True` vs `deep=0`).
- NumPy buffer lifetime.

The current implementation uses `deep=True` in `VtkImageAdapter`, which
duplicates the voxel buffer. For a 512 cubed volume this is about 500 MB
of duplicated memory. The duplication is safe (no lifetime bug possible)
but costly.

Document the trade-off explicitly in the adapter docstring. If memory
becomes a problem, evaluate `deep=0` with a documented lifetime contract
(`Volume.data` must outlive `vtkImageData`).

#### Acceptance Criteria

- Volume orientation is preserved, verified by
  `test_vtk_image_adapter_ordering.py`.
- VTK receives the correct dimensions.
- Physical geometry remains consistent.
- The memory strategy (`deep=True` or `deep=0`) is documented with its
  rationale.
- If `deep=0` is chosen, a test asserts that the `Volume.data` is retained
  while the `vtkImageData` exists.

### 10.2. Visualization Pipeline Review

**Priority:** P2  
**Category:** Consolidation  
**Subsystem:** Visualization / VTK

#### Required Corrections

- Review actor management.
- Ensure separation between clinical data and rendering objects.
- Prevent Views from assuming data processing responsibilities.
- Verify graphical resource management.
- Review the use of `vtkSmartVolumeMapper`.
- Review the `vtkCellArray.GetData()` deprecation (VTK 9.6 and later;
  removal planned for VTK 10) in `stl.py:135`, and migrate to
  `ExportLegacyFormat()` when convenient.
- Avoid globally disabling VTK warnings (`GlobalWarningDisplayOff`)
  without a documented policy; if warnings are suppressed for a specific
  reason, document the reason and re-enable them per-test where feasible.

#### Acceptance Criteria

- Domain objects remain independent of graphical representation.
- The scene can be reconstructed from project data.
- Graphical resources are properly released.
- Rendering problems produce useful diagnostic information (no silent
  warning suppression).

---

## 11. Repository Quality and Maintenance

### 11.1. Removal of Personal Absolute Paths

**Priority:** P2  
**Category:** Correction  
**Subsystem:** Scripts / Tests

#### Identified Issue

Personal absolute paths, such as `C:\Users\JozeiasNote2026\...`, are
present in debug scripts and tests.

#### Required Corrections

- Replace personal paths with command-line arguments.
- Use environment variables when appropriate (`CRANIOZ_TEST_DICOM_PATH`,
  which `test_spacing_z.py` already uses).
- Use `tmp_path` in tests instead of absolute paths.
- Avoid dependencies on machine-specific directory structures.
- Document external datasets required by diagnostic tools.

#### Acceptance Criteria

- Tests do not depend on personal paths.
- Scripts are executable across different environments.
- Test data are accessed through configurable paths.
- `grep -r "C:\\\\Users" src tests scripts` returns nothing.

### 11.2. Debug Script Organization

**Priority:** P3  
**Category:** Reorganization (deferred)  
**Subsystem:** Scripts

#### Identified Issue

`scripts/debug/` contains several scripts related to the DICOM 2D rendering
investigation.

#### Classification Note

The 10 obsolete scripts were removed on 2026-11-13 (see §7.2). The
remaining 11 scripts are well-named, well-organized by subdirectory
(`2D/`, `3D/`, `2D/vtk/`, `2D/ITK/`, `2D/numpy/`), and documented in
their own docstrings.

The reorganization proposed in an earlier draft of this plan
(`scripts/development/`, `scripts/diagnostics/`, `scripts/maintenance/`,
`scripts/validation/`) is not justified:

- It would move 11 files without resolving an observable problem.
- It would break relative imports and hardcoded paths inside the scripts.
- It would cost time that is better spent on §3 (Medical Imaging).

**Directive:** Do not reorganize `scripts/debug/` at this time. If the
directory grows beyond 30 scripts, or if a category of scripts becomes
duplicated, revisit.

#### Revisit Criteria

- `scripts/debug/` contains more than 30 scripts.
- Two scripts serve the same diagnostic purpose without justification.
- A diagnostic script is referenced by documentation in a way that
  requires reorganization.

### 11.3. Test Inconsistency Corrections

**Priority:** P1  
**Category:** Correction  
**Subsystem:** Tests

#### Identified Issues

- Tests that describe nine fields in comments but verify only seven
  (`test_editor_context_propagation.py`).
- The architectural test
  `tests/unit/architecture/test_no_hardcoded_appearance.py` differs from
  `tests/architecture/test_no_hardcoded_appearance.py`.
- Invalid locale value `"pt-BR-BR"` in `test_loader.py`.
- Potential inconsistencies in the `_KNOWN_DEBT_FILES` list.

#### Required Corrections

- Review comments and assertions; align them.
- Remove the duplicate `test_no_hardcoded_appearance.py` in
  `tests/unit/architecture/`. A `Compare-Object` between the two files
  shows that the `tests/unit/` version differs only by two placeholder
  lines (the literal text `# ...` twice) and is otherwise a truncated copy
  of the live `tests/architecture/` version, which contains the full
  module docstring and the same `_KNOWN_DEBT_FILES` rules. The
  `tests/architecture/` version is the live one.
- Correct the locale value `"pt-BR-BR"` to `"pt-BR"`.
- Review `_KNOWN_DEBT_FILES` and ensure the count matches the current
  number of literals per file.
- Add a test that asserts the `_KNOWN_DEBT_FILES` counts, so that future
  additions are caught (the test already exists; verify it passes).

#### Acceptance Criteria

- Comments accurately describe the tested behavior.
- No contradictory tests exist for the same rule.
- All locale values are valid (`pt-BR`, `en`, `en-US`).
- Architectural exceptions have documented justifications and tracking.
- The `_KNOWN_DEBT_FILES` test passes.

### 11.4. ProjectMetadata.with_status Correction

**Priority:** P2  
**Category:** Correction  
**Subsystem:** Domain / Projects

#### Identified Issue

An ellipsis (`...`) appears before the docstring in
`ProjectMetadata.with_status`, preventing the text from being recognized
as the function's docstring. The method's body begins with an unreachable
ellipsis statement followed by a string literal, so the string literal is
not treated as a docstring by the Python runtime.

#### Required Corrections

- Remove the misplaced ellipsis.
- Review the method implementation.
- Verify consistency with model immutability and domain rules.

#### Acceptance Criteria

- The method has a valid docstring.
- Its behavior is covered by tests.

---

## 12. Technology Evaluation: pydicom, SimpleITK, and DCMTK

**Priority:** P3  
**Category:** Investigation  
**Subsystem:** Infrastructure / Imaging / DICOM

#### Objective

Investigate whether the current DICOM reading and processing infrastructure
should be complemented by a specialized medical imaging library.

#### Technologies to Evaluate

**pydicom**

Retain as the primary candidate for reading and manipulating DICOM
datasets and metadata. The correction in §3.2 depends on pydicom's
`pixel_array`, not on a replacement.

**SimpleITK**

Evaluate as an alternative or complement for decoding, geometry, volumetric
processing, and image operations.

**DCMTK**

Evaluate for broader DICOM infrastructure requirements, particularly
networking services and interoperability.

#### Recommended Strategy

Do not immediately replace the current reader.

First, establish a library-independent interface (see §4.3). The
interface is a Protocol named `DicomSeriesReader` with a single method
that returns a `Volume` from a source path. The Protocol lives in the
Application layer.

Possible implementations:

- `PydicomSeriesReader` — current pydicom-based implementation, moved to
  Infrastructure and made to conform to the Protocol.
- `SimpleITKSeriesReader` — alternative implementation using SimpleITK,
  evaluated only after the criteria below are met.

#### Evaluation Criteria

- Transfer syntax compatibility.
- Compressed image decoding.
- Intensity value fidelity.
- Spatial geometry accuracy.
- Oblique volume handling.
- Performance.
- Additional dependencies.
- Python and Windows compatibility.
- Distribution complexity.
- Licensing.
- NumPy and VTK integration.

#### Acceptance Criteria

Adoption of another library should occur only if comparative testing
demonstrates a concrete benefit in reliability, format coverage,
performance, or maintainability. The comparison must be documented in an
ADR before the library is adopted.

---

## 13. Technical Debt Consolidation

**Priority:** P1  
**Category:** Consolidation  
**Subsystem:** Architecture / Documentation / Development

#### Objective

Establish an explicit process for identifying, classifying, and tracking
technical debt.

#### Proposed Classification

| Category | Usage |
|---|---|
| `TECH-DEBT` | Implementation requiring refactoring. |
| `KNOWN-LIMITATION` | Known and documented limitation. |
| `ARCH-DECISION` | Intentional architectural decision. |
| `TODO` | Pending implementation work. |
| `INVESTIGATION` | Issue requiring research or validation. |

#### Applying the Classification

- **Code comments** — use `# TECH-DEBT(<short-id>): ...`,
  `# KNOWN-LIMITATION: ...`, and `# TODO(<issue-id>): ...`. The
  `<short-id>` or `<issue-id>` is a stable identifier that links the
  comment to the corresponding entry in the repository's issue tracker.
- **ADRs** — `ARCH-DECISION` items live in `docs/adr/`. They are not
  marked in code; they are referenced by ADR number.
- **`KNOWN-LIMITATION`** — must also appear in the user-facing
  documentation (`docs/user/limitations.md`) so that clinical users are
  informed.
- **`INVESTIGATION`** — opens a discussion, not a code change. It closes
  with an ADR (adopted) or a `wontfix` decision (rejected).

#### Required Corrections

- Review existing TODOs and classify each one.
- Identify comments indicating temporary solutions.
- Create issues for relevant technical debt.
- Link architectural decisions to their corresponding ADRs.
- Define closure criteria for pending items.
- Prevent known limitations from being mistaken for completed
  functionality.

#### Acceptance Criteria

- Relevant technical debt has traceable records.
- Architectural decisions have documented justifications.
- Limitations are known and documented.
- Critical pending items have priorities and completion criteria.

---

## 14. Recommended Implementation Plan

Implementation should follow technical dependencies. New clinical
functionality should not be prioritized before consolidating the imaging
core.

### Phase A — Data Integrity and Geometry

**Priority:** P0

1. Review DICOM pixel decoding (§3.2).
2. Review intensity calibration (§3.4).
3. Correct `VolumeGeometry` construction.
4. Validate LPS/RAS orientation.
5. Correct MPR geometry and anatomical orientation (§3.1).
6. Implement anatomical orientation indicators.
7. Create reference datasets and regression tests.

**Completion Milestone:** Reliable DICOM import and geometrically correct
MPR visualization.

### Phase B — Import Pipeline Consolidation

**Priority:** P1

1. Create the `DicomSeriesReader` Protocol (§4.3).
2. Decouple `ImportDicomSeriesHandler` from Infrastructure.
3. Review handler registration (§4.4).
4. Integrate import with `QtTaskManager` (§5.1).
5. Implement progress reporting, cancellation, and error handling.
6. Ensure safe scene updates.

**Completion Milestone:** Asynchronous, decoupled, and reproducible import
workflow.

### Phase C — Application Consolidation

**Priority:** P1/P2

1. Reduce `MainWindow` responsibilities (§4.2) — extract
   `ImportController` first, then `ProjectController`.
2. Review `ProjectManager` lifecycle (§4.5).
3. Define project shutdown behavior.
4. Consolidate OpenGL configuration (§8.1).
5. Review `WorkspaceSpec` and Module System integration (§6.1) as a
   prerequisite for Phase 5.
6. Correct test inconsistencies (§11.3).
7. Correct `ProjectMetadata.with_status` docstring (§11.4).

**Completion Milestone:** Organized application initialization, navigation,
command execution, and lifecycle management.

### Phase D — Privacy and Quality

**Priority:** P1/P2

1. Define the PHI handling policy (§9.1).
2. Review logs and telemetry.
3. Review persistence and export of identifiable data.
4. Remove personal absolute paths (§11.1).
5. Complete the legacy code removal (§7).
6. Review `VtkImageAdapter` memory strategy (§10.1).
7. Review visualization pipeline (§10.2).

**Completion Milestone:** Consistent, testable repository with documented
privacy policies.

### Phase E — Technology Evaluation and Optimization

**Priority:** P2/P3

1. Evaluate MPR performance on the reference dataset (§3.5). Optimize
   only if the measurement justifies it.
2. Compare pydicom and SimpleITK on three reference datasets (§12).
3. Evaluate the need for DCMTK (§12).
4. Review dependencies and distribution.
5. Consolidate technical documentation.

**Completion Milestone:** Stabilized infrastructure and evidence-based
technology decisions.

---

## 15. Functional Validation Milestone — Medical Imaging MVP

After completing the priority corrections, CranioZ must demonstrate a
complete functional workflow.

### Validation Workflow

1. Create a project.
2. Import a DICOM series.
3. Validate metadata and geometry.
4. Visualize axial, coronal, and sagittal planes.
5. Navigate between slices.
6. Adjust window/level.
7. Visualize the volume in 3D.
8. Import an STL model.
9. Position the model in the same scene.
10. Apply transformations.
11. Save the project.
12. Close and reopen the project.
13. Verify preservation of state and geometry.

### General Completion Criteria

- The volume preserves its physical geometry.
- Anatomical orientation is correct.
- Intensity values are preserved and correctly interpreted.
- The UI remains responsive during import.
- Scene objects appear in their expected positions.
- The project can be reopened without information loss.
- Results are reproducible across reference examinations.

---

## 16. Implementation Guidelines

The following guidelines must be observed throughout this plan:

1. Do not perform broad refactoring without identifying consumers and
   dependencies.
2. Do not replace libraries based solely on technological preference.
3. Do not introduce infrastructure frameworks without a demonstrated need.
4. Do not duplicate responsibilities across Application, Domain,
   Infrastructure, and UI.
5. Do not allow silent normalization or transformation of clinical data.
6. Do not consider a module functional merely because its manifest is
   registered.
7. Do not consider visualization correct merely because the volume appears
   on screen.
8. Every geometry correction must include tests using reference data.
9. Every change to subsystem interfaces must include corresponding tests.
10. Every relevant architectural decision must be documented through an ADR
    when appropriate.
11. Every reorganization must justify itself as a Correction,
    Consolidation, or Optimization. If it cannot, defer it until it can.

---

## 17. Expected Outcomes

Upon completion of this plan, CranioZ should provide:

- Consistent medical imaging infrastructure.
- Validated DICOM reading.
- Reliable spatial geometry.
- Anatomically correct MPR visualization.
- 3D rendering integrated into the scene.
- Asynchronous import.
- Appropriate separation between UI, Application, Domain, and
  Infrastructure.
- Predictable project lifecycle.
- Documented privacy policy.
- Reproducible regression and validation tests.
- A repository free of unjustified legacy implementations.
- A codebase that distinguishes corrections from reorganizations, and
  defers the latter until they become the former.

**Core Directive:** Consolidate the reliability of the Medical Imaging core
and the stability of architectural interfaces before expanding the number
of clinical features in CranioZ. Reorganization without an observed
problem is not progress.

---

## Appendix A — What Changed from v2.0

This appendix documents the revisions from version 2.0 to version 2.1 for
reviewers who have read the previous draft.

### Formatting

- Replaced the `python` code block in §4.1 that was breaking Markdown
  rendering (the block contained a type union with the pipe character and
  was not closed with a proper fenced code block in some transcriptions).
  Replaced with a bullet list of fields and a plain paragraph describing
  the new `MainWindow.__init__` signature.
- Replaced inline type annotations containing the pipe character with
  prose where possible.
- Replaced the conceptual ASCII diagram in §4.3 and §12 with descriptive
  bullet lists.

### Content

- §3.1: added a `Status (2026-11-13)` subsection documenting that the
  `QImage.mirrored` to `QImage.flipped` migration is done and that the
  orientation test and documentation remain pending.
- §7.4: added the Block 1–3 delivery summary (Toolbar polish,
  `Toolbar.set_active`/`set_expanded`, `Editor.set_active_view`).
- §11.3: added the `Compare-Object` evidence for the duplicate
  `test_no_hardcoded_appearance.py` removal.
- §13: added the `Applying the Classification` subsection describing how
  each category is applied in practice.
- §3.2 and §3.4: replaced the numeric ranges (0 to 4095) and the specific
  integer comparisons with prose to avoid Markdown parser edge cases.
- Version bumped to 2.1.
- Companion documents line added at the top of the file.