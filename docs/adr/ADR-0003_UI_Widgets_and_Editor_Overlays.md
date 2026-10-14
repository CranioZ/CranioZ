Status: Proposed
Date: 2026-10-13
Deciders: Architecture team
Related: ADR-0001_Area_and_Editor.md, ADR-0002_EditorContext_and_Toolbar_Materialization.md,
         editors.md, tools.md, toolbar.md, workspace_en.md,
         Prototipagem_UI_07.pdf (página 15)

---

# 1. Context

The CranioZ UI prototype (Prototipagem_UI_07.pdf, page 15) presents a catalog of reusable visual elements: semantic buttons ("Continuar", "Concluído"), icon-based actions ("Expandir tela", "Fechar janela",
"Abrir pasta", "Ocultar/Exibir", "Puxar/Arrastar"), input controls (sliders, scroll bars), 3D manipulation controls (translation and rotation gizmos), and state indicators (active/inactive colors, collapsed/expanded triangles).

This catalog is not a screen. It is a specification of the visual language of CranioZ — the atoms that appear across multiple screens.

The architecture already provides homes for some of these elements:

- **Toolbars** (`toolbar.md`) present Tools inside an Editor.
- **Tools** (`tools.md`) represent user intentions
  (`tool.view.expand`, `tool.file.open_folder`).
- **ToolRegistry** resolves tool_ids to Tool implementations.
- **ThemeService** (`ui/theme/service.py`) resolves logical icon names.
- **Editor internal overlays** (`editors.md` §17) are floating elements   inside an Editor's content area (gizmos, crosshairs, measurements).

However, the architecture does **not** yet define where the following belong:

1. **Composite generic widgets** that are neither Toolbars nor Editor    overlays. Example: a primary action button (`Continuar`) with a    specific visual style, used in the `steps_panel` and likely in dialogs.
2. **3D manipulation gizmos** that overlay a Viewport. Example: translation and rotation controls shown in the prototype over the    3D model.
3. **Semantic colors** (active/inactive, success/warning/error) that    are currently outside the ThemeService's responsibility.

Without an explicit decision, three risks emerge:

- **Duplication.** The same button widget could be re-implemented in   the `steps_panel`, in dialogs, and in Editors, with slightly different behavior or styling.
- **Misplacement.** A Tool could be created for something that is actually a generic widget, or a widget could be created for
  something that is actually a Tool. The boundary is not yet documented.
- **Inconsistency.** Colors, spacings, and states could diverge across screens, since there is no single place to define them.

This ADR establishes the boundary and the homes for these elements.

---

# 2. Decision

CranioZ organizes reusable UI elements into **three distinct locations**, each with a specific purpose and rule set.

## 2.1 `src/cranioz/ui/widgets/` — Generic composite widgets

A **generic composite widget** is a reusable Qt widget that:

- Combines multiple Qt primitives (buttons, labels, layouts) into a   consistent visual element.
- Is agnostic of CranioZ domain concepts (no knowledge of Editor,   Area, Scene, Module, Flow).
- Consumes `ThemeService` for colors and icons.
- Is used in more than one context (or is clearly destined to be).

Structure:

    src/cranioz/ui/widgets/
    ├── __init__.py
    ├── buttons/
    │   ├── __init__.py
    │   ├── primary_button.py      # e.g. "Continuar"
    │   └── completed_button.py    # e.g. "Concluído"
    ├── sliders/
    │   ├── __init__.py
    │   └── labeled_slider.py      # slider with label and value
    └── ...

Rules:

- A widget in `ui/widgets/` must NOT import anything from   `ui/workspace/`, `ui/editors/`, `ui/tools/`, or `modules/`.
- A widget in `ui/widgets/` MAY import from `ui/theme/` and from   `PySide6`.
- A widget in `ui/widgets/` MUST NOT contain clinical logic, domain   rules, or user intentions. It presents; it does not act.
- A widget in `ui/widgets/` is created **when its first concrete   reuse appears**, not before. Speculative creation is forbidden by   the project's rule "do not create abstractions before the need".

## 2.2 `src/cranioz/ui/editors/overlays/` — Internal overlays of an Editor

An **internal overlay** is a visual element that floats over an Editor's content, participates in hit-testing, and is owned by that
Editor. It is defined in `editors.md` §17.

