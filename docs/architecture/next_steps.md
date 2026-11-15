# Next Steps

**Document type:** Action plan and handoff
**Status:** Active
**Scope:** Immediate next work items after Sprint H (`EditorStack`)
**Last updated:** 2026-11-15

---

## 1. Context

The VTK rendering pipeline is validated end-to-end. The DICOM visualization bug was resolved on 2026-11-06. The voxel-ordering contract is documented and enforced by regression tests. The imaging pipeline uses `int16` (`VTK_SHORT`) as the production scalar type, with the direction matrix applied and confirmed.

The appearance architecture has been decided. `docs/architecture/appearance/` is the canonical specification. ADR-0014 registers the toolkit decision (Qt Widgets + QSS modular + Design Tokens in Python, not QML). The DICOM path, the 3D viewport, the MPR view, and the workspace layout are operational and covered by a growing test suite.

**Current test baseline: 1633 passing, 0 failed, 0 errors, 2 skipped (Block 5.5 intencionais).** O baseline anterior era 1632; o delta de +1 reflete o Sprint H (`EditorLayoutSpec` refatorado com validação mais limpa, testes do `EditorStack` consolidados, e a remoção de testes redundantes em `specs/`). Os 9 warnings remanescentes são todos de `vtkCellArray.GetData` (deprecação do VTK 9.6+; remoção planejada para o VTK 10), rastreados em §7.

Sprint B (i18n) is complete: the shell — `MainWindow`, the Home Page tree, the three Top Bar segments, and the Workspace placeholder editor — resolves user-facing strings through the `TranslationService`. `tests/architecture/test_no_hardcoded_strings_in_shell_widgets.py` guards against regressions.

Sprint E (appearance foundation) is complete: `ThemeService` and `ThemeCompiler` are implemented, the 47 canonical design tokens are defined for `DARK` and `LIGHT`, the `cranioz.infrastructure.settings` package provides typed, versioned, and atomically written user settings, and `AppPathResolver.user_settings_path()` resolves the user settings file. The theme is applied at boot before the first window. The Modern Dark palette is applied, the QSS covers tables, headers, scrollbars, buttons, inputs, labels, cards, `StartButton`, `FlowRow`, and the Workspace Areas (Block 5.5). `tests/architecture/test_no_hardcoded_appearance.py` guards against new hardcoded colors and freezes the remaining debt.

Sprint F (icons) is complete: `IconState`, `IconProvider` Protocol and `UnicodeIconProvider` are implemented with the closed icon catalog (now 70 icons: 60 canonical + 6 shell + 4 window controls); the provider is injected into `MainWindow`, `Workspace`, `HomePage`, the three Top Bar segments, `Toolbar`, `StartButton`, and `FlowRow`. The five icon contract tests pass.

Sprint C (EditorContext propagation) is complete: `EditorContext` now carries `theme_service` and `icon_provider` alongside the existing seven fields, and `Workspace.load_spec` passes the complete set through `LayoutBuilder`'s `shared_context`. **Phase 1 is closed.**

The **2026-11-13 cleanup** removed a substantial amount of dead code (two source files, one package, one duplicated adapter, ten obsolete debug scripts), migrated `QImage.mirrored` to `QImage.flipped`, and raised the `PySide6` minimum to `>=6.9`.

**Blocks 1–6 are complete** (Toolbar polish, `set_active`/`set_expanded`/chevron, `Editor.set_active_view`, `ViewLayoutRenderer` event filter + `ACTIVE_ONLY`, `TomographyEditor` end-to-end, `debug_workspace.py` visual validation). Blocks 5.5, 5.6, 5.6.1 are complete (percentage-based Area layout, window controls in `ExtrasSegment` and `HomeTopBar`, `closeEvent` with confirmation). Sprint M is complete (frameless window + native chrome + drag + native resize).

**Sprint G is complete (`AreaLayoutRenderer`).** 2026-11-15.

