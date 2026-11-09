# Next Steps

**Document type:** Action plan and handoff
**Status:** Active
**Scope:** Immediate next work items after Sprint E closure
**Last updated:** 2026-11-08

---

## 1. Context

The VTK rendering pipeline is validated end-to-end. The DICOM visualization bug was resolved on 2026-11-06. The voxel-ordering contract is documented and enforced by regression tests. The imaging pipeline uses `int16` (`VTK_SHORT`) as the production scalar type, with the direction matrix applied and confirmed.

The appearance architecture has been decided. `docs/architecture/appearance/` is the canonical specification. ADR-0014 registers the toolkit decision (Qt Widgets + QSS modular + Design Tokens in Python, not QML). The DICOM path, the 3D viewport, the MPR view, and the workspace layout are operational and covered by **1510 passing tests** (0 failed, 1 skipped, 88% coverage).

Sprint B (i18n) is complete: the shell — `MainWindow`, the Home Page tree, the three Top Bar segments, and the Workspace placeholder editor — resolves user-facing strings through the `TranslationService`. `tests/architecture/test_no_hardcoded_strings_in_shell_widgets.py` guards against regressions.

Sprint E (appearance foundation) is complete: `ThemeService` and `ThemeCompiler` are implemented, the 47 canonical design tokens are defined for `DARK` and `LIGHT`, the `cranioz.infrastructure.settings` package provides typed, versioned, and atomically written user settings, and `AppPathResolver.user_settings_path()` resolves the user settings file. The theme is applied at boot before the first window. `tests/architecture/test_no_hardcoded_appearance.py` guards against new hardcoded colors and freezes the existing debt for the widget migration sprint.

The project is ready to close Phases 1, 2, and 3 formally before advancing deeper into Phase 4. This document defines the execution order and the acceptance criteria for each phase.

---

## 2. What is already done

### 2.1 Architecture and decisions

- `docs/architecture/appearance/` contains the canonical appearance specification:
  - `README.md`, `appearance-architecture.md`
  - `themes-and-design-tokens.md` (7 categories, 47 tokens, `ThemeMode`, `ThemeName`, `ThemeService`, `ThemeCompiler`, translucency composition)
  - `icons.md` (`IconProvider` Protocol, `UnicodeIconProvider` for Phase 2, `SvgIconProvider` for Phase 8, 60-icon catalog)
  - `surfaces-and-overlays.md` (Solid, Translucent, Simulated Glass; real blur is not supported)
  - `modal-focus-effect.md` (dimming + experimental blur, Phase 6)
  - `widget-system.md`, `viewport-appearance.md`, `persistence-and-settings.md`, `accessibility-and-performance.md`, `implementation-roadmap.md`
- ADR-0014 (Widget Toolkit Selection) is written in `docs/adr/ADR-0014-widget-toolkit-selection.md`.
- ADR-0013 (Editor Layout Tree, View Layout Tree, and Toolbar Placement) is accepted.

### 2.2 Code and tests

- **1510 tests passing, 0 failed, 1 skipped, 88% coverage.**
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
  - `__main__.py` boot order: `SettingsService` → `ThemeService` → `apply theme` → `MainWindow`.
  - Test suite grew by 177 tests: `test_service.py` (27), `test_tokens.py` (37), `test_compiler.py` (25), `test_settings_service.py` (27), `test_no_hardcoded_appearance.py` (10), `test_tokens_used.py` (8), `test_tokens_present.py` (2), `test_theme_completeness.py` (12), `test_theme_values.py` (9), `test_contrast.py` (20).
  - Known debt frozen in `_KNOWN_DEBT_FILES`: 26 hardcoded literals across 6 files (`flow_row.py` 9, `start_button.py` 5, `area_widget.py` 5, `workspace.py` 3, `workspace_spec.py` 1, `presets.py` 3).

### 2.3 Implementation plan

- `implementation_plan.md` is the current roadmap. It defines 11 phases.
- Phase 4 is marked as the next major implementation phase, with the following items already complete: voxel ordering, `int16`, direction matrix, `Viewport3DView.set_volume(Volume)`, STL path validation, DICOM path validation.

---

## 3. What is missing — by phase

### 3.1 Phase 1 — Contracts, Core Domain & i18n

**Goal:** close Phase 1 formally. Blocker: `EditorContext` propagation (Sprint C).

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

#### 3.1.2 `EditorContext` complete (Sprint C) — 🚧 Pending

**Depends on:** Sprint E (`theme_service`, ✅ complete), Sprint F (`icon_provider`, 🚧 pending).

Deliverables:

- Propagate `task_manager`, `telemetry`, `correlation_id`, `command_dispatcher`, `scene_query`, `event_subscription`, `translation_service`, `theme_service`, `icon_provider` through `EditorContext`.
- `Workspace._create_editor` and `MainWindow._create_workspace` pass the complete set.
- `TomographyEditor.initialize` and `MeshDebugEditor.initialize` accept the complete set.
- Contract test: every Editor registered in `EditorRegistry` receives all required fields with non-null values.

#### 3.1.3 Phase 1 tests

