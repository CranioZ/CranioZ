# CranioZ Appearance System

**Document type:** Architecture and design specification  
**Status:** Proposed  
**Scope:** Application appearance, design tokens, surfaces, overlays, widgets, viewport presentation, and related settings  
**Technology:** Python, PySide6, Qt, VTK

## Documentation Structure

```text
docs/architecture/appearance/
├── README.md
├── appearance-architecture.md
├── themes-and-design-tokens.md
├── surfaces-and-overlays.md
├── modal-focus-effect.md
├── widget-system.md
├── viewport-appearance.md
├── persistence-and-settings.md
├── accessibility-and-performance.md
└── implementation-roadmap.md
```

Each document covers one responsibility within a shared architecture. **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, and **MAY** are normative terms.

---

# 1. `README.md`

## 1.1 Purpose and Scope

The Appearance System defines CranioZ's visual language and presentation behavior. It provides a consistent, accessible, configurable, and performant interface while allowing Editors to meet the needs of medical imaging, anatomical modeling, and surgical planning.

Appearance is an application-wide capability consumed by the Main Window, Workspace, Areas, Editors, toolbars, dialogs, overlays, and reusable widgets. Modules and Editors use shared appearance contracts rather than implementing independent visual systems.

The system covers themes and design tokens; widget styling and states; surfaces and overlays; optional transparency and blur; modal focus effects; viewport appearance; object display properties and their architectural boundaries; and user- and project-scoped visual settings.

The system does **not** own clinical rules, geometry or mesh modification, image processing or segmentation, anatomical semantics, Scene membership or object lifecycle, Workspace layout persistence, module or Editor registration, or clinical workflow execution. It may provide visual defaults and reusable presentation components for these systems.

## 1.2 Design Principles

- **Global consistency:** shared design tokens and defaults apply unless a documented local override is supported.
- **Explicit overrides:** an Editor may override only supported properties. Overrides affect only their declared target and never silently change global settings.
- **Separation of concerns:** theme, surface style, viewport appearance, object display properties, and clinical data are distinct. Appearance changes must not modify clinical data.
- **Reuse:** shared patterns should use reusable widgets or presentation services rather than module-specific duplicates.
- **Performance:** effects must not significantly degrade interaction with large volumes, complex meshes, or interactive VTK scenes. Each optional effect needs a practical fallback.
- **Accessibility:** the interface must remain usable without transparency, blur, animation, or color-only indicators. Keyboard focus, contrast, scalable elements, and reduced motion must be supported.

## 1.3 Terminology

| Term | Definition |
|---|---|
| Appearance | Visual presentation rules and configuration |
| Theme | Global interface palette and styling |
| Design token | Named value used by the design system |
| Surface | Visual background of a window, panel, or overlay |
| Overlay | Element layered above another interface region |
| Modal focus effect | Presentation effect that emphasizes an active modal dialog |
| Local override | Explicit deviation from an inherited default |
| Viewport appearance | Visual configuration of an imaging or rendering viewport |
| Display properties | Settings controlling how an individual object is rendered |
| Preset | Named collection of compatible appearance settings |

---

# 2. `appearance-architecture.md`

## 2.1 Architecture

The Appearance System is a shared presentation capability with four conceptual responsibilities:

1. Appearance configuration and resolution.
2. Theme and design-token management.
3. Widget and surface presentation.
4. Specialized viewport presentation.

It must not become a general-purpose state manager or an alternative to CranioZ's existing domain, application, or Settings architecture.

### Conceptual components

- **Appearance Configuration:** resolves application defaults, user preferences, project presentation settings, and permitted local overrides.
- **Theme Manager:** selects the active theme, resolves tokens, notifies interested components, and updates shared styling resources. It does not own module state, clinical objects, or rendering algorithms.
- **Design Tokens:** provide semantic values for colors, typography, spacing, borders, radii, and elevation.
- **Surface Presentation:** defines reusable treatments for windows, panels, dialogs, popovers, and overlays, including opacity, borders, shadows, and supported blur.
- **Viewport Appearance:** defines visual settings for imaging and rendering viewports, using the appropriate VTK rendering APIs where necessary.
- **Widget Library:** provides reusable components built on Qt, with custom widgets only where they add meaningful shared behavior or application-specific interaction.

