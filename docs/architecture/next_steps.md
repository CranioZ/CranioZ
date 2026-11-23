# Next Steps

**Document type:** Action plan and development handoff  
**Status:** Active  
**Scope:** Current development priorities and execution sequence for Phase 3  
**Last updated:** 2026-11-23 (post-L.0.2 Delivery A)

---

## 1. Context

Phase 3 — Project, Home Page & Professional Module — is the current implementation phase.

Phases 0, 1, and 2 are complete. The structural Editor Architecture Refactoring and Sprints I, J, and K have also been completed. The remaining Phase 3 deliverable is Sprint L — Professional Editor.

Sprint L is now divided into two macro-blocks:

- **L.0** — System form widgets required by the Professional Editor. **Complete (2026-11-23).**
- **L.0.2** — Extended widget suite, covering every atom required by the Professional Module prototype. **In progress — Delivery A complete (2026-11-23).**
- **L.1** — Professional Editor proper (registration, profile UI, ModuleUISpec, settings, SQLite persistence).
- **L.2** — Professional navigation, sections and configuration interactions.

L.0.2 was promoted after the UI prototype review (`Prototipagem_UI_19_Profissional.pdf` and `Prototipagem_UI_19_Widgets.pdf`) showed that the Professional Editor requires a broader set of reusable widgets than the four originally scoped for L.0. Implementing them now avoids refactoring the Editor in L.2.

The widget inventory is maintained separately in:

- `docs/architecture/widgets/widget_catalog.md` — system-wide widget catalog, classifications, implementation status, dependencies, and architectural guidelines.
- `docs/architecture/widgets/sprint_l0_system_widgets.md` — implementation specification for the four L.0 widgets. **Delivered.**

### 1.1 Current validation baseline

**Baseline recorded on 2026-11-23 (post-L.0.2 Delivery A):**

- 1773 tests passing.
- 0 failed.
- 0 errors.
- 2 skipped.
- `ruff check .` clean.
- `ruff format --check .` clean (602 files).
- `mypy src` clean (299 source files).

Previous baselines:

- Post-L.0 (2026-11-23): 1743 passed, 575 files formatted, 289 source files.
- Pre-L.0 (reference): recorded in §1.1 of the previous revision.

Update the numbers after each delivery.

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
- System widget catalog (`widget_catalog.md` v0.4).
- L.0 system form widgets (FormField, FormCombo, FilePicker, SignaturePreview).
- L.0.2 Delivery A widgets (DateField, FormRow, DragHandle, EyeToggleButton, VisibilityToggle, SearchField, ProgressBar).

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

Recommended execution sequence:

1. ~~Consolidate the system widget catalog.~~ ✅
2. ~~Specify and implement the L.0 form widgets.~~ ✅ (2026-11-23)
3. **Implement L.0.2 — Extended widget suite** (14 widgets, divided into 4 deliveries). Delivery A complete; B, C, D pending.
4. Implement and integrate the Professional Editor and its profile persistence (L.1).
5. Implement the Professional Editor's internal navigation and configuration interactions (L.2).
6. Validate and close Sprint L.
7. Review the remaining Phase 3 criteria and close Phase 3 formally.

### 3.1 Sprint L — Professional Editor

Sprint L is divided into the following execution stages.

| Stage | Scope | Main deliverable | Status |
|---|---|---|---|
| **L.0** | System form widgets | FormField, FormCombo, FilePicker, SignaturePreview. | Complete (2026-11-23) |
| **L.0.2** | Extended widget suite | 14 additional atoms required by the Professional Module prototype. | In progress — Delivery A complete (2026-11-23) |
| **L.1** | Professional Editor | Editor registration, profile interface, ModuleUISpec, settings integration, SQLite persistence. | Planned |
| **L.2** | Professional Navigation | Reusable navigation, sections, visibility controls, drag-and-drop, persisted presentation state. | Planned |

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
- New system widgets that require icons must accept an injected `IconProvider` (Protocol) and fall back to `text_glyph()` when `icon()` returns a null `QIcon`.
- Auxiliary enums (e.g. `FilePickerMode`) live in the same file as the widget that consumes them, never in separate files under `ui/widgets/`.
- Package `__init__.py` must preserve all previously exported symbols when new ones are added.

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
| Coordinated project deletion (Sprint J) | Complete | `ProjectManager` / project subsystem |
| Asynchronous loading (Sprint K) | Complete | Flow loading and TaskManager integration |
| Sprint L.0 — System form widgets | Complete (2026-11-23) | `sprint_l0_system_widgets.md` |
| Sprint L.0.2 Delivery A — Simple Qt-native widgets | Complete (2026-11-23) | §5.2 of this document |