- `AreaLayoutSpec` introduced with `SINGLE`, `SPLIT`, and `STACK` types.
- `AreaLayoutRenderer._resolve_spec()` returns `SINGLE` for one Editor and `SPLIT` for multiple Editors (behavior preserved).
- `STACK` is declared and raises `NotImplementedError` until Sprint H; the extension point is explicit.
- `AreaLayoutRenderer` validates that `spec.editor_ids` matches the Area's Editors, guarding against future drift.
- 6 unit tests for `AreaLayoutSpec` + 1 integration test for the `STACK` failure mode.
- `stl.py` reverted to `GetData()` with `# TODO(vtk-10)` (see §7).
- `main_window.py` `mouseMoveEvent` and `mousePressEvent` annotated with `QMouseEvent`.
- `ruff check .` clean, `mypy src` clean, `pytest` 1632 passing.

**Sprint H is complete (`EditorStack`).** 2026-11-15. Phase 2 is now closed.

- `EditorLayoutSpec` (LEAF/SPLIT/STACK) with structural validation, `stack(...)` constructor, and `EditorStackOrientation` (TOP/BOTTOM/LEFT/RIGHT).
- `EditorStack` widget (QStackedWidget + `EditorStackSwitcher`), not a `QTabWidget` (ADR-0013 §2.5).
- Lazy materialization: only the active Editor's `content_widget()` is materialized eagerly.
- Lifecycle: `activate()`/`deactivate()` fire on tab switch; `dispose()` fires exactly once per Editor.
- `AreaLayoutRenderer` extended to materialize the N-ary `EditorLayoutSpec` (LEAF → container; SPLIT → QSplitter; STACK → EditorStack).
- `LayoutBuilder` collects `editor_ids` recursively (handles LEAF, SPLIT, and STACK) and propagates the spec to the Area via `set_editor_layout_spec()`.
- `AreaWidget` forwards `IconProvider` to the renderer and disposes the `EditorStack` before detaching content widgets.
- Backward-compatibility shim at `specs/editor_layout_spec.py` (re-exports the canonical implementation in `areas/`).
- `PlaceholderEditor` moved to `src/cranioz/ui/editors/placeholder_editor.py` (public).
- `debug_workspace.py` updated to use a `STACK` `ModuleUISpec`; visual validation confirmed.
- 6 unit tests for `EditorLayoutSpec`, 4 unit tests for `EditorStack`, 1 integration test for `STACK` materialization.
- `tests/unit/ui/workspace/specs/test_editor_layout_spec.py` removed (redundant with the canonical test under `areas/`).
- `tests/architecture/test_no_hardcoded_appearance.py` updated with `placeholder_editor.py` (1 literal) and `editor_stack.py` (7 literals) in `_KNOWN_DEBT_FILES` and `_DEBT_MAX_LITERALS`.
- `ruff check .` clean, `ruff format` clean, `mypy src` clean, `pytest` 1633 passing, 2 skipped.

**Next work item:** Phase 3 begins. The next logical deliverable is the **Sprint de Refatoração de Arquitetura de Editores** (a nova estrutura `ui/editors/central`, `ui/editors/left`, etc.) or **Sprint I (`ProjectIndex`)**. Both depend on a decision from the user.

---

## 2. What is already done

### 2.1 Architecture and decisions

- `docs/architecture/appearance/` contains the canonical appearance specification:
  - `appearance.md`
  - `themes/themes_and_design_tokens.md` (7 categories, 47 tokens, `ThemeMode`, `ThemeName`, `ThemeService`, `ThemeCompiler`, translucency composition)
  - `icons/icons_and_icon_manager.md` (`IconState`, `IconProvider` Protocol, `UnicodeIconProvider` for Phase 2, `SvgIconProvider` for Phase 8, closed catalog)
  - `icons/icon_assets_and_visual_standards.md` (SVG format, directory structure, naming, visual standards)
  - `surfaces_and_overlays.md` (Solid, Translucent, Simulated Glass; real blur is not supported)
- ADR-0014 (Widget Toolkit Selection) is written in `docs/adr/ADR-0014-widget-toolkit-selection.md`.
- ADR-0013 (Editor Layout Tree, View Layout Tree, and Toolbar Placement) is accepted.

### 2.2 Code and tests