## 2.2 Appearance Resolution

Resolve the effective appearance in this order:

1. Application defaults.
2. User preferences and active theme.
3. Project- or scene-scoped presentation settings, where supported.
4. Explicit Editor-instance overrides.
5. Accessibility constraints and capability fallbacks.
6. Rendering through the appropriate Qt or VTK APIs.

This is a conceptual resolution order, not a requirement that every property support every scope. Each property must define its supported scopes, inheritance behavior, and persistence policy.

For viewport properties, distinguish:

- **Global default:** fallback for compatible viewports.
- **Editor-type default:** optional default for a category of Editor.
- **Editor-instance override:** explicit value for one Editor instance.

Implement only the levels required by the property. In particular, per-instance viewport overrides should be supported where two instances of the same Editor may need different backgrounds. An override must identify its target and property; changing one property must not alter unrelated settings.

## 2.3 Inheritance and Reset

When no override exists, the property inherits the applicable default. Stored configuration must distinguish inherited values from explicit overrides rather than copying the current default. Removing an override restores inheritance. A theme change must not erase explicit viewport overrides unless the relevant property contract explicitly defines that behavior.

## 2.4 Integration with CranioZ

The Appearance System provides presentation infrastructure, not clinical functionality. Modules and Editors may declare appearance requirements through supported contracts; they must not create independent global theme managers or bypass shared services.

Settings must be read and updated through CranioZ's established Settings architecture. Appearance must not introduce a parallel configuration or persistence system. The Settings architecture remains responsible for settings ownership, validation, and storage; Appearance resolves and applies the resulting effective values.

Appearance changes normally use presentation APIs, not clinical Commands. If an operation also changes persistent clinical state, it must follow the application's Command and validation contracts.

## 2.5 Separation from Workspace

Workspace controls the arrangement and hosting of Areas and Editors; Appearance controls their presentation.

- Moving an Editor between Areas is a Workspace operation.
- Maximizing an Editor is a Workspace operation.
- Changing a viewport background is an appearance operation.
- Applying a translucent toolbar surface is an appearance operation.

The systems may interact but must not take ownership of each other's responsibilities.

## 2.6 Qt and VTK Boundaries

Qt handles ordinary application widgets, including menus, buttons, panels, dialogs, and controls. VTK renders 3D geometry and other visualization content in its rendering context. Qt stylesheet rules must not be assumed to affect VTK-rendered content; VTK-specific appearance must use appropriate rendering APIs.

## 2.7 Failure and Fallbacks

- Frosted glass falls back to translucent or solid presentation.
- Modal blur falls back to dimming without blur.
- An unavailable theme resource falls back to a valid default theme.
- Unsupported effects must not prevent a dialog or Editor from opening.

The interface must never become unusable because a decorative effect failed.

---

# 3. `themes-and-design-tokens.md`

## 3.1 Theme Modes

- **Light:** light interface surfaces and dark text.
- **Dark:** darker interface surfaces and appropriate text contrast.
- **System:** follows the operating system's preferred appearance when reliably available. If unavailable, CranioZ uses a documented fallback.

The initial default theme is a product decision; it must not be inferred from the availability of dark mode.

## 3.2 Theme and Viewport Independence

A theme styles interface components but does not dictate every viewport background. For example, a dark interface may contain a black CT viewport, a gray 3D viewport, and a white document preview. Medical imaging and anatomical visualization have contrast requirements distinct from ordinary interface surfaces.

## 3.3 Semantic Design Tokens

Tokens should represent semantic roles rather than component-specific hard-coded values. Names below are illustrative and may be refined during implementation.

**Color**
```text
color.background.application
color.background.panel
color.background.elevated
color.background.input
color.text.primary
color.text.secondary
color.text.disabled
color.text.inverse
color.border.default
color.border.subtle
color.border.focus
color.interactive.default
color.interactive.hover
color.interactive.pressed
color.interactive.selected
color.feedback.information
color.feedback.success
color.feedback.warning
color.feedback.error
```

