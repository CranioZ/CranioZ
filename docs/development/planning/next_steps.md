# Next Steps

**Document type:** Development action plan and handoff  
**Status:** Active  
**Current phase:** Phase 4A — Imaging Core & Rendering Validation
**Last updated:** 2026-11-27

---

## 1. Purpose and Planning Hierarchy

This document defines the immediate development priorities, execution sequence, current status, and handoff information for CranioZ.

`implementation_plan.md` is the authoritative roadmap. It defines phase scope, dependencies, and completion criteria. This document must not redefine those decisions.

| Document | Responsibility |
|---|---|
| `implementation_plan.md` | Authoritative implementation roadmap |
| `next_steps.md` | Immediate priorities and development handoff |
| `architectural_consolidation_plan.md` | Architectural inconsistencies and consolidation |
| `refactoring_plan.md` | Editor and Module architecture refactoring |
| `widget_catalog.md` | Authoritative inventory and contracts for reusable system widgets |
| `professional.md` | Professional profile domain and persistence |
| `monitor_logs.md` | Logs Monitor specification |
| ADRs | Accepted architectural decisions and constraints |

The widget catalog must be consulted before creating or modifying reusable system widgets. Widget classification follows ADR-0003.

## 2. Current Project Status

Phases 0, 1, 2, and 3 are closed.

The Editor Architecture Refactoring (ADR-0015) and Sprints I, J, and K are complete.

Phase 3 closed on 2026-11-27. Sprint L delivered the Professional profile and navigation workflow. The developer determined that the remaining Professional screens neither block nor unlock any phase, so Telas 3–7 and the remaining Professional capabilities are deferred.

**Phase 4A is now active.**

### 2.1 Completed Deliverables

| Deliverable | Status |
|---|---|
| Foundation & Boot (Phase 0) | Complete |
| Contracts, Core Domain & i18n (Phase 1) | Complete |
| Workspace Engine & Icons (Phase 2) | Complete |
| Editor Architecture Refactoring (ADR-0015) | Complete |
| Sprint I — ProjectIndex (ADR-0016) | Complete |
| Sprint J — Coordinated project deletion | Complete |
| Sprint K — Asynchronous flow loading | Complete |
| Sprint L.0 — System form widgets | Complete |
| Sprint L.0.2 Delivery A — Qt-native widgets | Complete |
| Sprint L.0.2 Delivery B — Sections and lists | Complete |
| SVG provider, central asset catalog, and UI icon migration | Complete |
| Main Window display states: maximize, full screen, and restore | Complete |
| Home Page top bar: SVG wordmark and logs/help/settings actions | Complete |
| Home Page visual refinement: StartButton, action variants, and table rows | Complete |
| Home Page project management: selection, removal, and catalog refresh | Complete |
| Seed project names: patient name without the `Caso ` prefix | Complete |
| Phase 3 closure with remaining Professional screens deferred | Complete |

### 2.2 Current Validation Baseline

Last recorded baseline after the Home Page refinement and project-management UI delivery,
2026-11-27:

- 1935 passed.
- 0 failed.
- 0 errors.
- 2 skipped.
- `ruff check` clean.
- `ruff format --check` clean (649 files).
- `mypy src` clean (328 source files).

This validation was rerun for the current delivery. Update the baseline after each subsequent completed delivery.

Focused L.1 validation on 2026-11-26: 9 tests passed for the Professional Module contract, Editor/Workspace materialization, and dependency boundaries.

### 2.3 Latest UI Delivery

The Main Window, Home Page, Workspace shell, and Professional navigation now
use the centralized SVG asset catalog. The implemented interface includes:

- SVG wordmark and logs/help/settings actions on the Home Page top bar.
- `logs_requested` forwarding through `HomePage` to a temporary MainWindow
  placeholder; the Logs Dialog itself remains deferred.
- Distinct maximize, full-screen, and restore icons synchronized across both
  top bars.