- **Test baseline after Sprint H: 1633 passing, 2 skipped.**
- `ruff check` clean; `ruff format --check` clean.
- `mypy src` clean.
- `VtkImageAdapter` corrected (no transposition, `int16`, direction matrix).
- `Viewport3DView` stabilized (`QTimer` cleanup on `dispose`); `content_widget()` eagerly creates the VTK pipeline so `activation_widget()` returns the interactor before the renderer installs its filter.
- `MPRView` renders correctly with the Volume direction matrix, and uses `QImage.flipped(Qt.Orientation.Vertical)`.
- `MainWindow` registers built-in tools before creating the Workspace.
- **Sprint B (i18n) complete.** The shell resolves every user-facing string through the `TranslationService`.
- **Sprint E (appearance foundation) complete.** See prior versions for the full list. Additions in Block 5.5:
  - QSS `QWidget[area_placement="central"]`, `QWidget[area_placement="left"/"right"/"bottom"]` with `border-radius`.
  - QSS `QSplitter::handle` (8px, `background_application`) so gaps read as empty space.
  - QSS `QFrame#top_overlay` with `border-radius`.
  - `AreaWidget` sets dynamic property `area_placement`, `WA_StyledBackground`, and calls `unpolish/polish` for immediate QSS application.
  - `LayoutRenderer._render_split` sets `setHandleWidth(8)`.
- **Sprint F (icons) complete.** Catalog grew from 66 to 70 icons in Block 5.6 (`window_minimize`, `window_maximize`, `window_restore`, `window_close`).
- **Sprint C (EditorContext propagation) complete.** Unchanged from prior versions.
- **2026-11-13 cleanup.** Unchanged from prior versions.
- **Blocks 1–3 complete** (Toolbar polish, `set_active`/`set_expanded`/chevron, `Editor.set_active_view`).
- **Block 4 complete** (`ViewLayoutRenderer` event filter + `ACTIVE_ONLY`).
  - `View.activation_widget()` default returns `content_widget()`.
  - `Viewport3DView.activation_widget()` returns the `QVTKRenderWindowInteractor`; `content_widget()` calls `_ensure_pipeline()` so the interactor exists before the filter installs.
  - `ViewLayoutRenderer` gained an optional `editor` parameter; installs an activation filter per View (on `activation_widget()`), indexes Toolbars per View (`_toolbars_by_view`), and connects `editor.active_view_changed` to `_on_active_view_changed`.
  - `_ViewActivationFilter` forwards `MouseButtonPress` and `FocusIn` to `editor.set_active_view` and returns `False` (never consumes the event).
  - `clear_cache()` removes filters from the correct target widget, clears `_view_filters`, `_view_filter_targets`, `_toolbars_by_view`.
  - Toolbars `ACTIVE_ONLY` start inactive in `_build_view_container` (matching `Editor.active_view_id is None` at start).
  - 12 tests in `tests/unit/ui/editors/test_view_layout_renderer_active_only.py`.
- **Block 5 complete** (`TomographyEditor` materializes Editor-level Toolbars).
  - `TomographyEditor.content_widget()` wraps the View grid with the Editor-level Toolbars via `_wrap_with_editor_toolbars`.
  - `_editor_toolbars` list; `dispose()` clears it.
  - 7 tests in `tests/integration/ui/editors/test_tomography_editor_active_view.py`.
- **Block 5.5 complete** (Workspace percentage-based Area layout).
  - `Workspace._LEFT_RATIO = 0.20`, `_RIGHT_RATIO = 0.25`, `_BOTTOM_RATIO = 0.20`.
  - `Workspace._apply_default_splitter_sizes()` computes sizes as percentages (Central = fill), never letting the Central Area drop below `TopOverlay.minimum_width()`.
  - `AreaWidget.refresh()` returns early when the Area model is hidden.
  - `_build_empty_placeholder()` uses `WA_TranslucentBackground` so the QSS background shows through.
  - Debug Editors `MockPosicaoEditor`, `MockObjetosEditor`, `MockConsoleEditor`, `MockMPREditor` added under `src/cranioz/ui/editors/mock/`.
