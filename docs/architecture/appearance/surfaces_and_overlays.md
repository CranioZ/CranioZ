# Surfaces and Overlays

**Document type:** Architecture specification
**Status:** Accepted
**Scope:** Surface styles, overlay composition, translucency, and platform fallbacks
**Depends on:** `README.md`, `themes-and-design-tokens.md`, `appearance-architecture.md`
**References:** ADR-0014 (Widget Toolkit Selection)

---

## 1. Purpose

This document defines how CranioZ renders surfaces (windows, panels, dialogs) and overlays (floating toolbars, popovers, modal backdrops, selection menus).

It establishes:

- The three surface styles: **Solid**, **Translucent**, and **Simulated Glass**.
- The component-to-surface mapping: which components use which style.
- The Qt implementation strategy for each style.
- The fallback behavior when effects are unavailable.
- The relationship between surfaces and the theme (color is derived from tokens; opacity is derived from tokens).
- The relationship between overlays and modality (styling is independent of interaction semantics).

The styling of medical visualization (VTK viewports, LUTs, segmentation overlays) is out of scope. See `viewport-appearance.md`.

---

## 2. Design Principles

1. **Structure before decoration.** Surfaces exist to organize content. Effects (translucency, shadow) are secondary and must not obscure structure or reduce contrast.
2. **Deterministic composition.** A translucent surface is composed from a base color token and an opacity token. Widgets do not define their own translucency.
3. **Theme-aware by construction.** Surfaces change with the active theme. A translucent surface on `DARK` and `LIGHT` uses the same opacity but different base colors, producing appropriate results in both.
4. **Solid by default.** Persistent panels and clinical forms are solid. Translucency is reserved for floating or contextual elements.
5. **Simulated glass, not real blur.** CranioZ does not use real background blur (`QGraphicsBlurEffect` or platform-specific blur). It uses a simulated glass effect built from translucency, gradient, and border. See §5.
6. **Accessibility is non-negotiable.** Text, icons, and focus indicators must remain readable over any surface. If contrast is insufficient, opacity is increased or the surface becomes solid.
7. **Modality is orthogonal to styling.** A visually prominent overlay is not necessarily modal. The dialog or interaction component owns modality; the surface system owns appearance.
8. **Performance matters.** Surfaces must not cause continuous recomposition when content has not changed. Effects are static or triggered by user interaction, not by animation loops.

---

## 3. Surface Styles

CranioZ supports three surface styles. Every surface in the application belongs to exactly one of them.

### 3.1 Solid

- **Appearance:** Fully opaque background. No translucency.
- **Contrast:** Deterministic. The background color is the theme's `color.background.panel` or `color.background.elevated`.
- **Performance:** Lowest cost. No composition required.
- **Recommended for:** Persistent panels (Left Area, Right Area, Bottom Area), clinical forms, configuration dialogs, data tables, toolbars that are always docked.

### 3.2 Translucent

- **Appearance:** Base color with an alpha channel. The underlying content is visible through the surface.
- **Contrast:** Depends on the underlying content. The composed color is computed at compile time from `base_color + opacity`. See `themes-and-design-tokens.md` §6.
- **Performance:** Low cost. Alpha composition is handled by the OS.
- **Recommended for:** Floating toolbars, contextual tool palettes, popovers that need visual continuity with the surrounding workspace.

### 3.3 Simulated Glass

- **Appearance:** Translucent background with a subtle gradient, a 1px highlight border, and optionally a 1px inner shadow. Visually reads as "glass" without actual blur.
- **Contrast:** Same rules as Translucent. The gradient and border enhance the affordance but do not change the underlying composited color.
- **Performance:** Low cost. The gradient and border are static. No blur computation.
- **Recommended for:** Floating toolbars over VTK viewports, popovers that need to feel elevated without occluding clinical content.

**This is the only "glass" style in CranioZ.** Real background blur is not supported. See §5.

---

## 4. Component-to-Surface Mapping

The following table defines which components use which surface style. It is normative.

| Component | Style | Rationale |
|---|---|---|
| Left Area (persistent) | Solid | Dense data; contrast matters |
| Right Area (persistent) | Solid | Dense controls; contrast matters |
| Bottom Area (persistent) | Solid | Console, history, logs; contrast matters |
| Central Area (persistent) | Solid | Hosts Editors; VTK background is per-viewport |
| Top Bar | Solid | Structural element; must be anchored |
| Dialogs (configuration, import, project management) | Solid | Clinical forms; contrast matters |
| Message boxes, confirmations | Solid | Critical decisions; contrast matters |
| Toolbars docked to an Area | Solid | Structural element |
| Toolbars floating over a viewport | Simulated Glass | Contextual, must not occlude |
| Popovers (object properties, presets) | Translucent | Contextual, must remain readable |
| Selection menus, context menus | Solid | Critical choices; contrast matters |
| Modal backdrop | Translucent | Emphasizes the dialog without hiding the workspace |
| Notification banners | Translucent | Non-blocking, must remain readable |
| Tool palettes (segmentation, measurement) | Simulated Glass | Contextual, must remain readable over VTK |
| Splash screen | Solid | Standalone window |
| Tooltips | Solid | Must be readable in any background |

### 4.1 Rules derived from the mapping

- If a component is **persistent** or **hosts clinical decisions**, it is **Solid**.
- If a component is **contextual** and **must not occlude** content, it is **Translucent** or **Simulated Glass**.
- A component MUST NOT change its surface style based on the theme. The mapping is fixed.
- A component MUST NOT implement its own translucency. It requests a named surface role from the `ThemeService` or uses a pre-composed surface from `CompiledStyles`. See `themes-and-design-tokens.md` §9.4.