The completed work must not be reopened as part of Sprint L unless a concrete regression or missing contract is identified.

---

## 5. Sprint L — Professional Editor

### 5.1 L.0 — System Widgets

**Status:** Complete (2026-11-23)  
**Purpose:** Implement the four system form widgets required by the Professional Editor.

#### Delivered

| Component | File | Tests |
|---|---|---|
| `FormField` | `src/cranioz/ui/widgets/forms/form_field.py` | 8 |
| `FormCombo` | `src/cranioz/ui/widgets/forms/form_combo.py` | 7 |
| `FilePicker` | `src/cranioz/ui/widgets/forms/file_picker.py` | 8 |
| `SignaturePreview` | `src/cranioz/ui/widgets/forms/signature_preview.py` | 7 |

Package: `src/cranioz/ui/widgets/forms/`  
Tests: `tests/unit/ui/widgets/forms/`  
Public API: `cranioz.ui.widgets.forms.__all__`  
Visual debug harness: `scripts/debug/ui/widgets/forms/debug_forms.py`

#### Validation

- 30 widget tests passing.
- 85 architecture tests passing.
- `ruff check` clean.
- `ruff format --check` clean.
- `mypy src` clean (289 files).

#### Known deferrals

- `SignaturePreview` uses integer RGB constants (`QColor(160,160,160)`) instead of
  design tokens. Tracked with `TODO(L.2)` — migrate when `SignaturePreview`
  accepts an optional `ThemeService` (see `widget_catalog.md` §8.4).
- `FilePicker` browse button uses a text glyph `"…"` instead of an icon from
  `IconProvider`. Migrate in L.2.
- pt-BR translations for `"Browse…"`, `"No signature"`, `"Text field"`,
  `"Selection field"` pending L.2.

#### Completion criteria

- [x] Four widgets implemented in the system UI package.
- [x] Public APIs and signals documented.
- [x] Unit tests passing.
- [x] Theme and translation behavior validated.
- [x] No dependency on Professional-specific code.
- [x] Widget catalog statuses updated.
- [x] Visual debug harness validated (Dark + Light themes).

---

### 5.2 L.0.2 — Extended Widget Suite

**Status:** In progress  
**Purpose:** Implement every reusable widget required by the Professional Module prototype (`Prototipagem_UI_19_Profissional.pdf`) and the shared widgets catalog (`Prototipagem_UI_19_Widgets.pdf`), so that L.1 (`ProfessionalEditor`) can be built by composition without refactoring later.

#### Approach

Four delivery batches, ordered by dependency. Each batch ships with code, unit tests, and visual debug coverage before starting the next.

#### Package layout (target)

```text
src/cranioz/ui/widgets/
├── forms/
│   ├── form_field.py         ✅ L.0
│   ├── form_combo.py         ✅ L.0
│   ├── file_picker.py        ✅ L.0
│   ├── signature_preview.py  ✅ L.0
│   ├── date_field.py         ✅ L.0.2 A
│   └── form_row.py           ✅ L.0.2 A
├── sections/
│   ├── __init__.py           🆕
│   ├── collapsible_section.py 🆕 L.0.2
│   └── drag_list.py          🆕 L.0.2
├── navigation/
│   ├── __init__.py           ✅ L.0.2 A
│   ├── icon_sidebar.py       🆕 L.0.2
│   ├── eye_toggle_button.py  ✅ L.0.2 A
│   └── visibility_toggle.py  ✅ L.0.2 A
├── lists/
│   ├── __init__.py           ✅ L.0.2 A
│   └── drag_handle.py        ✅ L.0.2 A
├── horizontal/
│   ├── __init__.py           🆕
│   ├── timeline_slider.py    🆕 L.0.2
│   └── ruler.py              🆕 L.0.2
└── advanced/
    ├── __init__.py           ✅ L.0.2 A
    ├── search_field.py       ✅ L.0.2 A
    ├── color_picker.py       🆕 L.0.2
    ├── histogram.py          🆕 L.0.2
    └── progress_bar.py       ✅ L.0.2 A
```

Explicitly excluded from L.0.2

