# Themes and Design Tokens

**Document type:** Architecture specification  
**Status:** Accepted  
**Scope:** Theme modes, semantic design tokens, surface opacity, and theme compilation  
**Depends on:** `../../../../README.md`, `appearance-architecture.md`, `docs/architecture/startup.md`  
**References:** ADR-0014 (Widget Toolkit Selection)  
**Minimum Qt version:** PySide6 6.5.0

---

## 1. Purpose

This document defines the canonical semantic design tokens used by the CranioZ Appearance System, the concrete values for the `DARK` and `LIGHT` themes, and the mechanism that compiles tokens into Qt stylesheets and related visual resources.

It is normative. Widgets, panels, dialogs, toolbars, and Editor chrome MUST use the tokens defined here for shared visual properties.

Shared visual properties MUST NOT be hardcoded in individual widgets. Component-specific constraints and intrinsic dimensions MAY be defined locally when they do not belong to the shared visual system. The definitive boundary is specified in §10.

**Out of scope:**

- **Clinical colors:** segmentation palettes, validation severity colors, anatomical label colors, and other colors that convey clinical meaning. These belong to the imaging domain and MUST NOT change with the shell theme.
- **Viewport label colors:** Axial, Coronal, Sagittal, 3D, and other viewport identifiers, including their active and inactive states. See `viewport-appearance.md`.
- **VTK-specific appearance:** lookup tables (LUTs), transfer functions, and per-viewport renderer backgrounds. See `viewport-appearance.md`.
- **Icons:** icon assets and naming conventions are defined in `icons.md`.
- **Modal focus effect:** workspace dimming and optional focus effects are defined in `modal-focus-effect.md`.
- **Workspace layout:** panel arrangement, Editor hosting, and Area configuration belong to the Workspace architecture.

This document governs the shell appearance of the application: windows, panels, dialogs, toolbars, and ordinary Qt controls.

---

## 2. Theme Modes

CranioZ exposes three theme modes:

| Mode | Description |
|---|---|
| `DARK` | Dark interface surfaces with appropriate text contrast. Default for medical imaging contexts. |
| `LIGHT` | Light interface surfaces with dark text. Optional, user-selectable. |
| `SYSTEM` | Follows the operating system's preferred color scheme when available. |

The initial application default is `DARK`.

### 2.1 Resolution model

`SYSTEM` is a configuration mode, not a `ThemeName`.

`ThemeService` resolves the selected `ThemeMode` into a concrete `ThemeName`. `ThemeCompiler` only receives a resolved theme and MUST NOT handle operating-system theme detection.

```python
from enum import StrEnum


class ThemeMode(StrEnum):
    DARK = "dark"
    LIGHT = "light"
    SYSTEM = "system"


class ThemeName(StrEnum):
    DARK = "dark"
    LIGHT = "light"
    # HIGH_CONTRAST reserved for a future phase.
```

The effective theme is always concrete. `SYSTEM` MUST never be exposed as the active `ThemeName`.

### 2.2 SYSTEM resolution

When the selected mode is `SYSTEM`, the active theme is resolved from `QStyleHints.colorScheme()`.

| Qt color scheme | Resolved theme |
|---|---|
| `Qt.ColorScheme.Dark` | `DARK` |
| `Qt.ColorScheme.Light` | `LIGHT` |
| `Qt.ColorScheme.Unknown` | `DARK` |

`Unknown` is returned when the platform does not expose a preference or reports an unspecified state.

The fallback to `DARK` matches the application default and avoids an unexpected first-launch appearance.

### 2.3 SYSTEM reactivity

When the selected mode is `SYSTEM`, `ThemeService` subscribes to `QStyleHints.colorSchemeChanged` when the platform exposes the signal.

When the operating-system preference changes, the service:

1. Reads the new color scheme.
2. Resolves the corresponding `ThemeName`.
3. Retrieves the matching `ThemeTokens`.
4. Recompiles the visual resources.
5. Applies the updated appearance.
6. Emits `theme_changed`.

If the signal is unavailable, `SYSTEM` is resolved at application startup and does not react to runtime operating-system changes.

This limitation MUST be documented in the user-facing Settings help.

### 2.4 Boot order

