# Next Steps

**Document type:** Action plan and development handoff  
**Status:** Active  
**Scope:** Current development priorities and execution sequence for Phase 3  
**Last updated:** 2026-11-24

---

## 1. Context

Phase 3 — Project, Home Page & Professional Module — is the current implementation phase.

Phases 0, 1, and 2 are complete. The structural Editor Architecture Refactoring and Sprints I, J, and K are also complete.

The remaining major Phase 3 deliverable is **Sprint L — Professional Module and Editor**.

Sprint L is divided into four internal stages:

- **L.0 — System Form Widgets:** Complete.
- **L.0.2 — Extended Widget Suite:** Deliveries A and B complete; C and D deferred.
- **L.1 — Professional Editor:** In progress; domain, SQLite persistence, and
  profile command/query flow complete.
- **L.2 — Professional Navigation:** Planned after L.1.

These stages are internal execution steps of Sprint L. They are not independent implementation phases.

### 1.1 Current validation baseline

**Baseline recorded on 2026-11-24 (post-L.1 profile persistence):**

- 1854 tests passing.
- 0 failed.
- 0 errors.
- 3 skipped.
- `ruff check .` clean.
- `ruff format --check .` clean (636 files).
- `mypy src` clean (318 source files).

Previous baseline:

- Post-L.1 SQLite foundation (2026-11-24): 1804 tests passing.
- Post-L.0.2 Delivery B (2026-11-23): 1795 tests passing.
- Post-L.0 (2026-11-23): 1743 tests passing.

Update the numbers and date after each completed delivery. Do not report a new baseline until the validation commands have actually been executed.

### 1.2 Architecture status

The following foundations are implemented:

- Structural Editor Architecture Refactoring, including Editor lifecycle and registry foundations.
- Workspace composition through Areas and Editors.
- `EditorStack` with lazy materialization and lifecycle management.
- `AreaLayoutRenderer` for intra-Area composition.
- Editor-level Toolbar integration.
- Active View handling and `ACTIVE_ONLY` Toolbar policy.
- `ThemeService`, `ThemeCompiler`, design tokens, and QSS styling.
- `IconProvider` and `UnicodeIconProvider`.
- `TranslationService` integration for the application shell.
- `ProjectIndex` and coordinated project deletion.
- Asynchronous flow loading.
- Project and Home Page foundations.
- System widget catalog (`../../architecture/widgets/widget_catalog.md` v0.4).
- L.0 system form widgets.
- L.0.2 Delivery A widgets.
- L.0.2 Delivery B widgets.
- Professional profile domain contracts.
- Professional profile repository/service boundary and SQLite adapter.
- Professional profile command/query flow.

The application uses Qt Widgets, modular QSS, and Python Design Tokens, as defined by ADR-0014.

### 1.3 Phase boundary

Phase 4 — Scene & Visualization — remains planned.

It must not formally begin until Phase 3 is closed according to `implementation_plan.md`.

Maintenance, bug fixes, and corrections to existing infrastructure may continue. New Phase 4 deliverables must not be absorbed into Sprint L without an explicit planning decision.

---

## 2. Planning hierarchy

The project documents have distinct responsibilities.

| Document | Responsibility |
|---|---|
| `implementation_plan.md` | Authoritative roadmap: phases, deliverables, dependencies, and completion criteria. |
| `next_steps.md` | Immediate priorities, execution sequence, current status, and development handoff. |
| `../architectural_consolidation_plan.md` | Architectural inconsistencies, duplication, legacy code, and consolidation decisions. |
| `refactoring_plan.md` | Technical procedure for Editor and Module architecture refactoring. |
| `widget_catalog.md` | Authoritative inventory of reusable system widgets, contracts, classifications, status, and dependencies. |
| `professional.md` | Professional Module domain, persistence, behavior, and implementation specification. |
| `monitor_logs.md` | Technical specification for the deferred Logs Monitor. |
| `ADR-0003` | Classification of reusable UI elements: generic widgets, Editor overlays, icon-based actions, and semantic colors. |
| `ADR-0018` | Ownership, access, schema versioning, and migration for the Professional Module SQLite database. |

