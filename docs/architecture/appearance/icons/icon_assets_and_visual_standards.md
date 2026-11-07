# Icon Assets and Visual Standards

**Document type:** UI asset specification  
**Status:** Accepted  
**Scope:** Icon assets, SVG standards, directory structure, visual consistency, sizing, color, and theme integration  
**Related documents:** `icons-and-icon-manager.md`, `themes-and-design-tokens.md`

---

## 1. Purpose

Define the practical standards for creating, acquiring, organizing, and maintaining icons in CranioZ.

The icon system uses SVG as its primary asset format. Icon rendering, sizing, color adaptation, and theme integration are handled centrally by the `IconProvider`.

## 2. Asset Format

SVG is the standard format for interface icons.

SVG provides:
- Resolution-independent rendering.
- Flexible scaling without quality loss.
- Theme-aware color adaptation.
- Compact and maintainable assets.

Icons may be:
- Created specifically for CranioZ using vector editors.
- Acquired from established icon libraries.
- Adapted from existing assets, respecting their licenses.

PNG and other raster formats are not standard formats for interface icons.

## 3. Asset Directory

All shared icon assets are stored in a centralized directory:

```text
src/cranioz/assets/icons/
├── application/
├── editing/
├── visualization/
├── anatomy/
└── medical/
```

Directories organize assets by functional category.

Individual modules may register additional icons through the central catalog when necessary. Module-specific assets should remain associated with their respective modules rather than unnecessarily expanding the global asset collection.

## 4. Naming Convention

Icon filenames use lowercase `snake_case`.

Examples:

```text
open.svg
save.svg
settings.svg
select.svg
move.svg
rotate.svg
mandible.svg
maxilla.svg
segmentation.svg
measurement.svg
```

The filename should represent the icon's semantic meaning, not its appearance or color.

The icon catalog provides the canonical identifier used by application code. Asset filenames and catalog identifiers should remain consistent whenever possible.

## 5. SVG Visual Standards

Icons should follow a consistent visual language.

General requirements:

- Prefer simple, recognizable silhouettes.
- Maintain consistent stroke thickness.
- Use balanced proportions and optical alignment.
- Avoid unnecessary details and visual complexity.
- Avoid embedded text.
- Avoid platform-dependent fonts and external dependencies.
- Prefer monochromatic designs for standard interface icons.

A `24 × 24` SVG viewBox is the preferred design canvas. Other viewBox dimensions may be accepted when required by the original asset, provided that visual proportions remain consistent.

Icons acquired from external libraries should be reviewed before inclusion. Inconsistent stroke widths, proportions, and visual styles should be corrected or replaced.

## 6. Icon Sizes

The default interface icon size is **20 × 20 logical pixels**.

Supported standard sizes:

| Size | Typical application |
|---|---|
| 16 px | Compact controls |
| 20 px | Default interface size |
| 24 px | Standard toolbars and menus |
| 32 px | Prominent tools and controls |
| 48 px | Large interface representations |

The same SVG asset is reused across all supported sizes.

Separate files for different sizes are not required.

The rendering system must account for device pixel ratio (DPR) when generating and caching rasterized icon representations.

## 7. Color Standards

Standard interface icons should be monochromatic.

Their colors are controlled by the `IconProvider`, using semantic design tokens from the active theme.

The application must not maintain separate SVG files for light and dark themes.

Example:

```text
mandible.svg
```

The same asset can be rendered with different foreground colors depending on the active theme.

Color adaptation should support the relevant icon states, including normal, disabled, active, and selected.

Pressed visual feedback is handled by widget styling rather than a dedicated `QIcon` mode.

### 7.1 Semantic Color Exceptions

Some icons may require specific colors because color carries clinical or functional meaning.

These exceptions must be explicitly defined and must not be treated as ordinary monochromatic interface icons.

Clinical visualization colors belong to the medical visualization system and must remain independent of the general application theme.

## 8. Theme Integration

The `IconProvider` is responsible for resolving the appropriate icon appearance.

When the application theme changes:

1. The active theme is updated.
2. The `IconProvider` resolves the new semantic icon colors.
3. Cached representations affected by the theme are invalidated or refreshed.
4. Registered widgets update their displayed icons.

Individual widgets must not implement their own theme-dependent SVG recoloring.

The SVG asset remains unchanged; only its rendered representation changes.

## 9. Icon Catalog and Registration

The Python icon catalog is the canonical registry of available icons.

Each entry identifies the icon by a stable semantic name and its corresponding asset.

Example:

```python
"mandible": "anatomy/mandible.svg"
```

The catalog is responsible for:
- Defining available icon identifiers.
- Mapping identifiers to asset paths.
- Preventing inconsistent naming.
- Supporting catalog validation and automated tests.

Widgets should request icons by catalog identifier rather than constructing asset paths directly.

## 10. Asset Licensing

Third-party icons must comply with their original licenses.

The project must preserve required attribution, copyright notices, and license information.

A library's license should be reviewed before its assets are incorporated into the repository.

Modified third-party assets remain subject to the applicable license terms.

## 11. Quality Control

New or modified icons should be checked for:

- Correct SVG rendering.
- Consistent visual style.
- Appropriate proportions and alignment.
- Legibility at 16, 20, and 24 px.
- Correct theme-dependent color rendering.
- High-DPI rendering behavior.
- Valid asset paths and catalog registration.
- License compliance when applicable.

Automated tests should verify catalog references and asset availability. Visual inspection remains necessary to assess icon quality and consistency.

## 12. Non-Goals

This specification does not define:

- Clinical color maps or anatomical visualization palettes.
- Illustrations, logos, or promotional graphics.
- A general-purpose vector graphics editor.
- Independent icon customization by individual users.
- Separate light and dark versions of standard interface icons.

---

## 13. Core Decisions

| Property | Standard |
|---|---|
| Primary format | SVG |
| Default size | 20 × 20 logical px |
| Additional sizes | 16, 24, 32, 48 px |
| Preferred viewBox | 24 × 24 |
| Design style | Consistent, predominantly monochromatic |
| Asset location | `src/cranioz/assets/icons/` |
| Naming | `snake_case` |
| Asset registration | Central Python catalog |
| Color management | `IconProvider` |
| Theme adaptation | Automatic |
| High-DPI support | Required |
| External assets | License verification required |