The theme MUST be applied before the first application window is shown.

The startup sequence, defined in `docs/architecture/startup.md`, performs:

1. `QApplication` creation.
2. `QSurfaceFormat` and OpenGL context configuration.
3. `SettingsService` initialization and reading of `appearance.theme_mode`.
4. `ThemeService` construction and effective theme resolution.
5. `ThemeCompiler` compilation and application.
6. Main window construction and display.

If `appearance.theme_mode` is missing, invalid, or unreadable:

- `ThemeMode.DARK` is used.
- A `WARNING` is logged with the invalid value and fallback.
- Application startup continues.

If the Settings file is corrupt or a schema migration fails:

- `ThemeMode.DARK` is used.
- A `WARNING` is logged.
- `SettingsService` reports the failure to the user at the first appropriate opportunity.
- Application startup continues.

Appearance configuration MUST NOT prevent the application from starting.

---

## 3. Design Token Principles

1. **Semantic, not chromatic.** Tokens are named by role, such as `color.text.primary`, never by their current color value. A token name MUST remain valid if its underlying value changes.

2. **Closed set, additive only.** The token list is closed for the current phase. Adding a token requires a concrete use case and justification in a PR. Adding a new category requires an ADR amendment.

3. **Single source of truth.** Every token value for every supported theme is defined in Python dataclasses. Widgets MUST NOT maintain independent copies of shared token values.

4. **Cross-theme completeness.** Every token MUST exist in every supported theme. Missing tokens are a compilation error.

5. **Independent from medical visualization.** Clinical colors and viewport presentation properties are not shell design tokens.

6. **Independent from i18n.** Tokens and translations are orthogonal. Token names MUST NOT contain user-facing strings.

7. **Shared properties use tokens; local properties may be local.** The definitive boundary is specified in §10.

8. **Translucency is composed, not hardcoded.** A translucent surface combines a theme-dependent base color with an opacity token. Widgets MUST NOT construct these colors independently.

9. **Accessibility is testable.** Color contrast and relevant non-text visual indicators are verified by automated tests.

10. **Graceful degradation.** Unsupported visual effects MUST have a defined fallback and MUST NOT prevent a widget or window from being displayed.

---

## 4. Token Categories

The Appearance System defines seven token categories:

| Category | Purpose |
|---|---|
| **Colors** | Backgrounds, text, borders, interactive states, and feedback |
| **Typography** | Font family, size scale, and weight scale |
| **Spacing** | Shared layout spacing scale |
| **Dimensions** | Standard control heights and icon sizes |
| **Borders** | Border widths and corner radii |
| **Effects** | Focus-independent overlays, selection highlights, and elevation |
| **Surfaces** | Opacity values for translucent surfaces |

`Components` is reserved for a future phase. Component-specific tokens, such as `button.primary.background`, MUST only be introduced when implemented components demonstrate a concrete need for shared component-level values.

---

## 5. Canonical Token List (Phase 2)

This is the closed token set for Phase 2. Tokens are listed by their Python attribute path.

### 5.1 Colors (19 tokens)

```python
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

### 5.2 Typography (8 tokens)

```python
typography.family.interface

typography.size.caption
typography.size.body
typography.size.label
typography.size.heading

typography.weight.regular
typography.weight.medium
typography.weight.semibold
```

### 5.3 Spacing (5 tokens)

```python
spacing.xs  # 4 logical px
spacing.sm  # 8 logical px
spacing.md  # 16 logical px
spacing.lg  # 24 logical px
spacing.xl  # 32 logical px
```

### 5.4 Dimensions (2 tokens)

```python
dimension.control_height  # 28 logical px
dimension.icon_size  # 20 logical px
```

### 5.5 Borders (5 tokens)

```python
border.width.default  # 1 logical px
border.width.focus  # 2 logical px

radius.control  # 4 logical px
radius.panel  # 6 logical px
radius.dialog  # 8 logical px
```

### 5.6 Effects (5 tokens)

```python
effect.hover_overlay
effect.selection_highlight