Structure:

    src/cranioz/ui/editors/overlays/
    ├── __init__.py
    ├── gizmos/
    │   ├── __init__.py
    │   ├── translation_gizmo.py   # cross with orthogonal arrows
    │   └── rotation_gizmo.py      # rotation arc
    ├── rulers/
    │   ├── __init__.py
    │   └── ruler_overlay.py       # measurement ruler
    └── ...

Rules:

- An overlay in `ui/editors/overlays/` MUST live inside the   `content_widget()` of the Editor that uses it.
- An overlay MUST NOT mutate clinical state directly. Interactive   overlays emit Commands through the Editor's `EditorContext`.
- An overlay MAY participate in hit-testing.
- An overlay is created **when the Editor that uses it is   implemented**, not before.

## 2.3 Icon-based actions — Tools, not widgets

An icon-based action in the prototype (e.g. "Expandir tela", "Fechar janela", "Abrir pasta", "Ocultar/Exibir", "Puxar/Arrastar") represents a **user intention**. In CranioZ, user intentions are
Tools (`tools.md`).

Therefore, an icon-based action is:

- Declared as a Tool in `src/cranioz/ui/tools/builtin/<category>/`.
- Registered in the `ToolRegistry`.
- Referenced by `tool_id` in a `ToolbarSpec`.
- Presented by a `Toolbar` widget, inside the Editor that declares the Toolbar.
- Resolved for its icon via `ThemeService.icon_name()`.

Structure:

    src/cranioz/ui/tools/builtin/
    ├── view/
    │   ├── expand.py              # tool.view.expand
    │   └── toggle_visibility.py   # tool.view.toggle_visibility
    ├── file/
    │   └── open_folder.py         # tool.file.open_folder
    ├── window/
    │   └── close.py               # tool.window.close
    └── interaction/
        └── drag_handle.py         # tool.interaction.drag_handle

Rules:

- An icon-based action MUST NOT be implemented as a widget in `ui/widgets/`. It is a Tool.
- An icon-based action MUST NOT be materialized ad-hoc by an Editor.
  It is materialized by a `Toolbar` from a `ToolbarSpec`.
- The Tool's `icon` attribute is a logical name. `ThemeService` resolves it to a concrete icon for the active theme.

## 2.4 Semantic colors — ThemeService

Colors that express state or meaning ("active" green, "inactive" gray, "success", "warning", "error") are **semantic colors**. They belong to `ThemeService`.

The ThemeService will be extended, when the first concrete use appears, with a method:

    def color(self, semantic_name: str) -> str:
        """Return the concrete color for a semantic role.

        Examples: "active", "inactive", "success", "warning", "error".
        """

Rules:

- No widget, Editor, or Toolbar may hardcode a semantic color.
  All semantic colors are resolved via `ThemeService.color()`.
- Non-semantic colors (transient layout constants) may be resolved locally but should eventually be moved to ThemeService if they become repeated.

## 2.5 Native Qt controls

Some elements in the prototype are simply native Qt controls and do not require a custom widget:

- Horizontal slider → `QSlider`
- Vertical and horizontal scroll bars → `QScrollBar` / `QScrollArea`
- Collapsed/expanded triangles → native tree/grouper indicators

Rules:

- A native Qt control is used directly, without an intermediate CranioZ widget, unless a specific composition (e.g. label + value
  + unit) is needed repeatedly.
- When a specific composition is needed, it becomes a widget in
  `ui/widgets/` and is created only at that point.

## 2.6 No premature creation

No folder under `ui/widgets/`, `ui/editors/overlays/`, or `ui/tools/builtin/<new_category>/` may be created in advance of a concrete need.

A folder is created together with its first widget or first tool.

Rationale: the same rule that governed the LayoutBuilder (ADR-0002 §2.3) governs widgets. Abstractions are created when the need is concrete, not speculatively.

---

# 3. Rationale

## 3.1 Three homes, three responsibilities

The three locations are not arbitrary. They correspond to three
distinct kinds of responsibility:

| Location | Responsibility | Depends on |
|---|---|---|
| `ui/widgets/` | Generic visual composition | Qt, ThemeService |
| `ui/editors/overlays/` | Editor-internal interaction layers | Qt, Editor's `EditorContext` |
| `ui/tools/builtin/` | User intentions | ToolRegistry (declaration) |

If these were merged into one folder, the boundaries between "generic presentation", "interactive overlay", and "user intention" would blur.
A generic button would sit next to a 3D rotation gizmo, and nobody would know where to add the next widget.

The three locations preserve the following invariants:

- **Widgets do not know the domain.** A `PrimaryButton` is the same button in the `steps_panel` and in a dialog. It has no idea what a   Flow is.
- **Overlays do not escape their Editor.** A translation gizmo belongs to the Editor that uses it. It is not a shared widget; another
  Editor that needs one declares its own.
- **Tools are declared, not materialized.** A `tool.view.expand` is a declaration. The widget is created by the Toolbar, from the Tool contract. The Tool does not create its own widget.

## 3.2 The prototype does not dictate the structure

The prototype (page 15) presents a visual catalog. It does not say where each element lives. That is an architectural decision, and this ADR makes it.

The catalog is used as evidence for **which** elements exist, not for **where** they belong. The mapping from catalog to location is established by this ADR, following the existing architectural principles.

## 3.3 Consistency with ADR-0001 and ADR-0002

- **ADR-0001** establishes that a Toolbar is internal to an Editor.
  This ADR extends that: an icon-based action is a Tool, presented by a Toolbar inside an Editor. The Tool does not become an Area or a Workspace element.
- **ADR-0002** establishes that the `LayoutRenderer` materializes widgets and that `EditorContext` is per-Editor (hybrid). This ADR extends that: overlays inside an Editor belong to that Editor's
  `content_widget()`, not to the `LayoutRenderer`. The `LayoutRenderer` materializes Areas, Splits, Editors, and Toolbars;
  it does not materialize gizmos or overlay widgets.

## 3.4 Avoiding three common anti-patterns

Without this ADR, the project would naturally drift into three anti-patterns:

**Anti-pattern 1 — Widget spam.**
Every Editor creates its own buttons, its own sliders, its own styling. The UI becomes visually inconsistent.

**Anti-pattern 2 — Tool/widget confusion.**
A "toggle visibility" action could be implemented as a widget in `ui/widgets/` instead of a Tool. It would then be un-discoverable by the ToolRegistry and would not participate in the Toolbar mechanism.

**Anti-pattern 3 — Gizmo leakage.**
A 3D rotation gizmo could be placed in `ui/widgets/` and reused between an Editor and, say, a settings dialog. This would break the overlay's ownership contract and couple unrelated contexts.

The three homes prevent all three.

## 3.5 The "no premature creation" rule

The project has consistently applied the rule "do not create abstractions before the need". This is visible in:

- `EditorContext` (ADR-0002 §2.3): `shared_context` is accepted but not propagated until shared services exist.
- `LayoutBuilder` (ADR-0002 §2.2): does not materialize widgets until the `LayoutRenderer` exists.
- `EditorContext` fields (ADR-0002 §3.2): added only when the corresponding service is implemented.

This ADR applies the same rule to widgets, overlays, and Tools. No folder is created speculatively. Each folder appears with its first concrete member.

---

# 4. Consequences

## 4.1 Positive consequences

- **Clear homes for every UI element.** Every element in the prototype catalog has exactly one architectural home, documented here.
- **No duplication.** A `PrimaryButton` is created once and reused.
  A `tool.view.expand` is declared once and referenced by any Toolbar.
- **Consistent visual language.** Semantic colors, spacings, and states flow through `ThemeService`, not through ad-hoc local code.
- **Discoverable tools.** All icon-based actions are Tools, visible to the `ToolRegistry`. They can be discovered by menus, Toolbars,
  automation, and future MCP integration.
- **Overlay ownership is preserved.** Gizmos belong to the Editor that uses them. No cross-Editor leakage.
- **Parallel development.** Each location can be developed in parallel once its first member is needed. No folder blocks another.
- **Aligned with existing ADRs.** This ADR does not contradict ADR-0001 or ADR-0002. It extends them.

## 4.2 Negative consequences

- **Discipline is required.** A developer who needs a button must decide whether it belongs in `ui/widgets/` or is a Tool. This
  requires reading the rules in §2.
- **First-reuse decision is a judgment call.** "Used in more than one context" is a heuristic, not a mechanical rule. The ADR gives
  guidelines but not a decision procedure. When in doubt, the developer should prefer local implementation first and promote only on real reuse.
- **ThemeService must grow.** Semantic colors require expanding `ThemeService`. This is a future change, not part of this ADR.
- **No immediate impact.** This ADR creates no code today. It documents rules that apply to future work. This is a benefit, not a drawback, but it means the ADR has no immediate test coverage.

## 4.3 Neutral consequences

- **Widgets and Tools are separated, even when they look similar.** A button and a Tool may look identical on screen. Architecturally they are different: a button is presented by a Toolbar and resolved
  by the ToolRegistry; a widget is presented directly by a parent widget. This is intentional.