`implementation_plan.md` remains authoritative. This document must not redefine phase scope or silently introduce new roadmap deliverables.

The widget catalog is the authoritative reference for system widget availability and contracts. This document defines when and how the catalog must be consulted during implementation.

---

## 3. Current focus

**Phase 3 is in progress. Sprint L is its remaining major deliverable.**

The current implementation sequence is:

1. ~~Consolidate the system widget catalog.~~ Complete.
2. ~~Specify and implement L.0 form widgets.~~ Complete.
3. ~~Implement L.0.2 Deliveries A and B.~~ Complete.
4. **Implement L.1 — Professional Editor, ModuleUISpec, settings integration, and SQLite profile persistence.**
5. Implement L.2 — Professional navigation, sections, and configuration interactions.
6. Validate and close Sprint L.
7. Review the remaining Phase 3 completion criteria.
8. Close Phase 3 formally when all authoritative criteria are satisfied.

L.0.2 Deliveries C and D remain documented as deferred work. They do not block L.1 according to the current implementation plan.

### 3.1 Sprint L stages

| Stage | Scope | Main deliverable | Status |
|---|---|---|---|
| **L.0** | System form widgets | FormField, FormCombo, FilePicker, SignaturePreview | Complete |
| **L.0.2 A** | Simple Qt-native widgets | DateField, FormRow, DragHandle, EyeToggleButton, VisibilityToggle, SearchField, ProgressBar | Complete |
| **L.0.2 B** | Sections, lists, and navigation | CollapsibleSection, DragList, IconSidebar | Complete |
| **L.0.2 C** | Custom-painted and advanced widgets | TimelineSlider, ColorPicker, Histogram | Deferred |
| **L.0.2 D** | Debug harness consolidation and validation | Consolidated visual debug harness and catalog closure | Deferred |
| **L.1** | Professional Editor | Editor registration, profile interface, ModuleUISpec, settings, SQLite persistence | In progress — profile persistence complete |
| **L.2** | Professional Navigation | Sections, visibility controls, drag-and-drop, persisted presentation state | Planned |

### 3.2 Architectural principles for Sprint L

The following constraints apply throughout implementation:

- `ProfessionalEditor` is a concrete Editor, not a Module-specific tab system.
- It is hosted by the central Area.
- The Professional Module contributes declarative UI configuration through `ModuleUISpec`.
- Module definitions must not instantiate concrete Editors.
- Reusable system widgets belong to `../../../src/cranioz/ui/widgets`.
- The Professional Editor consumes system widgets; it does not own their implementations.
- Professional-specific compositions remain inside the Professional Editor unless a broader reuse case is demonstrated.
- Use native Qt Widgets when they satisfy the required behavior.
- Do not introduce abstractions without a demonstrated need.
- Profile persistence must follow `professional.md`.
- `persistent_state()` and `restore_state()` are for visual Editor state, not professional profile data.
- Theme and translation integration must follow the existing global infrastructure.
- New system widgets that require icons must accept an injected `IconProvider` Protocol and fall back to `text_glyph()` when `icon()` returns a null `QIcon`.
- Auxiliary enums (e.g. `FilePickerMode`) live in the same file as the widget that consumes them, not in separate files under `ui/widgets/`.
- Package `__init__.py` changes must preserve all previously exported symbols.
- Classification of reusable UI elements follows ADR-0003:
  - Generic composite widgets → `../../../src/cranioz/ui/widgets`.
  - Editor-internal overlays → `../../../src/cranioz/ui/editors/overlays`.
  - Icon-based actions → Tools in `../../../src/cranioz/ui/tools/builtin`.
- A component that depends on a specific Editor's content area, hit-testing, viewport state, or `EditorContext` is an overlay, not a generic widget.
- Clinical rulers, gizmos, and measurement tools are overlays. They are scheduled with their first consuming Editor, not speculatively.

---

## 4. Completed work

### 4.1 Phase 0 — Foundation & Boot

Complete.

### 4.2 Phase 1 — Contracts, Core Domain & i18n

Complete.

### 4.3 Phase 2 — Workspace Engine & Icons

Complete.

### 4.4 Phase 3 — Completed deliverables

