# Next Steps

**Document type:** Action plan and handoff
**Status:** Active
**Scope:** Immediate next work items after Blocks 1–6, 5.5–5.6.1, and Sprint M (frameless window)
**Last updated:** 2026-11-15

---

## 1. Context

The VTK rendering pipeline is validated end-to-end. The DICOM visualization bug was resolved on 2026-11-06. The voxel-ordering contract is documented and enforced by regression tests. The imaging pipeline uses `int16` (`VTK_SHORT`) as the production scalar type, with the direction matrix applied and confirmed.

The appearance architecture has been decided. `docs/architecture/appearance/` is the canonical specification. ADR-0014 registers the toolkit decision (Qt Widgets + QSS modular + Design Tokens in Python, not QML). The DICOM path, the 3D viewport, the MPR view, and the workspace layout are operational and covered by a growing test suite.

**Current test baseline: 1625 passing, 0 failed, 0 errors, 2 skipped (Block 5.5 intencionais).** A baseline anterior ao cleanup de 2026-11-13 era 1528 passing, 88% coverage. Os 9 warnings restantes são todos de `vtkCellArray.GetData` (deprecação do VTK 9.6+; remoção planejada para o VTK 10), rastreados em §7.

Sprint B (i18n) is complete: the shell — `MainWindow`, the Home Page tree, the three Top Bar segments, and the Workspace placeholder editor — resolves user-facing strings through the `TranslationService`. `tests/architecture/test_no_hardcoded_strings_in_shell_widgets.py` guards against regressions.

Sprint E (appearance foundation) is complete: `ThemeService` and `ThemeCompiler` are implemented, the 47 canonical design tokens are defined for `DARK` and `LIGHT`, the `cranioz.infrastructure.settings` package provides typed, versioned, and atomically written user settings, and `AppPathResolver.user_settings_path()` resolves the user settings file. The theme is applied at boot before the first window. The Modern Dark palette is applied, the QSS covers tables, headers, scrollbars, buttons, inputs, labels, cards, `StartButton`, `FlowRow`, and now the Workspace Areas (Block 5.5). `tests/architecture/test_no_hardcoded_appearance.py` guards against new hardcoded colors and freezes the remaining debt.

Sprint F (icons) is complete: `IconState`, `IconProvider` Protocol and `UnicodeIconProvider` are implemented with the closed icon catalog (now 70 icons: 60 canonical + 6 shell + 4 window controls); the provider is injected into `MainWindow`, `Workspace`, `HomePage`, the three Top Bar segments, `Toolbar`, `StartButton`, and `FlowRow`. The five icon contract tests pass.

Sprint C (EditorContext propagation) is complete: `EditorContext` now carries `theme_service` and `icon_provider` alongside the existing seven fields, and `Workspace.load_spec` passes the complete set through `LayoutBuilder`'s `shared_context`. **Phase 1 is closed.**

The **2026-11-13 cleanup** removed a substantial amount of dead code (two source files, one package, one duplicated adapter, ten obsolete debug scripts), migrated `QImage.mirrored` to `QImage.flipped`, and raised the `PySide6` minimum to `>=6.9`.

**Blocks 1–3 are complete** (Toolbar polish, `set_active`/`set_expanded`/chevron, `Editor.set_active_view`).

**Block 4 is complete** (`ViewLayoutRenderer` event filter + `ACTIVE_ONLY` wiring). 12 new tests.

**Block 5 is complete** (`TomographyEditor` materializes Editor-level Toolbars + 2×2 end-to-end). 7 new tests.

**Blocks 5.5, 5.6, 5.6.1 are complete** (`Workspace` percentage-based Area layout with rounded corners and gap; window controls in `ExtrasSegment` and `HomeTopBar`; `closeEvent` with confirmation). These add the visual layout polish required before the final Phase 2 visual validation.

**Sprint M is complete (frameless window + native chrome + drag + native resize).** The `MainWindow` now removes the native Windows title bar, wraps the `QStackedWidget` in a `_central_container` with 4px margins, and supports native resizing via `windowHandle().startSystemResize(edges)` and dragging via `WindowDragFilter` on the custom top bars. 3 new integration tests. Suite: 1625 passed, 2 skipped.

**Block 6 is complete (debug_workspace.py visual validation).** The script `scripts/debug/ui/workspace/debug_workspace.py` was run end-to-end with Blocks 4–6, 5.5–5.6.1, and Sprint M applied. The visual matches the Prototipagem_UI_17 reference with the frameless window (drag, resize, maximize, minimize, close). Committed.

