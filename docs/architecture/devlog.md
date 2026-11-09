# Dev Log

Narrative record of CranioZ's engineering and design decisions.
Each entry covers a work session or a sprint. `git log` records the
*what*; this file records the *why*, what was tried and discarded, and
what was left pending.

The log starts at Sprint E. Everything before it is summarized below
and detailed in `git log` and `implementation_plan.md`.

---

## Before Sprint E — warm-up summary

**Phases 0–3 (partial) and Sprints A, B.**

- **Phase 0 — Foundation:** repository, `pyproject.toml`, CI,
  `ConfigurationLoader`, `AppPathResolver`, `EventBus`, boot in
  `__main__.py`.
- **Phase 1 — Domain and i18n:** Patient, Project, `EditorRegistry`,
  `LayoutBuilder`, `LayoutRenderer`, ADRs 0001–0014. Sprint B (i18n)
  migrated the shell to `TranslationService`; the
  `test_no_hardcoded_strings_in_shell_widgets.py` guard prevents
  regressions.
- **Phase 2 — Workspace:** `LayoutTree`, `AreaManager`, `Workspace`,
  `TopOverlay`, three-segment Top Bar.
- **Phase 3 — Project and Home Page:** `ProjectManager`,
  `ProjectCatalog`, `HomePage`, `MainWindow`, project lifecycle.
- **DICOM and visualization:** `DicomSeriesReader`, `DicomValidator`,
  `DicomSorter`, `Volume`, `MPRView`, `Viewport3DView`. The voxel
  ordering bug was resolved on 2026-11-06; the root cause was
  `transpose(2, 1, 0)` combined with `ravel(order="C")` in
  `VtkImageAdapter`. The contract is `int16`, `VTK_SHORT`, no
  transposition, direction matrix applied.
- **ADR-0014:** decision for Qt Widgets + modular QSS + Design Tokens
  in Python, not QML.

**Debt inherited by the next sprints:**

- `EditorContext` incomplete (Sprint C).
- `IconProvider` does not exist yet (Sprint F).
- `AreaLayoutRenderer` and `EditorStack` (Sprints G, H).
- `ProjectIndex`, coordinated deletion, async loading (Sprints I, J, K).
- 4 files with hardcoded colors listed in `_KNOWN_DEBT_FILES`.

The detail of each item lives in `implementation_plan.md` §5–§6 and in
the corresponding commits.

---

## 2026-11-09 — Sprint E: design tokens, ThemeService, ThemeCompiler

**Context.** Sprint E had to deliver the appearance foundation: tokens,
ThemeService, ThemeCompiler, SettingsService, and tests. The
specification lived in `docs/architecture/appearance/themes-and-design-tokens.md`.

**What was done.**
- `cranioz.infrastructure.settings`: SettingsService with two
  implementations (in-memory, filesystem), migrator, closed key set.
- `ui/theme/tokens.py`: 47 tokens, `ThemeMode`, `ThemeName`, validation.
- `ui/theme/service.py`: ThemeService with SYSTEM resolution via
  QStyleHints.
- `ui/theme/compiler.py`: ThemeCompiler with surface composition and
  QSS emission.
- Boot: SettingsService → ThemeService → apply → MainWindow.
- 177 new tests, 1508 passing.

**Decisions.**
- `modal_backdrop` uses a fixed `#000000`, not `background_application`.
  Reason: the backdrop must darken the interface, not tint it.
- `set_mode()` does not persist. Persistence is owned by the settings
  page, which allows a live preview before applying.
- `feedback_information` stayed at `#4A90D9` (the spec value) because
  `#0071E3` failed WCAG AA against `background_panel`.

**Debt and open items.**
- `_KNOWN_DEBT_FILES`: 4 files with hardcoded literals
  (`area_widget.py`, `workspace.py`, `workspace_spec.py`, `presets.py`).
  To be migrated in the widget migration sprint.
- `StartButton` still uses the `→` glyph; Sprint F replaces it with
  `IconProvider.icon(...)`.
- `QSlider` is not covered by the expanded QSS; the adjustment is
  deferred to the widget migration sprint.

**Next.** Sprint F — `IconProvider` + `UnicodeIconProvider` + glyph
migration.

## 2026-11-09 — Sprint F: IconProvider + UnicodeIconProvider + glyph migration