| Deliverable | Status | Reference |
|---|---|---|
| Structural Editor Architecture Refactoring | Complete | ADR-0015 |
| ProjectIndex (Sprint I) | Complete | ADR-0016 |
| Coordinated project deletion (Sprint J) | Complete | Project subsystem |
| Asynchronous loading (Sprint K) | Complete | Flow loading and TaskManager integration |
| Sprint L.0 — System form widgets | Complete | `widget_catalog.md` |
| Sprint L.0.2 Delivery A | Complete | §5.2 |
| Sprint L.0.2 Delivery B | Complete | §5.2 |

Completed work must not be reopened during Sprint L unless a concrete regression or missing contract is identified.

---

## 5. Sprint L — Professional Editor

### 5.1 L.0 — System Form Widgets

**Status:** Complete (2026-11-23)

**Purpose:** Implement the four system form widgets required by the Professional Editor.

#### Delivered

| Component | File | Tests |
|---|---|---:|
| `FormField` | `../../../src/cranioz/ui/widgets/forms/form_field.py` | 8 |
| `FormCombo` | `../../../src/cranioz/ui/widgets/forms/form_combo.py` | 7 |
| `FilePicker` | `../../../src/cranioz/ui/widgets/forms/file_picker.py` | 8 |
| `SignaturePreview` | `../../../src/cranioz/ui/widgets/forms/signature_preview.py` | 7 |

**Package:** `../../../src/cranioz/ui/widgets/forms`  
**Tests:** `tests/unit/ui/widgets/forms/`  
**Public API:** `cranioz.ui.widgets.forms.__all__`  
**Visual debug harness:** `scripts/debug/ui/widgets/forms/debug_forms.py`

#### Validation

- 30 widget tests passing.
- 85 architecture tests passing.
- `ruff check` clean.
- `ruff format --check` clean.
- `mypy src` clean at the time of delivery.

#### Known deferrals

- `SignaturePreview` uses integer RGB constants instead of design tokens. Migrate when it supports an optional `ThemeService`.
- `FilePicker` browse button uses a text glyph instead of an icon from `IconProvider`. Migrate in L.2.
- pt-BR translations for static widget strings remain pending L.2.

#### Completion criteria

- [x] Four widgets implemented in the system UI package.
- [x] Public APIs and signals documented.
- [x] Unit tests passing.
- [x] Theme and translation behavior validated.
- [x] No dependency on Professional-specific code.
- [x] Widget catalog statuses updated.
- [x] Visual debug harness validated in Dark and Light themes.

---

### 5.2 L.0.2 — Extended Widget Suite

**Status:** Deliveries A and B complete; Deliveries C and D deferred.

**Purpose:** Implement reusable widgets identified by the Professional Module prototype and the shared widgets prototype, allowing L.1 and L.2 to compose the interface without introducing unnecessary widget refactoring.

#### Widget catalog and implementation rule

Before implementing, modifying, or replacing a reusable UI component:

1. Consult `../../architecture/widgets/widget_catalog.md`.
2. Check whether an existing widget already provides the required behavior.
3. Reuse the existing widget when its contract satisfies the requirement.
4. Compose existing widgets when the requirement is specific to the Professional Editor.
5. Create a new system widget only when a broader reuse case is demonstrated.
6. Update the catalog when a widget's implementation status, public contract, dependencies, or classification changes.

The catalog is the authoritative system-wide inventory. This document records the Sprint L implementation sequence and must not duplicate the complete widget specifications.

#### Architectural classification

Follow ADR-0003:

| Classification | Location | Intended use |
|---|---|---|
| System widgets | `../../../src/cranioz/ui/widgets` | Reusable components independent of a specific Editor |
| Editor overlays | `../../../src/cranioz/ui/editors/overlays` | Components bound to an Editor's viewport or interaction context |
| Tools | `../../../src/cranioz/ui/tools/builtin` | User actions and icon-based commands |
| Professional compositions | Professional Editor implementation | Higher-level combinations specific to this consumer |

Do not place Editor overlays or Professional-specific compositions in the generic system widget package.

#### Implemented package structure

