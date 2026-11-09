# Next Steps

**Document type:** Action plan and handoff
**Status:** Active
**Scope:** Immediate next work items after Sprint C closure
**Last updated:** 2026-11-09

---

## 1. Context

The VTK rendering pipeline is validated end-to-end. The DICOM visualization bug was resolved on 2026-11-06. The voxel-ordering contract is documented and enforced by regression tests. The imaging pipeline uses `int16` (`VTK_SHORT`) as the production scalar type, with the direction matrix applied and confirmed.

The appearance architecture has been decided. `docs/architecture/appearance/` is the canonical specification. ADR-0014 registers the toolkit decision (Qt Widgets + QSS modular + Design Tokens in Python, not QML). The DICOM path, the 3D viewport, the MPR view, and the workspace layout are operational and covered by **1528 passing tests** (0 failed, 0 errors, 0 skipped, 88% coverage).

Sprint B (i18n) is complete: the shell — `MainWindow`, the Home Page tree, the three Top Bar segments, and the Workspace placeholder editor — resolves user-facing strings through the `TranslationService`. `tests/architecture/test_no_hardcoded_strings_in_shell_widgets.py` guards against regressions.

Sprint E (appearance foundation) is complete: `ThemeService` and `ThemeCompiler` are implemented, the 47 canonical design tokens are defined for `DARK` and `LIGHT`, the `cranioz.infrastructure.settings` package provides typed, versioned, and atomically written user settings, and `AppPathResolver.user_settings_path()` resolves the user settings file. The theme is applied at boot before the first window. The Modern Dark palette is applied, the QSS covers tables, headers, scrollbars, buttons, inputs, labels, cards, `StartButton`, and `FlowRow`, and the two Home Page widgets are migrated from inline `setStyleSheet` to `setProperty` + the global QSS. `tests/architecture/test_no_hardcoded_appearance.py` guards against new hardcoded colors and freezes the remaining debt for the widget migration sprint.

Sprint F (icons) is complete: `IconState`, `IconProvider` Protocol and `UnicodeIconProvider` are implemented with the closed 60-icon catalog; the provider is injected into `MainWindow`, `Workspace`, `HomePage`, the three Top Bar segments, `Toolbar`, `StartButton`, and `FlowRow`; the hardcoded glyphs in those widgets are migrated to `provider.icon(...)`; and the `_WHITELIST` in `test_no_hardcoded_strings_in_shell_widgets.py` is empty, meaning the Sprint B glyph debt is paid. The five icon contract tests pass.

Sprint C (EditorContext propagation) is complete: `EditorContext` now carries `theme_service` and `icon_provider` alongside the existing seven fields, and `Workspace.load_spec` passes the complete set through `LayoutBuilder`'s `shared_context`. The contract test `tests/integration/ui/workspace/test_editor_context_propagation.py` asserts that every Editor registered in `EditorRegistry` receives all fields. **Phase 1 is closed.**

The project is ready to close Phases 2 and 3 formally before advancing deeper into Phase 4. This document defines the execution order and the acceptance criteria for each phase.

---

## 2. What is already done

### 2.1 Architecture and decisions

- `docs/architecture/appearance/` contains the canonical appearance specification:
  - `appearance.md`
  - `themes/themes_and_design_tokens.md` (7 categories, 47 tokens, `ThemeMode`, `ThemeName`, `ThemeService`, `ThemeCompiler`, translucency composition)
  - `icons/icons_and_icon_manager.md` (`IconState`, `IconProvider` Protocol, `UnicodeIconProvider` for Phase 2, `SvgIconProvider` for Phase 8, closed 60-icon catalog)
  - `icons/icon_assets_and_visual_standards.md` (SVG format, directory structure, naming, visual standards)
  - `surfaces_and_overlays.md` (Solid, Translucent, Simulated Glass; real blur is not supported)
- ADR-0014 (Widget Toolkit Selection) is written in `docs/adr/ADR-0014-widget-toolkit-selection.md`.
- ADR-0013 (Editor Layout Tree, View Layout Tree, and Toolbar Placement) is accepted.

### 2.2 Code and tests

