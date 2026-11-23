# Next Steps

**Document type:** Action plan and development handoff  
**Status:** Active  
**Scope:** Current development priorities and execution sequence for Phase 3  
**Last updated:** 2026-11-23

---

## 1. Context

Phase 3 — Project, Home Page & Professional Module — is the current implementation phase.

Phases 0, 1, and 2 are complete. The structural Editor Architecture Refactoring and Sprints I, J, and K have also been completed. The remaining Phase 3 deliverable is Sprint L — Professional Editor.

The immediate priority is to implement the reusable system widgets required by the Professional Editor, followed by the Editor itself and its internal navigation and configuration interface.

The widget inventory is maintained separately in:

- `widget_catalog.md` — system-wide widget catalog, classifications, implementation status, dependencies, and architectural guidelines.
- `sprint_l0_system_widgets.md` — implementation specification for the system widgets required by Sprint L. To be created before implementation.

The `widget_catalog.md` is an inventory, not an execution plan. Sprint L implements only the components required by the Professional Editor. Other catalog entries remain planned or in the backlog until their consuming workflows justify implementation.

### 1.1 Current validation baseline

**Baseline recorded on 2026-11-23 (post-L.0):**

- 1742 tests passing.
- 0 failed.
- 0 errors.
- 2 skipped.
- `ruff check .` clean.
- `ruff format --check .` clean (574 files).
- `mypy src` clean (289 source files).

This is the reference baseline before Sprint L. Update the numbers after each delivery.

### 1.2 Architecture status

The following foundations are implemented:

- Structural Editor Architecture Refactoring, including the Editor lifecycle and registry foundations.
- Workspace composition through Areas and Editors.
- `EditorStack` with lazy materialization and lifecycle management.
- `AreaLayoutRenderer` for intra-Area composition.
- Editor-level Toolbar integration.
- Active View handling and `ACTIVE_ONLY` Toolbar policy.
- ThemeService, ThemeCompiler, design tokens, and QSS styling.
- IconProvider and UnicodeIconProvider.
- TranslationService integration for the application shell.
- ProjectIndex and coordinated project deletion.
- Asynchronous flow loading.
- Project and Home Page foundations.

The application uses Qt Widgets, modular QSS, and Python Design Tokens, as defined by ADR-0014.

### 1.3 Phase boundary

Phase 4 — Scene & Visualization — remains planned.

It must not formally begin until Phase 3 is closed according to `implementation_plan.md`.

This does not prohibit isolated maintenance or corrections to existing infrastructure. It prevents new Phase 4 deliverables from being absorbed into the current sprint without an explicit planning decision.

---

## 2. Planning hierarchy

The following documents have distinct responsibilities.

| Document | Responsibility |
|---|---|
| `implementation_plan.md` | Authoritative roadmap: phases, deliverables, dependencies, and completion criteria. |
| `next_steps.md` | Immediate priorities, execution sequence, current status, and handoff. |
| `architectural_consolidation_plan.md` | Architectural inconsistencies, duplication, legacy code, and consolidation decisions. |
| `refactoring_plan.md` | Technical procedure for Editor and Module architecture refactoring. |
| `widget_catalog.md` | Permanent inventory of reusable system widgets. |
| `sprint_l0_system_widgets.md` | Detailed implementation specification for L.0 widgets. |
| `professional.md` | Professional profile domain, persistence, and behavior specification. |
| `monitor_logs.md` | Technical specification for the deferred Logs Monitor. |

`implementation_plan.md` remains authoritative. This document must not redefine phase scope or silently introduce new roadmap deliverables.

---

## 3. Current focus

**Phase 3 is in progress. Sprint L is the remaining major deliverable.**

The recommended execution sequence is:

1. Consolidate the system widget catalog.
2. Specify and implement the widgets required by the Professional Editor (L.0).
3. Implement and integrate the Professional Editor and its profile persistence (L.1).
4. Implement the Professional Editor's internal navigation and configuration interactions (L.2).
5. Validate and close Sprint L.
6. Review the remaining Phase 3 criteria and close Phase 3 formally.

### 3.1 Sprint L — Professional Editor

Sprint L is divided into three execution stages.