---

# 5. Rules applied by this ADR

1. Generic composite widgets live in `src/cranioz/ui/widgets/`.
2. Widgets in `ui/widgets/` do not import from `ui/workspace/`,
   `ui/editors/`, `ui/tools/`, or `modules/`.
3. Widgets in `ui/widgets/` present; they do not act on the domain.
4. Editor-internal overlays live in
   `src/cranioz/ui/editors/overlays/`.
5. Overlays live inside the `content_widget()` of the Editor that
   uses them.
6. Overlays emit Commands; they do not mutate clinical state directly.
7. Icon-based actions are Tools in
   `src/cranioz/ui/tools/builtin/<category>/`.
8. Icon-based actions are presented by a Toolbar from a `ToolbarSpec`; they are not materialized ad-hoc.
9. Tool `icon` attributes are logical names, resolved by
   `ThemeService.icon_name()`.
10. Semantic colors are provided by `ThemeService.color()`.
11. No widget, Editor, or Toolbar hardcodes a semantic color.
12. Native Qt controls are used directly when no specific composition is needed.
13. A folder under `ui/widgets/`, `ui/editors/overlays/`, or
    `ui/tools/builtin/<new_category>/` is created only together with its first member.
14. No folder is created speculatively.

---

# 6. Alternatives considered

## 6.1 A single `ui/widgets/` folder for everything

Rejected. Would mix generic widgets, Editor overlays, and icon-based actions. Would blur responsibilities and violate the principle that overlays belong to their Editor.

## 6.2 A `ui/atoms/` folder with all visual primitives

Rejected. "Atom" is not an architectural concept in CranioZ. It would require a separate design language documentation and would not align with the existing structure (Toolbars, Tools, Editor overlays).

## 6.3 Icon-based actions as widgets, not Tools

Rejected. It would remove these actions from the ToolRegistry, making them undiscoverable by menus, automation, and future MCP. It would also violate `tools.md`, which establishes that user intentions are Tools.

## 6.4 All overlays as Workspace Overlays

Rejected. Workspace Overlays (`workspace.md` §7) are floating layers over a Region of Areas. Gizmos inside a Viewport are internal to the Editor and belong to its content. Conflating the two would break the Workspace's single rule (`workspace.md` §1.2).

## 6.5 Gizmos as generic widgets in `ui/widgets/`

Rejected. A gizmo is bound to a specific Editor's content area and participates in its hit-testing. It is not a generic widget.

---

# 7. Example

## 7.1 `Continuar` button in `steps_panel`

The `steps_panel` (a Workspace Overlay) needs a `Continuar` button.

- The button is a **generic widget**: it is used in the `steps_panel` and will likely appear in dialogs. It presents a primary action.
- It lives in `src/cranioz/ui/widgets/buttons/primary_button.py`.
- It consumes `ThemeService` for the "active" semantic color (green).
- It does not know what a Flow is; the `steps_panel` handles the click and dispatches the appropriate application command.

## 7.2 "Fechar janela atual" in a Viewport Toolbar

A Viewport toolbar wants a "close window" action.

- The action is a **Tool**: `tool.window.close`.
- It lives in `src/cranioz/ui/tools/builtin/window/close.py`.
- It is registered in the `ToolRegistry` at boot.
- The Viewport Editor's `ToolbarSpec` references it by
  `tool_id="tool.window.close"`.
- The Toolbar widget resolves the Tool, calls `is_available` and
  `is_enabled`, and presents the icon.
- The Tool's `icon` attribute is `"close"`. `ThemeService` resolves it.

## 7.3 Rotation gizmo over a 3D model

A Viewport3D Editor needs a rotation gizmo.

- The gizmo is an **Editor internal overlay**.
- It lives in
  `src/cranioz/ui/editors/overlays/gizmos/rotation_gizmo.py`.
- It is instantiated by the `Viewport3DEditor` inside its
  `content_widget()`.
- On interaction, it emits a Command through the Editor's `EditorContext`; it does not mutate the Scene directly.
- The Workspace and the LayoutRenderer never see the gizmo; only the Editor's content widget does.

## 7.4 "Active" green in the `steps_panel`

The `steps_panel` shows completed steps in green.

- The color is a **semantic color**: "active" / "completed".
- It is resolved via `ThemeService.color("active")`.
- The `steps_panel` does not hardcode `#00AA00` or similar.
- Future themes (e.g. high-contrast) can change the color without changing the panel.

---