```text
src/cranioz/ui/widgets/
├── forms/
│   ├── form_field.py
│   ├── form_combo.py
│   ├── file_picker.py
│   ├── signature_preview.py
│   ├── date_field.py
│   └── form_row.py
├── sections/
│   ├── collapsible_section.py
│   └── drag_list.py
├── navigation/
│   ├── icon_sidebar.py
│   ├── eye_toggle_button.py
│   └── visibility_toggle.py
├── lists/
│   └── drag_handle.py
├── advanced/
│   ├── search_field.py
│   └── progress_bar.py
└── horizontal/
    └── timeline_slider.py  (deferred)
```

The catalog remains authoritative for the complete inventory and current file locations.

#### Delivery A — Simple Qt-native widgets

**Status:** Complete (2026-11-23)

| Widget | File | Tests |
|---|---|---:|
| DateField | `forms/date_field.py` | 5 |
| FormRow | `forms/form_row.py` | 3 |
| DragHandle | `lists/drag_handle.py` | 5 |
| EyeToggleButton | `navigation/eye_toggle_button.py` | 5 |
| VisibilityToggle | `navigation/visibility_toggle.py` | 3 |
| SearchField | `advanced/search_field.py` | 6 |
| ProgressBar | `advanced/progress_bar.py` | 3 |
| **Total** | | **30** |

Supporting changes:

- Added four Unicode icon names: `eye-open`, `eye-closed`, `clear`, and `drag`.
- Updated the icon catalog count from 71 to 75.
- Added a `NullIconProvider` test fixture to validate the text-glyph fallback.
- Extended the visual debug harness to render L.0 and Delivery A widgets in Dark and Light themes.
- Preserved existing public exports in the forms package.

#### Delivery A acceptance criteria

- [x] Seven widgets implemented under `../../../src/cranioz/ui/widgets`.
- [x] Unit tests cover default state, public properties, signals, disabled state, and `accessibleName`.
- [x] Ruff, formatting, and mypy validation clean.
- [x] Visual debug harness covers all seven widgets in Dark and Light themes.
- [x] No Professional-specific imports.
- [x] `widget_catalog.md` statuses updated.

#### Delivery B — Sections and lists

**Status:** Complete (2026-11-23)

Depends on Delivery A (`DragHandle`).

| Widget | Classification | Contract summary |
|---|---|---|
| `CollapsibleSection` | Composite Widget | Expandable section with header, body, optional drag handle, and keyboard interaction |
| `DragList` | Custom Widget | Vertical container supporting drag-and-drop reordering through stable string keys |
| `IconSidebar` | Composite Widget | Vertical icon navigation with selection state and accessibility support |

#### Delivery B acceptance criteria

- [x] Three widgets implemented.
- [x] `CollapsibleSection` tests cover expand/collapse, keyboard interaction, body visibility, and drag-handle visibility.
- [x] `DragList` tests cover API reordering, drop-based reordering, stable-key payloads, and membership signals.
- [x] `IconSidebar` tests cover item registration, selection, icon fallback, and accessibility.
- [x] Visual debug harness includes the section-list composition using real widgets.
- [x] `widget_catalog.md` statuses updated.

Implemented files:

- `../../../src/cranioz/ui/widgets/sections/collapsible_section.py`
- `../../../src/cranioz/ui/widgets/sections/drag_list.py`
- `../../../src/cranioz/ui/widgets/navigation/icon_sidebar.py`
- `../../../tests/unit/ui/widgets/sections`
- `../../../tests/unit/ui/widgets/navigation/test_icon_sidebar.py`

#### Delivery C — Custom-painted and advanced widgets

**Status:** Deferred. Does not block L.1.

| Widget | Classification | Contract summary |
|---|---|---|
| `TimelineSlider` | Custom Widget | Horizontal timeline with play/pause/step controls, frame range, current frame, and frame-related signals |
| `ColorPicker` | Composite Widget | QColorDialog wrapper with inline color swatch and color-change signal |
| `Histogram` | Custom Widget | Data-distribution visualization with bins, optional log scale, and bin-click interaction |

Acceptance criteria when this delivery is rescheduled:

- [ ] Three widgets implemented.
- [ ] `TimelineSlider` tests cover paint-event smoke, public properties, and signals.
- [ ] `Histogram` tests cover data assignment, clearing, and bin-click emission.
- [ ] `ColorPicker` tests cover property and signal behavior without opening a real dialog.
- [ ] Visual debug harness reproduces the corresponding prototype screens.
- [ ] Dark and Light themes validated.
- [ ] `widget_catalog.md` updated.

The clinical `RulerOverlay` is not part of Delivery C. It is an Editor overlay under ADR-0003.

#### Delivery D — Debug harness consolidation and closure

**Status:** Deferred with Delivery C.

Planned scope when rescheduled:

- [ ] Extend `../../../scripts/debug/ui/widgets/forms/debug_forms.py` into a multi-tab debug window.
- [ ] Reproduce the Professional profile, document templates, schedule, procedures, budgets, and configuration screens using the actual widgets.
- [ ] Include the shared widgets prototype components.
- [ ] Validate Dark and Light themes.
- [ ] Validate HiDPI at `QT_SCALE_FACTOR=1.5` and `2`.
- [ ] Run the full validation suite.
- [ ] Update `widget_catalog.md` statuses and milestone information.
- [ ] Record a new validation baseline.

Delivery D must not be treated as a prerequisite for L.1. Its rescheduling requires an explicit planning decision.

#### Excluded from L.0.2

| Component | Reason |
|---|---|
| `ActionButtonRow` | Trivial composition; build directly in the consuming Editor. |
| `SectionItemRow` | Unified into `CollapsibleSection(draggable=True)`. |
| `ObjectMovementControl` | Backlog; interaction specification required. |
| `DualRangeSlider` | Backlog; tied to future tomography workflows. |
| `RulerOverlay` | Editor overlay, not a generic system widget. |

---

### 5.3 L.1 — Professional Editor

**Status:** In progress. Domain contracts, SQLite persistence, and the profile
command/query flow are complete; settings and Editor work remain.

**Purpose:** Deliver the first functional Professional Editor using the existing system widget infrastructure and the domain specification in `professional.md`.

#### Scope

- Implement `ProfessionalEditor`.
- Register it in `EditorRegistry`.
- Provide the Professional Module's `ModuleUISpec`.
- Host the Editor in the central Area.
- Implement the initial professional profile interface (Tela 2 of the prototype).
- Integrate the `professional.*` settings namespace.
- Implement SQLite persistence according to `professional.md`.
- Add Editor contract and integration tests.

#### Widget catalog consultation

Before implementing the interface:

- Review `../../architecture/widgets/widget_catalog.md`.
- Identify existing widgets suitable for the profile screen.
- Prefer existing system widgets and native Qt components.
- Compose Professional-specific components inside the Professional Editor.
- Do not create generic widgets merely to reproduce a single screen.
- Update the catalog only if a system widget is added, modified, or reclassified.

The Professional Editor should use the existing system form widgets, including `FormField`, `FormCombo`, `FilePicker`, `SignaturePreview`, `DateField`, and `FormRow`, wherever their contracts satisfy the required behavior.

#### Architectural constraints

- `ProfessionalEditor` is a concrete Editor implementation.
- The Professional Module is declarative and contributes the UI specification required to expose the Editor.
- The Module must not instantiate the Editor directly.
- The Editor must follow the existing lifecycle and context contracts.
- Do not create a separate Module-specific tab system.
- Do not duplicate existing system widgets inside the Professional Module.

#### Persistence

Professional profile persistence must use the SQLite database defined in `professional.md`:

```text
~/.cranioz/professional/professional.db
```

Do not introduce a temporary JSON persistence layer.

Do not use Editor visual-state persistence to store profile data.

The initial implementation must remain limited to the profile fields and operations required by `professional.md`.

The persistence work implemented on 2026-11-24 provides `professional_root`,
database lifecycle, schema versioning, migration backup/rollback, the initial
profile/registration schema, an application repository port, an in-memory
reference repository, `ProfessionalService`, `ProfessionalQueries`,
`UpdateProfessionalProfileCommand`, and the SQLite profile adapter. Profile
saves atomically replace the profile and its registrations; reads reconstruct
and validate the domain aggregate.

#### Settings integration

- Use the `professional.*` namespace for appropriate presentation and application settings.
- Do not duplicate profile data in settings when it belongs in the Professional database.
- Keep visual Editor state separate from persistent professional domain data.