**Next work item:** Sprint G — `AreaLayoutRenderer`. It is the next Phase 2 deliverable after Block 6. Before starting Sprint G, close the two small pending items in §8 (Block 5.5 correction 6 and the `"pt-BR-BR"` locale bug).

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

- **Test baseline after Blocks 1–6, 5.5–5.6.1, and Sprint M: 1625 passing, 2 skipped (Block 5.5 intencionais).**
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
- **Blocks 1–3 complete** (Toolbar polish, `set_active`/`set_expanded`/chevron, `Editor.set_active_view`). See §2.2 of prior versions for the full delivery list.
- **Block 4 complete (ViewLayoutRenderer event filter + ACTIVE_ONLY).**
  - `View.activation_widget()` default returns `content_widget()`.
  - `Viewport3DView.activation_widget()` returns the `QVTKRenderWindowInteractor`; `content_widget()` calls `_ensure_pipeline()` so the interactor exists before the filter installs.
  - `ViewLayoutRenderer` gained an optional `editor` parameter; installs an activation filter per View (on `activation_widget()`), indexes Toolbars per View (`_toolbars_by_view`), and connects `editor.active_view_changed` to `_on_active_view_changed`.
  - `_ViewActivationFilter` forwards `MouseButtonPress` and `FocusIn` to `editor.set_active_view` and returns `False` (never consumes the event).
  - `clear_cache()` removes filters from the correct target widget, clears `_view_filters`, `_view_filter_targets`, `_toolbars_by_view`.
  - Toolbars `ACTIVE_ONLY` start inactive in `_build_view_container` (matching `Editor.active_view_id is None` at start).
  - 12 tests in `tests/unit/ui/editors/test_view_layout_renderer_active_only.py`. `test_viewport_3d_view.py::test_viewport_3d_content_widget_returns_container` updated to reflect eager pipeline creation.
- **Block 5 complete (TomographyEditor materializes Editor-level Toolbars).**
  - `TomographyEditor.content_widget()` wraps the View grid with the Editor-level Toolbars via `_wrap_with_editor_toolbars` (LEFT `ALWAYS` + RIGHT `COLLAPSIBLE`).
  - `_editor_toolbars` list; `dispose()` clears it.
  - 7 tests in `tests/integration/ui/editors/test_tomography_editor_active_view.py`.