Component	Reason
ActionButtonRow	Trivial composition (QHBoxLayout + QPushButton); build directly in the Editor.
SectionItemRow	Unified into CollapsibleSection(draggable=True) — one widget, one API.
ObjectMovementControl	Backlog; requires interaction specification.
DualRangeSlider	Backlog; tied to future tomography workflows.
Decisions

DragList — Custom widget, not QListView, because list items are complex CollapsibleSection widgets (header + body + drag handle), not plain text rows.

EyeToggleButton — QToolButton with setCheckable(True) and eye-open/eye-closed icon swap on toggle.

IconSidebar — Generic (no Professional-specific references). The ProfessionalEditor registers its 6 icons in L.1.

CollapsibleSection — Single widget with draggable: bool = False; shows DragHandle when True.

Delivery A — Simple Qt-native atoms
Status: Complete (2026-11-23)

Widget	File	Tests
DateField	src/cranioz/ui/widgets/forms/date_field.py	5
FormRow	src/cranioz/ui/widgets/forms/form_row.py	3
DragHandle	src/cranioz/ui/widgets/lists/drag_handle.py	5
EyeToggleButton	src/cranioz/ui/widgets/navigation/eye_toggle_button.py	5
VisibilityToggle	src/cranioz/ui/widgets/navigation/visibility_toggle.py	3
SearchField	src/cranioz/ui/widgets/advanced/search_field.py	6
ProgressBar	src/cranioz/ui/widgets/advanced/progress_bar.py	3
Total		30
Supporting changes:

src/cranioz/ui/icons/unicode.py — 4 names added (eye-open, eye-closed, clear, drag); catalog count 71 → 75.

tests/unit/ui/icons/test_icon_catalog.py — count updated 71 → 75; required-names set extended.

tests/unit/ui/widgets/conftest.py — NullIconProvider fixture (forces text_glyph() fallback path).

scripts/debug/ui/widgets/forms/debug_forms.py — extended to render L.0 + L.0.2 A widgets, Dark + Light.

src/cranioz/ui/widgets/forms/__init__.py — DateField, FormRow added; FilePickerMode preserved from L.0.

Acceptance criteria:

☑ 7 widgets implemented under src/cranioz/ui/widgets/.
☑ Unit tests under tests/unit/ui/widgets/ covering default state, public properties, signals, disabled state, accessibleName.
☑ ruff, ruff format, mypy clean.
☑ Extended scripts/debug/ui/widgets/forms/debug_forms.py shows all 7 widgets in Dark and Light.
☑ No Professional-specific imports.
☑ widget_catalog.md §5 statuses updated (Planned → Existing, milestone L.0.2) — pending catalog edit (tracked as a documentation follow-up in §9).
Delivery B — Sections and lists
Depends on: Delivery A (DragHandle). Ready to start (2026-11-23).

Widget	Classification	Base	Contract summary
CollapsibleSection	Composite Widget	QFrame + header + body	Header with expand/collapse toggle. Optional left DragHandle when draggable=True. Properties: title, expanded, draggable, header_widget, body_widget. Signals: expanded_changed(bool), drag_started. Keyboard: Space/Enter toggles.
DragList	Custom Widget	QWidget hosting CollapsibleSection children	Vertical container with drag-and-drop reordering of child sections. Methods: add_section, remove_section, move_section. Signal: order_changed(list[int]). Uses Qt drag events; no external deps.
IconSidebar	Composite Widget	QToolButton column + selection state	Vertical navigation bar. Methods: add_item(key, icon_name, tooltip), set_active(key). Signal: item_selected(str). No Professional-specific content.
Acceptance for Delivery B

□ 3 widgets implemented.
□ CollapsibleSection unit tests include: expand/collapse toggle, keyboard interaction, draggable=True shows handle, draggable=False hides handle.
□ DragList unit test simulates reordering via API (move_section) and asserts order_changed payload.
□ IconSidebar unit tests cover add/set_active/item_selected and accessibility.
□ Extended visual debug harness: Tela 3, Tela 4, Tela 6 mockups reproduced with real widgets.
□ widget_catalog.md §5.3 / §5.4 statuses updated.
Delivery C — Custom-painted horizontal and advanced widgets
Depends on: nothing from A/B beyond theme integration.