- **1528 tests passing, 0 failed, 0 errors, 0 skipped, 88% coverage.**
- `ruff check` clean; `ruff format --check` clean.
- `mypy src` clean.
- `VtkImageAdapter` corrected (no transposition, `int16`, direction matrix).
- `Viewport3DView` stabilized (`QTimer` cleanup on `dispose`).
- `MPRView` renders correctly with the Volume direction matrix.
- `MainWindow` registers built-in tools before creating the Workspace.
- **Sprint B (i18n) complete.** The shell resolves every user-facing string through the `TranslationService`:
  - `MainWindow`, `HomePage`, `HomeTopBar`, `CommunitySidebar`, `ProjectTable`, `FlowList`, `FlowRow`, `StartButton`
  - `HomeSegment`, `ModulesSegment`, `ExtrasSegment`
  - `Workspace._PlaceholderEditor`
  - `__main__.py` startup error dialog
  - `tests/architecture/test_no_hardcoded_strings_in_shell_widgets.py` prevents regressions.
- `test_modules_segment.py` was rewritten to test `ModulesSegment` (it previously contained a duplicate of `test_home_segment.py`).
- **Sprint E (appearance foundation) complete.**
  - `cranioz.infrastructure.settings` package: `SettingsService` protocol, `InMemorySettingsService`, `FilesystemSettingsService`, `SettingsStore`, `SettingsMigrator`, `KNOWN_KEYS`, `SettingsError`, `SettingsMigrationError`.
  - `AppPathResolver.user_settings_path()` and `PathsConfig.settings_root` (default `~/.cranioz/Settings/settings.json`).
  - `src/cranioz/ui/theme/tokens.py`: `ThemeMode`, `ThemeName` (`StrEnum`), 8 token dataclasses, 47 canonical tokens for `DARK` and `LIGHT`, `validate_tokens`, `validate_all_themes`, `count_tokens`.
  - `src/cranioz/ui/theme/service.py`: `ThemeService` with `mode()`, `set_mode()`, `theme()`, `tokens()`, `color()`, `dimension()`, `surface_color()`, `icon_name()`, `theme_changed` signal, `SYSTEM` resolution via `QStyleHints.colorScheme()`.
  - `src/cranioz/ui/theme/compiler.py`: `ThemeCompiler` + `CompiledStyles` with surface composition (toolbar, popover, modal_backdrop), typed elevations, QSS emission.
  - Modern Dark palette applied to `DARK_TOKENS`. `feedback_information` kept at `#4A90D9` (spec value) to pass WCAG AA against `background_panel`.
  - Expanded `_build_qss`: tables + headers + scrollbars, `QLineEdit` placeholder and focus, `QComboBox` dropdown, `QLabel` roles, `QFrame` cards, `QMenu`, `QToolTip`, `StartButton` states, `FlowRow` checked/step/separator/arrow.
  - `StartButton` and `FlowRow` migrated from inline `setStyleSheet` to `setProperty` + the global QSS.
  - `__main__.py` boot order: `SettingsService` → `ThemeService` → `apply theme` → `MainWindow`.
  - Test suite grew by 177 tests: `test_service.py` (27), `test_tokens.py` (37), `test_compiler.py` (25), `test_settings_service.py` (27), `test_no_hardcoded_appearance.py` (10), `test_tokens_used.py` (8), `test_tokens_present.py` (2), `test_theme_completeness.py` (12), `test_theme_values.py` (9), `test_contrast.py` (20).
  - Known debt frozen in `_KNOWN_DEBT_FILES`: **12 hardcoded literals across 4 files** (`area_widget.py` 5, `workspace.py` 3, `workspace_spec.py` 1, `presets.py` 3). The budget is now exact (`==`), not an upper bound (`<=`).
- **Sprint F (icons) complete.**
  - `IconState` enum (`DEFAULT`, `HOVER`, `PRESSED`, `SELECTED`, `DISABLED`) in `src/cranioz/ui/icons/state.py`.
  - `IconProvider` Protocol (`icon(name, size, state) -> QIcon`, `text_glyph(name) -> str`, `invalidate_cache() -> None`) in `src/cranioz/ui/icons/provider.py`.
  - `UnicodeIconProvider` with the closed 60-icon catalog in `src/cranioz/ui/icons/unicode.py`.
  - Injection into `MainWindow`, `Workspace`, `HomePage`, the three Top Bar segments, `Toolbar`, `StartButton`, `FlowRow`.
  - Hardcoded glyphs in `TopBar`, `HomeSegment`, `ModulesSegment`, `ExtrasSegment`, `HomePage`, `Toolbar`, `StartButton`, `FlowRow` migrated to `provider.icon(...)`.
  - `_WHITELIST` in `test_no_hardcoded_strings_in_shell_widgets.py` emptied (Sprint B debt paid). The guardrail remains active against new hardcoded glyphs.
  - Contract tests: `test_icon_catalog.py`, `test_icon_fallback.py`, `test_icon_theme.py`, `test_icon_widget_contract.py`, `test_icon_accessibility.py`.
  - Test suite grew from 1508 to 1527 passing (19 new icon tests). The ~150 tests that were failing or in error due to the missing `icon_provider` in `conftest.py` and widget fixtures were fixed.
  - `test_toolbar_resolves_icon_name_via_theme` was renamed to `test_toolbar_resolves_icon_via_icon_provider` and now asserts that `button.icon().isNull() is False`, matching the actual contract (`icon_provider.icon(...)` returns a `QIcon`, not a dynamic property).
