# Implementation Plan

**Document type:** Roadmap and execution plan
**Status:** Living document
**Scope:** Phased implementation of the CranioZ platform, from foundation to release
**Last updated:** 2026-11-15

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
- **UI Framework:** PySide6 / Qt 6 (minimum 6.9 for `QImage.flipped()`; `QStyleHints.colorScheme()` requires 6.5+, but the project pins `>=6.9,<7.0`)
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

**Note on `uv sync`:** the project uses **extras** (not `dependency-groups`). To restore the full development environment, run `uv sync --extra dev`. Plain `uv sync` removes dev tools (pytest, mypy, ruff) from the active `.venv`. See `Next Steps.md` §8.

---

## 4. Phase Overview

The implementation is divided into 11 phases. The sequence establishes the platform progressively while prioritizing a validated clinical core.

| Phase | Name | Status | Main Pending Work |
|---|---|---|---|
| **Phase 0** | Foundation & Boot | ✅ Implemented | Startup performance improvements |
| **Phase 1** | Contracts, Core Domain & i18n | ✅ Implemented | — |
| **Phase 2** | Workspace Engine & Icons | 🚧 In Progress | Sprint H (`EditorStack`) |
| **Phase 3** | Project, Home Page & Professional Module | 🚧 In Progress | `ProjectIndex`, coordinated deletion, async loading, Professional module |
| **Phase 4** | Scene & Visualization | ⏳ Planned | Import Dialog, Viewer Layout Manager, 2D/3D Tools, LUTs |
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

Phase 1 is now closed. Phase 2 is one deliverable away from closure (`EditorStack`, Sprint H). Phase 3 remains in progress. Phase 4 begins only after Phases 2–3 are marked `✅ Implemented` in this document.

### 5.1 Immediate Priorities

The work order below respects dependencies between Phases 2–3. Blocks 1–6 completed the Toolbar/Editor active-View foundation; Sprint G completed the intra-Area split; Sprint H completes the multi-Editor Area composition.

| Sprint | Phase | Deliverable | Status | Depends on |
|---|---|---|---|---|
| **B** | 1 | i18n contract and catalogs | ✅ Complete | — |
| **C** | 1 | `EditorContext` propagation | ✅ Complete | B, E, F |
| **E** | 2 | `ThemeService`, `ThemeCompiler`, tokens | ✅ Complete | — |
| **F** | 2 | `IconProvider`, `UnicodeIconProvider`, glyph migration | ✅ Complete | E |
| — | — | **2026-11-13 cleanup** (dead code, `QImage.flipped`, PySide6 bump) | ✅ Complete | — |
| **M** | 2 | **Frameless window, drag support, native resize** (UI Shell polish) | ✅ Complete | E, F |
| **1** | 2 | **Toolbar polish** (`AlignTop`, fixed width, `Expanding` grid) | ✅ Complete | — |
| **2** | 2 | **`Toolbar.set_active` / `set_expanded` / chevron** | ✅ Complete | 1 |
| **3** | 2 | **`Editor._EditorSignals` + `Editor.set_active_view`** | ✅ Complete | — |
| **4** | 2 | **`ViewLayoutRenderer` event filter + `ACTIVE_ONLY`** | ✅ Complete | 3 |
| **5** | 2 | **`TomographyEditor` wires the active-View flow** | ✅ Complete | 4 |
| **5.5** | 2 | **Percentage-based Area layout, QSS Areas, TopOverlay minimum width** | ✅ Complete | 4, 5 |
| **5.6** | 2 | **Window controls in ExtrasSegment; `closeEvent` with confirmation** | ✅ Complete | 5.5 |
| **5.6.1** | 2 | **Window controls in HomeTopBar; end-to-end tests** | ✅ Complete | 5.6 |
| **6** | 2 | **`debug_workspace.py` final visual validation** | ✅ Complete | 5, 5.5, 5.6, 5.6.1, M |
| **G** | 2 | **`AreaLayoutRenderer` (inter-Area vs intra-Area split)** | ✅ Complete | 6 |
| **H** | 2 | **`EditorStack`** | ⏳ Next | G |
| **I** | 3 | `ProjectIndex` | 🚧 Pending | — |
| **J** | 3 | Coordinated deletion | 🚧 Pending | I |
| **K** | 3 | Async loading | 🚧 Pending | I, J |
| **L** | 3 | Professional module | 🚧 Pending | C, E, F |

**Next work item:** Sprint H — `EditorStack`. It is the last Phase 2 deliverable. The point of extension is `AreaLayoutRenderer._resolve_spec`: change it to return `AreaLayoutType.STACK` for multiple Editors, and replace `_render_split` with `_render_stack`.