Widget	Classification	Contract summary
TimelineSlider	Custom Widget	Horizontal timeline with play/pause/step controls and a tick-based slider. Properties: frame_range (min, max), current_frame. Signals: frame_changed(int), play_requested, pause_requested. Custom paintEvent renders ticks and track.
Ruler	Custom Widget	Horizontal measurement scale. Properties: range, units, major_tick_interval, minor_tick_interval. Custom paintEvent. Signal: position_clicked(float).
ColorPicker	Composite Widget	Wraps QColorDialog plus an inline swatch preview. Properties: color. Signal: color_changed(QColor). Uses native dialog; custom presentation optional.
Histogram	Custom Widget	Data-distribution visualization. Input: list[float] or (bins, counts). Properties: data, bins, log_scale. Custom paintEvent renders bars + optional axis labels. Signal: bin_clicked(int).
Acceptance for Delivery C

□ 4 widgets implemented.
□ TimelineSlider and Ruler unit tests cover paintEvent smoke (no exceptions on empty data), public properties, signals emitted from API calls.
□ Histogram unit tests cover data set/clear, bin_clicked emission after simulated click on a bin.
□ ColorPicker tests cover property and signal, dialog suppressed via monkeypatch.
□ Visual debug harness: Tela 3 (TimelineSlider, Ruler) and Tela 4 (ColorPicker, Histogram, ProgressBar) reproduced.
□ widget_catalog.md §5.6 / §5.7 statuses updated.
Delivery D — Debug harness consolidation and closure
□ Extend scripts/debug/ui/widgets/forms/debug_forms.py into a full multi-tab debug window that reproduces:
Tela 2 (Profissional) — with FormRow-based two-column layout and DateField.

Telas 3–6 (Modelo de documentos, Agenda, Procedimentos, Orçamentos) — with CollapsibleSection, DragList, DragHandle.

Tela 7 (Config) — with EyeToggleButton / VisibilityToggle.

Shared widgets page (PDF Prototipagem_UI_19_Widgets.pdf) — SearchField, ProgressBar, TimelineSlider, Ruler, ColorPicker, Histogram.

□ Validate Dark + Light themes visually.
□ Validate HiDPI (QT_SCALE_FACTOR=1.5 and 2).
□ Full validation suite green (pytest, ruff, ruff format, mypy).
□ widget_catalog.md closed: all L.0.2 widgets Existing, milestone L.0.2.
□ Update baseline in §1.1 with new counts.
Delivery D — Commit strategy
Five commits, in order:

feat(ui): add L.0.2 delivery A — simple Qt-native widgets ✅ (ready)

feat(ui): add L.0.2 delivery B — sections and lists

feat(ui): add L.0.2 delivery C — custom-painted widgets

chore(debug): consolidate L.0.2 visual debug harness (delivery D)

docs: mark L.0.2 widgets as Existing in catalog (final)

Alternatively, one consolidated commit at the end of Delivery D if the project prefers larger PRs. Decision deferred to the next session.

5.3 L.1 — Professional Editor
Status: Planned
Purpose: Deliver the first functional Professional Editor using the L.0 and L.0.2 system widgets.

Scope
Implement ProfessionalEditor.

Register it in EditorRegistry.

Provide the Professional Module's ModuleUISpec.

Host the Editor in the central Area.

Implement the initial professional profile interface (Tela 2 of the prototype).

Integrate the professional.* settings namespace.

Implement persistence according to professional.md.

Add Editor contract and integration tests.

Architectural constraints
ProfessionalEditor is a concrete Editor implementation.

The Professional Module is declarative and contributes the UI specification required to expose the Editor. It must not instantiate the Editor directly.

The Editor must follow the existing lifecycle and context contracts.

Persistence
Professional profile persistence must use the SQLite database defined in professional.md:

text
~/.cranioz/professional/professional.db
Do not introduce a temporary JSON persistence layer or use Editor visual-state persistence to store profile data.

The initial implementation should remain limited to the profile fields and operations required by the existing specification.

Settings integration
Use the professional.* namespace for appropriate user or application settings.

Do not duplicate profile data in settings when it belongs in the professional database.

Completion criteria
□ ProfessionalEditor registered and materialized through the established Editor architecture.
□ Professional Module exposes the correct ModuleUISpec.
□ Initial profile interface functional (Tela 2 of the prototype).
□ SQLite persistence integrated according to professional.md.
□ Settings namespace integrated.
□ Editor lifecycle and integration tests passing.
□ No Professional-specific widgets incorrectly placed in the generic system widget package.
5.4 L.2 — Professional Navigation
Status: Planned
Purpose: Implement the internal navigation and configuration interactions required by the Professional Editor.