- ✅ i18n contract tests.
- ✅ `test_no_hardcoded_strings_in_shell_widgets.py`.
- 🚧 `EditorContext` propagation tests (pending Sprint C).

**Phase 1 is complete when:** `EditorContext` propagates all fields, contract tests pass, and CI is green.

---

### 3.2 Phase 2 — Workspace Engine & Icons

**Goal:** close Phase 2 formally. Blockers: `IconProvider` + `UnicodeIconProvider`, `AreaLayoutRenderer`, `EditorStack`.

#### 3.2.1 `ThemeService` + `ThemeCompiler` + tokens (Sprint E) — ✅ Complete

Delivered:

- `ThemeMode` (`DARK`, `LIGHT`, `SYSTEM`) and `ThemeName` (`DARK`, `LIGHT`) as `StrEnum`.
- `ThemeTokens` and the 7 dataclasses (`ColorTokens`, `TypographyTokens`, `SpacingTokens`, `DimensionTokens`, `BorderTokens`, `EffectTokens`, `SurfaceTokens`).
- `DARK` and `LIGHT` token values as specified in `themes-and-design-tokens.md` (47 tokens).
- `ThemeService` with `mode()`, `set_mode()`, `theme()`, `tokens()`, `color()`, `dimension()`, `surface_color()`, `icon_name()`, `theme_changed` signal, `SYSTEM` resolution via `QStyleHints.colorScheme()`.
- `ThemeCompiler` with `compile()` and `apply()`.
- Surface composition (`base_color + opacity`) for `toolbar`, `popover`, `modal_backdrop`. `modal_backdrop` uses a fixed `#000000` base per spec §6.2.
- QSS emission for styled widgets.
- `cranioz.infrastructure.settings` package: `SettingsService` protocol, `InMemorySettingsService`, `FilesystemSettingsService`, `SettingsStore`, `SettingsMigrator`, `KNOWN_KEYS`, `SettingsError`, `SettingsMigrationError`.
- `AppPathResolver.user_settings_path()` and `PathsConfig.settings_root`.
- Boot integration: read `appearance.theme_mode` from `SettingsService` before constructing `MainWindow`; invalid values fall back to `DARK` with a `WARNING`; apply theme before the first window.
- Contract tests: `test_no_hardcoded_appearance.py`, `test_tokens_used.py`, `test_tokens_present.py`, `test_theme_completeness.py`, `test_theme_values.py`, `test_contrast.py`.
- Unit tests: `test_service.py`, `test_tokens.py`, `test_compiler.py`, `test_settings_service.py`.
- Known debt registered in `_KNOWN_DEBT_FILES` for the widget migration sprint (6 files, 26 literals).

#### 3.2.2 `IconProvider` + `UnicodeIconProvider` (Sprint F) — 🚧 Pending

**Depends on:** Sprint E (✅ complete).

Deliverables:

- `IconState` enum.
- `IconProvider` Protocol.
- `UnicodeIconProvider` with the 60-icon catalog from `icons.md`.
- Injection into `MainWindow`, `Workspace`, `EditorContext`.
- Migration of hardcoded glyphs in `TopBar`, `HomeSegment`, `ModulesSegment`, `ExtrasSegment`, `HomePage`, `Toolbar`.
- Contract tests: `test_icon_catalog.py`, `test_icon_fallback.py`, `test_icon_theme.py`, `test_icon_widget_contract.py`, `test_icon_accessibility.py`.

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

**Phase 2 is complete when:** `ThemeService`, `ThemeCompiler`, `IconProvider`, `UnicodeIconProvider`, `AreaLayoutRenderer`, and `EditorStack` are implemented, contract tests pass, all glyphs are migrated to `provider.icon(...)`, and CI is green.

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

**Depends on:** Sprints C, E (✅ complete), F.

Deliverables:

- `ProfessionalEditor` registered in `EditorRegistry`.
- `ModuleUISpec` for the Professional module.
- Settings integration (`professional.*` keys in `SettingsService`).
- Tests.

**Phase 3 is complete when:** `ProjectIndex`, coordinated deletion, async loading, and the Professional module are implemented, contract tests pass, and CI is green.

---

### 3.4 Phase 4 — Scene & Visualization (deferred until Phases 1–3 close)

Phase 4 remains the active implementation phase after Phases 1–3 close. It is not started in this handoff. See `implementation_plan.md` §4 and §5.1 for the complete scope.

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

The order below respects the dependencies between Phases 1–3.

| Sprint | Phase | Deliverable | Status | Depends on |
|---|---|---|---|---|
| B | 1 | i18n contract and catalogs | ✅ Complete | — |
| C | 1 | `EditorContext` propagation | 🚧 Pending | B, E (✅ `theme_service`), F (`icon_provider`) |
| E | 2 | `ThemeService`, `ThemeCompiler`, tokens | ✅ Complete | — |
| F | 2 | `IconProvider`, `UnicodeIconProvider`, glyph migration | 🚧 Pending | E |
| G | 2 | `AreaLayoutRenderer` | 🚧 Pending | — |
| H | 2 | `EditorStack` | 🚧 Pending | G |
| I | 3 | `ProjectIndex` | 🚧 Pending | — |
| J | 3 | Coordinated deletion | 🚧 Pending | I |
| K | 3 | Async loading | 🚧 Pending | I, J |
| L | 3 | Professional module | 🚧 Pending | C, E, F |