**Note on ordering:** Blocks 4–6, 5.5–5.6.1, Sprint M, and Sprint G are complete. Sprint H is the last Phase 2 deliverable. Sprints I and J are independent of H. Sprints J and K depend on I; Sprint L depends on C (complete), E (complete), and F (complete).

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

**Goal:** Close Phase 1 formally.

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
- ✅ **Sprint C (`EditorContext` propagation):**
  - `EditorContext` carries nine fields: `task_manager`, `telemetry`, `correlation_id`, `command_dispatcher`, `scene_query`, `domain_object_store`, `event_subscription`, `translation_service`, `theme_service`, `icon_provider`.
  - `theme_service` and `icon_provider` added to `EditorContext` (Sprint C).
  - `Workspace.load_spec` passes the complete set through `LayoutBuilder`'s `shared_context`.
  - `LayoutBuilder` propagates via `EditorContext(**shared)`, no closed key list.
  - `TomographyEditor.initialize` and `MeshDebugEditor.initialize` receive the full context.
  - Contract test: `tests/integration/ui/workspace/test_editor_context_propagation.py` asserts every Editor receives all fields.

**Tests:**

- Pure Python Domain tests.
- Repository contract tests.
- Project serialization round-trips.
- Domain invariant and error-case tests.
- ✅ i18n contract tests.
- ✅ `test_no_hardcoded_strings_in_shell_widgets.py`.
- ✅ `EditorContext` propagation tests (Sprint C).

**Status:** ✅ Implemented.

---

### Phase 2: Workspace Engine & Icons

**Goal:** Close Phase 2 formally. Blocker: Sprint H (`EditorStack`).

**Deliverables:**

- ✅ `LayoutTree`, `AreaManager`, `LayoutBuilder`, `LayoutRenderer`.
- ✅ `Workspace` facade, `TopOverlay`, `OverlayManager`.
- ✅ Three-segment Top Bar.
- ✅ Area toggles (Left, Right, Bottom).
- ✅ Atomic `Workspace.load_spec()`.
- ✅ **Sprint E (`ThemeService` + `ThemeCompiler` + tokens):**
  - `ThemeMode` (`DARK`, `LIGHT`, `SYSTEM`) and `ThemeName` (`DARK`, `LIGHT`) as `StrEnum`.
  - `ThemeTokens` + 7 dataclasses (Colors, Typography, Spacing, Dimensions, Borders, Effects, Surfaces).
  - 47 tokens as specified in `docs/architecture/appearance/themes/themes_and_design_tokens.md`.
  - `ThemeService`: `mode()`, `set_mode()`, `theme()`, `tokens()`, `color()`, `dimension()`, `surface_color()`, `icon_name()`, `theme_changed` signal, `SYSTEM` resolution via `QStyleHints.colorScheme()`.
  - `ThemeCompiler`: `compile()`, `apply()`, surface composition (toolbar, popover, modal_backdrop), QSS emission. `modal_backdrop` uses a fixed `#000000` base per spec §6.2.
  - Modern Dark palette applied to `DARK_TOKENS` (neutral greys + iOS system colors). `feedback_information` kept at `#4A90D9` (spec value) to pass WCAG AA against `background_panel`.
  - `cranioz.infrastructure.settings` package: `SettingsService` protocol, `InMemorySettingsService`, `FilesystemSettingsService`, `SettingsStore`, `SettingsMigrator`, `KNOWN_KEYS`, `SettingsError`, `SettingsMigrationError`.
  - `AppPathResolver.user_settings_path()` and `PathsConfig.settings_root` (default `~/.cranioz/Settings/settings.json`).
  - Boot integration: read `appearance.theme_mode` from `SettingsService` before `MainWindow`; invalid → `DARK` + `WARNING`; apply theme before the first window.
  - Expanded `_build_qss`: tables + headers + scrollbars, `QLineEdit` placeholder and focus, `QComboBox` dropdown, `QLabel` roles (`title`/`subtitle`/`caption`/`arrow`), `QFrame` cards, `QMenu`, `QToolTip`, `StartButton` states, and `FlowRow` checked/step/separator/arrow.
  - `StartButton` and `FlowRow` migrated from inline `setStyleSheet` to `setProperty` + the global QSS.
  - Contract tests: `test_no_hardcoded_appearance.py`, `test_tokens_used.py`, `test_tokens_present.py`, `test_theme_completeness.py`, `test_theme_values.py`, `test_contrast.py`.
  - Unit tests: `test_service.py`, `test_tokens.py`, `test_compiler.py`, `test_settings_service.py`.