- **Sprint C (EditorContext propagation) complete.**
  - `EditorContext` in `src/cranioz/ui/editors/editor_context.py` carries nine fields: `task_manager`, `telemetry`, `correlation_id`, `command_dispatcher`, `scene_query`, `domain_object_store`, `event_subscription`, `translation_service`, `theme_service`, `icon_provider`.
  - `theme_service` and `icon_provider` were added in Sprint C (optional, default `None`, consistent with the other context fields).
  - `Workspace.load_spec` passes the complete set through `LayoutBuilder`'s `shared_context`.
  - `LayoutBuilder` propagates via `EditorContext(**shared)`, with no closed key list, so future context fields flow automatically.
  - `TomographyEditor.initialize` and `MeshDebugEditor.initialize` receive the full context (no change required — they accept the `EditorContext` object).
  - Contract test: `tests/integration/ui/workspace/test_editor_context_propagation.py` asserts every Editor registered in `EditorRegistry` receives the fields.
  - Fields not asserted in the contract test (tracked as debt):
    - `correlation_id`: not yet propagated by `Workspace` (the `Workspace` does not receive it in its `__init__`).
    - `event_subscription`: passed as `None` in the test; a dedicated test should cover it once the `EventBus` exposes a subscription helper suitable for unit tests.
    - `domain_object_store`: not in the Sprint C target set.
- **Test count baseline for future sprints: 1528 passing, 0 failed, 0 errors, 0 skipped, 88% coverage.**

### 2.3 Implementation plan

- `implementation_plan.md` is the current roadmap. It defines 11 phases.
- Phase 4 is marked as the next major implementation phase, with the following items already complete: voxel ordering, `int16`, direction matrix, `Viewport3DView.set_volume(Volume)`, STL path validation, DICOM path validation.

---

## 3. What is missing — by phase

### 3.1 Phase 1 — Contracts, Core Domain & i18n — ✅ Complete

**Status:** ✅ Complete.

#### 3.1.1 Internationalization (Sprint B) — ✅ Complete

Delivered:

- `Locale` value object (`pt_BR`, `en_US`).
- `TranslationService` Protocol (`tr`, `language`, `set_language`).
- `TranslationCatalog` (JSON loader) and `TranslationCatalogRegistry`.
- Concrete `CatalogTranslationService` with `en` fallback.
- `en` and `pt-BR` catalogs covering all currently used keys.
- Injection into `MainWindow`, `Workspace`, `HomePage`; leaf widgets use the singleton `tr(...)`.
- `MainWindow._humanize_translation_key` removed.
- Contract tests: every `name_key` in every `flow.json` resolves; `test_no_hardcoded_strings_in_shell_widgets.py` guards the shell.

#### 3.1.2 `EditorContext` complete (Sprint C) — ✅ Complete

**Depends on:** Sprint E (`theme_service`, ✅ complete), Sprint F (`icon_provider`, ✅ complete).

Delivered:

- `EditorContext` carries the nine fields listed in §2.2.
- `Workspace.load_spec` passes the complete set through `LayoutBuilder`'s `shared_context`.
- `TomographyEditor.initialize` and `MeshDebugEditor.initialize` accept the complete context.
- Contract test: `tests/integration/ui/workspace/test_editor_context_propagation.py`.

#### 3.1.3 Phase 1 tests

- ✅ i18n contract tests.
- ✅ `test_no_hardcoded_strings_in_shell_widgets.py`.
- ✅ `EditorContext` propagation test.

**Phase 1 is complete.** CI is green; the contract test passes.

---

### 3.2 Phase 2 — Workspace Engine & Icons

**Goal:** close Phase 2 formally. Blockers: `AreaLayoutRenderer`, `EditorStack`.

#### 3.2.1 `ThemeService` + `ThemeCompiler` + tokens (Sprint E) — ✅ Complete