| Stage | Scope | Main deliverable |
|---|---|---|
| **L.0** | System Widgets | Reusable form widgets required by the Professional Editor. |
| **L.1** | Professional Editor | Editor registration, profile interface, ModuleUISpec, settings integration, and SQLite persistence. |
| **L.2** | Professional Navigation | Reusable navigation, sections, visibility controls, drag-and-drop, and persisted presentation state. |

These stages are internal execution steps of Sprint L. They are not new implementation phases or independent sprints.

### 3.2 Architectural principles for Sprint L

The following constraints apply throughout implementation:

- `ProfessionalEditor` is an Editor, not a Module-specific tab system.
- It is hosted by the central Area.
- The Professional Module contributes declarative UI configuration through `ModuleUISpec`.
- Reusable widgets belong to `src/cranioz/ui/widgets/`.
- The Professional Editor consumes system widgets; it does not own their implementations.
- Professional-specific compositions remain inside the Professional Editor implementation unless reuse is demonstrated.
- Module definitions must not instantiate concrete Editors.
- Use native Qt Widgets when they satisfy the required behavior.
- Do not introduce abstractions without a demonstrated need.
- Profile data persistence must follow `professional.md`.
- `persistent_state()` and `restore_state()` are for visual Editor state, not professional profile data.
- Theme and translation integration must follow the existing global infrastructure.

---

## 4. Completed work

### 4.1 Phase 0 — Foundation & Boot

Complete.

### 4.2 Phase 1 — Contracts, Core Domain & i18n

Complete.

The contracts and core domain foundations are implemented. TranslationService is integrated into the application shell.

### 4.3 Phase 2 — Workspace Engine & Icons

Complete.

The Workspace, Areas, Editor lifecycle, Toolbar integration, EditorStack, theme foundation, and icon infrastructure are implemented.

### 4.4 Phase 3 — Completed deliverables

The following work is complete:

| Deliverable | Status | Reference |
|---|---|---|
| Structural Editor Architecture Refactoring | Complete | ADR-0015 |
| ProjectIndex (Sprint I) | Complete | ADR-0016 |
| Coordinated project deletion (Sprint J) | Complete | `ProjectManager` / project subsystem |
| Asynchronous loading (Sprint K) | Complete | Flow loading and TaskManager integration |

Sprint K adopted a minimal scope: flow loading is asynchronous, while project loading remains synchronous.

The completed work must not be reopened as part of Sprint L unless a concrete regression or missing contract is identified.

---

## 5. Sprint L — Professional Editor

### 5.1 L.0 — System Widgets

**Status:** Complete (2026-11-23)  
**Purpose:** Implement the reusable system widgets required to build the Professional Editor.

#### Delivered

| Component | File | Tests |
|---|---|---|
| `FormField` | `src/cranioz/ui/widgets/forms/form_field.py` | 8 |
| `FormCombo` | `src/cranioz/ui/widgets/forms/form_combo.py` | 7 |
| `FilePicker` | `src/cranioz/ui/widgets/forms/file_picker.py` | 7 |
| `SignaturePreview` | `src/cranioz/ui/widgets/forms/signature_preview.py` | 7 |

Package: `src/cranioz/ui/widgets/forms/`  
Tests: `tests/unit/ui/widgets/forms/`  
Public API: `cranioz.ui.widgets.forms.__all__`

#### Validation

- 29 tests passing.
- `ruff check` clean.
- `ruff format --check` clean.
- `mypy src` clean.

#### Known deferrals

- `SignaturePreview` uses integer RGB constants (`QColor(160,160,160)`) instead of
  design tokens. Tracked with `TODO(L.2)` — migrate when `SignaturePreview`
  accepts an optional `ThemeService` (see `widget_catalog.md` §8.4).
- No QSS specific to the four widgets yet; they inherit the global theme
  (`compiler.py` `_build_qss`). `objectName`s are already in place
  (`CraniozFormFieldInput`, `CraniozFormComboInput`, etc.) for future QSS work.

#### Completion criteria

- [x] Four widgets implemented in the system UI package.
- [x] Public APIs and signals documented.
- [x] Unit tests passing.
- [x] Theme and translation behavior validated (accessibility names, `LanguageChange`).
- [x] No dependency on Professional-specific code.
- [x] Widget catalog statuses updated.

### 5.2 L.1 — Professional Editor

**Status:** Planned  
**Purpose:** Deliver the first functional Professional Editor using the L.0 system widgets.

#### Scope

