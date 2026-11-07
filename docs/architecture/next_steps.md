# Next Steps

**Document type:** Action plan and handoff
**Status:** Active
**Scope:** Immediate next work items after the VTK pipeline validation and appearance architecture decisions
**Last updated:** 2026-11-07

---

## 1. Context

The VTK rendering pipeline is validated end-to-end. The DICOM visualization bug was resolved on 2026-11-06. The voxel-ordering contract is documented and enforced by regression tests. The imaging pipeline uses `int16` (`VTK_SHORT`) as the production scalar type, with the direction matrix applied and confirmed.

The appearance architecture has been decided. `docs/architecture/appearance/` is the canonical specification. ADR-0014 registers the toolkit decision (Qt Widgets + QSS modular + Design Tokens in Python, not QML). The DICOM path, the 3D viewport, the MPR view, and the workspace layout are operational and covered by 1315 passing tests.

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
- ADR-0014 (Widget Toolkit Selection) is written in `docs/adr/0014-widget-toolkit-selection.md`.
- ADR-0013 (UI Widgets and Editor Overlays) is accepted.

### 2.2 Code and tests

- 1315 tests passing.
- `ruff` clean.
- `mypy` clean.
- `VtkImageAdapter` corrected (no transposition, `int16`, direction matrix).
- `Viewport3DView` stabilized (`QTimer` cleanup on `dispose`).
- `MPRView` renders correctly with the Volume direction matrix.
- `MainWindow` registers built-in tools before creating the Workspace.

### 2.3 Implementation plan

- `implementation_plan.md` is the current roadmap. It defines 11 phases.
- Phase 4 is marked as the active phase, with the following items already complete: voxel ordering, `int16`, direction matrix, `Viewport3DView.set_volume(Volume)`, STL path validation, DICOM path validation.

---

## 3. What is missing — by phase

### 3.1 Phase 1 — Contracts, Core Domain & i18n

**Goal:** close Phase 1 formally. Blockers: i18n contract and `EditorContext` propagation.

#### 3.1.1 Internationalization (Sprint B)

Deliverables:

- `Locale` value object (`pt_BR`, `en_US`).
- `TranslationService` Protocol with `tr(key, **params)`, `locale()`, `set_locale()`.
- `TranslationCatalog` (JSON loader) and `TranslationCatalogRegistry`.
- Concrete `TranslationService` implementation with `en_US` fallback.
- `en_US` catalog covering all currently used keys (TopBar, HomePage, import errors, message boxes).
- `pt_BR` catalog with minimum coverage.
- Injection into `MainWindow`, `Workspace`, `HomePage`, `TomographyEditor`.
- Removal of `MainWindow._humanize_translation_key`.
- Contract test: every `name_key` in every `flow.json` resolves in `en_US`.

#### 3.1.2 `EditorContext` complete (Sprint C)

Deliverables:

- Propagate `task_manager`, `telemetry`, `correlation_id`, `command_dispatcher`, `scene_query`, `event_subscription`, `translation_service`, `theme_service`, `icon_provider` through `EditorContext`.
- `Workspace._create_editor` and `MainWindow._create_workspace` pass the complete set.
- `TomographyEditor.initialize` and `MeshDebugEditor.initialize` accept the complete set.
- Contract test: every Editor registered in `EditorRegistry` receives all required fields with non-null values.

#### 3.1.3 Phase 1 tests

- i18n contract tests.
- `EditorContext` propagation tests.
- `test_no_hardcoded_strings_in_shell_widgets.py` (detects user-facing strings not routed through `TranslationService`).

**Phase 1 is complete when:** i18n contract exists, `EditorContext` propagates all fields, contract tests pass, and CI is green.

---

### 3.2 Phase 2 — Workspace Engine & Icons

**Goal:** close Phase 2 formally. Blockers: `AreaLayoutRenderer`, `EditorStack`, `ThemeService` + `ThemeCompiler`, `IconProvider` + `UnicodeIconProvider`.

#### 3.2.1 `ThemeService` + `ThemeCompiler` + tokens (Sprint E)

Deliverables:

- `ThemeMode`, `ThemeName` enums.
- `ThemeTokens` and the 7 dataclasses (`ColorTokens`, `TypographyTokens`, `SpacingTokens`, `DimensionTokens`, `BorderTokens`, `EffectTokens`, `SurfaceTokens`).
- `DARK` and `LIGHT` token values as specified in `themes-and-design-tokens.md`.
- `ThemeService` with `mode()`, `set_mode()`, `theme()`, `tokens()`, `color()`, `dimension()`, `surface_color()`.
- `ThemeCompiler` with `compile()` and `apply()`.
- Surface composition (`base_color + opacity`).
- QSS emission for styled widgets.
- Boot integration: read `appearance.theme_mode` from `SettingsService` before constructing `MainWindow`; invalid values fall back to `DARK` with a `WARNING`.
- Contract tests: `test_no_hardcoded_appearance.py`, `test_tokens_used.py`, `test_tokens_present.py`, `test_theme_completeness.py`, `test_contrast.py`.

#### 3.2.2 `IconProvider` + `UnicodeIconProvider` (Sprint F)

Deliverables:

- `IconState` enum.
- `IconProvider` Protocol.
- `UnicodeIconProvider` with the 60-icon catalog from `icons.md`.
- Injection into `MainWindow`, `Workspace`, `EditorContext`.
- Migration of hardcoded glyphs in `TopBar`, `HomeSegment`, `ModulesSegment`, `ExtrasSegment`, `HomePage`, `Toolbar`.
- Contract tests: `test_icon_catalog.py`, `test_icon_fallback.py`, `test_icon_theme.py`, `test_icon_widget_contract.py`, `test_icon_accessibility.py`.