- Theme-aware `currentColor` rendering and aspect-ratio preservation for
  non-square SVG sources.
- `StartButton` refined to an 80 px control with a 32 px icon and reduced outer margin.
- SVG icons on the project and flow management actions.
- Collapsible project search opened and closed through the search icon.
- Project management page with multi-selection, removal confirmation, error handling,
  and Home Page catalog refresh.
- Dedicated visual variants for Home Page top-bar actions and Community
  Sidebar items.
- Alternating project-table row colors.
- Seed data stores the patient name directly, without the `Caso ` prefix, and
  normalizes projects created by previous seed runs.

## 3. Immediate Priorities

The DICOM visualization bug is considered resolved and must not be reopened as an active task. The current execution sequence is:

1. Define the Phase 4A Imaging Reference Dataset using a synthetic asymmetric phantom.
2. Establish objective reference results for geometry, MPR, and 3D rendering.
3. Validate Scene integration and persistence.
4. Complete the minimal `RenderingAdapter`.
5. Run the Phase 4A acceptance suite on Windows.
6. Close Phase 4A before beginning Phase 4B.

Professional Telas 3–7, L.0.2 Deliveries C/D, and the remaining Professional capabilities are future backlog work. They do not block Phase 4A.

## 4. Sprint L — Closed Professional Module Scope

Sprint L is closed for the accepted Phase 3 scope.

| Stage | Scope | Status |
|---|---|---|
| L.0 | System form widgets | Complete |
| L.0.2 A/B | Extended widget suite | Complete |
| L.0.2 C/D | TimelineSlider, ColorPicker, Histogram, final harness and HiDPI closure | Deferred |
| L.1 | Professional Editor and profile integration | Complete; visually approved 2026-11-26 |
| L.2 | Navigation, sections, ordering, and persistence for the profile workflow | Complete for Phase 3 scope; remaining screens deferred |

### 4.1 L.1 — Remaining Actions

The implementation includes:

- Professional domain and SQLite profile persistence.
- Repository and service layer.
- Command/query flow.
- `ProfessionalEditor`.
- Tela 2 profile interface.
- Central-Area composition.
- `professional.*` settings integration.
- Visual debug harness and focused tests.

Remaining actions:

- [x] Decide the ownership and exposure contract for `ModuleUISpec`, respecting the package dependency rules established by ADR-0015.
- [x] Align `professional.md` and related architecture documentation with the approved decision.
- [x] Validate the Editor registration and Workspace materialization path.
- [x] Decide whether application-level selection of `PROFESSIONAL_UI_SPEC` belongs to Sprint L or to the future module activation flow. The decision assigns selection to the UI Workspace composition root; the harness and integration test prove spec materialization.
- [x] Perform manual visual review of Tela 2.
- [x] Record approval or required corrections.

Visual review on 2026-11-26 identified that the Tela 2 title was hidden
under the Workspace Top Bar. Header clearance was corrected and the
corrected Tela 2 was approved by the developer on 2026-11-26.

**Approved decision (2026-11-26):** `PROFESSIONAL_UI_SPEC` remains owned by the UI Workspace composition layer and is selected and registered by the composition root. Built-in Modules must not import Workspace components or concrete Editors. This preserves the dependency boundaries established by ADR-0015 and the existing architecture guard.

### 4.2 L.2 — Professional Navigation

**Goal:** Complete the Professional Editor's internal navigation and configuration interactions for the delivered profile workflow.

Scope:

- [x] Integrate `CollapsibleSection` into the Tela 2 profile groups.
- [x] Integrate `DragList` for ordering the Tela 2 profile groups.
- [x] Persist and restore the Tela 2 section order through `professional.ui.navigation_order`.
- [x] Persist and restore Tela 2 section expansion state through `professional.ui.collapsed_sections`.
- [x] Integrate `IconSidebar` with the six Professional tabs.
- [x] Implement `SvgIconProvider` with Unicode fallback and migrate the six Professional navigation icons.
- [x] Implement navigation between the six Professional tabs; unimplemented tabs show localized placeholders.
- [x] Support section expansion/collapse and drag ordering in Tela 2.
- [x] Persist and restore Tela 2 navigation order.
- [x] Validate theme changes, including SVG icon recoloring and refresh.