- ✅ **Sprint F (`IconProvider` + `UnicodeIconProvider`):**
  - `IconState` enum (`DEFAULT`, `HOVER`, `PRESSED`, `SELECTED`, `DISABLED`).
  - `IconProvider` Protocol (`icon(name, size, state) -> QIcon`, `text_glyph(name) -> str`, `invalidate_cache() -> None`).
  - `UnicodeIconProvider` with the closed 70-icon catalog (60 canonical + 6 shell + 4 window controls).
  - Injection into `MainWindow`, `Workspace`, `HomePage`, `TopBar` segments, `Toolbar`, `StartButton`, `FlowRow`.
  - Migration of hardcoded glyphs in `TopBar`, `HomeSegment`, `ModulesSegment`, `ExtrasSegment`, `HomePage`, `Toolbar`, `StartButton`, `FlowRow`.
  - `_WHITELIST` in `test_no_hardcoded_strings_in_shell_widgets.py` emptied (Sprint B debt paid).
  - Contract tests: `test_icon_catalog.py`, `test_icon_fallback.py`, `test_icon_theme.py`, `test_icon_widget_contract.py`, `test_icon_accessibility.py`.
- ✅ **Sprint M (Frameless Window & Native Chrome):** *(2026-11-15)*
  - `MainWindow` now uses `Qt.FramelessWindowHint`; the native Windows title bar is removed.
  - `WindowDragFilter`: allows dragging the window by clicking and dragging on the custom top bars (HomePage and Workspace TopOverlay).
  - `_central_container` wraps the `QStackedWidget` with a 4px margin, creating a dead zone where native resize is detected.
  - Native resizing via `windowHandle().startSystemResize(edges)` in `mousePressEvent`, with dynamic cursor feedback in `mouseMoveEvent` (Qt 6 API, cross-platform).
  - Maximize/restore icon sync between `HomeTopBar` and `ExtrasSegment` via `_update_maximize_icon`.
  - Integration tests: `test_main_window_is_frameless`, `test_main_window_drag_filter_is_installed`, `test_main_window_central_container_has_margins`.
- ✅ **Toolbar and Editor active-View foundation (Blocks 1–3, 2026-11-13):**
  - **Block 1 — Toolbar polish.** `Toolbar._root_layout.setAlignment(Qt.AlignmentFlag.AlignTop)`; `ViewLayoutRenderer._VERTICAL_TOOLBAR_WIDTH = 96` with `setFixedWidth(96)` for LEFT/RIGHT toolbars (fits "Toggle" without truncation); grid container and outer splitter use `QSizePolicy.Expanding`; vertical toolbars get `(Fixed, Expanding)` and horizontal toolbars get `(Expanding, Fixed)`. 8 tests.
  - **Block 2 — `Toolbar.set_active` / `set_expanded` / chevron.** `set_active(bool)` attenuates via `QGraphicsOpacityEffect(0.5)` without hiding; `set_expanded(bool)` compresses to a chevron; `expanded_changed` signal. Chevron flips automatically; persistence deferred. 11 tests.
  - **Block 3 — `Editor._EditorSignals` + `Editor.set_active_view`.** `active_view_changed = Signal(object)` (str | None); `set_active_view` validates `view_id` against the Editor's Views (unknown → WARNING, no signal); idempotent for the same id; `None` clears. `dispose()` resets without emitting. 12 tests in `tests/unit/ui/editors/test_editor_active_view.py`.
- ✅ **Block 4 (`ViewLayoutRenderer` event filter + `ACTIVE_ONLY`):**
  - Installs `QObject` event filter on each View's `activation_widget()` (Viewport3DView returns the `QVTKRenderWindowInteractor`; other Views return `content_widget()`).
  - Filter detects `QEvent.MouseButtonPress` and `QEvent.FocusIn`; calls `editor.set_active_view(view_id)`. Hover is not used.
  - Connects `editor.active_view_changed` to a slot that applies `toolbar.set_active(...)` per `ACTIVE_ONLY` toolbar.
  - `clear_cache()` removes filters from the correct target widget.
  - Toolbars `ACTIVE_ONLY` start inactive; `editor.set_active_view(None)` after rendering.
  - Regression test: rendering the same View Layout twice does not duplicate event filters.
  - 12 tests in `tests/unit/ui/editors/test_view_layout_renderer_active_only.py`.