- **Block 5.6 complete** (window controls in ExtrasSegment). 19 tests.
- **Block 5.6.1 complete** (window controls in HomeTopBar). 11 tests + 3 end-to-end.
- **Sprint M complete** (frameless window + native chrome).
  - `MainWindow` sets `Qt.FramelessWindowHint` and uses a `_central_container` with `setContentsMargins(4, 4, 4, 4)` to create a resize dead zone.
  - `WindowDragFilter` installed on `HomeTopBar` and `Workspace`'s `TopOverlay`.
  - Native resize via `windowHandle().startSystemResize(edges)`.
  - `_update_maximize_icon(restore=...)` keeps the maximize/restore icon in sync.
  - 3 new integration tests in `test_main_window.py`.
- **Block 6 complete** (`debug_workspace.py` visual validation). Committed.
- **Sprint G complete** (`AreaLayoutRenderer`). 2026-11-15.
  - `AreaLayoutSpec` (`SINGLE`, `SPLIT`, `STACK`) with structural validation.
  - `AreaLayoutRenderer._resolve_spec()` returns `SINGLE` for one Editor and `SPLIT` for multiple (behavior preserved).
  - `STACK` is declared and raises `NotImplementedError` until Sprint H — the point of extension is explicit.
  - `AreaLayoutRenderer` validates that `spec.editor_ids` matches the Area's Editors.
  - 6 unit tests for `AreaLayoutSpec` + 1 integration test for the `STACK` failure mode.
  - `stl.py` reverted to `GetData()` with `# TODO(vtk-10)`.
  - `main_window.py` `mouseMoveEvent` and `mousePressEvent` annotated with `QMouseEvent`.
- **Sprint H complete** (`EditorStack`). 2026-11-15.
  - `EditorLayoutSpec` (LEAF/SPLIT/STACK) with `stack(...)` constructor and `EditorStackOrientation`.
  - `EditorStack` widget + `EditorStackSwitcher` (compact, dark-styled, not a `QTabWidget`).
  - `AreaLayoutRenderer` materializes the N-ary tree (`_materialize_tree`, `_materialize_split`, `_materialize_stack`).
  - `LayoutBuilder` collects `editor_ids` recursively and propagates the spec to the Area.
  - `Area` exposes `editor_layout_spec` / `set_editor_layout_spec()`.
  - `AreaWidget` forwards `IconProvider` to the renderer and disposes the `EditorStack` before detaching content widgets.
  - Backward-compatibility shim at `specs/editor_layout_spec.py`.
  - `PlaceholderEditor` moved to `src/cranioz/ui/editors/placeholder_editor.py` (public).
  - `debug_workspace.py` updated to use a `STACK` `ModuleUISpec`.
  - 6 `EditorLayoutSpec` tests + 4 `EditorStack` tests + 1 `STACK` integration test.
  - `tests/unit/ui/workspace/specs/test_editor_layout_spec.py` removed (redundant).
  - `test_no_hardcoded_appearance.py` updated with `placeholder_editor.py` (1 literal) and `editor_stack.py` (7 literals).
  - `ruff check .` clean, `ruff format` clean, `mypy src` clean, `pytest` 1633 passing.

### 2.3 Implementation plan

- `implementation_plan.md` is the current roadmap. It defines 11 phases.
- Phase 2 is now complete (`✅ Implemented`).
- Phase 3 is the next major implementation phase. Blockers: `ProjectIndex` (Sprint I), coordinated deletion (Sprint J), async loading (Sprint K), Professional module (Sprint L).
- **Sprint H is complete.** The `Implementation Plan` §5.1 and §6 should be updated to mark Sprint H as `✅ Complete` and Phase 2 as `✅ Implemented`.

---

## 3. What is missing — by phase

### 3.1 Phase 1 — Contracts, Core Domain & i18n — ✅ Complete

Unchanged from prior versions. Phase 1 is closed.

---

### 3.2 Phase 2 — Workspace Engine & Icons — ✅ Complete

All Sprint E, F, G, H deliverables are complete. Phase 2 is closed.

#### 3.2.1 `ThemeService` + `ThemeCompiler` + tokens (Sprint E) — ✅ Complete

Unchanged from prior versions. Block 5.5 extended the QSS with Workspace Area styling and splitter handle width.