See §2.2 (Sprint E entry) for the full delivery list.

#### 3.2.2 `IconProvider` + `UnicodeIconProvider` (Sprint F) — ✅ Complete

See §2.2 (Sprint F entry) for the full delivery list.

#### 3.2.3 `AreaLayoutRenderer` (Sprint G) — 🚧 Pending

Deliverables:

- `AreaLayoutRenderer` that separates inter-Area from intra-Area layout.
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

**Phase 2 is complete when:** `AreaLayoutRenderer` and `EditorStack` are implemented, contract tests pass, and CI is green.

---

### 3.3 Phase 3 — Project, Home Page & Professional Module

**Goal:** close Phase 3 formally. Blockers: `ProjectIndex`, coordinated deletion, async loading, Professional module.

#### 3.3.1 `ProjectIndex` (Sprint I)

Deliverables:

- `ProjectIndex` interface (`add`, `remove`, `lookup`, `list`).
- `InMemoryProjectIndex`.
- `FilesystemProjectIndex`.
- `ProjectCatalog` refactored to consume `ProjectIndex` (instead of scanning the filesystem directly on `list_projects()`).
- Contract tests: add/remove/lookup/list round-trips, concurrent access, cache invalidation.

#### 3.3.2 Coordinated deletion (Sprint J)

**Depends on:** Sprint I.

Deliverables:

- `ProjectManager.delete_project` coordinates `ProjectCatalog` → `ProjectIndex` → `FilesystemProjectRepository`.
- Rollback when any step fails.
- External source data (External Reference mode) is never removed by project deletion.
- Contract tests.

#### 3.3.3 Async loading (Sprint K)

**Depends on:** Sprints I, J.

Deliverables:

- `HomePage` loads projects and flows via `TaskManager`.
- No blocking I/O in `MainWindow.__init__`.
- `HomePage.refresh()` does not block the GUI thread.
- Rollback if `Workspace` creation fails after project open.
- Regression tests: existing project open/close tests continue to pass.

#### 3.3.4 Professional module (Sprint L)

**Depends on:** Sprints C (✅ complete), E (✅ complete), F (✅ complete).

Deliverables:

- `ProfessionalEditor` registered in `EditorRegistry`.
- `ModuleUISpec` for the Professional module.
- Settings integration (`professional.*` keys in `SettingsService`).
- Tests.

**Phase 3 is complete when:** `ProjectIndex`, coordinated deletion, async loading, and the Professional module are implemented, contract tests pass, and CI is green.

---

### 3.4 Phase 4 — Scene & Visualization (deferred until Phases 2–3 close)

Phase 4 remains the active implementation phase after Phases 2–3 close. It is not started in this handoff. See `implementation_plan.md` §4 and §5.1 for the complete scope.

Key Phase 4 items that are **not** in scope for this handoff:

- Unified Import Dialog (§4.3.4).
- `RenderingAdapter`.
- `ViewerLayoutManager`.
- 2D and 3D tools.
- Clinical transfer function presets.
- Real module loading.
- End-to-end Editor workflows.

---

## 4. Recommended execution sequence

The order below respects the dependencies between Phases 2–3.

| Sprint | Phase | Deliverable | Status | Depends on |
|---|---|---|---|---|
| B | 1 | i18n contract and catalogs | ✅ Complete | — |
| C | 1 | `EditorContext` propagation | ✅ Complete | B, E (✅), F (✅) |
| E | 2 | `ThemeService`, `ThemeCompiler`, tokens | ✅ Complete | — |
| F | 2 | `IconProvider`, `UnicodeIconProvider`, glyph migration | ✅ Complete | E |
| G | 2 | `AreaLayoutRenderer` | 🚧 Pending | — |
| H | 2 | `EditorStack` | 🚧 Pending | G |
| I | 3 | `ProjectIndex` | 🚧 Pending | — |
| J | 3 | Coordinated deletion | 🚧 Pending | I |
| K | 3 | Async loading | 🚧 Pending | I, J |
| L | 3 | Professional module | 🚧 Pending | C, E, F |

**Next sprint:** Sprint G — `AreaLayoutRenderer`. It is the next Phase 2 deliverable and is independent of the other open sprints.

**Note on ordering:** Sprints G and I are independent. Sprint G is the next Phase 2 deliverable. Sprint H depends on G; Sprints J and K depend on I; Sprint L depends on C (complete), E (complete), and F (complete).

---

## 5. Definition of Done for this handoff

This handoff is complete when:

1. `implementation_plan.md` reflects Sprint C closed, Phase 1 marked `✅ Implemented`, and Sprint G marked as the next sprint.
2. `docs/adr/ADR-0014-widget-toolkit-selection.md` is committed.
3. `docs/architecture/appearance/` is consolidated:
   - `appearance.md`, `themes/themes_and_design_tokens.md`, `icons/icons_and_icon_manager.md`, `icons/icon_assets_and_visual_standards.md`, `surfaces_and_overlays.md` are the canonical documents.
   - Any remaining placeholder documents reference the corresponding sections of `CranioZ_Appearance_System.md` as the source of truth until they are written.
4. The next conversation starts with **Sprint G (`AreaLayoutRenderer`)**.

---

## 6. What is not in this handoff

The following items are explicitly out of scope for this handoff and belong to Phase 4 or later:

- Unified Import Dialog.
- `RenderingAdapter`.
- `ViewerLayoutManager`.
- 2D and 3D tools.
- Clinical transfer functions.
- Real module loading.
- End-to-end Editor workflows.
- Full Geometry Infrastructure.
- SQLite ProjectIndex (Phase 8).
- Recent Projects (Phase 8).
- `SvgIconProvider` and SVG assets (Phase 8).
- Locale selector UI (Phase 8).
- Complete `pt_BR`/`en_US` catalogs beyond current keys (Phase 8).
- PDF report localization (Phase 8).
- High-contrast theme (future).
- Real background blur (not supported by design).

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
| Hardcoded colors in shell | ✅ Guarded by `test_no_hardcoded_appearance.py` with frozen `_KNOWN_DEBT_FILES` | `tests/architecture/` |
| Icon provider (Sprint F) | ✅ Complete | This document §3.2.2 |
| Glyph migration (Sprint F) | ✅ Complete; `_WHITELIST` is empty in `test_no_hardcoded_strings_in_shell_widgets.py` | `tests/architecture/` |
| `EditorContext` propagation (Sprint C) | ✅ Complete | This document §3.1.2 |
| `correlation_id` propagation through `EditorContext` | 🚧 Not yet propagated by `Workspace`; tracked as debt | `implementation_plan.md` §3.1.2 |
| `event_subscription` in the contract test | 🚧 Passed as `None`; a dedicated test should cover it once `EventBus` exposes a subscription helper | `tests/integration/ui/workspace/test_editor_context_propagation.py` |
| Widget migration to tokens (12 literals in 4 files) | 🚧 Tracked in `_KNOWN_DEBT_FILES` | `test_no_hardcoded_appearance.py` |
| `AreaLayoutRenderer` (Sprint G) | 🚧 Pending | This document §3.2.3 |
| `EditorStack` (Sprint H) | 🚧 Pending | This document §3.2.4 |
| `ProjectIndex` (Sprint I) | 🚧 Pending | This document §3.3.1 |
| Coordinated deletion (Sprint J) | 🚧 Pending | This document §3.3.2 |
| Async loading (Sprint K) | 🚧 Pending | This document §3.3.3 |
| Professional module (Sprint L) | 🚧 Pending | This document §3.3.4 |
| `QImage.mirrored` deprecation | 🚧 Tracked, separate piece | `mpr_viewer/view.py:216` |
| `vtkCellArray.GetData` deprecation | 🚧 Tracked, separate piece | `stl.py:135` |
| Real background blur | ⛔ Not supported by design | `themes/themes_and_design_tokens.md` §6.3 |
| Full Geometry Infrastructure | ⏳ Deferred | `implementation_plan.md` §5.3 |
| SQLite ProjectIndex | ⏳ Deferred to Phase 8 | `implementation_plan.md` §5.3 |

---

## 8. Immediate next action

Begin **Sprint G — `AreaLayoutRenderer`**. The sprint has three parts:

1. Implement `AreaLayoutRenderer` to separate inter-Area from intra-Area layout.
2. Refactor `AreaWidget` to delegate the intra-Area composition to the new renderer.
3. Add regression tests that prove no visible behavior change for the single-Editor case, and add the new intra-Area layout behavior for the multi-Editor case.

**Acceptance for Sprint G:** `AreaLayoutRenderer` exists; `AreaWidget` delegates to it; no behavior change for the single-Editor case; the existing `test_area_widget.py`, `test_workspace.py`, and `test_main_window.py` suites continue to pass; CI is green; and the total test count grows from 1528 to a new stable baseline.

**After Sprint G:** Sprint H (`EditorStack`), which depends on G and completes Phase 2.