Scope
Wire the L.0.2 CollapsibleSection, DragList, IconSidebar, EyeToggleButton, and VisibilityToggle into the Professional Editor.

Implement Telas 3–7 of the prototype.

Persist navigation order and visibility through the appropriate application settings mechanism.

Implement pt-BR translations for the widget static strings.

Migrate SignaturePreview empty-state colors to design tokens once it accepts an optional ThemeService.

Migrate FilePicker browse button to IconProvider.

Professional-specific compositions
The Professional Editor may compose the system widgets into higher-level components, such as:

ProfessionalSidebar;

ProfessionalSectionTree;

ProfessionalConfigPanel.

These are consumer-specific compositions and should remain inside the Professional Editor implementation unless a separate reuse case emerges.

Completion criteria
□ All prototype screens (Tela 2 through 7) functional.
□ Navigation between sections works.
□ Expand/collapse, visibility, and drag ordering work.
□ Ordering and visibility preferences are persisted and restored.
□ Keyboard and accessibility behavior validated.
□ Theme and language changes propagate correctly.
5.5 Sprint L integration and closure
After L.0, L.0.2, L.1, and L.2:

□ Validate the Professional Editor through the actual Workspace and Editor lifecycle.
□ Validate ModuleUISpec registration and materialization.
□ Validate profile persistence across application restarts.
□ Validate settings restoration.
□ Validate theme and language changes.
□ Run the full test suite and static analysis.
□ Update widget_catalog.md to reflect implemented components.
□ Update implementation_plan.md if the completion status of Sprint L or Phase 3 changes.
□ Record any remaining limitations explicitly.
Sprint L must not absorb unrelated Phase 4 or general UI backlog items.

6. Deferred work
6.1 Logs Monitor
The Logs Monitor remains a dedicated deferred implementation task.

Its specification is maintained in monitor_logs.md.

It is not a Phase 3 deliverable and does not block Sprint L.

It may be scheduled as a separate sprint after the completed Sprints I–K, without changing the dependency sequence of Sprint L.

6.2 Phase 4 — Scene & Visualization
Phase 4 remains deferred until Phase 3 is formally closed.

Its pending deliverables include:

Unified Import Dialog.

ViewerLayoutManager and dynamic viewer layouts.

2D and 3D visualization tools.

Viewer status indicators.

Clinical transfer functions.

Further Editor workflows and visualization integration.

The widget catalog may contain components intended for these future workflows, but their presence in the catalog does not authorize implementation during Sprint L.

6.3 Widget backlog
The following components remain outside L.0.2 unless a concrete requirement is approved:

ObjectMovementControl;

DualRangeSlider;

BlurToggle;

StartButton, ContinueButton, CompleteButton, PreviousButton, NextButton, RemoveButton, SettingsButton (implemented as styled QPushButton variants only if a concrete consumer requires them);

additional tomography and cephalometry controls.

Their implementation milestones must follow the consuming Editor or subsystem dependencies documented in widget_catalog.md.

7. Known issues and deferred items
Item	Status	Action
Logs Monitor	Planned	Schedule separately; specification already exists.
Test stub documentation	Pending	Add README and TODO markers to the identified infrastructure test stubs.
correlation_id propagation	Deferred	Revisit according to the implementation plan.
event_subscription contract test	Deferred	Add dedicated coverage when the corresponding integration is implemented.
Remaining hardcoded appearance literals	Tracked debt	Continue using the existing architecture guard and debt list.
VTK GetData() deprecation	Deferred	Migrate according to the VTK 10 compatibility plan.
pyproject.toml unused ignore_missing_imports entries	Cleanup	Remove when appropriate; no functional impact.
Phase 4 viewer and visualization work	Deferred	Start only after Phase 3 closure.
SignaturePreview empty-state colors	L.2 deferral	Migrate to design tokens once optional ThemeService supported.
FilePicker browse button glyph	L.2 deferral	Migrate to IconProvider.
pt-BR translations for L.0 / L.0.2 widgets	L.2 deferral	Add catalog entries for static strings.
widget_catalog.md L.0.2 Delivery A statuses	Documentation follow-up	Mark the 7 Delivery A widgets as Existing (milestone L.0.2) before Delivery B closes.
ruff format touched docs/architecture/home_page/monitor_logs.md	Pre-existing debt	The file was out of format before L.0.2. Not a regression from Delivery A; revisit when the Logs Monitor sprint begins.
7.1 Test stub documentation
The intentionally empty infrastructure test stubs must be documented so that their purpose is clear.