**Context.** Sprint F had to deliver the icon system: contract, Phase 2 implementation, shell migration, and contract tests. The specification lived in `docs/architecture/appearance/icons/`.

**What was done.**
- `ui/icons/`: `IconState` enum, `IconProvider` Protocol, `UnicodeIconProvider` with 66 names (60 canonical + 6 shell-specific).
- Injection: `__main__` → `MainWindow` → `Workspace` → shell widgets (`HomePage`, `TopBar` segments, `StartButton`, `FlowRow`).
- Migration: 8 files with hardcoded glyphs replaced by `provider.icon(...)`.
- Tests: 5 contract tests (`test_icon_catalog.py`, `test_icon_fallback.py`, `test_icon_theme.py`, `test_icon_widget_contract.py`, `test_icon_accessibility.py`).
- `_KNOWN_DEBT_FILES`: `workspace_spec.py` and `start_button.py` removed (glyphs are gone). `area_widget.py`, `workspace.py`, and `presets.py` remain (colors only).

**Decisions.**
- `IconProvider` lives in `ui/icons/`, not `ui/theme/icons/`. Icons are a distinct system (assets, catalog, provider), even though they depend on `ThemeService` for color.
- `EditorContext` injection deferred to Sprint C. Sprint F injects only into the shell.
- The 60-icon catalog was extended with 6 names required by the shell: `community`, `library`, `news`, `feedback`, `contribute`, `start`.

**Debt and open items.**
- `SvgIconProvider` and SVG assets remain Phase 8.
- `QImage.mirrored` and `vtkCellArray.GetData` deprecations tracked separately.
- The `test_icon_widget_contract.py` replaces the glyph-related debt from `test_no_hardcoded_appearance.py`.

**Next.** Sprint C — `EditorContext` propagation (now unblocked).

# Dev Log

**Document type:** Development log
**Status:** Active
**Scope:** Sprint-by-sprint record of what was done, what broke, and how it was resolved
**Last updated:** 2026-11-09

---

## Sprint F — IconProvider + UnicodeIconProvider + glyph migration

**Status:** ✅ Complete
**Date closed:** 2026-11-09
**Phase:** 2 (Workspace Engine & Icons)

### Objective

Deliver `IconState`, the `IconProvider` Protocol, `UnicodeIconProvider` with the closed 60-icon catalog, inject the provider into every shell widget that renders a glyph, migrate the hardcoded glyphs to `provider.icon(...)`, and add the five icon contract tests. Unblock Sprint C (`EditorContext` propagation), which depends on `icon_provider`.

### What was delivered

**Production code:**

- `src/cranioz/ui/icons/state.py` — `IconState` enum (`DEFAULT`, `HOVER`, `PRESSED`, `SELECTED`, `DISABLED`).
- `src/cranioz/ui/icons/provider.py` — `IconProvider` Protocol (`icon(name, size, state) -> QIcon`, `text_glyph(name) -> str`, `invalidate_cache() -> None`).
- `src/cranioz/ui/icons/unicode.py` — `UnicodeIconProvider` with the closed 60-icon catalog from `docs/architecture/appearance/icons/icons_and_icon_manager.md` §6.
- Injection into `MainWindow`, `Workspace`, `HomePage`, `HomeSegment`, `ModulesSegment`, `ExtrasSegment`, `Toolbar`, `StartButton`, `FlowRow`.
- Hardcoded glyphs in those widgets migrated to `provider.icon(...)`.
- `_WHITELIST` in `tests/architecture/test_no_hardcoded_strings_in_shell_widgets.py` emptied.

**Tests:**

- `test_icon_catalog.py` — count and required names.
- `test_icon_fallback.py` — unknown name and unknown text glyph.
- `test_icon_theme.py` — state → token mapping (5 parametrized cases).
- `test_icon_widget_contract.py` — AST scan of 7 widget files for hardcoded glyphs and direct `UnicodeIconProvider` imports.
- `test_icon_accessibility.py` — `HomeSegment` buttons expose accessible names.

**Test infrastructure:**