effect.elevation_panel
effect.elevation_dialog
effect.elevation_overlay
```

Focus indicators use `color.border.focus` and `border.width.focus`. They MUST NOT be duplicated as separate effect tokens.

Elevation values are structured specifications, not arbitrary strings. The ThemeCompiler translates them into `QGraphicsDropShadowEffect` for widgets that declare support.

Qt stylesheets do not expose a native `box-shadow` equivalent. When elevation effects are unavailable or unsuitable, the fallback is a subtle border and background differentiation.

### 5.7 Surfaces (3 tokens)

```python
surface.opacity.toolbar  # 0.92
surface.opacity.popover  # 0.96
surface.opacity.modal_backdrop  # 0.60 in DARK / 0.40 in LIGHT
```

**Total: 47 tokens.**

---

## 6. Translucency and Surface Composition

Translucent surfaces are composed at compilation time from a theme-dependent base color and an opacity token.

There is no universal translucent color. A surface that works against a dark background may produce inadequate visual separation against a light background.

### 6.1 Composition rule

For every translucent surface:

```python
composed_color = rgba(base_color, opacity)
```

Where:

- `base_color` is obtained from the active theme.
- `opacity` is obtained from the corresponding `SurfaceTokens` entry.
- Composition is performed by `ThemeCompiler`.

Widgets MUST NOT construct translucent colors independently.

### 6.2 Theme-aware composition

| Surface | DARK base | LIGHT base | Opacity |
|---|---|---|---|
| Floating toolbar | `#252526` | `#FFFFFF` | 0.92 |
| Popover | `#2D2D30` | `#FAFAFA` | 0.96 |
| Modal backdrop | `#000000` | `#000000` | 0.60 / 0.40 |

The modal backdrop uses different opacity values because a dark overlay has a different perceptual effect on light and dark interfaces.

### 6.3 Frosted glass definition

The `Prototipagem_UI_17` interface concept includes toolbars with a subtle glass-like appearance.

For CranioZ, frosted glass means a simulated visual treatment, not real background blur.

The simulated treatment MAY combine:

- A translucent background.
- A subtle visual gradient.
- A discrete highlight border.
- An optional inner highlight.

These details are presentation techniques, not additional token categories.

Real background blur is not supported as a general mechanism because:

- `QGraphicsBlurEffect` cannot reliably sample VTK-rendered content beneath a widget.
- Platform APIs such as DWM on Windows and `NSVisualEffectView` on macOS require platform-specific handling and do not provide equivalent behavior for embedded widgets.
- Multiple VTK viewports make real-time blur potentially expensive and inconsistent.

The simulated approach is deterministic, cross-platform, and compatible with the intended Qt-based interface.

### 6.4 VTK and translucency

A translucent Qt widget MAY be positioned over a `QVTKRenderWindowInteractor`, provided that the widget hierarchy and platform compositor support the required alpha composition.

A Qt overlay may use `Qt.WA_TranslucentBackground` and a composed RGBA surface color.

However, actual transparency behavior MUST be validated on the supported operating systems and window configurations. It MUST NOT be assumed that every VTK hosting configuration supports identical composition.

`QGraphicsBlurEffect` MUST NOT be used as a mechanism for sampling VTK pixels.

If a toolbar is implemented inside the VTK rendering scene, for example as a VTK widget or actor, Qt surface translucency does not apply. Such controls SHOULD instead be implemented as Qt overlays when appropriate.

The ThemeCompiler does not manage VTK rendering or viewport backgrounds. VTK-specific appearance remains the responsibility of `viewport-appearance.md`.

### 6.5 Translucency fallback

When translucency is unsupported, visually unstable, or incompatible with the hosting configuration:

1. Replace the translucent surface with a solid theme-dependent background.
2. Preserve the border and visual hierarchy.
3. Keep controls and information readable.
4. Do not prevent the widget from being displayed.

Essential controls and clinical information MUST NOT depend on an uncertain background composition for readability.

---

## 7. Canonical Values

Every token MUST have a value in both `DARK` and `LIGHT`.

All dimensions and spacing values are expressed in logical pixels unless explicitly stated otherwise.

Typography sizes are expressed in points.

### 7.1 Colors