#### 3.2.2 `IconProvider` + `UnicodeIconProvider` (Sprint F) — ✅ Complete

Catalog now 70 icons (60 canonical + 6 shell-specific + 4 window controls). Unchanged otherwise.

#### 3.2.3 `AreaLayoutRenderer` (Sprint G) — ✅ Complete

Delivered:

- `AreaLayoutSpec` with `SINGLE`, `SPLIT`, and `STACK`.
- `AreaLayoutRenderer._resolve_spec()` returns `SINGLE` for one Editor and `SPLIT` for multiple.
- `STACK` raises `NotImplementedError` until Sprint H.
- `AreaLayoutRenderer` validates `spec.editor_ids` against the Area's Editors.
- `_build_editor_container` applies `Expanding` on the container and `Ignored` on the content (preserves the percentage-based layout computed by the Workspace).
- 6 unit tests for `AreaLayoutSpec` + 1 integration test for the `STACK` failure mode.

#### 3.2.4 `EditorStack` (Sprint H) — ✅ Complete

**Depends on:** Sprint G (complete).

Delivered:

- `EditorLayoutSpec.stack([...])` with `EditorStackOrientation`.
- `EditorStack` widget (QStackedWidget + `EditorStackSwitcher`, not a `QTabWidget`).
- `AreaLayoutRenderer._materialize_tree()` (replaces the old `_render_split`-only path and supports LEAF/SPLIT/STACK).
- `LayoutBuilder` collects `editor_ids` recursively.
- `Area` exposes `editor_layout_spec` / `set_editor_layout_spec()`.
- `AreaWidget` forwards `IconProvider` and disposes the `EditorStack`.
- Backward-compatibility shim at `specs/editor_layout_spec.py`.
- `debug_workspace.py` visual validation (confirmed in the console + screenshot).
- 6 `EditorLayoutSpec` tests + 4 `EditorStack` tests + 1 `STACK` integration test.

**Phase 2 is complete.** All contract tests pass, CI is green, and the visual validation is confirmed.

---

### 3.3 Phase 3 — Project, Home Page & Professional Module

**Goal:** close Phase 3 formally. Blockers: `ProjectIndex` (Sprint I), coordinated deletion (Sprint J), async loading (Sprint K), Professional module (Sprint L).

#### 3.3.1 `ProjectIndex` (Sprint I) — 🚧 Pending

Deliverables:

- `ProjectIndex` interface (`add`, `remove`, `lookup`, `list`).
- `InMemoryProjectIndex`.
- `FilesystemProjectIndex`.
- `ProjectCatalog` consumes `ProjectIndex` instead of scanning the filesystem directly.
- Contract tests: add/remove/lookup/list, concurrent access, cache invalidation.

#### 3.3.2 Coordinated deletion (Sprint J) — 🚧 Pending

Deliverables:

- `ProjectManager.delete_project` coordinates `ProjectCatalog` → `ProjectIndex` → `FilesystemProjectRepository`.
- Rollback when any step fails.
- External source data (External Reference mode) is never removed by project deletion.
- Contract tests.

#### 3.3.3 Async loading (Sprint K) — 🚧 Pending

Deliverables:

- `HomePage` loads projects and flows via `TaskManager`.
- No blocking I/O in `MainWindow.__init__`.
- `HomePage.refresh()` does not block the GUI thread.
- Rollback if `Workspace` creation fails after project open.
- Regression tests.

#### 3.3.4 Professional module (Sprint L) — 🚧 Pending

Deliverables:

- `ProfessionalEditor` registered in `EditorRegistry`.
- `ModuleUISpec` for the Professional module.
- Settings integration (`professional.*` keys).
- Tests.

#### 3.3.5 Test stub documentation — 🚧 Pending

- `tests/infrastructure/i18n/` (4 stubs) and `tests/infrastructure/scene/test_scene_query_adapter.py` are intentionally empty. They reserve the contract for the missing granular unit tests of `infrastructure/i18n/` and `infrastructure/scene/`. End-to-end coverage already exists in `tests/integration/i18n/`.
- Add `README.md` to `tests/infrastructure/i18n/` explaining the contract, and a `# TODO(sprint-i18n)` line to each stub. Same for `tests/infrastructure/scene/`.