Clinical annotation colors, anatomical colors, and segmentation palettes must remain separate from ordinary interface colors.

**Typography**
```text
typography.family.interface
typography.size.caption
typography.size.body
typography.size.label
typography.size.heading
typography.weight.regular
typography.weight.medium
typography.weight.semibold
```

Typography must support appropriate scaling and platform font rendering.

**Spacing**
```text
spacing.inline
spacing.stack
spacing.section
spacing.panel
```

**Shape and elevation**
```text
radius.control
radius.panel
radius.dialog
border.width.default
border.width.focus
elevation.panel
elevation.dialog
elevation.overlay
```

Elevation should remain restrained and must not replace clear structural boundaries.

## 3.4 Component States

Reusable widgets must define relevant states: default, hover, pressed, selected/checked, disabled, keyboard-focused, loading/busy, and invalid where applicable. Not every widget needs every state. Selected, focused, and hovered states must remain distinguishable.

## 3.5 Qt Implementation and Theme Changes

Use Qt palette and styling facilities where appropriate. `QPalette` may provide semantic colors for supported widgets; stylesheets may handle component-specific presentation when behavior is predictable.

Avoid scattered hard-coded colors and repeated broad stylesheet rules across the widget hierarchy. On theme change, the Theme Manager resolves tokens, updates shared styling resources, and notifies components that need refresh. VTK settings update only when explicitly defined to depend on theme-derived defaults. Theme changes must not discard user input, selection, or unrelated interaction state.

## 3.6 Extensibility

The architecture should permit additional themes without requiring per-widget theme-selection logic. Custom themes may be added in a later phase; importing arbitrary third-party themes is not required for the first release.

---

# 4. `surfaces-and-overlays.md`

## 4.1 Surface Styles

- **Solid:** opaque, predictable contrast, low rendering complexity. Default for persistent panels, clinical forms, configuration panels, and information-dense dialogs.
- **Translucent:** partial transparency and greater visual continuity, but potentially variable contrast. Suitable for selected floating toolbars, compact contextual controls, and overlays.
- **Frosted glass:** translucent surface with background blur. Suitable only for selected floating panels, popovers, or contextual tool palettes. It is optional and must not be required for all surfaces.

A conceptual surface model may include `background`, `opacity`, `blur_radius`, `border`, `corner_radius`, and `shadow`. This does not require a public class with exactly these fields; each component should use only properties it supports.

## 4.2 Defaults and Contrast

The Appearance System defines global surface defaults. Components may declare justified, explicit alternatives:

- Persistent panels and dense clinical forms: solid.
- Floating controls: optionally translucent.
- Selected popovers: optionally frosted glass.

A component must not silently change the global surface configuration. Text, icons, focus indicators, and control boundaries must remain readable over representative backgrounds. If contrast is insufficient, increase opacity or fall back to a solid surface.

## 4.3 Overlay and Modality

An overlay is layered above another interface region and may be a tool palette, floating control, selection menu, popover, modal backdrop, or temporary panel. Presentation and interaction semantics are separate: a visually prominent overlay is not necessarily modal.

A modal dialog blocks interaction with its designated context until dismissed or completed. A non-modal overlay permits continued interaction. Surface styling does not determine modality; the relevant dialog or interaction component owns that behavior.

## 4.4 Qt and Platform Constraints

Transparency and background effects vary by window type, operating system, compositor, and rendering configuration. `QGraphicsBlurEffect` must not be assumed to blur pixels in an independently rendered window behind another window. Frosted glass requires a verified composition strategy for the target widget and platform, plus a solid fallback.

## 4.5 Performance

Decorative effects should not trigger continuous full-window recomposition when content has not changed. Avoid unnecessary blur recalculation and large intermediate buffers. Reduce or disable effects if they cause noticeable lag during interactive medical visualization.

---

# 5. `modal-focus-effect.md`

## 5.1 Purpose and Behavior

The Modal Focus Effect emphasizes an eligible modal dialog by visually subduing the Workspace behind it. The dialog remains sharp and readable, and normal Qt focus and modality rules remain authoritative. When the dialog closes, the background returns to its normal appearance.