| Token | DARK | LIGHT |
|---|---|---|
| `color.background.application` | `#1E1E1E` | `#F4F4F4` |
| `color.background.panel` | `#252526` | `#FFFFFF` |
| `color.background.elevated` | `#2D2D30` | `#FAFAFA` |
| `color.background.input` | `#1A1A1A` | `#FFFFFF` |
| `color.text.primary` | `#E8E8E8` | `#1A1A1A` |
| `color.text.secondary` | `#A8A8A8` | `#555555` |
| `color.text.disabled` | `#5A5A5A` | `#AAAAAA` |
| `color.text.inverse` | `#FFFFFF` | `#FFFFFF` |
| `color.border.default` | `#3A3A3C` | `#D0D0D0` |
| `color.border.subtle` | `#2E2E30` | `#E8E8E8` |
| `color.border.focus` | `#4A90D9` | `#2563EB` |
| `color.interactive.default` | `#1F5FCC` | `#2563EB` |
| `color.interactive.hover` | `#4A8AFF` | `#3B82F6` |
| `color.interactive.pressed` | `#1F4FB8` | `#1E40AF` |
| `color.interactive.selected` | `#2C5FCC` | `#1D4ED8` |
| `color.feedback.information` | `#4A90D9` | `#2563EB` |
| `color.feedback.success` | `#4CAF50` | `#2E7D32` |
| `color.feedback.warning` | `#FFA726` | `#9A4D00` |
| `color.feedback.error` | `#FF6B6B` | `#B42318` |

These values are initial design-system defaults. Their use in text, icons, borders, and backgrounds MUST comply with the accessibility requirements in §12.

None of these values applies to clinical overlays, segmentation palettes, or viewport label colors.

### 7.2 Typography

| Token | DARK | LIGHT |
|---|---|---|
| `typography.family.interface` | `"Segoe UI", "Inter", sans-serif` | `"Segoe UI", "Inter", sans-serif` |
| `typography.size.caption` | 11 pt | 11 pt |
| `typography.size.body` | 13 pt | 13 pt |
| `typography.size.label` | 14 pt | 14 pt |
| `typography.size.heading` | 18 pt | 18 pt |
| `typography.weight.regular` | 400 | 400 |
| `typography.weight.medium` | 500 | 500 |
| `typography.weight.semibold` | 600 | 600 |

The font family is a preference list. The runtime MUST use an available font and MUST provide a valid fallback.

### 7.3 Spacing

| Token | DARK | LIGHT |
|---|---:|---:|
| `spacing.xs` | 4 | 4 |
| `spacing.sm` | 8 | 8 |
| `spacing.md` | 16 | 16 |
| `spacing.lg` | 24 | 24 |
| `spacing.xl` | 32 | 32 |

### 7.4 Dimensions

| Token | DARK | LIGHT |
|---|---:|---:|
| `dimension.control_height` | 28 | 28 |
| `dimension.icon_size` | 20 | 20 |

Values are logical pixels. Qt's device-independent scaling MUST be respected; the application MUST NOT apply a second HiDPI scaling factor to values already managed by Qt.

### 7.5 Borders

| Token | DARK | LIGHT |
|---|---:|---:|
| `border.width.default` | 1 | 1 |
| `border.width.focus` | 2 | 2 |
| `radius.control` | 4 | 4 |
| `radius.panel` | 6 | 6 |
| `radius.dialog` | 8 | 8 |

### 7.6 Effects

| Token | DARK | LIGHT |
|---|---|---|
| `effect.hover_overlay` | `rgba(255,255,255,0.04)` | `rgba(0,0,0,0.04)` |
| `effect.selection_highlight` | `rgba(58,122,254,0.24)` | `rgba(37,99,235,0.20)` |
| `effect.elevation_panel` | `offset(0,1), blur(3), rgba(0,0,0,0.40)` | `offset(0,1), blur(3), rgba(0,0,0,0.10)` |
| `effect.elevation_dialog` | `offset(0,4), blur(12), rgba(0,0,0,0.50)` | `offset(0,4), blur(12), rgba(0,0,0,0.15)` |
| `effect.elevation_overlay` | `offset(0,8), blur(24), rgba(0,0,0,0.60)` | `offset(0,8), blur(24), rgba(0,0,0,0.20)` |

Elevation values are represented internally by typed specifications, not by parsing the descriptive strings shown in this table.

### 7.7 Surfaces