Required actions:

Add a README.md to tests/infrastructure/i18n/.

Add a # TODO(sprint-i18n) marker to each relevant stub.

Add equivalent documentation to tests/infrastructure/scene/.

Preserve the distinction between reserved infrastructure contracts and actual integration coverage.

This is maintenance work and must not expand into a general test architecture refactoring.

8. Validation requirements
Run the complete validation suite after each delivery and before closing Sprint L.

8.1 Tests
powershell
.venv\Scripts\python.exe -m pytest
8.2 Ruff
powershell
.venv\Scripts\python.exe -m ruff check .
.venv\Scripts\python.exe -m ruff format --check .
8.3 Mypy
powershell
.venv\Scripts\python.exe -m mypy src
8.4 Validation rules
Do not accept new test failures.

Do not introduce new Ruff violations.

Do not introduce new mypy errors.

Investigate regressions against the recorded baseline.

Update the test count and validation date after each completed delivery.

Do not reduce test coverage merely to obtain a passing suite.

9. Immediate action items
The next implementation sequence is:

~~Review and consolidate widget_catalog.md.~~ ✅ (v0.4)

~~Create sprint_l0_system_widgets.md.~~ ✅

~~Implement and test L.0.~~ ✅ (2026-11-23)

~~Implement L.0.2 — Delivery A (DateField, FormRow, DragHandle, EyeToggleButton, VisibilityToggle, SearchField, ProgressBar).~~ ✅ (2026-11-23)

Implement L.0.2 — Delivery B (CollapsibleSection, DragList, IconSidebar).

Implement L.0.2 — Delivery C (TimelineSlider, Ruler, ColorPicker, Histogram).

Implement L.0.2 — Delivery D (debug harness consolidation + catalog update + validation).

Implement L.1 — ProfessionalEditor, ModuleUISpec, settings integration, SQLite persistence.

Implement L.2 — Professional navigation, sections, and configuration interactions.

Run complete validation and close Sprint L.

Review the remaining Phase 3 deliverables against implementation_plan.md.

Close Phase 3 formally only when its authoritative completion criteria are satisfied.

9.1 Next handoff
The next development task is:

Implement L.0.2 — Delivery B (3 widgets: CollapsibleSection, DragList, IconSidebar).

Reference documents for the next session:

docs/architecture/widgets/widget_catalog.md v0.4 — full inventory.

docs/architecture/widgets/sprint_l0_system_widgets.md — L.0 contracts (patterns to replicate).

docs/architecture/modules/professional/professional.md — to be provided, required for L.1.

src/cranioz/ui/theme/tokens.py, compiler.py, service.py — theme integration.

src/cranioz/ui/widgets/forms/* — L.0 reference implementations.

src/cranioz/ui/widgets/lists/drag_handle.py — L.0.2 A reference (Delivery B depends on it).

src/cranioz/ui/widgets/headers/section_header.py — to be inspected; decide whether CollapsibleSection reuses it or builds its own header.

src/cranioz/ui/icons/provider.py and unicode.py — icon integration contract.

Delivery B depends on Delivery A (DragHandle) and can start immediately from the §5.2 specification.

10. Definition of Done
This handoff is considered current when:

Completed Sprints I, J, K, L.0, and L.0.2 Delivery A are reflected accurately.

Sprint L is divided into L.0, L.0.2, L.1, and L.2.

L.0 is marked complete with its delivery table and known deferrals.

L.0.2 Delivery A is marked complete with its delivery table, supporting changes, and acceptance criteria.

L.0.2 Deliveries B, C, and D are defined with explicit widget lists and acceptance criteria.

The excluded widgets (ActionButtonRow, SectionItemRow, ObjectMovementControl, DualRangeSlider) are documented with reasons.

L.1 defines ProfessionalEditor as an Editor hosted by the central Area.

Professional profile persistence follows professional.md.

L.2 covers navigation, sections, translations, and theme-token migration.

The widget catalog remains the authoritative system-wide inventory.

Logs Monitor remains deferred and does not block Sprint L.

Phase 4 remains deferred until Phase 3 is closed.

Validation requirements and the current baseline are recorded.

Authority: implementation_plan.md defines phase scope and completion criteria. This document defines the immediate execution sequence and handoff.