The background is dimmed; blur is optional. The effect must not be applied automatically to every popup or notification.

## 5.2 Eligibility

| Interaction | Policy |
|---|---|
| Editor selection | Enable |
| Module selection | Enable |
| General settings dialog | Evaluate by context |
| Destructive confirmation | Enable dimming; blur optional |
| Brief notification | Disable |
| Non-modal popover | Disable global modal focus |
| Persistent floating toolbar | Disable |

Eligibility policy should be centralized rather than independently implemented by each module.

## 5.3 Configuration

The global settings model may include:

```text
modal_focus.enabled
modal_focus.blur_enabled
modal_focus.blur_strength
modal_focus.dimming_strength
modal_focus.animation_enabled
```

Do not expose every low-level parameter in the initial UI; an enable/disable option and sensible default intensity may be sufficient.

## 5.4 Interaction and Fallback Requirements

The effect is presentational only. It must not change modality, independently block input, modify Workspace layout or clinical state, change viewport camera/rendering settings, or prevent access to dialog controls. The dialog remains responsible for focus, keyboard behavior, confirmation, cancellation, and dismissal.

If blur is unavailable, too expensive, or incompatible with the active rendering configuration, use dimming alone. If all effects are disabled, the dialog must remain functional and distinguishable through its surface, border, elevation, and focus behavior.

## 5.5 Implementation and Accessibility

Validate the implementation against the actual Workspace composition, including VTK widgets, multiple Areas, docked and floating widgets, resizing, HiDPI, multiple monitors, and nested dialogs. Do not assume a screenshot or cached Workspace representation is always valid.

**Status:** Blur behind VTK renderers is platform- and compositor-dependent. Treat it as experimental; dimming-only is the initial default, and blur requires explicit opt-in.

Users must be able to disable the effect. Reduced-motion settings must be respected. The dialog must remain understandable without blur, and the effect must not cause unexpected focus changes.

---

# 6. `widget-system.md`

## 6.1 Purpose and Principles

The Widget System provides reusable interface components built on PySide6 and Qt; it does not replace Qt's widget framework.

- **Native components first:** use standard Qt widgets when they meet functional and visual requirements.
- **Customize repeated patterns:** create custom components when they provide shared behavior, consistent states, a coherent combination of native controls, a recurring CranioZ interaction, or integration with shared appearance configuration.
- **Avoid premature abstraction:** do not wrap a native component without meaningful value or duplicate Qt behavior unnecessarily.
- **Separate presentation from domain logic:** widgets may manage local interaction state and present values, but must not own clinical validation, geometry algorithms, or domain mutations. State-changing interactions use the appropriate application contracts.

## 6.2 Widget Categories

**Buttons and tools:** `IconButton`, `ToolButton`, `SegmentedControl`, and `Toolbar`. They standardize dimensions, icon alignment, tooltips, selection states, keyboard focus, and feedback. A `ToolButton` invokes a registered Tool or another explicit action; it does not implement the Tool's clinical operation.

**Workspace navigation:** module and Editor selectors, add-item buttons, Editor title-bar controls, maximize/restore, and close/remove controls. These use explicit Workspace and module-management interfaces and must respect registration and lifecycle contracts.

**Property controls:** numeric slider with value field, numeric input with units, color selector, opacity control, visibility toggle, and coordinate/angle controls. They must preserve value meaning and units; clinical validation belongs to the appropriate domain or application layer.

**Dialogs and selection:** Editor and module selection, reusable confirmation and message dialogs, searchable item selectors, and contextual popovers. They should share visual and keyboard conventions.

**3D interaction:** translation and rotation manipulators, object-positioning controls, and planning handles. These may combine Qt and VTK interaction mechanisms but must preserve the separation between visual interaction, application Commands, and domain operations.

## 6.3 Widget Contracts

Each custom widget must document its purpose, inputs and outputs, supported states, keyboard interaction, accessibility, theme-change behavior, resource ownership, application-state effects, and failure/fallback behavior. State must be exposed through explicit APIs; consumers must not need to inspect internal child widgets.

## 6.4 Styling, Icons, and Internationalization