| Token | DARK | LIGHT |
|---|---:|---:|
| `surface.opacity.toolbar` | 0.92 | 0.92 |
| `surface.opacity.popover` | 0.96 | 0.96 |
| `surface.opacity.modal_backdrop` | 0.60 | 0.40 |

The opacity of `modal_backdrop` differs by theme because the perceptual weight of a dark overlay depends on the underlying luminance.

---

## 8. Token Dataclasses

Tokens are defined in immutable Python dataclasses.

A `ThemeTokens` instance aggregates the seven categories.

```python
from dataclasses import dataclass
from enum import StrEnum


@dataclass(frozen=True)
class ColorTokens:
    background_application: str
    background_panel: str
    background_elevated: str
    background_input: str

    text_primary: str
    text_secondary: str
    text_disabled: str
    text_inverse: str

    border_default: str
    border_subtle: str
    border_focus: str

    interactive_default: str
    interactive_hover: str
    interactive_pressed: str
    interactive_selected: str

    feedback_information: str
    feedback_success: str
    feedback_warning: str
    feedback_error: str


@dataclass(frozen=True)
class TypographyTokens:
    family_interface: str

    size_caption: int
    size_body: int
    size_label: int
    size_heading: int

    weight_regular: int
    weight_medium: int
    weight_semibold: int


@dataclass(frozen=True)
class SpacingTokens:
    xs: int
    sm: int
    md: int
    lg: int
    xl: int


@dataclass(frozen=True)
class DimensionTokens:
    control_height: int
    icon_size: int


@dataclass(frozen=True)
class BorderTokens:
    width_default: int
    width_focus: int

    radius_control: int
    radius_panel: int
    radius_dialog: int


@dataclass(frozen=True)
class ElevationSpec:
    offset_x: int
    offset_y: int
    blur_radius: int
    color: str


@dataclass(frozen=True)
class EffectTokens:
    hover_overlay: str
    selection_highlight: str

    elevation_panel: ElevationSpec
    elevation_dialog: ElevationSpec
    elevation_overlay: ElevationSpec


@dataclass(frozen=True)
class SurfaceTokens:
    opacity_toolbar: float
    opacity_popover: float
    opacity_modal_backdrop: float


@dataclass(frozen=True)
class ThemeTokens:
    name: ThemeName

    colors: ColorTokens
    typography: TypographyTokens
    spacing: SpacingTokens
    dimensions: DimensionTokens
    borders: BorderTokens
    effects: EffectTokens
    surfaces: SurfaceTokens
```

The dataclasses MUST be immutable after construction.

Theme definitions MUST be validated before being made available to `ThemeService`.

Validation includes:

- Completeness of all token categories.
- Correct value types.
- Valid color representations.
- Valid opacity ranges.
- Non-negative dimensions and radii.
- Valid elevation specifications.
- Consistency between supported theme definitions.

Opacity values MUST be within the inclusive range `0.0–1.0`.

---

## 9. Theme Compilation

`ThemeCompiler` converts a resolved `ThemeTokens` instance into visual resources consumed by the application.

It has four responsibilities.

### 9.1 Responsibilities

**1. Token resolution**

Retrieve the semantic values of the active theme.

The compiler receives a concrete `ThemeTokens` instance. Theme mode resolution belongs to `ThemeService`.

**2. Surface composition**

For each declared translucent surface, compose the final color from:

- The corresponding base color token.
- The corresponding opacity token.

Widgets MUST NOT independently construct these colors.

**3. Style compilation**

Convert tokens into the appropriate visual resources:

- QSS for ordinary Qt widgets.
- `QPalette` adjustments for native widgets that do not reliably honor QSS.
- `QGraphicsDropShadowEffect` specifications for widgets that declare elevation support.
- Compiled surface colors for widgets that draw their own translucent backgrounds.

**4. Runtime application**

Provide the compiled resources to the runtime and apply the updated appearance without restarting the application.

### 9.2 What ThemeCompiler Does Not Do

The compiler MUST NOT:

- Resolve operating-system theme preferences.
- Know clinical modules, Editors, or domain rules.
- Query the Scene or `DomainObjectStore`.
- Modify clinical data, geometry, or imaging values.
- Manage VTK renderers, cameras, LUTs, or viewport backgrounds.
- Implement widget-specific interaction or appearance decisions.
- Allow widgets to define independent shared token values.
- Compose translucent colors outside the surface composition step.

The ThemeCompiler is a presentation infrastructure component, not a domain or viewport rendering service.

### 9.3 Contract

```python
class ThemeCompiler:
    def compile(self, tokens: ThemeTokens) -> CompiledStyles:
        """Compile tokens into QSS, palette adjustments,
        composed surfaces, and supported visual effects."""

    def apply(self, styles: CompiledStyles) -> None:
        """Apply compiled resources to the running Qt application."""
```

`CompiledStyles` is an opaque object that carries:

- The compiled QSS string.
- A `QPalette` delta or equivalent palette configuration.
- A dictionary of composed surface colors keyed by role.
- A dictionary of typed elevation specifications keyed by role.
- Any additional shared visual resource required by the widget hierarchy.

The compiled resources MUST be derived from the supplied `ThemeTokens`.

### 9.4 Widget-side contract

Widgets:

- Consume compiled styles through the application appearance infrastructure.
- Request translucent surface colors through `CompiledStyles.surface_color(role)` when they draw their own surfaces.
- Request elevation specifications through `CompiledStyles.elevation(role)` when they declare support.
- MUST NOT instantiate or invoke `ThemeCompiler`.
- MUST NOT call `QApplication.setStyleSheet()` independently.
- MUST NOT compose RGBA colors from theme tokens themselves.
- MUST NOT maintain local copies of shared token values.

`ThemeCompiler.apply()` is the single owner of global stylesheet application.

### 9.5 Runtime theme changes

When the effective theme changes:

1. `ThemeService` resolves the new theme.
2. The corresponding `ThemeTokens` are retrieved.
3. `ThemeCompiler` generates new `CompiledStyles`.
4. The application appearance is updated.
5. `theme_changed` is emitted.

The transition MUST preserve:

- Current input values.
- Current selection.
- Active focus where possible.
- Workspace layout.
- Current project and clinical state.

Theme changes MUST NOT modify domain objects, geometry, image data, or clinical presentation parameters.

### 9.6 Testing

The compiler is covered by unit and integration tests that assert:

- All 47 tokens are consumed by the compilation pipeline and represented in the appropriate compiled resource or runtime interface.
- No shared appearance value is introduced through independent widget-level literals.
- Composing the same tokens twice produces equivalent compiled styles.
- Composed surface colors use the base color and opacity of the active theme.
- Missing tokens are a compilation error, not a silent omission.
- Unsupported effects use their declared fallbacks.
- Theme application does not modify clinical or workspace state.

Token consumption MUST be verified at the appropriate compilation stage. A token used during composition does not need to appear literally in the final QSS output.

---

## 10. Intrinsic vs. Shared Properties — Definitive Boundary

### 10.1 Definition

**Shared visual property:** a property whose value is chosen to maintain consistency between different components. Changing it in the shared design system MUST be reflected in all equivalent components.

**Intrinsic property:** a property determined by the specific content, function, or constraint of an individual widget and which does not generalize across components.

### 10.2 Examples of intrinsic properties (MAY be local)

- Minimum width of an icon button, derived from `dimension.icon_size` and local padding.
- Row height of a specialized or virtualized table, when determined by its content and density requirements.
- Minimum width of a combo box popup, determined by its longest item.
- Content-dependent minimum dimensions.
- Specialized layout constraints that do not represent a shared visual standard.

Local formulas MAY use shared tokens as their inputs.

Example:

```python
minimum_width = icon_size + 2 * local_padding
```

The resulting value is local, while the shared icon size remains token-controlled.

### 10.3 Examples of shared properties (MUST use tokens)

- Shared interface colors.
- Shared surface opacity.
- Spacing between equivalent elements.
- Standard control heights.
- Default icon sizes.
- Shared corner radii.
- Shared font families, sizes, and weights.
- Standard focus indicators.
- Shared elevation levels.

If a widget requires a shared visual property that has no corresponding token, the token set MUST be reviewed before introducing an independent value.

### 10.4 Automated enforcement

Architecture tests enforce the boundary.

