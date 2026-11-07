# Icons and Icon Manager

**Document type:** Architecture specification  
**Status:** Accepted  
**Scope:** Icon representation, resolution, catalog, lifecycle, and the IconProvider contract  
**Depends on:** `README.md`, `themes-and-design-tokens.md`, `appearance-architecture.md`  
**References:** ADR-0014 (Widget Toolkit Selection)

---

## 1. Purpose

This document defines how CranioZ represents, resolves, and applies icons across the interface. It establishes:

- The `IconProvider` contract that widgets consume.
- The current `UnicodeIconProvider` implementation (Phase 2).
- The future `SvgIconProvider` implementation (Phase 8).
- The canonical icon name catalog.
- Icon state handling, theme integration, accessibility, and fallbacks.

Icons are interface elements. They are NOT clinical imagery. Anatomical overlays, segmentation palettes, cephalometric point markers, and VTK-rendered symbols belong to `viewport-appearance.md` and are outside the scope of this document.

---

## 2. The Problem

The current codebase uses hardcoded Unicode glyphs (`☰`, `▢`, `□`, `?`) inside widget code. This is acceptable as a short-term placeholder, but:

- It does not scale to production: the glyphs render differently across fonts and platforms.
- It fragments the catalog: one widget uses `☰` for menu, another uses `≡`, another uses `⋮`.
- It cannot support hover, pressed, disabled, and selected states consistently.
- It embeds icon choices inside widget code, defeating the appearance system.

At the same time, waiting for Phase 8 to introduce production SVG assets would leave the UI inconsistent through Phases 2–7, and the test suite would depend on placeholders that will later be removed.

The solution is to introduce the **contract** now and defer the **assets**.

---

## 3. Architecture — Two Layers

The icon system separates the **contract** (Phase 2) from the **product** (Phase 8).

```text
┌─────────────────────────────────────────────┐
│ IconProvider (Protocol)                     │ Stable contract
├─────────────────────────────────────────────┤
│ UnicodeIconProvider (Phase 2)               │ Current implementation
│ SvgIconProvider (Phase 8)                   │ Future implementation
├─────────────────────────────────────────────┤
│ Widgets consume provider.icon(...)          │ No widget knows which provider
└─────────────────────────────────────────────┘
```

Widgets consume `provider.icon(name, size, state)` and `provider.text_glyph(name)`. They MUST NOT know whether the provider is Unicode-based or SVG-based.

Switching providers in Phase 8 changes a single line in the boot sequence. No widget changes.

---

## 4. The IconProvider Contract

```python
class IconState(StrEnum):
    DEFAULT = "default"
    HOVER = "hover"
    PRESSED = "pressed"
    SELECTED = "selected"
    DISABLED = "disabled"


class IconProvider(Protocol):
    def icon(
        self,
        name: str,
        size: int | None = None,
        state: IconState = IconState.DEFAULT,
    ) -> QIcon: ...

    def text_glyph(self, name: str) -> str: ...

    def invalidate_cache(self) -> None: ...
```

### 4.1 Rules

- `icon(name, size, state)` returns a `QIcon`. It MUST NOT return `None`. If the name is unknown, it returns a fallback icon (see §10).
- `size` is optional. When omitted, the provider uses `dimension.icon_size` from the active theme. Any explicit size different from 16, 24, 32, or 48 requires justification in code review.
- `state` defaults to `IconState.DEFAULT`. Widgets that participate in the shared appearance system pass the state when calling.
- `text_glyph(name)` returns a single Unicode character for debug overlays and tooltips. It is used only by the UnicodeIconProvider and by tests. Production widgets use `icon(...)`.
- `invalidate_cache()` exists for the SvgIconProvider to clear cached icons on theme change. The UnicodeIconProvider treats it as a no-op.

### 4.2 Injection

`IconProvider` is injected:

- Via `EditorContext` for Editors.
- Via `MainWindow` for the shell.
- Via `Workspace` for panels and toolbars hosted by the workspace.

Widgets MUST NOT instantiate a provider directly. They MUST NOT import `UnicodeIconProvider` or `SvgIconProvider`.

---

## 5. The UnicodeIconProvider (Phase 2)

The UnicodeIconProvider maps icon names to Unicode glyphs and builds a QIcon from the glyph via QPainter. This ensures:

- Deterministic rendering across platforms (the glyph is drawn, not font-dependent).
- Stable test snapshots (the same glyph produces the same pixels).
- No external asset dependency.
- Immediate availability for Phase 2 widgets.

