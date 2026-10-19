# ADR-0005: Top Bar — Structural Component Materialized as a Floating Overlay

**Status:** Accepted
**Date:** 2026-10-19
**Deciders:** Architecture team
**Related:** ADR-0001_Area_and_Editor.md, ADR-0002_EditorContext_and_Toolbar_Materialization.md, workspace.md §3.3, workspace.md §7, top-bar.md

---

## 1. Context

The Top Bar (Painel Superior) is a permanent navigation component of the Workspace. Its geometry is constrained by the available space between the Left and Right Areas, and its background is translucent.

Three readings coexisted in the documentation:
- A rigid structural widget fixed in the layout.
- A flow-dependent Overlay.
- A hybrid model.

This ADR resolves the ambiguity by defining the Top Bar as a **hybrid component**: structural in purpose, floating in materialization.

---

## 2. Decision

### 2.1 Nature

The Top Bar is a structural component of the Workspace. It exists for the entire lifetime of the Workspace, independently of any active Flow, Module, or Project.

### 2.2 Materialization

The Top Bar is rendered as a floating layer over the Central Region. It is not part of the Area Layout Tree and does not push the Central Area down. Its geometry is computed and applied by the `OverlayManager`.

### 2.3 Geometry

- **Position:** anchored to the top of the Central Region, with configured margins (horizontal and vertical).
- **Width:** dynamic, equal to the current width of the Central Region minus the lateral margins.
- **Height:** fixed.
- **Adaptation:** recomputed whenever the layout changes (window resize, Area visibility toggle, module switch).

### 2.4 Appearance

- Background: translucent, allowing the Central Region content to remain visible beneath.
- Fallback: a semi-opaque solid background is used on platforms where translucency over the rendering surface is unavailable.

### 2.5 Components

The Top Bar contains three horizontal segments:

| Segment | Content | Anchoring |
|---|---|---|
| **Left** | Menu, Home, Toggle Area Left | Left-aligned. |
| **Center** | Module tabs, `+` button | Always horizontally centered within the Top Bar. |
| **Right** | Extras, Toggle Area Bottom, Toggle Area Right, Window controls | Right-aligned. |

The Center segment remains centered regardless of the width of the Left and Right segments.

### 2.6 Lifecycle and Persistence

- The Top Bar is registered in the `OverlayManager` at Workspace creation.
- It is never created or destroyed by the Flow engine.
- Its visibility (shown/hidden via the user toggle) is a presentation preference, persisted in `LayoutState`.
- Its presence is not persisted in `OverlayState`. `OverlayState` is reserved for flow-dependent Overlays (e.g., `steps_panel`).

---

## 3. Rules Applied

1. The Top Bar exists for the lifetime of the Workspace.
2. The Top Bar is positioned by the `OverlayManager` over the Central Region.
3. The Top Bar does not participate in the Area Layout Tree.
4. The Top Bar's width adapts to the Central Region's current bounds.
5. The Top Bar's background is translucent, with a solid fallback.
6. The Center segment is always horizontally centered.
7. The Top Bar's visibility is persisted in `LayoutState`, not in `OverlayState`.

---

## 4. Consequences

### 4.1 Positive

- Consistent with the UI specification.
- Maximizes Central Region space (no layout displacement).
- Single owner of geometry (`OverlayManager`).
- Visibility is independent of Flow.
- Single materialization path for all floating components.

### 4.2 Negative

- The `OverlayManager` must distinguish the Top Bar (persisted in `LayoutState`) from flow-dependent Overlays (persisted in `OverlayState`).
- Translucency requires a platform-specific fallback.

### 4.3 Neutral

- The Top Bar is not part of the `LayoutTree`.
- The Top Bar is not serialized in `OverlayState`.

---

## 5. Alternatives Rejected

- **Rigid widget in the layout:** loses translucency and reduces Central Region space.
- **Flow-dependent Overlay:** contradicts the requirement that the Top Bar is always present.
- **Full-window width:** contradicts the requirement that it adapts to the Left and Right Areas.
- **Opaque background:** contradicts the requirement that the Central Region content remains visible beneath.

---

## 6. Summary

The Top Bar is a structural component of the Workspace materialized as a floating, translucent Overlay. This hybrid model satisfies the requirement that the component is always present while preserving the Central Region's usable space and visual continuity. The `OverlayManager` is the single owner of its geometry; its visibility is a presentation preference persisted in `LayoutState`.