`tests/architecture/test_no_hardcoded_appearance.py`

- Detects hardcoded appearance literals in the Qt presentation layer.
- Checks for color literals such as `#rrggbb`, `rgb()`, `rgba()`, `hsl()`, and `hsla()`.
- Restricts enforcement to shared interface presentation code.
- Explicitly excludes clinical color definitions, imaging data, and approved visual resources outside the shell appearance system.

`tests/architecture/test_tokens_used.py`

- Verifies that every declared token is consumed by the compilation pipeline.

`tests/architecture/test_tokens_present.py`

- Verifies that every token referenced by the compiler exists in the canonical token definitions.

`tests/architecture/test_theme_completeness.py`

- Verifies that `DARK` and `LIGHT` contain identical token structures.

`tests/architecture/test_theme_values.py`

- Validates token types, color formats, opacity ranges, dimensions, and elevation specifications.

Any PR introducing a hardcoded shared appearance value in the Qt presentation layer MUST fail CI unless an explicit architectural exception is documented and approved.

---

## 11. ThemeService

`ThemeService` is the runtime owner of the selected theme mode and the currently resolved theme.

It coordinates theme resolution, token access, persistence through `SettingsService`, and notifications of theme changes.

### 11.1 Contract

```python
class ThemeService(QObject):
    theme_changed = Signal(ThemeName)

    def __init__(self, mode: ThemeMode) -> None: ...

    def mode(self) -> ThemeMode: ...

    def set_mode(self, mode: ThemeMode) -> None: ...

    def theme(self) -> ThemeName: ...

    def tokens(self) -> ThemeTokens: ...

    def color(self, path: str) -> str: ...

    def dimension(self, path: str) -> int: ...

    def surface_color(self, role: str) -> str: ...
```

`theme()` MUST always return a concrete theme.

`tokens()` MUST return the immutable token definition associated with the effective theme.

`color()`, `dimension()`, and `surface_color()` are convenience accessors. They MUST resolve values from the canonical token definitions or compiled resources, never from independent local configuration.

### 11.2 Persistence scope

`appearance.theme_mode` is an application-level user preference.

It is:

- Machine-local.
- Independent from individual projects.
- Independent from Workspace layout.
- Not synchronized across machines in v1.0.

The setting is stored in the CranioZ user settings file resolved through:

```python
AppPathResolver.user_settings_path()
```

`SettingsService` owns:

- File format.
- Validation.
- Serialization.
- Schema migration.
- Error reporting.

`ThemeService` MUST read and write the preference through `SettingsService`. It MUST NOT access the settings file directly.

### 11.3 Persistence and boot interaction

The startup sequence reads the persisted theme mode before the first application window is constructed.

If the persisted value is missing, invalid, or unreadable:

- `ThemeMode.DARK` is used.
- A warning is logged.
- Application startup continues.

The detailed startup sequence remains defined in `docs/architecture/startup.md`.

### 11.4 High-contrast theme

`ThemeName.HIGH_CONTRAST` is reserved for a future phase.

It is a concrete theme, not a `ThemeMode`.

It MUST NOT be resolved through `Qt.ColorScheme.HighContrast`, because `Qt.ColorScheme` does not define a `HighContrast` value.

A future high-contrast implementation MAY support:

- Manual selection by the user.
- Integration with operating-system contrast preferences through a separately supported Qt API.
- Platform-specific capability detection.

Adding the theme requires:

1. A complete `ThemeTokens` instance.
2. Compliance with the contrast requirements in §12.
3. Tests for all required foreground/background combinations.
4. Settings integration.
5. Documentation of platform behavior and fallback.

The minimum Qt version MUST be reviewed before adding platform-dependent contrast preference detection.

---

## 12. Accessibility — Testable Requirements

### 12.1 Text contrast

Text on its effective background MUST meet WCAG 2.2 AA contrast requirements:

- **4.5:1** for normal text.
- **3:1** for large text.

The following foreground/background pairs are tested for every supported theme.