Widgets use design tokens and shared appearance services; they must not independently define global colors, typography, or surface defaults. Component-specific details may remain local when they are not reusable design-system properties.

Widgets must respond to theme changes without reconstruction unless required by a documented implementation limitation. Theme changes must not discard input or selection. Use consistent icon style, sizing, and alignment. Icon-only controls need tooltips and accessible names; icons must not be the sole means of conveying critical information. Clinical symbols and anatomical annotations must remain distinct from ordinary UI icons.

All user-visible text must be translatable. Identifiers, class/API names, and internal tokens should remain language-independent. Layouts must accommodate localized text without truncating important content.

## 6.5 Recommended Package Organization

```text
src/cranioz/ui/
├── appearance/
│   ├── theme_manager.py
│   ├── design_tokens.py
│   └── surface_styles.py
└── widgets/
    ├── buttons/
    ├── controls/
    ├── dialogs/
    ├── navigation/
    ├── overlays/
    └── selection/
```

Treat this as a responsibility-based proposal, not a requirement to create every directory immediately. A category with only one component does not necessarily need a subpackage. Settings storage and ownership remain in CranioZ's established Settings architecture.

---

# 7. `viewport-appearance.md`

## 7.1 Purpose and Properties

Viewport Appearance defines the presentation of imaging and rendering regions hosted by Editors. It is separate from the global theme because CT, anatomical visualization, and document presentation may require different visual environments.

Depending on Editor capabilities, properties may include background color or gradient; foreground and annotation colors; grid and axis visibility; rendering mode; surface representation; lighting and material presentation; line width; and annotation scale. Not every Editor must expose every property.

## 7.2 Scope and Overrides

The effective viewport configuration may resolve from a global default, an optional Editor-type default, and an explicit Editor-instance override. Support only the levels needed by the property. Per-instance overrides are important when two instances of the same Editor need different backgrounds.

An Editor inherits defaults unless it explicitly overrides supported properties. Overrides must identify the target and properties; overriding a background must not change the global theme, Qt panel surfaces, anatomical object colors, annotation meaning, or underlying imaging data.

An explicit local override must survive theme changes unless its contract says otherwise. Removing it restores inheritance. A global change must not overwrite a local override.

## 7.3 Object Display Properties

Viewport appearance controls the visual environment. Object display properties control individual-object rendering, such as color, opacity, visibility, surface/wireframe representation, and rendering-specific material properties.

These properties must be owned by the appropriate presentation/display model—not automatically embedded in geometric objects or the global theme. Changing an object's color must not change its geometry; hiding it must not remove it from the Scene. Scene membership, object lifecycle, geometry, imaging values, transforms, and clinical measurements remain separate.

Object display properties and project-specific viewport settings may be persisted with a project or scene when needed to reproduce its intended presentation. They are not application theme tokens.

## 7.4 Clinical Integrity and VTK

Changing a background, material, visibility, or display mode must not modify clinical geometry or image values. Any future operation combining presentation with a data-changing action must follow the application's Command and validation contracts.

Apply VTK-specific settings through the rendering infrastructure. Distinguish renderer background configuration, actor properties, lighting/materials, annotation rendering, and camera/interaction state. A background change should not require unnecessary reconstruction of the scene or actors.

## 7.5 Presets and Validation

Named presets may configure compatible presentation properties, for example:

- Bone visualization
- Soft-tissue visualization
- Segmentation review
- General 3D planning
- Presentation and export

Classify presets by scope: user preference/library presets differ from project-specific presentation presets. Presets must not silently change clinical data.

Validate viewport appearance against CT/CBCT slices, bone and soft-tissue surfaces, overlapping anatomy, landmarks, measurement annotations, and high-/low-density content. Background and foreground colors must preserve visibility of relevant information.

---

# 8. `persistence-and-settings.md`

## 8.1 Purpose and Ownership

Appearance persistence must preserve user preferences while allowing projects to reproduce their intended presentation when required.

Use CranioZ's established Settings architecture for configuration ownership, validation, and storage. The Appearance System defines setting semantics and applies effective values; it must not introduce a parallel settings store.

