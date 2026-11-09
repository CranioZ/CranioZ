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