```python
class UnicodeIconProvider:
    def __init__(
        self,
        theme_service: ThemeService,
        glyph_map: dict[str, str] | None = None,
    ) -> None:
        self._theme_service = theme_service
        self._glyphs = glyph_map or _DEFAULT_GLYPHS

    def text_glyph(self, name: str) -> str:
        return self._glyphs.get(name, "?")

    def icon(
        self,
        name: str,
        size: int | None = None,
        state: IconState = IconState.DEFAULT,
    ) -> QIcon:
        resolved_size = size or self._theme_service.dimension("dimension.icon_size")
        color = self._color_for_state(state)
        return self._render_glyph(self.text_glyph(name), resolved_size, color)

    def invalidate_cache(self) -> None:
        pass

    def _color_for_state(self, state: IconState) -> QColor:
        match state:
            case IconState.DEFAULT:
                return QColor(self._theme_service.color("color.text.primary"))
            case IconState.HOVER:
                return QColor(self._theme_service.color("color.interactive.hover"))
            case IconState.PRESSED:
                return QColor(self._theme_service.color("color.interactive.pressed"))
            case IconState.SELECTED:
                return QColor(self._theme_service.color("color.interactive.default"))
            case IconState.DISABLED:
                return QColor(self._theme_service.color("color.text.disabled"))

    def _render_glyph(self, glyph: str, size: int, color: QColor) -> QIcon:
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        font = QFont(self._theme_service.tokens().typography.family_interface)
        font.setPixelSize(int(size * 0.75))
        painter.setFont(font)
        painter.setPen(color)
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, glyph)
        painter.end()
        return QIcon(pixmap)
```

### 5.1 Limitations Acknowledged

- The glyph style is not the production design. It is a recognizable, deterministic placeholder.
- Hover, pressed, and disabled states are rendered via color substitution, not via distinct glyphs. This is sufficient for development and testing.
- The glyph set is limited to the catalog in §6.
- These limitations are acceptable because the contract guarantees replacement without widget changes.

---

## 6. Canonical Icon Catalog (Phase 2)

The following names are the closed set for Phase 2. Adding a name requires a PR that updates this document.

### 6.1 Navigation (8)

| Name | Glyph | Purpose |
|---|---|---|
| `home` | ⌂ | Return to the Home Page |
| `menu` | ☰ | Open the main menu |
| `close` | ✕ | Close a dialog, panel, or Editor |
| `maximize` | ▣ | Maximize an Editor or viewport |
| `restore` | ▢ | Restore a maximized Editor |
| `back` | ← | Navigate backward |
| `forward` | → | Navigate forward |
| `sidebar_toggle` | ▤ | Toggle the sidebar |

### 6.2 Area Toggles (4)

| Name | Glyph | Purpose |
|---|---|---|
| `toggle_left` | ◧ | Show/hide the Left Area |
| `toggle_right` | ◨ | Show/hide the Right Area |
| `toggle_bottom` | ⬓ | Show/hide the Bottom Area |
| `toggle_top` | ⬒ | Show/hide the Top Bar |

### 6.3 Actions (10)

| Name | Glyph | Purpose |
|---|---|---|
| `new` | ＋ | Create a new project, item, or object |
| `open` | 📂 | Open a project, file, or folder |
| `save` | 💾 | Save the current state |
| `save_as` | 📥 | Save as |
| `delete` | 🗑 | Delete the selected item |
| `duplicate` | ⧉ | Duplicate the selected item |
| `export` | ↗ | Export data or objects |
| `import` | ↘ | Import data or objects |
| `print` | 🖨 | Print or generate a PDF |
| `search` | ⌕ | Search or filter |

### 6.4 Feedback (4)

| Name | Glyph | Purpose |
|---|---|---|
| `info` | ℹ | Informational message |
| `success` | ✓ | Success message |
| `warning` | ⚠ | Warning message |
| `error` | ✕ | Error message |

### 6.5 2D Tools (10)

| Name | Glyph | Purpose |
|---|---|---|
| `cursor` | ↖ | Pointer / selection |
| `pan` | ✋ | Pan the viewport |
| `zoom_in` | ⊕ | Zoom in |
| `zoom_out` | ⊖ | Zoom out |
| `probe_hu` | ⊙ | Probe Hounsfield value |
| `measure_distance` | 📏 | Measure distance |
| `measure_angle` | 📐 | Measure angle |
| `crosshair` | ⊕ | MPR crosshair |
| `ruler` | 📏 | Ruler guides |
| `annotation` | ✎ | Add annotation |

### 6.6 3D Tools (8)

| Name | Glyph | Purpose |
|---|---|---|
| `rotate` | ↻ | Rotate object |
| `translate` | ✥ | Move object |
| `scale` | ⤢ | Scale object |
| `cut` | ✂ | Cut / remove part of the volume |
| `paint` | 🖌 | Paint mask or volume |
| `roi` | ▭ | Region of interest |
| `lock_rotation` | 🔒 | Lock rotation |
| `unlock_rotation` | 🔓 | Unlock rotation |

### 6.7 Modules (6)