- `make_icon_provider(theme_service=None)` factory in `tests/conftest.py`.
- `icon_provider` fixture in `tests/conftest.py`.
- 17 test files updated to pass `icon_provider` to constructors:
  - `tests/conftest.py`
  - `tests/integration/ui/test_main_window.py`
  - `tests/integration/ui/test_main_window_debug_mesh.py`
  - `tests/integration/ui/test_main_window_import.py`
  - `tests/integration/ui/test_main_window_top_bar.py`
  - `tests/integration/ui/workspace/layout/test_layout_renderer.py`
  - `tests/integration/ui/workspace/workspace/test_workspace.py`
  - `tests/integration/ui/workspace/areas/test_area_widget.py`
  - `tests/unit/ui/home/test_home_page.py`
  - `tests/unit/ui/home/widgets/test_community_sidebar.py`
  - `tests/unit/ui/home/widgets/test_flow_list.py`
  - `tests/unit/ui/home/widgets/test_flow_row.py`
  - `tests/unit/ui/home/widgets/test_home_bottom_bar.py`
  - `tests/unit/ui/home/widgets/test_home_top_bar.py`
  - `tests/unit/ui/workspace/structure/test_home_segment.py`
  - `tests/unit/ui/workspace/structure/test_modules_segment.py`
  - `tests/unit/ui/toolbars/test_toolbar.py`

### What broke, and how it was resolved

**1. Sprint F changed constructors, but tests were not adapted.**

- **Symptom:** `pytest -q` produced 96 failed, 65 errors. Every failure was `TypeError: X.__init__() missing 1 required keyword-only/positional argument: 'icon_provider'`.
- **Root cause:** The Sprint F deliverable requires `icon_provider` on every widget that renders a glyph. The production constructors were updated; the tests were not.
- **Resolution:** 17 test files updated. `make_icon_provider` and `icon_provider` fixture added to `conftest.py` to centralize construction. Each test file either uses the shared fixture or builds the provider locally.

**2. `test_whitelist_entries_are_used` failed with 6 stale entries.**

- **Symptom:** The test reported `'☰'`, `'?'`, `'⚙'`, `'→'`, `'+'`, `'→'` as no longer produced by the files.
- **Root cause:** Those were the exact glyphs migrated in Sprint F. The Sprint B whitelist listed them as known debt; after migration, they became stale.
- **Resolution:** `_WHITELIST` set to `()`. The guardrail remains active against new hardcoded glyphs.

**3. `test_home_bottom_bar.py` — `RuntimeError: libshiboken: Internal C++ object (StartButton) already deleted`.**

- **Symptom:** 4 teardown/setup errors, cascading to "previous item was not torn down properly".
- **Root cause:** The fixture registered `start_button` with `qtbot.addWidget(button)`. The test then constructed `HomeBottomBar(start_button)`, which reparents the button. At teardown, Qt destroyed `HomeBottomBar` (with the child `StartButton`), and `qtbot` also tried to `close()` the already-deleted `StartButton`.
- **Resolution:** The `start_button` fixture no longer registers with `qtbot`. Only `HomeBottomBar` is registered; it owns the button.

**4. `test_toolbar_resolves_icon_name_via_theme` failed with `assert None == 'log'`.**

- **Symptom:** `button.property("icon_name")` returned `None`.
- **Root cause:** The test was written against a pre-Sprint-F plan where the icon name was stored as a dynamic property on the button. Sprint F replaced that plan with `icon_provider.icon(...)`, which returns a `QIcon`. The `Toolbar` never sets `icon_name`.
- **Resolution:** Test renamed to `test_toolbar_resolves_icon_via_icon_provider` and now asserts `button.icon().isNull() is False`. The production `Toolbar` was correct; the test was outdated. The test was previously masked because the constructor failed before reaching the assertion.

**5. `ruff` flagged `F841 Local variable 'toolbar' is assigned to but never used` in `test_unknown_tool_id_raises`.**

- **Symptom:** `ruff check` reported one unsafe fix.
- **Root cause:** The test used `try/except` style and assigned `toolbar = toolbar_factory(spec)` but never used `toolbar`.
- **Resolution:** Rewritten with `pytest.raises(KeyError, match="tool.unknown")`, which is idiomatic and eliminates the unused variable.

### Final state

| Metric | Value |
|---|---|
| Tests passing | **1527** |
| Failed | 0 |
| Errors | 0 |
| Skipped | 0 |
| Coverage | 88% |
| `ruff check` | clean |
| `ruff format --check` | clean |
| `mypy src` | clean |

Warnings: 41 (two known deprecations: `QImage.mirrored` at `mpr_viewer/view.py:216`, `vtkCellArray.GetData` at `stl.py:135`). Both tracked separately in `Next Steps.md` §7.