#### Completion criteria

- [ ] `ProfessionalEditor` registered and materialized through the established Editor architecture.
- [ ] Professional Module exposes the correct `ModuleUISpec`.
- [ ] Editor hosted in the central Area.
- [ ] Initial profile interface functional (Tela 2).
- [ ] Existing system widgets reused where appropriate.
- [ ] No unnecessary Professional-specific widgets added to the generic system widget package.
- [x] SQLite persistence integrated according to `professional.md`.
- [ ] Settings namespace integrated.
- [x] Profile data survives application restarts.
- [ ] Editor lifecycle and integration tests passing.

---

### 5.4 L.2 — Professional Navigation

**Status:** Planned.

**Purpose:** Implement the internal navigation, sections, and configuration interactions required by the Professional Editor.

#### Scope

- Wire `CollapsibleSection`, `DragList`, `IconSidebar`, `EyeToggleButton`, and `VisibilityToggle` into the Professional Editor where appropriate.
- Implement the remaining prototype screens (Telas 3–7).
- Implement navigation between sections.
- Persist navigation order and visibility through the appropriate application settings mechanism.
- Implement pt-BR translations for widget static strings.
- Migrate `SignaturePreview` empty-state colors to design tokens once it supports an optional `ThemeService`.
- Migrate the `FilePicker` browse button to `IconProvider`.

#### Widget reuse

Consult `widget_catalog.md` before implementing any additional component.

Professional-specific compositions may include:

- `ProfessionalSidebar`
- `ProfessionalSectionTree`
- `ProfessionalConfigPanel`

These are consumer-specific compositions and should remain inside the Professional Editor implementation unless a separate system-wide reuse case emerges.

Do not move a composition into `../../../src/cranioz/ui/widgets` solely because it contains multiple widgets.

#### Editor overlays

The first `RulerOverlay` implementation must be scheduled with its first consuming Editor.

Expected location:

```text
src/cranioz/ui/editors/overlays/rulers/ruler_overlay.py
```

It is not a system widget and must follow ADR-0003.

#### Completion criteria

- [ ] Prototype screens (Telas 2–7) functional.
- [ ] Navigation between sections works.
- [ ] Expand/collapse, visibility, and drag ordering work.
- [ ] Ordering and visibility preferences are persisted and restored.
- [ ] Keyboard and accessibility behavior validated.
- [ ] Theme and language changes propagate correctly.
- [ ] Existing widgets reused instead of duplicated.
- [ ] Any new reusable widget has an updated catalog entry and tests.

---

### 5.5 Sprint L Integration and Closure

After L.1 and L.2:

- [ ] Validate `ProfessionalEditor` through the actual Workspace and Editor lifecycle.
- [ ] Validate `ModuleUISpec` registration and materialization.
- [ ] Validate profile persistence across application restarts.
- [ ] Validate settings restoration.
- [ ] Validate theme and language changes.
- [ ] Validate navigation state persistence.
- [ ] Run the full test suite and static analysis.
- [ ] Update `widget_catalog.md` to reflect implemented components.
- [ ] Update `implementation_plan.md` if Sprint L or Phase 3 completion status changes.
- [ ] Record remaining limitations explicitly.

Sprint L must not absorb unrelated Phase 4 or general UI backlog items.

---

## 6. Deferred work

### 6.1 L.0.2 Deliveries C and D

Deliveries C and D remain deferred.

They do not block L.1 or the initial Professional Editor implementation.

Their future implementation must be explicitly rescheduled and must not be treated as an implicit prerequisite.

### 6.2 Logs Monitor

The Logs Monitor remains a dedicated deferred implementation task.

Its specification is maintained in `monitor_logs.md`.

It is not a Phase 3 deliverable and does not block Sprint L.

It may be scheduled as a separate sprint after the completed Sprints I–K.

### 6.3 Phase 4 — Scene & Visualization

Phase 4 remains deferred until Phase 3 is formally closed.

Its pending deliverables include:

- Unified Import Dialog.
- `RenderingAdapter`.
- `ViewerLayoutManager` and dynamic viewer layouts.
- 2D and 3D visualization tools.
- Viewer status indicators.
- Clinical transfer functions.
- Further Editor workflows and visualization integration.