| Name | Glyph | Purpose |
|---|---|---|
| `module_tomography` | 🩻 | Tomography module tab |
| `module_registration` | ⚏ | Registration module tab |
| `module_cephalometry` | 👤 | Cephalometry module tab |
| `module_segmentation` | ▨ | Segmentation module tab |
| `module_osteotomy` | 🔪 | Osteotomy module tab |
| `module_guides` | 🧩 | Guides module tab |

### 6.8 Objects (6)

| Name | Glyph | Purpose |
|---|---|---|
| `object_volume` | ◉ | Volume object |
| `object_mesh` | ◈ | Mesh object |
| `object_landmark` | ◆ | Landmark point |
| `object_mask` | ▩ | Mask |
| `object_measurement` | 📐 | Measurement |
| `object_group` | ▤ | Object group |

### 6.9 System (4)

| Name | Glyph | Purpose |
|---|---|---|
| `settings` | ⚙ | Settings |
| `help` | ? | Help |
| `about` | ⓘ | About CranioZ |
| `log` | ☰ | Log console |

**Total: 60 icon names.**

### 6.10 Catalog Rules

- Names are `snake_case`, semantically descriptive.
- A name MUST be added to this catalog before it is used in widget code. Using a name not in the catalog produces the fallback icon and a WARNING.
- Removing or renaming a name requires a migration PR (widgets that reference the old name are updated in the same PR).
- The catalog is versioned with the document. The IconProvider test suite asserts that every glyph in the UnicodeIconProvider map corresponds to a name in this document, and vice versa.

---

## 7. Icon State Rendering

Widgets may request `IconState.HOVER`, `PRESSED`, `SELECTED`, or `DISABLED`.

### 7.1 UnicodeIconProvider

| State | Color token |
|---|---|
| DEFAULT | `color.text.primary` |
| HOVER | `color.interactive.hover` |
| PRESSED | `color.interactive.pressed` |
| SELECTED | `color.interactive.default` |
| DISABLED | `color.text.disabled` |

The glyph itself does not change. The color is derived from the theme, so hover and pressed states respond to theme changes automatically.

### 7.2 SvgIconProvider (Phase 8)

- Loads assets from `assets/icons/<theme>/<name>_<state>.svg` if present.
- Falls back to `<name>.svg` with a color substitution via `ThemeService.color(...)`.
- Falls back to `<name>.svg` at reduced opacity for `DISABLED`.
- The provider caches by `(name, size, theme, state)` and invalidates on `theme_changed`.

---

## 8. Theme Integration

The icon provider MUST be theme-aware.

The UnicodeIconProvider reads colors from ThemeService on every `icon(...)` call. No cache is needed because rendering is trivial.

The SvgIconProvider caches resolved icons and invalidates on `theme_changed`.

```python
class SvgIconProvider:
    def __init__(
        self,
        theme_service: ThemeService,
        icons_root: Path,
    ) -> None:
        self._theme_service = theme_service
        self._icons_root = icons_root
        self._cache: dict[tuple[str, int, ThemeName, IconState], QIcon] = {}
        theme_service.theme_changed.connect(self._on_theme_changed)

    def _on_theme_changed(self, _: ThemeName) -> None:
        self._cache.clear()
```

### 8.1 Widget-Side Rules

Widgets:

- MUST NOT cache QIcon instances themselves. The provider caches internally.
- MUST connect to `theme_changed` only if they display the icon via QPainter (not via QIcon), and must re-request the icon when the theme changes.
- MUST NOT set the icon color themselves. The provider handles color.

---

## 9. Widget Integration

Widgets consume the provider as an injected dependency:

```python
class ToolbarButton(QPushButton):
    def __init__(
        self,
        icon_name: str,
        icon_provider: IconProvider,
        accessible_name: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setIcon(icon_provider.icon(icon_name))
        self.setAccessibleName(accessible_name)
        self.setToolTip(accessible_name)
```

### 9.1 What Widgets MUST Do

- Request icons via `provider.icon(...)`.
- Set `accessible_name` and tooltip for icon-only controls.
- Use `dimension.icon_size` (or a token-derived size) when the widget itself draws the icon.

### 9.2 What Widgets MUST NOT Do

- Import `UnicodeIconProvider` or `SvgIconProvider` directly.
- Hardcode glyphs (`☰`, `▢`, `□`) or QIcon construction.
- Cache QIcon instances across theme changes.
- Set icon color or state themselves.

---

## 10. Fallback Behavior

If `provider.icon(name)` is called with a name that is not in the catalog:

- The provider MUST NOT raise an exception.
- It returns a fallback icon: a `?` glyph at the requested size.
- It logs a WARNING with the missing name and the calling widget's class, to ease detection during development.
- The widget continues to function.

Silent failures are not permitted. A missing icon is a defect that must be visible during review.