**Deferred to Phase 8:**

- SQLite `ProjectIndex` backend.
- Recent Projects.
- Background disk reconciliation.

---

### 3.4 Phase 4 — Scene & Visualization (deferred until Phases 2–3 close)

Phase 4 remains the active implementation phase after Phases 2–3 close. The following items from the original Phase 4 scope are now partially complete:

- `TomographyEditor` materializes Editor-level Toolbars (Block 5).
- `ViewLayoutRenderer` `ACTIVE_ONLY` policy is wired (Block 4).
- `Workspace` applies percentage-based sizes and respects the Top Bar minimum (Block 5.5).
- The application shell is frameless with custom drag and native resize (Sprint M).
- `AreaLayoutRenderer` is separate from `LayoutRenderer` (Sprint G) and materializes the N-ary `EditorLayoutSpec` (Sprint H).

Key Phase 4 items still pending:

- Unified Import Dialog (§4.3.4 of the Implementation Plan).
- `ViewerLayoutManager` (dynamic grids: 1×1, 2×2, 3×3, editable up to 6×4, panoramic, ATM).
- 2D and 3D tools (brightness/contrast, pan, zoom, HU probe, ROI, nerve drawing, distance/angle, crosshair, ruler, LUT selection, background color, animation, thumbnail).
- Viewer status indicators (active view badge, orientation badge, inactive state).
- Clinical transfer functions (HU-based presets).
- Real module loading.
- End-to-end Editor workflows.

---

## 4. Recommended execution sequence

| Sprint | Phase | Deliverable | Status | Depends on |
|---|---|---|---|---|
| B | 1 | i18n contract and catalogs | ✅ Complete | — |
| C | 1 | `EditorContext` propagation | ✅ Complete | B, E, F |
| E | 2 | `ThemeService`, `ThemeCompiler`, tokens | ✅ Complete | — |
| F | 2 | `IconProvider`, `UnicodeIconProvider`, glyph migration | ✅ Complete | E |
| — | — | 2026-11-13 cleanup | ✅ Complete | — |
| 1 | 2 | Toolbar polish | ✅ Complete | — |
| 2 | 2 | `Toolbar.set_active` / `set_expanded` / chevron | ✅ Complete | 1 |
| 3 | 2 | `Editor._EditorSignals` + `Editor.set_active_view` | ✅ Complete | — |
| 4 | 2 | `ViewLayoutRenderer` event filter + `ACTIVE_ONLY` | ✅ Complete | 3 |
| 5 | 2 | `TomographyEditor` wires the active-View flow | ✅ Complete | 4 |
| 5.5 | 2 | Percentage-based Area layout, QSS Areas, TopOverlay minimum width | ✅ Complete | 4, 5 |
| 5.6 | 2 | Window controls in ExtrasSegment; `closeEvent` with confirmation | ✅ Complete | 5.5 |
| 5.6.1 | 2 | Window controls in HomeTopBar; end-to-end tests | ✅ Complete | 5.6 |
| M | 2 | Frameless window, drag support, native resize | ✅ Complete | E, F |
| 6 | 2 | `debug_workspace.py` final visual validation | ✅ Complete | 5, 5.5, 5.6, 5.6.1, M |
| G | 2 | `AreaLayoutRenderer` (inter-Area vs intra-Area split) | ✅ Complete | 6 |
| **H** | **2** | **`EditorStack`** | **✅ Complete** | **G** |
| I | 3 | `ProjectIndex` | 🚧 Pending | — |
| J | 3 | Coordinated deletion | 🚧 Pending | I |
| K | 3 | Async loading | 🚧 Pending | I, J |
| L | 3 | Professional module | 🚧 Pending | C, E, F |

**Next work item:** Phase 3 begins. The user must choose between:

- **Refactor the Editor package layout** (the `ui/editors/central`, `ui/editors/left`, etc. structure discussed) to prepare the "Add Editor" catalog.
- **Sprint I (`ProjectIndex`)** — start Phase 3.