### Baseline change

- Before Sprint F: 1508 passing, 0 failed, 1 skipped, 88% coverage.
- After Sprint F: **1527 passing, 0 failed, 0 errors, 0 skipped, 88% coverage.**
- Net: +19 tests (the icon contract suite). The ~150 tests that were failing/erroring before the fixes returned to passing, which is why the total is not 1508 + 19 + 150 — those tests already existed and were blocked, not new.

### Documents updated

- `implementation_plan.md` — Sprint F marked ✅; Phase 2 pending work reduced; §9 Implementation Summary updated; §10 Known Issues updated.
- `Next Steps.md` — baseline corrected to 1527; Sprint F marked ✅; "Next sprint" changed from F to C; §3.2.2 rewritten as complete; §7 Known Issues updated; §8 Immediate next action rewritten for Sprint C.

### Next sprint

**Sprint C — `EditorContext` propagation.** Unblocked. Depends on Sprint E (`theme_service`, ✅) and Sprint F (`icon_provider`, ✅), both complete.

Sprint C has four parts:

1. Audit current `EditorContext` fields against the target set (9 fields).
2. Propagate missing fields.
3. Update `Workspace._create_editor` and `MainWindow._create_workspace`.
4. Add a contract test asserting every `EditorRegistry`-registered Editor receives all nine fields non-null in `initialize`.

# Dev Log

**Document type:** Development log
**Status:** Active
**Scope:** Sprint-by-sprint record of what was done, what broke, and how it was resolved
**Last updated:** 2026-11-09

---

## Sprint C — EditorContext propagation

**Status:** ✅ Complete
**Date closed:** 2026-11-09
**Phase:** 1 (Contracts, Core Domain & i18n)

### Objective

Propagate `theme_service` and `icon_provider` through `EditorContext`, and add the contract test that asserts every Editor registered in the `EditorRegistry` receives all nine context fields. Close Phase 1 formally.

### What was delivered

**Production code:**

- `src/cranioz/ui/editors/editor_context.py` — added `theme_service: ThemeService | None = None` and `icon_provider: IconProvider | None = None`. Both are optional with `None` default, consistent with the other context fields. Imports added under `if TYPE_CHECKING`.
- `src/cranioz/ui/workspace/workspace.py` (`load_spec`) — added `"theme_service": self._theme_service` and `"icon_provider": self._icon_provider` to the `shared_context` dict passed to `LayoutBuilder.build(...)`.

**Tests:**

- `tests/integration/ui/workspace/test_editor_context_propagation.py` — new contract test. Builds a real `Workspace` with `DummyEditor` registered, loads a `ModuleUISpec`, and asserts that the created `EditorContext` carries the expected instance of each propagated field.

**No changes required in:**

- `LayoutBuilder` — it constructs `EditorContext(**shared)`, so new context fields flow automatically with no closed key list.
- `TomographyEditor.initialize` / `MeshDebugEditor.initialize` — both accept the full `EditorContext` object; no per-field parameters.
- `MainWindow._create_workspace` — already passes `theme_service` and `icon_provider` to `Workspace` since Sprint E/F.

### What broke, and how it was resolved

**1. `CatalogTranslationService(catalog=None)` — `TypeError: unexpected keyword argument 'catalog'`.**

- **Symptom:** The test failed during construction with a `TypeError` from the test body, not from production.
- **Root cause:** I wrote the test assuming `CatalogTranslationService` accepts a `catalog` keyword. Its real constructor is `CatalogTranslationService(registry: TranslationCatalogRegistry, language: str = "en")`.
- **Resolution:** Replaced `CatalogTranslationService` with `IdentityTranslationService()`, which requires no registry and is explicitly documented as suitable for tests. The contract test verifies propagation, not translation.

**2. `tool_registry = ToolRegistry()` shadowed the fixture — `KeyError: 'tool_id not registered: tool.log'`.**

- **Symptom:** `load_spec` failed in `AreaWidget._build_toolbars` when materializing the `DummyEditor`'s toolbar. The toolbar references `tool.log` and `tool.toggle`, neither of which was registered.
- **Root cause:** The test received `tool_registry: ToolRegistry` as a fixture parameter (correct), but then re-assigned it inside the function body: `tool_registry = ToolRegistry()`. The fixture's registrations were discarded.
- **Resolution:** Removed the re-assignment line. The fixture's registry (which registers `tool.log` and `tool.toggle`) is now passed to `Workspace`.