- ✅ **Block 5 (`TomographyEditor` wires the active-View flow):**
  - `TomographyEditor.content_widget()` wraps the View grid with the Editor-level Toolbars via `_wrap_with_editor_toolbars` (LEFT `ALWAYS` + RIGHT `COLLAPSIBLE`).
  - `_editor_toolbars` list; `dispose()` clears it.
  - 7 tests in `tests/integration/ui/editors/test_tomography_editor_active_view.py`.
- ✅ **Block 5.5 (Workspace percentage-based Area layout):**
  - `Workspace._LEFT_RATIO = 0.20`, `_RIGHT_RATIO = 0.25`, `_BOTTOM_RATIO = 0.20`.
  - `Workspace._apply_default_splitter_sizes()` computes sizes as percentages (Central = fill), never letting the Central Area drop below `TopOverlay.minimum_width()`.
  - `AreaWidget.refresh()` returns early when the Area model is hidden, preventing placeholder rendering in hidden Areas.
  - `_build_empty_placeholder()` uses `WA_TranslucentBackground` so the QSS background shows through.
  - Debug Editors `MockPosicaoEditor`, `MockObjetosEditor`, `MockConsoleEditor`, `MockMPREditor` added under `src/cranioz/ui/editors/mock/`.
- ✅ **Block 5.6 (Window controls in ExtrasSegment):**
  - `ExtrasSegment.minimize_requested`, `maximize_requested`, `close_requested`.
  - 3 new buttons, 28px wide, icons via `IconProvider`.
  - `MainWindow._wire_top_bar_segments` connects the 3 signals.
  - `MainWindow._on_window_maximize_requested` toggles `showMaximized`/`showNormal`.
  - `MainWindow.closeEvent` asks for confirmation when a project is open, then tears it down via `_close_active_project`.
  - `test_extras_segment.py` — 19 tests.
  - `test_main_window.py` — 3 tests for `closeEvent`.
- ✅ **Block 5.6.1 (Window controls in HomeTopBar):**
  - `HomeTopBar.minimize_requested`, `maximize_requested`, `close_requested`.
  - `HomePage` forwards the 3 new signals.
  - `MainWindow._connect_home_signals` connects them.
  - `test_home_top_bar.py` +5 tests, `test_home_page.py` +3 tests, `test_main_window.py` +3 end-to-end tests.
- ✅ **Block 6 (`debug_workspace.py` final visual validation):**
  - The script `scripts/debug/ui/workspace/debug_workspace.py` was run end-to-end with Blocks 4–6, 5.5–5.6.1, and Sprint M applied.
  - The visual matches the Prototipagem_UI_17 reference with the frameless window (drag, resize, maximize, minimize, close).
  - Committed.
- ✅ **Sprint G (`AreaLayoutRenderer`):** *(2026-11-15)*
  - `AreaLayoutSpec` introduced in `src/cranioz/ui/workspace/areas/area_layout_spec.py` with `SINGLE`, `SPLIT`, and `STACK` types, validated structurally in `__post_init__`.
  - `AreaLayoutRenderer._resolve_spec()` returns `SINGLE` for one Editor and `SPLIT` for multiple (current behavior preserved).
  - `STACK` is declared and raises `NotImplementedError` until Sprint H; the point of extension is explicit and testable.
  - `AreaLayoutRenderer._materialize()` validates that `spec.editor_ids` matches the Area's Editors, guarding against future drift between spec and instances.
  - `_render_split()` extracted from the previous `else` branch; `_build_editor_container()` unchanged (preserves the `Expanding`/`Ignored` policy that Block 5.5 corrected).
  - 6 unit tests for `AreaLayoutSpec` in `tests/unit/ui/workspace/areas/test_area_layout_spec.py`.
  - 1 integration test for the `STACK` failure mode in `tests/integration/ui/workspace/areas/test_area_layout_renderer.py`.
  - `stl.py` reverted to `GetData()` with `# TODO(vtk-10)` (the `ExportLegacyFormat()` migration requires a `vtkIdTypeArray` destination, not a `vtkCellArray`; deferred to Phase 4.5).
  - `main_window.py` `mouseMoveEvent` and `mousePressEvent` annotated with `QMouseEvent` (mypy `no-untyped-def` resolved).
  - `ruff check .` clean; `mypy src` clean; `pytest` 1632 passing, 2 skipped.