- **Block 5.5 complete (Workspace percentage-based Area layout).**
  - `Workspace._LEFT_RATIO = 0.20`, `_RIGHT_RATIO = 0.25`, `_BOTTOM_RATIO = 0.20`.
  - `Workspace._apply_default_splitter_sizes()` computes sizes as percentages (Central = fill), never letting the Central Area drop below `TopOverlay.minimum_width()`. Lateral sizes shrink proportionally when needed.
  - Called from `load_spec`, `set_area_visible`, `resizeEvent`, `showEvent`, `_hide_lateral_areas_by_default`, and via the `ModulesSegment.modules_changed` signal wired in `MainWindow`.
  - `TopOverlay.minimum_width()` is dynamic (sum of the three segments' `sizeHint`s), replacing the previous 380px constant.
  - `TopOverlay.reposition()` respects bounds; no longer overflows the Central Area.
  - `AreaWidget.refresh()` returns early when the Area model is hidden, preventing placeholder rendering in hidden Areas.
  - `_build_empty_placeholder()` uses `WA_TranslucentBackground` so the QSS background shows through.
  - Debug Editors `MockPosicaoEditor`, `MockObjetosEditor`, `MockConsoleEditor`, `MockMPREditor` added under `src/cranioz/ui/editors/mock/` (used by `scripts/debug/ui/workspace/debug_layout.py`).
- **Block 5.6 complete (window controls in ExtrasSegment).**
  - `ExtrasSegment.minimize_requested`, `maximize_requested`, `close_requested`.
  - 3 new buttons, 28px wide, icons via `IconProvider`.
  - `MainWindow._wire_top_bar_segments` connects the 3 signals.
  - `MainWindow._on_window_maximize_requested` toggles `showMaximized`/`showNormal`.
  - `MainWindow.closeEvent` asks for confirmation when a project is open, then tears it down via `_close_active_project` (extracted from `_on_home_clicked`).
  - `test_extras_segment.py` — 19 tests.
  - `test_main_window.py` — 3 tests for `closeEvent`.
- **Block 5.6.1 complete (window controls in HomeTopBar).**
  - `HomeTopBar.minimize_requested`, `maximize_requested`, `close_requested`.
  - 3 new buttons, 28px wide, icons via `IconProvider`.
  - `HomePage` forwards the 3 new signals.
  - `MainWindow._connect_home_signals` connects them.
  - `test_home_top_bar.py` +5 tests, `test_home_page.py` +3 tests, `test_main_window.py` +3 end-to-end tests.
- **Sprint M complete (frameless window + native chrome).**
  - `MainWindow` now sets `Qt.FramelessWindowHint` and uses a `_central_container` with `setContentsMargins(4, 4, 4, 4)` to create a resize dead zone.
  - `WindowDragFilter` installed on `HomeTopBar` and `Workspace`'s `TopOverlay`; allows dragging the window by clicking on the custom top bars. Ignores `QPushButton` clicks.
  - Native resize via `windowHandle().startSystemResize(edges)` in `mousePressEvent`; dynamic cursor in `mouseMoveEvent`.
  - `_update_maximize_icon(restore=...)` keeps the maximize/restore icon in sync between `HomeTopBar` and `ExtrasSegment`.
  - 3 new integration tests in `test_main_window.py`: `test_main_window_is_frameless`, `test_main_window_drag_filter_is_installed`, `test_main_window_central_container_has_margins`.
  - Known limitation: `window_restore` may not be present in the `IconProvider` catalog yet; tracked as a future icon-set task.
- **Block 6 complete (debug_workspace.py visual validation).**
  - The script was run end-to-end with Blocks 4–6, 5.5–5.6.1, and Sprint M applied.
  - Visual matches the Prototipagem_UI_17 reference with the frameless window (drag, resize, maximize, minimize, close).
  - Committed.

### 2.3 Implementation plan

- `implementation_plan.md` is the current roadmap. It defines 11 phases.
- Phase 4 is marked as the next major implementation phase, with the following items already complete: voxel ordering, `int16`, direction matrix, `Viewport3DView.set_volume(Volume)`, STL path validation, DICOM path validation.
- **Phase 2 has advanced further than the plan reflects.** The frameless window work (Sprint M) and the resize/drag support are additional Phase 2 deliverables not yet recorded in `implementation_plan.md`. The plan update should be applied in the same commit as the Sprint M delivery.

---

## 3. What is missing — by phase

### 3.1 Phase 1 — Contracts, Core Domain & i18n — ✅ Complete

Unchanged from prior versions. Phase 1 is closed.

---

### 3.2 Phase 2 — Workspace Engine & Icons

**Goal:** close Phase 2 formally. Blockers: `AreaLayoutRenderer` (Sprint G) and `EditorStack` (Sprint H).

#### 3.2.1 `ThemeService` + `ThemeCompiler` + tokens (Sprint E) — ✅ Complete

Unchanged from prior versions. Block 5.5 extended the QSS with Workspace Area styling and splitter handle width.

#### 3.2.2 `IconProvider` + `UnicodeIconProvider` (Sprint F) — ✅ Complete

Catalog now 70 icons (60 canonical + 6 shell-specific + 4 window controls). Unchanged otherwise.

#### 3.2.3 `AreaLayoutRenderer` (Sprint G) — 🚧 Pending

Deliverables:

- `AreaLayoutRenderer` that separates inter-Area from intra-Area layout. **Partially complete**: the file exists (`area_layout_renderer.py`) and currently delegates the intra-Area layout to a single `_build_editor_container` per Editor. The `Expanding` policy must be applied to the container (Block 5.5 correction 6, pending) so the Editor fills the Area.
- `AreaWidget` delegates to `AreaLayoutRenderer`.
- No visible behavior change for the single-Editor case.
- Regression tests.

#### 3.2.4 `EditorStack` (Sprint H) — 🚧 Pending

**Depends on:** Sprint G.

Deliverables:

- `EditorLayoutSpec.stack([...])`.
- `EditorStack` widget (tabs per Leaf).
- Single-Editor case remains unchanged.
- Tests for tab switching, editor lifecycle, dispose.

**Phase 2 is complete when:** `AreaLayoutRenderer` and `EditorStack` are implemented, contract tests pass, CI is green, and the visual validation is confirmed (already confirmed in Block 6).

---

### 3.3 Phase 3 — Project, Home Page & Professional Module

Unchanged from prior versions. Blockers: `ProjectIndex`, coordinated deletion, async loading, Professional module. i18n unit-test stubs documented (see prior §3.3.5).

---

### 3.4 Phase 4 — Scene & Visualization (deferred until Phases 2–3 close)

Phase 4 remains the active implementation phase after Phases 2–3 close. The following items from the original Phase 4 scope are now partially complete:

- `TomographyEditor` materializes Editor-level Toolbars (Block 5).
- `ViewLayoutRenderer` `ACTIVE_ONLY` policy is wired (Block 4).
- `Workspace` applies percentage-based sizes and respects the Top Bar minimum (Block 5.5).
- The application shell is frameless with custom drag and native resize (Sprint M).

Key Phase 4 items still pending:

- Unified Import Dialog (§4.3.4).
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
| **G** | **2** | **`AreaLayoutRenderer` (inter-Area vs intra-Area split)** | **⏳ Next** | **6** |
| H | 2 | `EditorStack` | 🚧 Pending | G |
| I | 3 | `ProjectIndex` | 🚧 Pending | — |
| J | 3 | Coordinated deletion | 🚧 Pending | I |
| K | 3 | Async loading | 🚧 Pending | I, J |
| L | 3 | Professional module | 🚧 Pending | C, E, F |

**Next work item:** Sprint G — `AreaLayoutRenderer`. Before starting, close the two pending items in §8 (Block 5.5 correction 6 and the `"pt-BR-BR"` locale bug).

**Note on ordering:** Blocks 5.5/5.6/5.6.1, Sprint M, and Block 6 are complete. Sprint G (`AreaLayoutRenderer`) is the next Phase 2 deliverable. Sprint H depends on G. Sprints I–L belong to Phase 3.

---

## 5. Definition of Done for this handoff

This handoff is complete when:

1. `implementation_plan.md` reflects Phases 2–3 status with Blocks 4–6, 5.5–5.6.1, and Sprint M marked `✅ Implemented`.
2. `docs/adr/ADR-0014-widget-toolkit-selection.md` is committed.
3. `docs/architecture/appearance/` is consolidated.
4. The 2026-11-13 cleanup is committed.
5. Blocks 1–6, 5.5–5.6.1, and Sprint M are committed.
6. The `test_no_hardcoded_appearance.py` duplicate under `tests/unit/architecture/` is resolved.
7. The current test count and coverage are recorded in §2.2 (1625 passing, 2 skipped).
8. The next conversation starts with **Sprint G (`AreaLayoutRenderer`)**.

---

## 6. What is not in this handoff

Unchanged from prior versions, with the following additions:

- Viewer status indicators (active view badge, orientation badge) — Phase 4.5.
- Dynamic grids (1×1, 2×2, 3×3, editable) — Phase 4.5 (`ViewerLayoutManager`).
- 2D tools and clinical transfer function presets — Phase 4.5.
- Persistence of user-dragged splitter sizes — Phase 4.5 (ADR-0010).
- Real toolbar icons (currently `tool.log` and `tool.toggle` placeholders) — Phase 4.5.
- `closeEvent` toggle of the maximize icon (`window_maximize` ↔ `window_restore`) — **Delivered in Sprint M** (icon toggle is functional; catalog asset may still be missing).
- `window_restore` icon in `UnicodeIconProvider` — Phase 4.5 (icon-set task).
- Drop shadow under the frameless window — optional, deferred (would require `WA_TranslucentBackground` + an inner container with 10px margins).

---

## 7. Known issues and their status

| Issue | Status | Reference |
|---|---|---|
| DICOM visualization bug (voxel ordering) | ✅ Resolved 2026-11-06 | `implementation_plan.md` §10.5 |
| ADR-0003 legacy | ✅ Superseded by ADR-0014 | `docs/adr/ADR-0014-widget-toolkit-selection.md` |
| `steps_panel` overlay | ✅ Removed; replaced by `WorkflowBreadcrumb` (Phase 5) | `implementation_plan.md` §10.4 |
| i18n contract (Sprint B) | ✅ Complete | This document §3.1.1 |
| Shell hardcoded strings | ✅ Guarded by `test_no_hardcoded_strings_in_shell_widgets.py`; `_WHITELIST` is empty | `tests/architecture/` |
| `test_modules_segment.py` duplicate | ✅ Rewritten to test `ModulesSegment` | `tests/unit/ui/workspace/structure/` |
| Appearance foundation (Sprint E) | ✅ Complete | This document §3.2.1 |
| Hardcoded colors in shell | ✅ Guarded by `test_no_hardcoded_appearance.py`; `_KNOWN_DEBT_FILES` now includes `mock/mpr.py` (debug-only mock) | `tests/architecture/` |
| Icon provider (Sprint F) | ✅ Complete (70 icons) | This document §3.2.2 |
| Glyph migration (Sprint F) | ✅ Complete | `tests/architecture/` |
| `EditorContext` propagation (Sprint C) | ✅ Complete | This document §3.1.2 |
| `correlation_id` propagation | 🚧 Not yet propagated by `Workspace`; tracked as debt | `implementation_plan.md` §3.1.2 |
| `event_subscription` in the contract test | 🚧 Passed as `None`; dedicated test pending | `tests/integration/ui/workspace/test_editor_context_propagation.py` |
| Widget migration to tokens (12 literals in 4 files) | 🚧 Tracked in `_KNOWN_DEBT_FILES` | `test_no_hardcoded_appearance.py` |
| Toolbar polish (Block 1) | ✅ Complete (8 tests) | This document §2.2 |
| `Toolbar.set_active` / `set_expanded` / chevron (Block 2) | ✅ Complete (11 tests) | This document §2.2 |
| `Editor._EditorSignals` + `Editor.set_active_view` (Block 3) | ✅ Complete (12 tests) | `tests/unit/ui/editors/test_editor_active_view.py` |
| `ACTIVE_ONLY` policy wired (Block 4) | ✅ Complete (12 tests) | `tests/unit/ui/editors/test_view_layout_renderer_active_only.py` |
| `TomographyEditor` materializes Editor-level Toolbars (Block 5) | ✅ Complete (7 tests) | `tests/integration/ui/editors/test_tomography_editor_active_view.py` |
| Percentage-based Area layout (Block 5.5) | ✅ Complete | This document §2.2 |
| `TopOverlay.minimum_width()` dynamic | ✅ Complete | This document §2.2 |
| Window controls in ExtrasSegment (Block 5.6) | ✅ Complete (19 tests) | `tests/unit/ui/workspace/structure/test_extras_segment.py` |
| Window controls in HomeTopBar (Block 5.6.1) | ✅ Complete (11 tests + 3 end-to-end) | `tests/unit/ui/home/widgets/test_home_top_bar.py`, `test_home_page.py`, `test_main_window.py` |
| `closeEvent` with confirmation and teardown | ✅ Complete (3 tests) | `tests/integration/ui/test_main_window.py` |
| Frameless window + native chrome + drag + native resize (Sprint M) | ✅ Complete (3 integration tests) | `tests/integration/ui/test_main_window.py` |
| `debug_workspace.py` visual validation (Block 6) | ✅ Complete | This document §2.2 |
| `AreaLayoutRenderer` intra-Area `Expanding` | 🚧 **Pending** (Block 5.5 correction 6 not yet applied) | `area_layout_renderer.py` |
| `AreaLayoutRenderer` (Sprint G) | 🚧 Pending | This document §3.2.3 |
| `EditorStack` (Sprint H) | 🚧 Pending | This document §3.2.4 |
| `ProjectIndex` (Sprint I) | 🚧 Pending | This document §3.3.1 |
| Coordinated deletion (Sprint J) | 🚧 Pending | This document §3.3.2 |
| Async loading (Sprint K) | 🚧 Pending | This document §3.3.3 |
| Professional module (Sprint L) | 🚧 Pending | This document §3.3.4 |
| Viewer status badges (A/C/S/3D) | 🚧 Phase 4.5 | `Implementation Plan` §4.5 |
| Dynamic grids (1×3, 3×3, 2×3) | 🚧 Phase 4.5 (`ViewerLayoutManager`) | `Implementation Plan` §4.5 |
| Persistence of user-dragged sizes | 🚧 Phase 4.5 (ADR-0010) | `Implementation Plan` §5 |
| Maximize/restore icon toggle in window controls | ✅ Delivered in Sprint M (icon asset may still be missing) | This document §6 |
| `window_restore` icon asset | 🚧 Phase 4.5 (icon-set task) | This document §6 |

---

## 8. Immediate action items

Before starting Sprint G:

1. Apply the **three remaining Block 5.5 corrections** (if not already applied):
   - `top_overlay.py`: remove `width = max(width, min_width)` from `reposition()`.
   - `tomography/editor.py`: `container.setSizePolicy(Expanding, Expanding)` in `_wrap_with_editor_toolbars`.
   - `area_layout_renderer.py`: `container.setSizePolicy(Expanding, Expanding)` in `_build_editor_container`.
2. Confirm that the 4 window-control icons exist in `UnicodeIconProvider`:
   - `window_minimize`, `window_maximize`, `window_restore`, `window_close`.
3. Update `test_icon_catalog.py` to expect 70 icons.
4. Fix the `"pt-BR-BR"` locale value in `test_loader.py` to `"pt-BR"`.
5. Run `pytest tests\unit\ui\icons\ tests\unit\ui\workspace\structure\ -q` to confirm.
6. Run `pytest tests\integration\ui\test_main_window.py -q` to confirm the 3 Sprint M tests pass.
7. Only then start Sprint G (`AreaLayoutRenderer`).