The following items belong to the future Professional backlog and do not block any phase:

- Integrate `EyeToggleButton` and `VisibilityToggle` in the Tela 7 top-level tab configuration.
- Implement prototype screens Tela 3–7.
- Implement and persist Tela 7 top-level tab visibility and ordering.
- Complete pending translations and language-change validation.
- Migrate remaining appearance and icon usage in Professional widgets.
- Validate keyboard and accessibility behavior across the complete Professional module.

Visual validation on 2026-11-26 confirmed the Tela 2 section layout,
expansion/collapse behavior, drag handles, ordering, and preview rendering.
The developer approved the resulting interface.

Tela 2 section visibility is not required by the approved prototype.
Visibility and ordering controls belong to the Tela 7 top-level tab
reorganization dialog.

Tela 2 section order and expansion state are now restored and persisted
independently through `professional.ui.navigation_order` and
`professional.ui.collapsed_sections`.

Professional-specific compositions must remain inside the Professional Editor unless a demonstrated reuse case justifies extracting them into system widgets.

The clinical `RulerOverlay` is not part of the generic widget catalog. Its implementation must follow ADR-0003 and the requirements of its first consuming Editor.

### 4.3 L.0.2 Deferred Deliveries

These deliveries remain outside the immediate execution sequence.

**Delivery C**
- `TimelineSlider`
- `ColorPicker`
- `Histogram`

**Delivery D**
- Consolidate the visual debug harness.
- Reproduce the required prototype screens.
- Validate Dark and Light themes.
- Validate HiDPI at scale factors 1.5 and 2.
- Close the widget catalog entries.
- Run complete validation.

Do not start C/D merely to complete the original widget list. Reassess their necessity when a concrete consumer requires them.

### 4.4 Sprint L Closure

- [x] Developer approved Sprint L closure for the accepted Phase 3 scope on 2026-11-27.
- [x] Validate the Professional Editor through the actual Workspace and Editor lifecycle.
- [x] Validate ModuleUISpec registration and materialization.
- [x] Validate navigation and presentation-state persistence.
- [x] Validate theme changes.
- [x] Run the complete test suite and static analysis.
- [x] Record remaining profiles, screens, translations, accessibility, and widget-catalog work as future Professional backlog.

Phase 3 and Sprint L are closed as of 2026-11-27. Future Professional work must be scheduled separately and must not reopen Phase 3.

## 5. Phase 3 Closure and Deferred Work

### 5.1 Project Management UI

The project deletion API and its Phase 3 user-facing interface are implemented.

- [x] Implement project search.
- [x] Implement project sorting.
- [x] Validate project sorting visually through the Home Page debug harness.
- [x] Implement project selection and multi-selection behavior.
- [x] Implement project removal UI.
- [x] Connect removal to the existing `ProjectManager.delete_project` API.
- [x] Validate confirmation, error handling, and catalog refresh.
- [x] Ensure External Reference source data is never deleted with the project.

Visual validation on 2026-11-26 confirmed ascending order and sort indicators for project name, ID, and creation date.

The project import/export interface is not part of Phase 3; it belongs to Phase 8.

### 5.2 Phase 3 Closure

Phase 3 was formally closed on 2026-11-27:

- [x] Complete Sprint L for the accepted Phase 3 scope.
- [x] Resolve ModuleUISpec ownership.
- [x] Approve Tela 2 visually (2026-11-26).
- [x] Complete project search, sorting, selection, and removal UI.
- [x] Run complete validation.
- [x] Update `implementation_plan.md` with verified completion status.
- [x] Update documentation and record remaining technical debt.
- [x] Defer Professional Telas 3–7 and remaining module capabilities to future work.