The widget catalog may contain components intended for these future workflows. Their presence in the catalog does not authorize implementation during Sprint L.

### 6.4 Widget and overlay backlog

The following components remain outside the current Sprint L scope unless a concrete requirement is approved.

**Future system widgets:**

- `ObjectMovementControl`.
- `DualRangeSlider`.
- `BlurToggle`.
- `StartButton`, `ContinueButton`, `CompleteButton`, `PreviousButton`, `NextButton`, `RemoveButton`, and `SettingsButton`, implemented as styled `QPushButton` variants only if a concrete consumer requires them.
- Additional tomography and cephalometry controls.

**Future Editor overlays:**

- `RulerOverlay` — clinical measurement scale for MPR, Osteotomy, or 2D Editor.
- `TranslationGizmo` and `RotationGizmo` — 3D manipulation overlays for Phase 4.

Their implementation milestones must follow the consuming Editor or subsystem dependencies documented in `widget_catalog.md` and ADR-0003.

---

## 7. Known issues and deferred items

| Item | Status | Action |
|---|---|---|
| Logs Monitor | Planned | Schedule separately; specification already exists. |
| Test stub documentation | Pending | Add README and TODO markers to identified infrastructure test stubs. |
| `correlation_id` propagation | Deferred | Revisit according to the implementation plan. |
| `event_subscription` contract test | Deferred | Add dedicated coverage when the corresponding integration is implemented. |
| Remaining hardcoded appearance literals | Tracked debt | Continue using the existing architecture guard and debt list. |
| VTK `GetData()` deprecation | Deferred | Migrate according to the VTK 10 compatibility plan. |
| Unused `ignore_missing_imports` entries in `../../../pyproject.toml` | Cleanup | Remove when appropriate; no functional impact. |
| Phase 4 viewer and visualization work | Deferred | Start only after Phase 3 closure. |
| `SignaturePreview` empty-state colors | L.2 deferral | Migrate to design tokens once optional `ThemeService` is supported. |
| `FilePicker` browse button glyph | L.2 deferral | Migrate to `IconProvider`. |
| pt-BR translations for L.0/L.0.2 widgets | L.2 deferral | Add catalog entries for static strings. |
| L.0.2 Delivery A/B catalog statuses | Resolved | Entries marked Existing with milestone L.0.2. |
| Ruler classification | Resolved | Reclassified as Editor overlay per ADR-0003; removed from L.0.2 Delivery C. |
| ADR-0003 status | Proposed | Ratify when the first overlay is implemented or earlier if required. |
| L.0.2 Deliveries C/D | Deferred | Do not block L.1; reschedule explicitly. |

### 7.1 Test stub documentation

The intentionally empty infrastructure test stubs must be documented so their purpose is clear.

Required actions:

- Add a `../../../README.md` to `tests/infrastructure/i18n/`.
- Add a `# TODO(sprint-i18n)` marker to each relevant stub.
- Add equivalent documentation to `../../../tests/infrastructure/scene`.
- Preserve the distinction between reserved infrastructure contracts and actual integration coverage.

This is maintenance work. It must not expand into a general test architecture refactoring.

---

## 8. Validation requirements

Run the complete validation suite after each implementation delivery and before closing Sprint L.

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
- Update the test count and validation date after each completed delivery.
- Do not reduce test coverage merely to obtain a passing suite.
- Validate new widgets independently and through their actual consumer.
- Validate theme, translation, and accessibility behavior when applicable.

---

## 9. Immediate action items

The current implementation sequence is:

- [x] Review and consolidate `widget_catalog.md` (v0.4).
- [x] Document and implement L.0 form widget contracts.
- [x] Implement and test L.0.
- [x] Implement L.0.2 Delivery A.
- [x] Implement L.0.2 Delivery B.
- [x] Establish the Professional SQLite persistence foundation (ADR-0018).
- [x] Implement the Professional profile domain contracts.
- [x] Implement the Professional repository/service and command/query flow.
- [ ] Implement L.1 — `ProfessionalEditor`, `ModuleUISpec`, settings integration, and SQLite persistence.
- [ ] Implement L.2 — Professional navigation, sections, and configuration interactions.
- [ ] Run complete validation and close Sprint L.
- [ ] Review remaining Phase 3 deliverables against `implementation_plan.md`.
- [ ] Close Phase 3 formally only when its authoritative completion criteria are satisfied.