## 8.2 Persistence Scopes

- **Application/user preferences:** theme mode, interface scale, general typography preferences, default surface style, modal-focus preference, default viewport appearance, and reduced-motion preference.
- **Project/scene presentation:** explicitly configured object display properties, project-specific viewport overrides, saved presentation presets, and visual configuration needed to reproduce a planning view.
- **Session-only state:** hover feedback, pointer feedback, transient modal effects, temporary selection highlights, and unsaved appearance experiments.

Persist only properties whose scope and reproducibility requirements justify it.

## 8.3 Scope Decision Table

| Property | Recommended scope |
|---|---|
| Application theme | User preferences |
| Interface scale | User preferences |
| Global surface style | User preferences |
| Modal-focus preference | User preferences |
| Default viewport appearance | User preferences |
| Editor-type default | Application defaults or user preferences, as defined by the property contract |
| Editor-instance override | Project/scene if reproducibility is intended; otherwise session or Editor configuration as specified by the Workspace contract |
| Object color, opacity, visibility | Project/scene when relevant to the intended presentation |
| Temporary hover state | Session only |
| Temporary modal blur | Session only |
| Saved visual preset | User library or project, according to intended use |

If a setting must be reproducible on another machine when a project opens, store it with the project. If it reflects personal comfort or environment, use user preferences. If it is meaningful only during a session, keep it session-only.

The final storage format and ownership of Editor configuration must align with the Workspace and project-persistence specifications.

## 8.4 Inheritance and Explicit Values

Represent a property as inherited or explicitly overridden when both behaviors are supported. For example:

```text
viewport_background:
  source: global_default
```

or:

```text
viewport_background:
  source: local_override
  value: configured_color
```

These examples define semantics, not a required serialization format. Never confuse an explicit value with a copied default; global changes should not unexpectedly overwrite local configuration.

## 8.5 Reset, Migration, and Validation

Support resetting an override to its inherited value where applicable. Use explicit migration or compatibility mechanisms when configuration changes between versions. Unknown optional appearance settings must not make a clinical project unreadable.

Validate persisted settings before use. Invalid colors, unsupported values, missing presets, and incompatible effects must resolve to safe defaults. Appearance configuration must not execute arbitrary content or bypass application validation.

Appearance preferences must not be stored in clinical domain objects merely because those objects are rendered. Conversely, project-specific display properties must not exist only in user preferences when that would prevent reproduction on another machine.

---

# 9. `accessibility-and-performance.md`

## 9.1 Accessibility

The interface must support reliable clinical work across supported hardware, display configurations, and user preferences. Effects are optional enhancements, never prerequisites for understanding the interface or completing a workflow.

- **Contrast:** use WCAG AA contrast criteria as a baseline for ordinary interface text and controls, while separately evaluating medical visualization needs. Increase opacity or use solid surfaces when transparency reduces readability.
- **Color independence:** do not communicate selection, active Editors, validation errors, warnings, destructive actions, or object visibility through color alone. Add labels, icons, outlines, shapes, or textual feedback. Clinical annotation colors require domain-aware treatment.
- **Keyboard and focus:** custom widgets must support appropriate keyboard navigation. Focus indicators must remain visible in light and dark themes. Modal effects must not change focus or intercept input unexpectedly.
- **Motion:** animations should be restrained and nonessential. Support reduced motion by disabling or shortening transitions; never rely on animation to communicate essential state changes.
- **HiDPI:** custom widgets must follow Qt's high-DPI behavior and not assume logical and physical pixels are interchangeable. Test VTK rendering and interaction coordinates separately.

## 9.2 Performance and Platform Compatibility

Evaluate effects under realistic CranioZ workloads: large CBCT volumes, synchronized viewports, high-polygon meshes, continuous rotation/zoom, frequent annotation updates, and modal dialogs over active VTK renderers.

The implementation should avoid unnecessary widget or scene reconstruction, continuous blur processing, large intermediate buffers, unnecessary global stylesheet recalculation, and unresponsive transitions. Reuse cached resources where correct and provide fallbacks when effects are expensive or unavailable.