#### 3.2.3 `AreaLayoutRenderer` (Sprint G)

Deliverables:

- `AreaLayoutRenderer` that separates inter-Area from intra-Area layout.
- `AreaWidget` delegates to `AreaLayoutRenderer`.
- No visible behavior change for the single-Editor case.
- Regression tests.

#### 3.2.4 `EditorStack` (Sprint H)

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

Deliverables:

- `ProjectManager.delete_project` coordinates `ProjectCatalog` → `ProjectIndex` → `FilesystemProjectRepository`.
- Rollback when any step fails.
- External source data (External Reference mode) is never removed by project deletion.
- Contract tests.

#### 3.3.3 Async loading (Sprint K)

Deliverables:

- `HomePage` loads projects and flows via `TaskManager`.
- No blocking I/O in `MainWindow.__init__`.
- `HomePage.refresh()` does not block the GUI thread.
- Rollback if `Workspace` creation fails after project open.
- Regression tests: existing project open/close tests continue to pass.

#### 3.3.4 Professional module (Sprint L)

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

| Sprint | Phase | Deliverable | Depends on |
|---|---|---|---|
| B | 1 | i18n contract and catalogs | — |
| C | 1 | `EditorContext` propagation | B, E (for `theme_service`), F (for `icon_provider`) |
| E | 2 | `ThemeService`, `ThemeCompiler`, tokens | — |
| F | 2 | `IconProvider`, `UnicodeIconProvider`, glyph migration | E |
| G | 2 | `AreaLayoutRenderer` | — |
| H | 2 | `EditorStack` | G |
| I | 3 | `ProjectIndex` | — |
| J | 3 | Coordinated deletion | I |
| K | 3 | Async loading | I, J |
| L | 3 | Professional module | C, E, F |

**Note on ordering:** Sprint C depends on Sprint E and Sprint F because `EditorContext` will carry `theme_service` and `icon_provider`. If you prefer to avoid that dependency, Sprint C can propagate only the services that exist at that time, and a follow-up PR adds `theme_service` and `icon_provider` to `EditorContext`. Either approach is valid; the first is cleaner.

---

## 5. Definition of Done for this handoff

This handoff is complete when:

1. `implementation_plan.md` is updated:
   - Remove `ADR-0003` as a blocker.
   - Reference `ADR-0014` and `docs/architecture/appearance/`.
   - Reflect that `steps_panel` was removed (already done in §10.4).
   - Mark Phase 1, 2, 3 with detailed status per sprint.
2. `docs/adr/0014-widget-toolkit-selection.md` is committed.
3. `docs/architecture/appearance/` is consolidated:
   - `README.md`, `appearance-architecture.md`, `themes-and-design-tokens.md`, `icons.md`, `surfaces-and-overlays.md` are the canonical documents.
   - Documents not yet written (`modal-focus-effect.md`, `widget-system.md`, `viewport-appearance.md`, `persistence-and-settings.md`, `accessibility-and-performance.md`, `implementation-roadmap.md`) are placeholders that reference the corresponding sections of `CranioZ_Appearance_System.md` as the source of truth until they are written.
4. The next conversation starts with **Sprint B (i18n)**.

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
| ADR-0003 legacy | ✅ Superseded by ADR-0014 | `docs/adr/0014-widget-toolkit-selection.md` |
| `steps_panel` overlay | ✅ Removed; replaced by `WorkflowBreadcrumb` (Phase 5) | `implementation_plan.md` §10.4 |
| i18n contract | 🚧 Pending (Sprint B) | This document §3.1.1 |
| `EditorContext` propagation | 🚧 Pending (Sprint C) | This document §3.1.2 |
| `ThemeService` / `ThemeCompiler` | 🚧 Pending (Sprint E) | This document §3.2.1 |
| `IconProvider` / `UnicodeIconProvider` | 🚧 Pending (Sprint F) | This document §3.2.2 |
| `AreaLayoutRenderer` | 🚧 Pending (Sprint G) | This document §3.2.3 |
| `EditorStack` | 🚧 Pending (Sprint H) | This document §3.2.4 |
| `ProjectIndex` | 🚧 Pending (Sprint I) | This document §3.3.1 |
| Coordinated deletion | 🚧 Pending (Sprint J) | This document §3.3.2 |
| Async loading | 🚧 Pending (Sprint K) | This document §3.3.3 |
| Professional module | 🚧 Pending (Sprint L) | This document §3.3.4 |
| Real background blur | ⛔ Not supported by design | `themes-and-design-tokens.md` §6.3 |
| Full Geometry Infrastructure | ⏳ Deferred | `implementation_plan.md` §5.3 |
| SQLite ProjectIndex | ⏳ Deferred to Phase 8 | `implementation_plan.md` §5.3 |

---

## 8. Immediate next action

Begin **Sprint B — i18n**. The sprint has four parts:

1. Define `Locale`, `TranslationService`, `TranslationCatalog`, `TranslationCatalogRegistry`.
2. Create `assets/i18n/en_US/*.json` and `assets/i18n/pt_BR/*.json` for existing keys.
3. Inject `translation_service` into `MainWindow`, `Workspace`, `HomePage`, `TomographyEditor`. Replace `MainWindow._humanize_translation_key`.
4. Add contract tests and CI checks.

**Acceptance for Sprint B:** every user-facing string in the shell is resolved via `TranslationService`, all `flow.json` keys resolve in `en_US`, and the `pt_BR` catalog covers the same keys.