- Implement `ProfessionalEditor`.
- Register it in `EditorRegistry`.
- Provide the Professional Module's `ModuleUISpec`.
- Host the Editor in the central Area.
- Implement the initial professional profile interface.
- Integrate the `professional.*` settings namespace.
- Implement persistence according to `professional.md`.
- Add Editor contract and integration tests.

#### Architectural constraints

`ProfessionalEditor` is a concrete Editor implementation.

The Professional Module is declarative and contributes the UI specification required to expose the Editor. It must not instantiate the Editor directly.

The Editor must follow the existing lifecycle and context contracts.

#### Persistence

Professional profile persistence must use the SQLite database defined in `professional.md`:

```text
~/.cranioz/professional/professional.db
```

Do not introduce a temporary JSON persistence layer or use Editor visual-state persistence to store profile data.

The initial implementation should remain limited to the profile fields and operations required by the existing specification.

#### Settings integration

Use the `professional.*` namespace for appropriate user or application settings.

Do not duplicate profile data in settings when it belongs in the professional database.

#### Completion criteria

- `ProfessionalEditor` registered and materialized through the established Editor architecture.
- Professional Module exposes the correct `ModuleUISpec`.
- Initial profile interface functional.
- SQLite persistence integrated according to `professional.md`.
- Settings namespace integrated.
- Editor lifecycle and integration tests passing.
- No Professional-specific widgets incorrectly placed in the generic system widget package.

### 5.3 L.2 — Professional Navigation

**Status:** Planned  
**Purpose:** Implement the internal navigation and configuration interactions required by the Professional Editor.

#### Scope

Implement the following reusable system widgets:

| Component | Classification | Main responsibility |
|---|---|---|
| `IconSidebar` | Composite Widget | Navigation between profile sections. |
| `CollapsibleSection` | Composite Widget | Expandable configuration sections. |
| `EyeToggleButton` | Qt Component | Visibility control. |
| `DragHandle` | Qt Component | Drag affordance for reordering. |
| `DragList` | Custom Widget | Reorderable list. |

These components belong to `src/cranioz/ui/widgets/`.

#### Professional-specific compositions

The Professional Editor may compose the system widgets into higher-level components, such as:

- `ProfessionalSidebar`;
- `ProfessionalSectionTree`;
- `ProfessionalConfigPanel`.

These are consumer-specific compositions and should remain inside the Professional Editor implementation unless a separate reuse case emerges.

#### Behavior and persistence

Implement the navigation, visibility, and ordering behavior required by the Professional interface.

Persist the corresponding presentation configuration through the appropriate application settings mechanism.

Do not store visual navigation state in the professional profile database unless the data is genuinely part of the professional domain.

#### Completion criteria

- Reusable widgets implemented and tested.
- Professional-specific compositions integrated.
- Navigation between sections works.
- Expand/collapse and visibility behavior works.
- Drag-and-drop ordering works where required.
- Ordering and visibility preferences are persisted and restored.
- Keyboard and accessibility behavior validated.

### 5.4 Sprint L integration and closure

After L.0, L.1, and L.2:

- Validate the Professional Editor through the actual Workspace and Editor lifecycle.
- Validate ModuleUISpec registration and materialization.
- Validate profile persistence across application restarts.
- Validate settings restoration.
- Validate theme and language changes.
- Run the full test suite and static analysis.
- Update `widget_catalog.md` to reflect implemented components.
- Update `implementation_plan.md` if the completion status of Sprint L or Phase 3 changes.
- Record any remaining limitations explicitly.

Sprint L must not absorb unrelated Phase 4 or general UI backlog items.

---

## 6. Deferred work

### 6.1 Logs Monitor

The Logs Monitor remains a dedicated deferred implementation task.

Its specification is maintained in `monitor_logs.md`.

It is not a Phase 3 deliverable and does not block Sprint L.

It may be scheduled as a separate sprint after the completed Sprints I–K, without changing the dependency sequence of Sprint L.

### 6.2 Phase 4 — Scene & Visualization

Phase 4 remains deferred until Phase 3 is formally closed.

Its pending deliverables include:

- Unified Import Dialog.
- ViewerLayoutManager and dynamic viewer layouts.
- 2D and 3D visualization tools.
- Viewer status indicators.
- Clinical transfer functions.
- Further Editor workflows and visualization integration.