Transparency, blur, and window composition differ across operating systems. The supported-platform matrix must define expected behavior. Use capability checks or controlled fallbacks rather than assuming identical support.

## 9.3 Testing

Test light/dark themes; theme changes with Editors open; local overrides across theme changes; solid/translucent/frosted surfaces; modal focus with blur enabled and disabled; reduced motion; keyboard navigation; HiDPI and multiple monitors; representative VTK workloads; and invalid persisted settings.

Performance testing must measure interactive responsiveness, not only static rendering benchmarks.

---

# 10. `implementation-roadmap.md`

The roadmap prioritizes stable contracts and repeated UI needs before experimental effects. Phase order is a proposed implementation sequence, not an approval of every feature.

## Phase 1 — Design System Foundation

**Scope:** semantic tokens; light/dark themes; system-theme behavior where supported; theme switching; standard widget states; shared styling resources; global appearance configuration and its integration with Settings.

**Acceptance:** common widgets use shared tokens; theme changes require no manual per-module styling; explicit viewport overrides survive theme changes; invalid settings resolve safely; standard Qt widgets remain usable.

## Phase 2 — Core Widget Library

**Scope:** icon/tool buttons, standard toolbars, property controls, selection components, module/Editor navigation, icon and tooltip conventions.

**Acceptance:** repeated patterns use shared components; APIs are explicit; keyboard focus and accessible names work; visual states are consistent; clinical operations remain outside presentation widgets.

## Phase 3 — Surfaces and Overlays

**Scope:** solid and translucent surfaces; capability-based frosted glass; shared overlay presentation; fallback behavior; surface configuration and validation.

**Acceptance:** components use the shared surface system; solid surfaces work on all supported platforms; unsupported effects do not block interaction; contrast and performance remain acceptable.

## Phase 4 — Viewport Appearance and Presets

**Scope:** global viewport defaults; optional Editor-type defaults; per-instance overrides and inheritance; background color/gradient; named viewport presets; user-versus-project preset scope.

**Acceptance:** inheritance and overrides behave predictably; overrides survive theme changes; settings do not modify clinical data; representative clinical content remains visible.

## Phase 5 — Persistence, Migration, and Validation

**Scope:** integration with Settings; user-preference storage; project/scene display-property storage; inheritance and explicit-value serialization; reset-to-inherited behavior; migrations; validation and safe defaults.

**Acceptance:** settings use the correct owner and scope; project presentation is reproducible when intended; unknown optional settings do not make projects unreadable; invalid settings resolve safely.

## Phase 6 — Modal Focus Effect (Experimental)

**Scope:** centralized eligibility policy; Workspace dimming; optional blur behind explicit opt-in; enable/disable setting; reduced-motion support.

**Acceptance:** dimming alone clearly emphasizes the dialog; optional blur degrades gracefully and does not interfere with VTK rendering or keyboard focus; dialogs remain fully functional with effects disabled.

**Status:** blur behind VTK is platform- and compositor-dependent. Keep dimming-only as the initial default and treat blur as experimental.

## Phase 7 — Custom Themes and Extensibility

**Scope:** adding custom themes without per-widget theme-selection logic; theme-resource validation; theme-authoring documentation.

**Acceptance:** a new theme can be added without changing existing widget implementations. Third-party theme import is not required.

---

## Proposed Architecture Decision Records

The following are **candidate ADR topics**, not approved decisions. Create individual ADRs only after the relevant decisions are reviewed and accepted, using CranioZ's existing ADR numbering and format. Avoid duplicating full specification text; link to the relevant sections instead.

- Appearance ownership and integration with Settings.
- Theme modes and semantic design tokens.
- Supported scope and inheritance for viewport appearance.
- Ownership and persistence of object display properties.
- Surface styles and platform fallbacks.
- Modal focus effect and experimental blur policy.
- Custom widget criteria and Qt/VTK presentation boundaries.
- Persistence scopes, migrations, and validation.
- Accessibility and performance requirements.
'''
target=Path('/mnt/data/CranioZ_Appearance_System_Corrected.md')
target.write_text(out, encoding='utf-8')
print(target, target.exists(), target.stat().st_size, len(out.splitlines()))