| Foreground | Background | Minimum |
|---|---|---:|
| `color.text.primary` | `color.background.application` | 4.5:1 |
| `color.text.primary` | `color.background.panel` | 4.5:1 |
| `color.text.primary` | `color.background.elevated` | 4.5:1 |
| `color.text.secondary` | `color.background.panel` | 4.5:1 |
| `color.text.inverse` | `color.interactive.default` | 4.5:1 |
| `color.feedback.error` | `color.background.panel` | 4.5:1 |
| `color.feedback.success` | `color.background.panel` | 4.5:1 |
| `color.feedback.warning` | `color.background.panel` | 4.5:1 |
| `color.feedback.information` | `color.background.panel` | 4.5:1 |

These requirements apply when the corresponding colors are used for normal text.

A token does not automatically guarantee compliance in every possible foreground/background combination. Components MUST use supported combinations or provide a validated alternative.

### 12.2 Non-text contrast

Relevant visual indicators MUST be tested against their adjacent colors.

This includes:

- Keyboard focus indicators.
- Control boundaries when necessary to identify an interactive element.
- Selected-state indicators.
- Other essential graphical information.

The target contrast ratio is at least 3:1 against adjacent colors, where WCAG non-text contrast requirements apply.

Focus indicators MUST remain visible in both themes and MUST NOT rely exclusively on subtle background changes.

### 12.3 Translucent surfaces

For translucent surfaces, contrast tests MUST use the final composed color rather than the uncomposed base token.

The test computes the alpha composition over the expected underlying background and evaluates the resulting foreground/background contrast.

However, a translucent surface positioned over VTK content may encounter different underlying colors.

Therefore:

- Contrast MUST be validated against representative supported backgrounds.
- Essential information MUST NOT depend on uncertain background composition.
- A solid surface fallback MUST be available when contrast cannot be maintained.
- Clinical information and essential controls SHOULD use sufficiently opaque backgrounds.

The automated test cannot guarantee contrast over every possible rendered image. Runtime and visual validation remain necessary.

### 12.4 Automated enforcement

`tests/architecture/test_contrast.py` verifies:

- Every defined text contrast pair.
- Relevant non-text indicators.
- Every supported theme.
- Every declared translucent surface against its defined test backgrounds.

A failing mandatory contrast requirement blocks the PR.

### 12.5 High-contrast theme

A future `HIGH_CONTRAST` theme MUST provide its own complete token set.

It SHOULD target a contrast ratio of 7:1 for normal text where practical, while satisfying applicable accessibility requirements.

---

## 13. Adding a New Token

New tokens are introduced only when a concrete shared visual requirement cannot be satisfied by the existing token set.

The process is:

1. Verify that no existing token covers the requirement.
2. Identify the components and shared properties affected.
3. Open a PR that:
   - Adds the token to the relevant dataclass.
   - Provides values for both `DARK` and `LIGHT`.
   - Updates the ThemeCompiler where necessary.
   - Updates the relevant tests.
   - Updates this document.
   - Updates the token count in §5.
4. Verify that the new token does not duplicate an existing responsibility.

Adding a new category additionally requires an ADR amendment.

The PR is reviewed as a change to the shared visual system, not as a routine widget-level adjustment.

---

## 14. Non-Goals

This document does not define:

- Clinical colors, including segmentation palettes, anatomical labels, and cephalometric colors. See `viewport-appearance.md`.
- Viewport label colors and their active/inactive states. See `viewport-appearance.md`.
- Viewport renderer backgrounds and VTK-specific appearance. See `viewport-appearance.md`.
- Real background blur or platform-specific frosted glass effects.
- Modal focus effect. See `modal-focus-effect.md`.
- Icon assets or names. See `icons.md`.
- Settings storage schema. See `persistence-and-settings.md` and `docs/architecture/startup.md`.
- Component-specific tokens. Reserved for a future phase.
- Clinical display properties or modifications to geometric objects.
- Workspace layout persistence or Editor registration.

---

## 15. References

- `../../../../README.md`
- `appearance-architecture.md`
- `surfaces-and-overlays.md`
- `viewport-appearance.md`
- `modal-focus-effect.md`
- `icons.md`
- `persistence-and-settings.md`
- `docs/architecture/startup.md`
- Qt Documentation: `QStyleHints`
- Qt Documentation: `QStyleHints.colorScheme()`
- WCAG 2.2 — Contrast Minimum and Non-text Contrast