The widget catalog may contain components intended for these future workflows, but their presence in the catalog does not authorize implementation during Sprint L.

### 6.3 Widget backlog

The following components remain outside Sprint L unless a concrete requirement is approved:

- `TimelineSlider`;
- `Ruler`;
- `DualRangeSlider`;
- `Histogram`;
- `ColorPicker`;
- `ProgressBar`;
- additional tomography and cephalometry controls.

Their implementation milestones must follow the consuming Editor or subsystem dependencies documented in `widget_catalog.md`.

---

## 7. Known issues and deferred items

The following items must remain visible and must not be silently absorbed into Sprint L:

| Item | Status | Action |
|---|---|---|
| Logs Monitor | Planned | Schedule separately; specification already exists. |
| Test stub documentation | Pending | Add README and TODO markers to the identified infrastructure test stubs. |
| `correlation_id` propagation | Deferred | Revisit according to the implementation plan. |
| `event_subscription` contract test | Deferred | Add dedicated coverage when the corresponding integration is implemented. |
| Remaining hardcoded appearance literals | Tracked debt | Continue using the existing architecture guard and debt list. |
| VTK `GetData()` deprecation | Deferred | Migrate according to the VTK 10 compatibility plan. |
| `pyproject.toml` unused `ignore_missing_imports` entries | Cleanup | Remove when appropriate; no functional impact. |
| Phase 4 viewer and visualization work | Deferred | Start only after Phase 3 closure. |

### 7.1 Test stub documentation

The intentionally empty infrastructure test stubs must be documented so that their purpose is clear.

Required actions:

- Add a `README.md` to `tests/infrastructure/i18n/`.
- Add a `# TODO(sprint-i18n)` marker to each relevant stub.
- Add equivalent documentation to `tests/infrastructure/scene/`.
- Preserve the distinction between reserved infrastructure contracts and actual integration coverage.

This is maintenance work and must not expand into a general test architecture refactoring.

---

## 8. Validation requirements

Run the complete validation suite after each milestone and before closing Sprint L.

### 8.1 Tests

```powershell
.venv\Scripts\python.exe -m pytest
```

### 8.2 Ruff

```powershell
.venv\Scripts\python.exe -m ruff check .
.venv\Scripts\python.exe -m ruff format --check .
```

### 8.3 Mypy

```powershell
.venv\Scripts\python.exe -m mypy src
```

### 8.4 Validation rules

- Do not accept new test failures.
- Do not introduce new Ruff violations.
- Do not introduce new mypy errors.
- Investigate regressions against the recorded baseline.
- Update the test count and validation date after each completed milestone.
- Do not reduce test coverage merely to obtain a passing suite.

---

## 9. Immediate action items

The next implementation sequence is:

1. Review and consolidate `widget_catalog.md` v0.3.
2. Create `sprint_l0_system_widgets.md` with the detailed contracts and acceptance criteria for the four L.0 widgets.
3. Implement and test L.0.
4. Implement L.1 — ProfessionalEditor, ModuleUISpec, settings integration, and SQLite persistence.
5. Implement L.2 — Professional navigation and configuration widgets.
6. Run complete validation and close Sprint L.
7. Review the remaining Phase 3 deliverables against `implementation_plan.md`.
8. Close Phase 3 formally only when its authoritative completion criteria are satisfied.

### 9.1 Next handoff

The next development task is:

**Create `sprint_l0_system_widgets.md` and begin L.0 implementation.**

Do not begin ProfessionalEditor implementation before the required L.0 widget contracts and components are available.

---

## 10. Definition of Done

This handoff is considered current when:

1. Completed Sprints I, J, and K are reflected accurately.
2. Sprint L is divided into L.0, L.1, and L.2.
3. L.0 contains only the four required system form widgets.
4. L.1 defines ProfessionalEditor as an Editor hosted by the central Area.
5. Professional profile persistence follows `professional.md`.
6. L.2 covers reusable navigation and configuration widgets.
7. The widget catalog remains the authoritative system-wide inventory.
8. Logs Monitor remains deferred and does not block Sprint L.
9. Phase 4 remains deferred until Phase 3 is closed.
10. Validation requirements and the current baseline are recorded.

**Authority:** `implementation_plan.md` defines phase scope and completion criteria. This document defines the immediate execution sequence and handoff.