- ⏳ **Sprint H (`EditorStack`):** *(next)*
  - `EditorLayoutSpec.stack([...])` — declarative spec for an Area that hosts multiple Editors as tabs. Symmetric to `ViewLayoutSpec` and `AreaLayoutSpec`.
  - `EditorStack` widget — a `QTabWidget`-based container, one tab per Editor. The Editor's `content_widget()` is placed in the tab. Lifecycle: `activate()` / `deactivate()` fire on tab change; `dispose()` fires when a tab is removed or the stack is destroyed.
  - `AreaLayoutRenderer._render_stack()` replaces `_render_split()` for multiple Editors.
  - `AreaLayoutRenderer._resolve_spec()` returns `AreaLayoutType.STACK` for multiple Editors (replacing the current `SPLIT`).
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
- ✅ Icon catalog, fallback, theme integration, widget contract, and accessibility tests (Sprint F).
- ✅ Frameless window, drag filter and native resize tests (Sprint M).
- ✅ Toolbar polish tests (Block 1).
- ✅ `Toolbar.set_active` / `set_expanded` / chevron tests (Block 2).
- ✅ `Editor.set_active_view` contract tests (Block 3).
- ✅ `ACTIVE_ONLY` wiring tests (Block 4).
- ✅ `TomographyEditor` active-View flow tests (Block 5).
- ✅ Percentage-based Area layout tests (Block 5.5).
- ✅ Window controls tests (Blocks 5.6, 5.6.1).
- ✅ `debug_workspace.py` visual validation (Block 6).
- ✅ `AreaLayoutSpec` structural tests (Sprint G).
- ✅ `STACK` failure-mode integration test (Sprint G).
- ⏳ `EditorStack` tab-switching, lifecycle, and dispose tests (Sprint H).

**Status:** 🚧 In Progress. Blocker: Sprint H (`EditorStack`).

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
- 🚧 **Test stub documentation (2026-11-13 cleanup follow-up):**
  - `tests/infrastructure/i18n/` (4 stubs) and `tests/infrastructure/scene/test_scene_query_adapter.py` are intentionally empty. They reserve the contract for the missing granular unit tests of `infrastructure/i18n/` and `infrastructure/scene/`. End-to-end coverage already exists in `tests/integration/i18n/`.
  - Add `README.md` to `tests/infrastructure/i18n/` explaining the contract, and a `# TODO(sprint-i18n)` line to each stub. Same for `tests/infrastructure/scene/`.

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

**Status:** 🚧 In Progress. Blockers: Sprints I, J, K, L, and stub documentation.

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

**Implemented:** `Mesh`, `CoordinateFrame`, STL I/O, VTK adapter, `MeshDebugEditor`. `VtkImageAdapter` is the sole bridge from `Volume` to `vtkImageData`.

**Deferred:** `GeometryRevision`, content-hash deduplication, persistent asset storage, `ValidationProfile`, `GeometryOperation`, booleans, welding, benchmarks.

#### 4.5 Visualization Infrastructure

**Implemented:**

- ✅ `MPRView` (manual `vtkImageReslice` pipeline).
- ✅ `Viewport3DView` (`vtkSmartVolumeMapper`, `VTK_SHORT`).
- ✅ Axial, coronal, sagittal, 3D orientations.
- ✅ Volume rendering presets.
- ✅ `set_volume(Volume)`, `set_mesh(Mesh)`.
- ✅ DICOM volume path validated in MPR and 3D.
- ✅ `QImage.flipped(Qt.Orientation.Vertical)` used in `MPRView` (replaces the deprecated `QImage.mirrored`; PySide6 minimum raised to 6.9).
- ✅ Viewer-level Toolbars (`toolbar_specs`, `control_panel_specs`) with `ACTIVE_ONLY` visibility mode declared in `MPRView` and `Viewport3DView`.
- ✅ `Toolbar.set_active` and `Toolbar.set_expanded` (Block 2) available to the ViewLayoutRenderer.
- ✅ `Editor.active_view_changed` and `Editor.set_active_view` (Block 3) available for View activation.
- ✅ `ViewLayoutRenderer` `ACTIVE_ONLY` policy wired (Block 4).
- ✅ `TomographyEditor` materializes Editor-level Toolbars (Block 5).

**Pending:**

- ⏳ `RenderingAdapter` (removed in the 2026-11-13 cleanup; will be reintroduced only if a real second backend is required).
- ⏳ **ViewerLayoutManager** (dynamic grids: 1×1, 2×2, 3×3, editable up to 6×4, panoramic, ATM).
- ⏳ **2D Tools** (brightness/contrast, pan, zoom, HU probe, ROI, nerve drawing, distance/angle, crosshair, ruler, LUT selection, LUT inversion, background color, animation, thumbnail).
- ⏳ **3D Tools** (