---

## 5. Frosted Glass — Definition and Constraints

### 5.1 What CranioZ means by "frosted glass"

"Frosted glass" in CranioZ is **simulated glass**, composed of:

1. A translucent background (`base_color + surface.opacity.toolbar` or similar).
2. A subtle vertical gradient (from `effect.elevation_*` colors).
3. A 1px highlight border (`border.width.default` in `color.border.subtle`).
4. Optional 1px inner shadow.

The visual result reads as a glass panel without any blur computation.

### 5.2 What CranioZ does NOT do

Real background blur is not supported. The reasons are technical and normative:

1. **`QGraphicsBlurEffect` cannot see VTK content.** It blurs pixels rendered by Qt, not pixels rendered by VTK. A translucent panel over a VTK viewport with `QGraphicsBlurEffect` shows the VTK content unblurred behind it. The result is inconsistent with the glass appearance.
2. **Platform APIs require separate windows.** Windows DWM (`DwmEnableBlurBehindWindow`) and macOS `NSVisualEffectView` work on separate windows, not on embedded Qt widgets. CranioZ's workspace is a single window with multiple embedded viewports; platform blur is not applicable.
3. **Multiple VTK viewports break composition.** Even if a window-level blur were possible, the workspace frequently hosts 4+ VTK viewports of different sizes. Blurring the window and then compositing VTK viewports on top produces inconsistent edges and artifacts.
4. **Performance.** Real-time blur on 4K displays is expensive, especially while the user rotates a 3D volume or pans an MPR view.
5. **Cross-platform inconsistency.** Blur behaves differently on Windows, macOS, and Linux. Simulated glass is identical everywhere.

Simulated glass is deterministic, cross-platform, works over VTK, and is visually consistent. It is the only frosted glass that CranioZ supports.

### 5.3 Widget implementation of simulated glass

A widget that declares `simulated_glass` support:

1. Sets `Qt.WA_TranslucentBackground` on itself.
2. Requests the composed surface color from `CompiledStyles.surface_color("toolbar")` (or the relevant role).
3. Paints the composed background.
4. Paints the subtle gradient overlay.
5. Paints the 1px highlight border.
6. Optionally paints the 1px inner shadow.

The `ThemeCompiler` provides the composed surface and the gradient stops. The widget does not compute any color, gradient, or opacity itself.

The widget MUST NOT use `QGraphicsBlurEffect`. If a widget needs it, the design must be revisited.

---

## 6. Overlays and Modality

### 6.1 Definitions

- **Overlay:** A widget rendered above another region of the interface. Overlays include floating toolbars, popovers, context menus, notification banners, modal backdrops, and tool palettes.
- **Modality:** The interaction semantic that blocks input to a designated context until the modal element is dismissed.
- **Surface style:** The visual treatment of an overlay (solid, translucent, simulated glass).

### 6.2 Independence

Surface style and modality are independent:

- A modal dialog has a **solid** surface. Its backdrop (the dimming layer over the workspace) has a **translucent** surface.
- A floating toolbar has a **simulated glass** surface, and is **not modal**. It does not block input to the workspace.
- A context menu has a **solid** surface, and is **modal in the sense that it intercepts input until dismissed**, but its backdrop is not dimmed.
- A notification banner has a **translucent** surface, and is **not modal**.

A widget MUST NOT infer modality from its surface style. Modality is declared by the component that owns the interaction (a `QDialog`, a `QMenu`, a custom overlay manager). The appearance system only styles the surface.

### 6.3 Modal focus effect

The modal focus effect (dimming the workspace behind a modal dialog) is specified in `modal-focus-effect.md`. It uses the `surface.opacity.modal_backdrop` token and is independent of the surface style of the dialog itself.

---

## 7. Fallbacks and Platform Constraints

### 7.1 Fallback policy

When a surface style cannot be rendered as specified, the application falls back to a lower-complexity style:

| Declared style | Fallback |
|---|---|
| Simulated Glass | Translucent |
| Translucent | Solid |
| Solid | (no fallback; solid is always available) |

Fallbacks are transparent to widgets: a widget declares the intended style, and the `ThemeCompiler` provides the composed surface. If the composed surface is unavailable (for example, a corrupted theme), the compiler falls back to Solid and logs a `WARNING`.

### 7.2 Platform constraints

- **Windows, macOS, Linux:** Translucency via `Qt.WA_TranslucentBackground` is supported on all three platforms. Alpha composition is handled by the OS.
- **Multiple monitors with different DPI:** Translucency is supported; the composed surface is in logical pixels and is scaled by Qt's high-DPI mechanism.
- **Remote desktop sessions:** Some remote desktop protocols render translucency as solid color. CranioZ does not detect this; the composed surface remains translucent at the Qt level, and the remote protocol resolves it. No fallback is needed at the application level.
- **Older GPUs or software rendering:** Alpha composition is still supported by Qt. Simulated glass (which is just translucency + gradient + border) works. No specific detection is required.

### 7.3 What CranioZ does NOT attempt

- **Detecting blur support:** Because CranioZ does not use real blur, there is no blur capability to detect.
- **Detecting compositor capabilities:** Translucency is handled by Qt; CranioZ does not query platform compositors.
- **Per-platform appearance differences:** Simulated glass is identical on all platforms. Differences are limited to font rendering and native widget chroming, which are outside the surface system.

---

## 8. Widget Contracts

### 8.1 Declaring a surface style

A widget declares its surface style through a class attribute or a constructor parameter:

```python
class FloatingToolbar(QToolBar):
    surface_role = "toolbar_simulated_glass"