The catalog test (§12) fails CI if a widget uses a name that is not in the catalog.

---

## 11. Accessibility

**Accessible names.** Every icon-only control MUST set `setAccessibleName(...)` with a translated string. The icon name is not a substitute for the accessible name.

**Tooltips.** Every icon-only control MUST have a tooltip. The tooltip uses the same translated string as the accessible name.

**Contrast.** Icons rendered over `color.background.panel` MUST meet WCAG AA contrast (3:1 minimum for graphical objects). The icon color for each state is derived from a token that is already validated by the contrast test in `themes-and-design-tokens.md §12`.

**Color independence.** Icons MUST NOT be the sole carrier of critical state. Active/inactive viewports, warnings, and errors use icons in combination with color, text, or shape.

**HiDPI.** Icons MUST scale correctly under Qt's high-DPI behavior. The provider handles scaling internally; widgets pass the logical size (`dimension.icon_size`).

---

## 12. Tests

The following tests are normative and live in `tests/architecture/`:

### 12.1 Catalog Completeness

`test_icon_catalog.py`:

- Asserts that every name in `_DEFAULT_GLYPHS` is present in the catalog table in this document.
- Asserts that every name in the catalog table has a glyph in `_DEFAULT_GLYPHS`.
- Fails if either is inconsistent.

### 12.2 Fallback

`test_icon_fallback.py`:

- Asserts that `provider.icon("nonexistent")` returns a valid QIcon (not None).
- Asserts that a WARNING is logged.

### 12.3 Theme Integration

`test_icon_theme.py`:

- Asserts that `provider.icon("save")` returns different pixels for DARK and LIGHT.
- Asserts that `provider.icon("save", state=IconState.SELECTED)` uses `color.interactive.default`.

### 12.4 Widget Contract

`test_icon_widget_contract.py`:

- Scans widget code for UnicodeIconProvider or SvgIconProvider imports outside the injection point; fails if any are found.
- Scans widget code for hardcoded glyphs (☰, ▢, etc.); fails if any are found.

### 12.5 Accessibility

`test_icon_accessibility.py`:

- Asserts that every ToolbarButton created in tests has a non-empty accessibleName and toolTip.
- Asserts that icon-only controls in the widget library set both.

---

## 13. Widget Migration Roadmap

Widgets currently using hardcoded glyphs are migrated incrementally.

| Phase | Migration |
|---|---|
| Phase 2 | TopBar, HomeSegment, ModulesSegment, ExtrasSegment |
| Phase 2 | HomePage navigation buttons |
| Phase 2 | Toolbar and ToolButton |
| Phase 4 | MPRView and Viewport3DView chrome |
| Phase 4 | Import dialog, settings dialog, project management dialog |
| Phase 8 | Complete migration to SvgIconProvider |

Each migration is a separate PR with a regression test asserting that the widget calls `provider.icon(...)` with a name that exists in the catalog.

---

## 14. The SvgIconProvider (Phase 8 — Deferred)

The Phase 8 implementation is out of scope for this document but is anticipated here to keep the contract stable.

**Scope:**

- Load SVG assets from `assets/icons/<theme>/<name>.svg`.
- Recolor SVGs using `ThemeService.color(...)` for state variants.
- Cache by `(name, size, theme, state)`.
- Invalidate on `theme_changed`.
- Fallback to UnicodeIconProvider if an SVG is missing (never fail silently).
- Support HiDPI rendering.

**Asset organization:**

```text
assets/icons/
├── dark/
│   ├── home.svg
│   ├── save.svg
│   ├── menu.svg
│   └── ...
└── light/
    ├── home.svg
    ├── save.svg
    ├── menu.svg
    └── ...
```

Adding a new icon in Phase 8 requires:

1. Adding the SVG to both `<theme>/` directories.
2. Adding the name to the catalog in this document.
3. Running the catalog test to confirm consistency.

---

## 15. Non-Goals

This document does not define:

- Clinical overlays (anatomical symbols, landmark markers). See `viewport-appearance.md`.
- Viewport label colors and viewport-specific affordances. See `viewport-appearance.md`.
- Tool cursors on VTK canvases. These are managed by VTK interactor styles.
- LUTs, transfer functions, or segmentation palettes.
- The final visual style of production icons. That is a Phase 8 design deliverable.
- Icon asset licensing and provenance. That is a Phase 8 operational concern.
- Accessibility of the icon content beyond what is stated in §11 (e.g., semantic alt text for decorative icons).

---

## 16. References

- `README.md`
- `themes-and-design-tokens.md §5.4` (dimension.icon_size), `§11` (ThemeService), `§12` (contrast tests)
- `surfaces-and-overlays.md`
- `viewport-appearance.md`
- `persistence-and-settings.md`
- ADR-0014 (Widget Toolkit Selection)