L.0.2 Deliveries C and D remain deferred. They are not part of the immediate implementation sequence.

### 9.1 Next handoff

**Next development task:**

Continue **L.1** with `ProfessionalEditor`, its central-Area materialization,
the Professional Module's `ModuleUISpec`, and `professional.*` settings
integration. Reuse the completed profile repository/service and dispatch profile
changes through `UpdateProfessionalProfileCommand`.

Before implementation, review these references:

**Primary specifications**

- `../../architecture/modules/professional/professional.md` — domain, persistence, behavior, and implementation specification.
- `../../architecture/widgets/widget_catalog.md` — authoritative system widget inventory and contracts.
- `implementation_plan.md` — Phase 3 scope and completion criteria.
- ADR-0003 — classification of widgets, overlays, and tools.

**Editor and Module architecture**

- `EditorRegistry` and existing Editor implementations.
- `ModuleUISpec` contracts and registration patterns.
- Existing Editor lifecycle and context contracts.
- Central Area composition and Workspace integration.

**Widget implementations**

- `../../../src/cranioz/ui/widgets/forms` — L.0 form widget implementations.
- `../../../src/cranioz/ui/widgets/sections` — `CollapsibleSection` and `DragList`.
- `../../../src/cranioz/ui/widgets/navigation` — navigation widget implementations.
- `../../../tests/unit/ui/widgets` — widget testing patterns.
- `../../../scripts/debug/ui/widgets/forms/debug_forms.py` — visual debug harness.

**Theme and icon infrastructure**

- `../../../src/cranioz/ui/theme/tokens.py`
- `../../../src/cranioz/ui/theme/compiler.py`
- `../../../src/cranioz/ui/theme/service.py`
- `../../../src/cranioz/ui/icons/provider.py`
- `../../../src/cranioz/ui/icons/unicode.py`

**Implementation instructions**

1. Read `professional.md` before defining profile models or persistence.
2. Inspect `widget_catalog.md` before implementing UI components.
3. Reuse existing widgets whenever their contracts satisfy the requirement.
4. Keep Professional-specific compositions inside the Professional Editor.
5. Implement the Editor through the established registry and lifecycle.
6. Keep profile persistence in SQLite and visual state in the Editor state mechanism.
7. Add unit, contract, and integration tests.
8. Run the complete validation suite and update this document with the actual results.

Do not begin L.0.2 Delivery C or D as a prerequisite for L.1.

---

## 10. Definition of Done

This handoff is considered current when:

- Completed Sprints I, J, and K are accurately reflected.
- Sprint L is divided into L.0, L.0.2, L.1, and L.2.
- L.0 is marked complete with its delivery table and known deferrals.
- L.0.2 Deliveries A and B are marked complete with their implementation details and acceptance criteria.
- L.0.2 Deliveries C and D are explicitly marked deferred.
- The current implementation focus is L.1, consistent with `implementation_plan.md`.
- The widget catalog is the authoritative system-wide inventory.
- Widget catalog consultation and reuse are explicit implementation requirements.
- Professional-specific compositions are distinguished from reusable system widgets.
- `ProfessionalEditor` is defined as an Editor hosted by the central Area.
- The Professional Module exposes declarative UI through `ModuleUISpec`.
- Professional profile persistence follows `professional.md`.
- L.2 covers navigation, sections, translations, and theme-token migration.
- Ruler is classified as an Editor overlay and excluded from the generic widget suite.
- Logs Monitor remains deferred and does not block Sprint L.
- Phase 4 remains deferred until Phase 3 is closed.
- Validation requirements and the latest verified baseline are recorded.
- The next handoff identifies L.1 and its required references.

**Authority:** `implementation_plan.md` defines phase scope and completion criteria. ADR-0003 defines the classification of reusable UI elements. `widget_catalog.md` defines the system widget inventory and contracts. This document defines the immediate execution sequence and development handoff.