**3. `ruff` SIM222 — `x is not None or True` in three asserts.**

- **Symptom:** `ruff check .` reported three unsafe fixes for `assert context.X is not None or True`.
- **Root cause:** The expression is a tautology; it passes regardless of the value. My intent was "do not fail if this field is None" — but the form made the assert meaningless.
- **Resolution:** Removed the three tautological asserts. Noted as debt in `Next Steps.md` §7:
  - `correlation_id`: not yet propagated by `Workspace` (it does not receive it in `__init__`).
  - `event_subscription`: passed as `None` in the test; a dedicated test should cover it once `EventBus` exposes a subscription helper for unit tests.
  - `domain_object_store`: not in the Sprint C target set.

**4. Windows Smart App Control blocked `vtkRenderingCore` (environmental).**

- **Symptom:** `ImportError: DLL load failed while importing vtkRenderingCore: Uma política de Controle de Aplicativo bloqueou este arquivo.`
- **Root cause:** Windows 11 Smart App Control blocks unsigned DLLs, including VTK's. The VTK wheels are not code-signed.
- **Resolution:** Smart App Control was disabled on the development machine. This is a development-environment requirement, not a code change. It must be documented in the contributor setup instructions.

### Final state

| Metric | Value |
|---|---|
| Tests passing | **1528** (1527 from Sprint F + 1 from Sprint C) |
| Failed | 0 |
| Errors | 0 |
| Skipped | 0 |
| Coverage | 88% |
| `ruff check` | clean |
| `ruff format --check` | 542 files already formatted |
| `mypy src` | 281 source files, no issues |

Warnings: 41 (the two known deprecations: `QImage.mirrored` at `mpr_viewer/view.py:216`, `vtkCellArray.GetData` at `stl.py:135`). Both tracked separately in `Next Steps.md` §7.

### Baseline change

- Before Sprint C: 1527 passing.
- After Sprint C: **1528 passing.**
- Net: +1 test (the contract test). No regressions.

### Documents updated

- `implementation_plan.md` — Phase 1 marked `✅ Implemented`; Sprint C marked `✅ Complete`; §9 Implementation Summary updated; §10 Known Issues updated; `Next sprint` changed from C to G.
- `Next Steps.md` — baseline corrected to 1528; Phase 1 marked `✅ Complete`; Sprint C marked `✅ Complete`; §7 Known Issues updated with the two new debt rows (`correlation_id`, `event_subscription`); §8 Immediate next action rewritten for Sprint G.

### Lessons learned

**Audit before implementation.** The `Next Steps.md` listed nine context fields as Sprint C deliverables, but an audit against the current codebase showed that seven already existed. Only two were missing, and both flowed automatically through `LayoutBuilder`'s `**shared` mechanism. The audit turned what looked like a multi-day sprint into a couple of hours of work — and would have been wasted effort if skipped.

**Tests reveal contract drift.** The `test_toolbar_resolves_icon_name_via_theme` failure in Sprint F and the `CatalogTranslationService(catalog=None)` failure in Sprint C were both cases of a test written against an assumed contract that production did not implement. The tests are valuable: they force the contract to be explicit. But they must be written against the real production signature, not the intended one.

**`x or True` is always a bug in a test.** If a field is optional and a test does not want to assert on it, the field should be omitted from the test, with a comment explaining why. A tautological assert adds no coverage and hides intent.

### Next sprint

**Sprint G — `AreaLayoutRenderer`.** Independent of the other open sprints. Splits `AreaWidget`'s intra-Area composition into a dedicated renderer, so that Sprint H (`EditorStack`) can build on it. No visible behavior change for the single-Editor case; the existing `test_area_widget.py`, `test_workspace.py`, and `test_main_window.py` suites must continue to pass.

### Phase impact

**Phase 1 is closed.** The contracts, core domain, i18n, and `EditorContext` propagation are complete and tested. The remaining phases in progress (2 and 3) have no dependency on Phase 1 beyond what is now stable.

This unblocks the path to Phase 4 (Scene & Visualization), which begins only after Phases 2–3 close. No further changes to the Phase 1 contract should be necessary; if a future sprint discovers a gap, it should be recorded as debt in `Next Steps.md` §7, not silently added to `EditorContext`.