**Note on ordering:** Blocks 5.5/5.6/5.6.1, Sprint M, Block 6, Sprint G, and Sprint H are complete. Sprints I–L belong to Phase 3 and can be executed in any order once the editor package refactor decision is made.

---

## 5. Definition of Done for this handoff

This handoff is complete when:

1. `implementation_plan.md` reflects Phases 2–3 status with Blocks 4–6, 5.5–5.6.1, Sprint M, Sprint G, and Sprint H marked `✅ Complete`.
2. `docs/adr/ADR-0014-widget-toolkit-selection.md` is committed.
3. `docs/architecture/appearance/` is consolidated.
4. The 2026-11-13 cleanup is committed.
5. Blocks 1–6, 5.5–5.6.1, Sprint M, Sprint G, and Sprint H are committed.
6. The `test_no_hardcoded_appearance.py` duplicate under `tests/unit/architecture/` is resolved.
7. The current test count and coverage are recorded in §2.2 (1633 passing, 2 skipped).
8. The next conversation starts with either the **Editor package refactor** or **Sprint I (`ProjectIndex`)**.

---

## 6. What is not in this handoff

Unchanged from prior versions, with the following additions:

- Viewer status indicators (active view badge, orientation badge) — Phase 4.5.
- Dynamic grids (1×1, 2×2, 3×3, editable) — Phase 4.5 (`ViewerLayoutManager`).
- 2D tools and clinical transfer function presets — Phase 4.5.
- Persistence of user-dragged splitter sizes — Phase 4.5 (ADR-0010).
- Real toolbar icons (currently `tool.log` and `tool.toggle` placeholders) — Phase 4.5.
- `window_restore` icon in `UnicodeIconProvider` — Phase 4.5 (icon-set task).
- Drop shadow under the frameless window — optional, deferred (would require `WA_TranslucentBackground` + an inner container with 10px margins).
- `stl.py` migration from `GetData()` to `ExportLegacyFormat()` — Phase 4.5 (P2; see §7).
- `pyproject.toml` `ignore_missing_imports` entries (`cupy.*`, `cv2.*`, `numba.*`, `reportlab.*`, `scipy.*`) — cleanup task, no functional impact.
- `EditorStack` styling literals (7 colors) — Sprint F+ (tracked in `_KNOWN_DEBT_FILES`).
- `PlaceholderEditor` styling literal (1 color) — Sprint F+ (tracked in `_KNOWN_DEBT_FILES`).

---

## 7. Known issues and their status