**Next sprint:** Sprint F — `IconProvider` + `UnicodeIconProvider` + glyph migration. It unblocks Sprint C.

**Note on ordering:** Sprint C depends on Sprint E and Sprint F because `EditorContext` will carry `theme_service` and `icon_provider`. Sprint E is now complete; Sprint F is the remaining dependency before Sprint C can start. Alternatively, Sprint C can propagate only the services that exist at that time, with a follow-up PR adding `theme_service` and `icon_provider`. Either approach is valid; the first is cleaner.

---

## 5. Definition of Done for this handoff

This handoff is complete when:

1. `implementation_plan.md` reflects Sprint E closed and Sprint F pending, and lists `test_no_hardcoded_appearance.py` under the Phase 2 tests.
2. `docs/adr/ADR-0014-widget-toolkit-selection.md` is committed.
3. `docs/architecture/appearance/` is consolidated:
   - `README.md`, `appearance-architecture.md`, `themes-and-design-tokens.md`, `icons.md`, `surfaces-and-overlays.md` are the canonical documents.
   - Documents not yet written (`modal-focus-effect.md`, `widget-system.md`, `viewport-appearance.md`, `persistence-and-settings.md`, `accessibility-and-performance.md`, `implementation-roadmap.md`) are placeholders that reference the corresponding sections of `CranioZ_Appearance_System.md` as the source of truth until they are written.
4. The next conversation starts with **Sprint F (`IconProvider` + `UnicodeIconProvider` + glyph migration)**.

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
| Shell hardcoded strings | ✅ Guarded by `test_no_hardcoded_strings_in_shell_widgets.py` | `tests/architecture/` |
| `test_modules_segment.py` duplicate | ✅ Rewritten to test `ModulesSegment` | `tests/unit/ui/workspace/structure/` |
| Appearance foundation (Sprint E) | ✅ Complete | This document §3.2.1 |
| Hardcoded colors in shell | ✅ Guarded by `test_no_hardcoded_appearance.py` with frozen `_KNOWN_DEBT_FILES` | `tests/architecture/` |
| `EditorContext` propagation (Sprint C) | 🚧 Pending | This document §3.1.2 |
| `IconProvider` / `UnicodeIconProvider` (Sprint F) | 🚧 Pending | This document §3.2.2 |
| `AreaLayoutRenderer` (Sprint G) | 🚧 Pending | This document §3.2.3 |
| `EditorStack` (Sprint H) | 🚧 Pending | This document §3.2.4 |
| `ProjectIndex` (Sprint I) | 🚧 Pending | This document §3.3.1 |
| Coordinated deletion (Sprint J) | 🚧 Pending | This document §3.3.2 |
| Async loading (Sprint K) | 🚧 Pending | This document §3.3.3 |
| Professional module (Sprint L) | 🚧 Pending | This document §3.3.4 |
| Widget migration to tokens (26 literals in 6 files) | 🚧 Tracked in `_KNOWN_DEBT_FILES` | `test_no_hardcoded_appearance.py` |
| `QImage.mirrored` deprecation | 🚧 Tracked, separate piece | `mpr_viewer/view.py:216` |
| `vtkCellArray.GetData` deprecation | 🚧 Tracked, separate piece | `stl.py:135` |
| Real background blur | ⛔ Not supported by design | `themes-and-design-tokens.md` §6.3 |
| Full Geometry Infrastructure | ⏳ Deferred | `implementation_plan.md` §5.3 |
| SQLite ProjectIndex | ⏳ Deferred to Phase 8 | `implementation_plan.md` §5.3 |

---

## 8. Immediate next action

Begin **Sprint F — `IconProvider` + `UnicodeIconProvider` + glyph migration**. The sprint has five parts:

1. Define `IconState` enum and `IconProvider` Protocol.
2. Implement `UnicodeIconProvider` with the 60-icon catalog from `icons.md`.
3. Inject `IconProvider` into `MainWindow`, `Workspace`, and (after Sprint C) `EditorContext`.
4. Migrate hardcoded glyphs in `TopBar`, `HomeSegment`, `ModulesSegment`, `ExtrasSegment`, `HomePage`, and `Toolbar` to `provider.icon(...)`.
5. Add the five contract tests: `test_icon_catalog.py`, `test_icon_fallback.py`, `test_icon_theme.py`, `test_icon_widget_contract.py`, `test_icon_accessibility.py`.

**Acceptance for Sprint F:** the 60-icon catalog resolves for `NORMAL`, `HOVER`, `PRESSED`, `DISABLED`, and `SELECTED` states; the fallback returns a stable placeholder for unknown names; the provider is injected into every shell widget that renders a glyph; all shell glyph literals are migrated; the five contract tests pass; CI is green; and the total test count grows from 1510 to a new stable baseline.

**After Sprint F:** Sprint C (`EditorContext` propagation), which depends on Sprint E (✅ complete) and Sprint F.