The deferral was approved by the developer because the remaining Professional pages neither block nor unlock any phase. Phase 4A is active.

## 6. Current Phase — Phase 4

Phase 4 is divided into two milestones. This section is a handoff summary; `implementation_plan.md` contains the complete scope and acceptance criteria.

### 6.1 Phase 4A — Imaging Core & Rendering Validation

**Primary objective:** Validate the complete DICOM → Volume → Scene → VTK → MPR/3D path.

**Status:** In progress.

Initial sequence:

1. Define the Imaging Reference Dataset using a synthetic asymmetric phantom.
2. Specify known dimensions, spacing, orientation, origin, slice positions, and intensity regions.
3. Establish objective reference results for MPR and 3D.
4. Complete Scene integration and persistence.
5. Implement the minimal `RenderingAdapter`.
6. Validate MPR and 3D against the reference dataset.
7. Validate geometry, orientation, intensity, crosshair, and resource lifecycle.
8. Run Windows rendering and integration tests.

The reference dataset and its tests must remain available for reuse in Phase 7.

**Do not expand the visualization UI before the rendering acceptance criteria are satisfied.**

### 6.2 Phase 4B — Import & Visualization UI

After Phase 4A validation:

- Unified Import Dialog and category-specific importers.
- Resource preview and management.
- `ViewerLayoutManager` and dynamic layouts.
- 2D and 3D tools.
- Clinical transfer functions.
- Viewer status indicators.
- VTK lifecycle and UI integration tests.

### 6.3 Module Registration Boundary

Phase 4 completes module discovery and registration for Editors, Tools, Services, and Flow definitions.

It does not implement workflow execution. `WorkflowEngine` and Flow execution belong to Phase 5.

## 7. Deferred Work and Known Issues

| Item | Status | Reference / Destination |
|---|---|---|
| Professional Telas 3–7 | Deferred | Future Professional backlog |
| Remaining Professional module capabilities | Deferred | Future Professional backlog |
| L.0.2 Deliveries C/D | Deferred | Future Professional backlog |
| Logs Monitor | Deferred; unscheduled | `monitor_logs.md` |
| SQLite ProjectIndex and Recent Projects | Planned | Phase 8 / ADR-0016 |
| Project import/export | Planned | Phase 8 |
| Remaining SVG migration outside Main Window, Home Page, Workspace, and Professional | Planned | Phase 8 |
| General AI and Node System | Planned | Phase 10 |
| GeometryRevision, asset deduplication, and advanced geometry operations | Deferred | Geometry roadmap |
| Startup optimization and lazy imports | Backlog | Future maintenance |
| VTK `GetData()` deprecation | Deferred | VTK compatibility work |
| Test stub documentation | Maintenance | Infrastructure tests |
| Remaining hardcoded appearance literals | Tracked debt | Appearance architecture |

### 7.1 Logs Monitor

The Logs Monitor is a developer-facing diagnostic subsystem specified in
`monitor_logs.md`. The Home Page button and `logs_requested` wiring are
implemented; `LogsDialog`, `QtLogHandler`, and diagnostic routing remain
deferred.

It is distinct from the clinical Console, History, and Telemetry. Its implementation belongs to a dedicated sprint and does not block Phase 4A.

### 7.2 Icon Infrastructure

The production composition root installs `SvgIconProvider` with
`UnicodeIconProvider` as the fallback. Theme-aware recoloring, cache
invalidation, HiDPI rendering, aspect-ratio preservation, and centralized
logical-name-to-path resolution are implemented. The Main Window, Home Page,
Workspace shell, and Professional navigation assets are migrated. Icons
without a migrated SVG continue to use Unicode without changing their
consumers. Progressive migration of the remaining assets is planned for Phase
8. Do not create a second icon-management system.