| Issue | Status | Reference |
|---|---|---|
| DICOM visualization bug (voxel ordering) | ✅ Resolved 2026-11-06 | `implementation_plan.md` §10.5 |
| ADR-0003 legacy | ✅ Superseded by ADR-0014 | `docs/adr/ADR-0014-widget-toolkit-selection.md` |
| `steps_panel` overlay | ✅ Removed; replaced by `WorkflowBreadcrumb` (Phase 5) | `implementation_plan.md` §10.4 |
| i18n contract (Sprint B) | ✅ Complete | This document §3.1 |
| Shell hardcoded strings | ✅ Guarded by `test_no_hardcoded_strings_in_shell_widgets.py`; `_WHITELIST` is empty | `tests/architecture/` |
| `test_modules_segment.py` duplicate | ✅ Rewritten to test `ModulesSegment` | `tests/unit/ui/workspace/structure/` |
| Appearance foundation (Sprint E) | ✅ Complete | This document §3.2.1 |
| Hardcoded colors in shell | ✅ Guarded by `test_no_hardcoded_appearance.py`; `_KNOWN_DEBT_FILES` includes `mock/mpr.py` (debug-only), `placeholder_editor.py` (1), and `editor_stack.py` (7) | `tests/architecture/` |
| Icon provider (Sprint F) | ✅ Complete (70 icons) | This document §3.2.2 |
| Glyph migration (Sprint F) | ✅ Complete | `tests/architecture/` |
| `EditorContext` propagation (Sprint C) | ✅ Complete | This document §3.1 |
| `correlation_id` propagation | 🚧 Not yet propagated by `Workspace`; tracked as debt | `implementation_plan.md` §3.1.2 |
| `event_subscription` in the contract test | 🚧 Passed as `None`; dedicated test pending | `tests/integration/ui/workspace/test_editor_context_propagation.py` |
| Widget migration to tokens (12 literals in 4 files + 8 new literals in Sprint H) | 🚧 Tracked in `_KNOWN_DEBT_FILES` | `test_no_hardcoded_appearance.py` |
| Toolbar polish (Block 1) | ✅ Complete (8 tests) | This document §2.2 |
| `Toolbar.set_active` / `set_expanded` / chevron (Block 2) | ✅ Complete (11 tests) | This document §2.2 |
| `Editor._EditorSignals` + `Editor.set_active_view` (Block 3) | ✅ Complete (12 tests) | `tests/unit/ui/editors/test_editor_active_view.py` |
| `ACTIVE_ONLY` policy wired (Block 4) | ✅ Complete (12 tests) | `tests/unit/ui/editors/test_view_layout_renderer_active_only.py` |
| `TomographyEditor` materializes Editor-level Toolbars (Block 5) | ✅ Complete (7 tests) | `tests/integration/ui/editors/test_tomography_editor_active_view.py` |
| Percentage-based Area layout (Block 5.5) | ✅ Complete | This document §2.2 |
| `TopOverlay.minimum_width()` dynamic | ✅ Complete | This document §2.2 |
| Window controls in ExtrasSegment (Block 5.6) | ✅ Complete (19 tests) | `tests/unit/ui/workspace/structure/test_extras_segment.py` |
| Window controls in HomeTopBar (Block 5.6.1) | ✅ Complete (11 + 3 end-to-end) | `tests/unit/ui/home/widgets/test_home_top_bar.py`, `test_home_page.py`, `test_main_window.py` |
| `closeEvent` with confirmation and teardown | ✅ Complete (3 tests) | `tests/integration/ui/test_main_window.py` |
| Frameless window + native chrome + drag + native resize (Sprint M) | ✅ Complete (3 integration tests) | `tests/integration/ui/test_main_window.py` |
| `debug_workspace.py` visual validation (Block 6) | ✅ Complete | This document §2.2 |
| `AreaLayoutRenderer` intra-Area `Expanding` | ✅ Complete (Block 5.5 correction 6) | `area_layout_renderer.py` |
| `AreaLayoutRenderer` (Sprint G) | ✅ Complete (7 tests; `AreaLayoutSpec` with SINGLE/SPLIT/STACK) | This document §3.2.3 |
| `EditorStack` (Sprint H) | ✅ Complete (6 `EditorLayoutSpec` tests + 4 `EditorStack` tests + 1 `STACK` integration test) | This document §3.2.4 |
| `ProjectIndex` (Sprint I) | 🚧 Pending | This document §3.3.1 |
| Coordinated deletion (Sprint J) | 🚧 Pending | This document §3.3.2 |
| Async loading (Sprint K) | 🚧 Pending | This document §3.3.3 |
| Professional module (Sprint L) | 🚧 Pending | This document §3.3.4 |
| Viewer status badges (A/C/S/3D) | 🚧 Phase 4.5 | `Implementation Plan` §4.5 |
| Dynamic grids (1×3, 3×3, 2×3) | 🚧 Phase 4.5 (`ViewerLayoutManager`) | `Implementation Plan` §4.5 |
| Persistence of user-dragged sizes | 🚧 Phase 4.5 (ADR-0010) | `Implementation Plan` §5 |
| Maximize/restore icon toggle in window controls | ✅ Delivered in Sprint M | This document §2.2 |
| `window_restore` icon asset | ✅ Present in `UnicodeIconProvider` (70 icons) | This document §2.2 |
| `stl.py` `GetData()` deprecation | 🚧 Reverted to `GetData()` with `# TODO(vtk-10)`; `ExportLegacyFormat()` migration deferred to Phase 4.5 | `stl.py`, `Consolidation Plan` §10.2 |
| `pyproject.toml` unused `ignore_missing_imports` | 🚧 Cleanup task, no functional impact | `pyproject.toml` |

---

## 8. Immediate action items

Sprint H is complete. Phase 2 is closed. Before starting Phase 3:

1. Commit the Sprint H delivery (code, tests, and