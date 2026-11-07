# ADR-0014: Widget Toolkit Selection

**Status:** Accepted
**Date:** 2026-11-07
**Deciders:** CranioZ core team
**Supersedes:** none
**Superseded by:** none
**Related:** ADR-0013 (UI Widgets and Editor Overlays)

---

## 1. Context

CranioZ needs a UI technology stack that supports:

- Dense, multi-panel clinical interfaces (the Prototipagem_UI_17 specification).
- Embedded medical visualization via VTK (`QVTKRenderWindowInteractor`).
- Dynamic viewport grids (1×1, 2×2, 3×3, editable up to 6×4, panoramic, ATM).
- A consistent, themeable appearance across the shell, panels, dialogs, toolbars, and controls.
- Incremental migration of existing Qt Widgets without reworking the imaging pipeline.
- Cross-platform behaviour on Windows, macOS, and Linux.
- Testability with `pytest` and `pytest-qt`.

Four candidate approaches were considered:

1. **Qt Widgets with the default Fusion style.**
2. **Qt Widgets with a modular QSS design system.**
3. **An external theme library** (e.g., `pyqtdarktheme`).
4. **QML (Qt Quick) for the shell, with Qt Widgets for embedded content.**

The appearance architecture that this decision implements is specified in `docs/architecture/appearance/`. It is not repeated here.

---

## 2. Decision

**Adopt Qt Widgets as the UI toolkit, with the Fusion base style and a modular QSS design system driven by semantic design tokens.**

The appearance architecture is defined in:

- `docs/architecture/appearance/README.md`
- `docs/architecture/appearance/appearance-architecture.md`
- `docs/architecture/appearance/themes-and-design-tokens.md`
- `docs/architecture/appearance/icons.md`
- `docs/architecture/appearance/surfaces-and-overlays.md` (future)
- `docs/architecture/appearance/viewport-appearance.md` (future)
- `docs/architecture/appearance/modal-focus-effect.md` (future)
- `docs/architecture/appearance/widget-system.md` (future)
- `docs/architecture/appearance/persistence-and-settings.md` (future)
- `docs/architecture/appearance/accessibility-and-performance.md` (future)
- `docs/architecture/appearance/implementation-roadmap.md` (future)

This ADR only records the toolkit and styling approach. It does not redefine the architecture.

---

## 3. Rationale

### 3.1 Why not QML for the shell

The prototype's most critical UI element is the embedded medical visualization. VTK renders inside `QVTKRenderWindowInteractor`, which is a Qt Widget, not a QML item. If the shell were QML, every VTK viewport would need to be embedded via `QQuickWidget`, introducing:

- OpenGL context conflicts between QML's scene graph and VTK's contexts, especially with multiple simultaneous viewports (the prototype requires 2×2 and larger grids).
- Resize and lifecycle issues with `QVTKRenderWindowInteractor` inside a QML scene.
- Additional synchronization requirements for `pytest-qt`.
- A second UI technology stack, doubling the maintenance surface.

The prototype does not require animations, transitions, or GPU-accelerated visual effects that would justify the cost of QML. It requires density, consistency, structure, and stable VTK embedding.

**Future migration is not prohibited.** If a future phase decides the HomePage (which does not embed VTK) would benefit from QML, it can be migrated in isolation via `QQuickWidget` without touching the Editors or the workspace engine.

### 3.2 Why not the default Fusion style alone

The prototype specifies a flat, controlled visual language with semantic states (active vs. inactive viewport, clinical badges, LUT previews, feedback severity). Fusion does not reproduce this language, and does not prevent hardcoded colors scattered across widget code.

### 3.3 Why not an external theme library

External theme libraries impose their own token structure and widget coverage. The prototype requires clinical-specific visual states that no generic theme library provides. The dependency also conflicts with the goal of a centralized internal design token system, which is the prerequisite for a coherent appearance architecture.

### 3.4 Why Qt Widgets + modular QSS + design tokens

- The existing codebase, tests (1315 passing), and imaging pipeline are Qt Widgets.
- QSS composes naturally with a centralized `ThemeCompiler` that resolves semantic tokens into stylesheets.
- The design token system separates shared properties (color, spacing, typography) from component-specific constraints, without forcing every widget to become a wrapper.
- The `IconProvider` and `ThemeService` contracts decouple widgets from concrete implementations, allowing the SVG icon provider and high-contrast theme to be introduced later without reworking widgets.
- The medical visualization color system remains independent of shell appearance, protecting the imaging domain from UI changes.

---

## 4. Consequences

### Positive

- No rewrite of the existing imaging pipeline or workspace engine.
- A single UI technology stack (Qt Widgets) across the shell, panels, dialogs, toolbars, and Editors.
- A centralized appearance architecture that supports theme switching, dynamic icons, translucent surfaces, and testable accessibility.
- A path to evolve the appearance (SVG icons, high-contrast theme, simulated glass) without reworking widgets.

### Negative

- QSS has no native variable system; the `ThemeCompiler` must resolve tokens into QSS at compile time.
- Real background blur is not supported as a general mechanism; the architecture uses simulated glass (translucency + gradient + border) instead.
- Designers collaborate through the design token files rather than a QML-like declarative UI language.

### Risks

- **Token proliferation.** Mitigated by the closed token set and the review process defined in `themes-and-design-tokens.md` §13.
- **QSS divergence across widget families.** Mitigated by the `ThemeCompiler` tests and the boundary enforced by `tests/architecture/test_no_hardcoded_appearance.py`.
- **Future QML requests.** The decision does not prohibit isolated QML migration. A new ADR would supersede this one for any component that adopts QML.

---

## 5. Alternatives Considered

### 5.1 Qt Widgets + default Fusion style

Rejected. Insufficient for the prototype's visual language and for the centralized appearance architecture.

### 5.2 External theme library (e.g., `pyqtdarktheme`)

Rejected. Conflicts with internal design tokens and clinical-specific visual states.

### 5.3 QML for the shell

Rejected as the foundation of the shell. The VTK embedding cost, test complexity, and dual-stack maintenance outweigh the aesthetic gains. Isolated future migration is not prohibited.

### 5.4 Minimal scope — only `SemanticColor`

Rejected. Insufficient for spacing, typography, dimensions, borders, effects, and surfaces. The appearance architecture requires the seven token categories defined in `themes-and-design-tokens.md`.

---

## 6. References

- `docs/architecture/appearance/README.md`
- `docs/architecture/appearance/appearance-architecture.md`
- `docs/architecture/appearance/themes-and-design-tokens.md`
- `docs/architecture/appearance/icons.md`
- `Prototipagem_UI_17.pdf` — canonical visual reference
- ADR-0013 (UI Widgets and Editor Overlays)
- ADR-0011 (TaskManager and thread boundaries — VTK render must remain on the GUI thread)
- ADR-0009 (persistence — relevant to user settings and project-scoped appearance)

---

## 7. Approval

This ADR is accepted. It unblocks:

- Phase 1 closure (i18n, `EditorContext` propagation, appearance architecture).
- Phase 2 closure (`ThemeService`, `ThemeCompiler`, `IconProvider`, `SemanticColor`).
- The appearance migration roadmap defined in `docs/architecture/appearance/implementation-roadmap.md`.

Any change to the toolkit, the styling approach, or the appearance architecture requires a new ADR that supersedes this one.