New SVG assets are added to:

`src/cranioz/assets/icons/`

Rules for manual asset addition:

- Register each logical name and relative asset path in
  `src/cranioz/ui/icons/catalog.py`.
- Use lowercase `snake_case`; there are no `dark/` or `light/` subdirectories.
- Use `currentColor` for monochrome paint so theme and state colors are applied.
- Prefer a `viewBox="0 0 24 24"` source with a transparent background.
- Do not embed raster images, fonts, scripts, or external references.
- Reuse the same SVG by requesting the same logical name from multiple widgets.
- A fully new logical name also requires catalog and Unicode fallback updates.

## 8. Architectural Constraints

The following constraints apply to all upcoming work:

- Follow accepted ADRs and package dependency boundaries.
- Consult `widget_catalog.md` before creating or modifying reusable system widgets.
- Generic reusable widgets belong in `src/cranioz/ui/widgets/`.
- Editor-specific overlays belong in `src/cranioz/ui/editors/overlays/`.
- Icon-based actions belong in `src/cranioz/ui/tools/builtin/`.
- Editor-specific compositions remain inside their Editor unless broader reuse is demonstrated.
- Modules must not instantiate concrete Editors.
- Domain data must not depend on Qt or VTK.
- Scene and domain objects remain the canonical source of clinical data.
- Long-running operations use `TaskManager` and support cancellation.
- VTK render-window operations remain on the GUI thread.
- User-facing strings use `TranslationService`.
- Shared visual properties use `ThemeService` and design tokens.
- Logs and telemetry must not expose PHI.

## 9. Validation Procedure

Run the complete validation suite after each delivery and before closing a phase or milestone.

### 9.1 Pytest

```powershell
.venv\Scripts\python.exe -m pytest
```

### 9.2 Ruff

```powershell
.venv\Scripts\python.exe -m ruff check .
.venv\Scripts\python.exe -m ruff format --check .
```

### 9.3 Mypy

```powershell
.venv\Scripts\python.exe -m mypy src
```

### 9.4 Validation Rules

- Do not accept new test failures.
- Do not introduce new Ruff violations.
- Do not introduce new mypy errors.
- Investigate regressions against the last recorded baseline.
- Do not reduce test coverage merely to obtain a passing suite.
- Record the execution date and actual results after each completed delivery.

## 10. Next Handoff

**Immediate task:** Establish the Phase 4A Imaging Reference Dataset and its
regression tests. Do not reopen the resolved DICOM visualization bug and do
not expand the visualization UI.

1. Define the synthetic asymmetric phantom and its expected geometry.
2. Add objective tests for NumPy → VTK conversion and MPR orientation.
3. Establish reference results for 3D rendering and resource lifecycle.
4. Validate Scene integration, persistence, and the minimal `RenderingAdapter`.
5. Run the Phase 4A acceptance suite before beginning Phase 4B.

Professional Telas 3–7 remain deferred. They may resume in a future,
separately scoped Professional module cycle.

### Reference Documents

- `implementation_plan.md` — authoritative roadmap and completion criteria.
- `docs/architecture/widgets/widget_catalog.md` — widget inventory and contracts.
- `docs/architecture/modules/professional/professional.md` — Professional domain and persistence.
- `docs/architecture/appearance/` — theme and design-token architecture.
- `ADR-0003` — widget, overlay, and tool classification.
- `ADR-0015` — Editor and Module package boundaries.
- `ADR-0016` — ProjectIndex synchronization.
- `ADR-0018` — Professional module SQLite persistence.
- `monitor_logs.md` — deferred Logs Monitor specification.

---

**Authority:** `implementation_plan.md` defines phase scope and completion criteria. ADRs define accepted architectural constraints. `widget_catalog.md` defines reusable widget contracts. This document defines immediate execution priorities and handoff.
