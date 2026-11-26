# Next Steps

**Document type:** Development action plan and handoff  
**Status:** Active  
**Current phase:** Phase 3 — Project, Home Page & Professional Module  
**Last updated:** 2026-11-26

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

Phases 0, 1, and 2 are closed.

The Editor Architecture Refactoring (ADR-0015) and Sprints I, J, and K are complete.

**Phase 3 remains in progress.** Sprint L is substantially implemented, but its remaining work and the project-management UI must be completed before Phase 3 can close.

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

### 2.2 Current Validation Baseline

Last recorded baseline, 2026-11-26:

- 1866 passed.
- 0 failed.
- 0 errors.
- 3 skipped.
- `ruff check` clean.
- `ruff format --check` clean (644 files).
- `mypy src` clean (325 source files).

This is the last recorded validation result, not a claim that the suite was rerun after every subsequent change. Update the baseline after each completed delivery.

## 3. Immediate Priorities

The `ModuleUISpec` ownership decision was approved on 2026-11-26. The current execution sequence is:

1. Perform manual visual review and approval of Professional Editor Tela 2.
2. Align the Professional architecture documentation with the approved `ModuleUISpec` ownership.
3. Implement Sprint L.2 — Professional navigation and configuration interactions.
4. Implement the pending project-management UI, especially project removal.
5. Run complete validation and close Sprint L.
6. Review all Phase 3 completion criteria against `implementation_plan.md`.
7. Close Phase 3 formally.
8. Begin Phase 4A only after Phase 3 closure.

L.0.2 Deliveries C and D remain deferred. They do not block L.1, L.2, or Phase 3 closure unless a concrete dependency is identified.

## 4. Sprint L — Professional Module

Sprint L is organized into four execution stages.

| Stage | Scope | Status |
|---|---|---|
| L.0 | System form widgets | Complete |
| L.0.2 A/B | Extended widget suite | Complete |
| L.0.2 C/D | TimelineSlider, ColorPicker, Histogram, final harness and HiDPI closure | Deferred |
| L.1 | Professional Editor and profile integration | Implemented; pending visual approval |
| L.2 | Navigation, sections, visibility, ordering, and persistence | Pending |

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
- [ ] Align `professional.md` and related architecture documentation with the approved decision.
- [ ] Validate the actual Editor registration and materialization path.
- [ ] Perform manual visual review of Tela 2.
- [ ] Record approval or required corrections.

**Approved decision (2026-11-26):** `PROFESSIONAL_UI_SPEC` remains owned by the UI Workspace composition layer and is selected and registered by the composition root. Built-in Modules must not import Workspace components or concrete Editors. This preserves the dependency boundaries established by ADR-0015 and the existing architecture guard.

### 4.2 L.2 — Professional Navigation

**Goal:** Complete the Professional Editor's internal navigation and configuration interactions.

Scope:

- [ ] Integrate `CollapsibleSection`, `DragList`, and `IconSidebar`.
- [ ] Integrate `EyeToggleButton` and `VisibilityToggle`.
- [ ] Implement prototype screens Tela 3–7.
- [ ] Implement navigation between sections.
- [ ] Support section expansion/collapse, visibility, and drag ordering.
- [ ] Persist and restore navigation order and visibility.
- [ ] Implement pending `pt_BR` translations.
- [ ] Migrate `SignaturePreview` empty-state colors to design tokens.
- [ ] Migrate the `FilePicker` browse action to the existing icon infrastructure.
- [ ] Validate keyboard and accessibility behavior.
- [ ] Validate theme and language changes.

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

- [ ] Validate the Professional Editor through the actual Workspace and Editor lifecycle.
- [ ] Validate ModuleUISpec registration and materialization.
- [ ] Validate profile persistence across application restarts.
- [ ] Validate settings restoration.
- [ ] Validate theme and language changes.
- [ ] Validate navigation and presentation-state persistence.
- [ ] Run the complete test suite and static analysis.
- [ ] Update `widget_catalog.md` for any implemented or changed widgets.
- [ ] Record unresolved limitations.

Sprint L must not absorb unrelated Phase 4 work.

## 5. Remaining Phase 3 Work

### 5.1 Project Management UI

The project deletion API is already implemented. The missing work is its user-facing interface.

- [x] Implement project search.
- [x] Implement project sorting.
- [x] Validate project sorting visually through the Home Page debug harness.
- [ ] Implement project selection and multi-selection behavior.
- [ ] Implement project removal UI.
- [ ] Connect removal to the existing `ProjectManager.delete_project` API.
- [ ] Validate confirmation, error handling, and catalog refresh.
- [ ] Ensure External Reference source data is never deleted with the project.

Visual validation on 2026-11-26 confirmed ascending order and sort indicators for project name, ID, and creation date.

The project import/export interface is not part of Phase 3; it belongs to Phase 8.

### 5.2 Phase 3 Closure

Before closing Phase 3:

- [ ] Complete Sprint L, including L.2.
- [x] Resolve ModuleUISpec ownership.
- [ ] Approve Tela 2 visually.
- [ ] Complete project search, sorting, selection, and removal UI.
- [ ] Run complete validation.
- [ ] Update `implementation_plan.md` with verified completion status.
- [ ] Update documentation and record remaining technical debt.

**Phase 4 must not formally begin until these criteria are satisfied.**

## 6. Next Phase — Phase 4

Phase 4 is divided into two milestones. This section is a handoff summary; `implementation_plan.md` contains the complete scope and acceptance criteria.

### 6.1 Phase 4A — Imaging Core & Rendering Validation

**Primary objective:** Validate the complete DICOM → Volume → Scene → VTK → MPR/3D path.

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
| L.0.2 Deliveries C/D | Deferred | Sprint L |
| Logs Monitor | Deferred; unscheduled | `monitor_logs.md` |
| SQLite ProjectIndex and Recent Projects | Planned | Phase 8 / ADR-0016 |
| Project import/export | Planned | Phase 8 |
| SVG integration into the existing IconManager | Planned | Phase 8 |
| General AI and Node System | Planned | Phase 10 |
| GeometryRevision, asset deduplication, and advanced geometry operations | Deferred | Geometry roadmap |
| Startup optimization and lazy imports | Backlog | Future maintenance |
| VTK `GetData()` deprecation | Deferred | VTK compatibility work |
| Test stub documentation | Maintenance | Infrastructure tests |
| Remaining hardcoded appearance literals | Tracked debt | Appearance architecture |

### 7.1 Logs Monitor

The Logs Monitor is a developer-facing diagnostic subsystem specified in `monitor_logs.md`.

It is distinct from the clinical Console, History, and Telemetry. Its implementation belongs to a dedicated sprint and does not block Sprint L or Phase 3 closure.

### 7.2 Icon Infrastructure

The `IconManager` and existing icon provider infrastructure are implemented. The current UI uses the existing Unicode-based provider.

SVG integration and progressive migration of UI icons are planned for Phase 8. Do not create a second icon-management system.

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

Run the complete validation suite after each delivery and before closing Sprint L.

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

**Immediate task:** Perform the manual visual review of Professional Editor Tela 2.

Run:

```powershell
.venv\Scripts\python.exe scripts\debug\ui\professional\debug_professional_editor.py
```

After the review:

1. Record visual approval or required corrections.
2. Align the Professional architecture documentation with the approved `ModuleUISpec` ownership.
3. Validate the actual Editor registration and materialization path.
4. Implement L.2.
5. Complete the remaining Phase 3 project-management UI.
6. Validate and close Sprint L.
7. Close Phase 3 according to `implementation_plan.md`.

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
