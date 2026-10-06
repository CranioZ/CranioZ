# Workspace — Implementation Plan

> **Status:** Draft
> **Related:** [workspace.md](../architecture/workspace.md)
> **Scope:** Phased implementation of the Workspace subsystem

---

## 1. Purpose

This document describes **how** the Workspace described in
[workspace.md](../architecture/workspace.md) is implemented, in which
order, and with which milestones.

Each phase:

- Delivers a **testable** increment.
- Has clear **acceptance criteria**.
- Does not break the previous phase.
- Can be reviewed and merged independently.

---

## 2. Guiding Principles

The implementation follows four rules:

1. **Vertical slices over horizontal layers.**
   Each phase delivers a working vertical slice (UI + logic + test), not
   "all models first, then all views".

2. **No forward dependencies.**
   A phase never depends on a phase that has not yet been completed.

3. **Testable at every step.**
   Every phase ships with tests proving it works.

4. **Reversible decisions.**
   If a decision turns out wrong, it can be changed without rewriting
   previous phases.

---

## 3. Phase Overview

| Phase | Name | Status |
|---|---|---|
| 1 | Base Model | Not started |
| 2 | Editor Host | Not started |
| 3 | Editor Registry | Not started |
| 4 | Layout Tree | Not started |
| 5 | Layout Builder | Not started |
| 6 | Layout Renderer | Not started |
| 7 | Regions and Overlays | Not started |
| 8 | Persistence | Not started |
| 9 | Advanced Features | Not started |

Each phase is independent and testable. Phases 1–4 have no external
dependencies. Phases 5–8 require external subsystems (Scene, VTK,
Project).

---

## 4. External Dependencies

Some phases depend on subsystems outside the Workspace.

| Phase | Depends on | Notes |
|---|---|---|
| 1 | None | — |
| 2 | None | — |
| 3 | None | — |
| 4 | None | — |
| 5 | None | Only needs Phase 4 |
| 6 | None | Only needs Phase 4 |
| 7 | None | Only needs Phase 4 |
| **8** | **Project** (minimal), **JSON schema** | Not yet implemented |
| **9** | **Scene** (minimal), **VTK rendering** | Not yet implemented |

**Implication:** Phase 8 and Phase 9 cannot be fully completed without
coordinating with the Project and Scene subsystems.

**Recommendation:** implement Phases 1–7 first (no external
dependencies), then assess scope of Phases 8–9.

---

## 5. Architectural Evolution

The Workspace evolves by **adding capabilities**, not by changing the
core model. The `LayoutTree` (N-ary split tree) is stable from Phase 4
onward.

### 5.1 Initial state

```text
+---------+--------------+---------+
| LEFT    | CENTRAL      | RIGHT   |
+---------+--------------+---------+
| BOTTOM                            |
+-----------------------------------+
```

- Areas declared by `ModuleUISpec`.
- Rendered via `QSplitter`.
- No tabs, no floating, no drag-and-drop.

**Purpose:** prove the concept, validate the API, run tests.

### 5.2 Adding tab bars and module switching

The Top Bar (Upper Panel Overlay) hosts module tabs. No change to the
Workspace API.

### 5.3 Adding toolbars and viewports

Toolbars become `Editor`-internal chrome. Viewports become Editors.
No change to the Workspace API.

### 5.4 Adding arbitrary splits

- Splits can be nested arbitrarily.
- Drag-and-drop between Leaves.
- Floating Areas.
- Custom trees.

**None of these change the Workspace API.**

---

## 6. Phase 1 — Base Model

**Goal:** the core Workspace types exist and can be instantiated.

### 6.1 Deliverables

| File | Purpose |
|---|---|
| `ui/workspace/placement.py` | `Placement` enum |
| `ui/workspace/area.py` | `Area` class (concrete, minimal) |
| `ui/workspace/area_manager.py` | `AreaManager` |
| `ui/workspace/area_spec.py` | `AreaSpec` dataclass |

### 6.2 Acceptance criteria

- [ ] `Placement` has `LEFT`, `CENTRAL`, `RIGHT`, `BOTTOM`.
- [ ] `Area` has `id`, `title`, `visible`, `editor_host` (stub).
- [ ] `Area` does **not** store `placement`.
- [ ] `AreaManager` registers, unregisters, retrieves Areas.
- [ ] Duplicate ID raises `ValueError` with clear message.

### 6.3 Tests

| Test | File | Type |
|---|---|---|
| `test_placement_enum_has_expected_members` | `tests/unit/ui/test_placement.py` | Unit |
| `test_area_has_id_and_title` | `tests/unit/ui/test_area.py` | Widget |
| `test_area_does_not_store_placement` | `tests/unit/ui/test_area.py` | Widget |
| `test_area_manager_register` | `tests/unit/ui/test_area_manager.py` | Unit |
| `test_area_manager_duplicate_id_raises` | `tests/unit/ui/test_area_manager.py` | Unit |
| `test_area_manager_unregister` | `tests/unit/ui/test_area_manager.py` | Unit |

### 6.4 Risks

- **Qt platform plugin issues on Windows.** Mitigation: pin PySide6.
- **Headless CI.** Mitigation: `QT_QPA_PLATFORM=offscreen`.

---

## 7. Phase 2 — Editor Host

**Goal:** `EditorHost` manages a list of Editors, with one active.

### 7.1 Deliverables

| File | Purpose |
|---|---|
| `ui/editors/base_editor.py` | `Editor` ABC |
| `ui/editors/editor_host.py` | `EditorHost` |
| `ui/workspace/area.py` | Extended: hosts an `EditorHost` |

### 7.2 Acceptance criteria

- [ ] `Editor` is abstract with `id`, `title`, `widget()`.
- [ ] `EditorHost` can `add_editor`, `remove_editor`, `list_editors`.
- [ ] `EditorHost` has an `active_editor` (only one at a time).
- [ ] `EditorHost` shows tabs when ≥ 2 editors.
- [ ] `EditorHost` shows no tabs when ≤ 1 editor.
- [ ] `detach_editor` returns the editor without destroying it.

### 7.3 Tests

| Test | File | Type |
|---|---|---|
| `test_editor_is_abstract` | `tests/unit/ui/test_editor.py` | Unit |
| `test_add_editor` | `tests/unit/ui/test_editor_host.py` | Widget |
| `test_remove_editor` | `tests/unit/ui/test_editor_host.py` | Widget |
| `test_set_active_editor` | `tests/unit/ui/test_editor_host.py` | Widget |
| `test_detach_does_not_destroy_editor` | `tests/unit/ui/test_editor_host.py` | Widget |

---

## 8. Phase 3 — Editor Registry

**Goal:** `EditorRegistry` resolves `editor_id` to concrete Editor
classes and creates instances.

### 8.1 Deliverables

| File | Purpose |
|---|---|
| `ui/editors/editor_registry.py` | `EditorRegistry` |

### 8.2 Acceptance criteria

- [ ] `register(editor_id, editor_type)` registers a class.
- [ ] `resolve(editor_id)` returns the class.
- [ ] `create(editor_id)` returns a new instance.
- [ ] Resolving an unknown `editor_id` raises `KeyError`.

### 8.3 Tests

| Test | File | Type |
|---|---|---|
| `test_register_and_resolve` | `tests/unit/ui/test_editor_registry.py` | Unit |
| `test_resolve_unknown_raises` | `tests/unit/ui/test_editor_registry.py` | Unit |
| `test_create_returns_instance` | `tests/unit/ui/test_editor_registry.py` | Widget |

---

## 9. Phase 4 — Layout Tree

**Goal:** `LayoutTree` (N-ary split tree) can be built from `AreaSpec`
lists.

### 9.1 Deliverables

| File | Purpose |
|---|---|
| `ui/workspace/layout_tree.py` | `LayoutTree`, `Leaf`, `Split`, `SplitDirection` |

### 9.2 Acceptance criteria

- [ ] `Leaf` contains exactly one `Area`.
- [ ] `Split` has a direction and ≥ 2 children.
- [ ] `LayoutTree.from_specs(specs, areas)` builds the correct tree.
- [ ] `[central]` → `Leaf`.
- [ ] `[left, central, right]` → `Split(HORIZONTAL)` with 3 children.
- [ ] `[central, bottom]` → `Split(VERTICAL)`.
- [ ] Spec without `CENTRAL` raises `ValueError`.

### 9.3 Tests

| Test | File | Type |
|---|---|---|
| `test_from_specs_single_central` | `tests/unit/ui/test_layout_tree.py` | Unit |
| `test_from_specs_left_central_right` | `tests/unit/ui/test_layout_tree.py` | Unit |
| `test_from_specs_with_bottom` | `tests/unit/ui/test_layout_tree.py` | Unit |
| `test_from_specs_requires_central` | `tests/unit/ui/test_layout_tree.py` | Unit |
| `test_to_dict_round_trip` | `tests/unit/ui/test_layout_tree.py` | Unit |

---

## 10. Phase 5 — Layout Builder

**Goal:** `LayoutBuilder` consumes a `ModuleUISpec` and produces a
`LayoutTree`.

### 10.1 Deliverables

| File | Purpose |
|---|---|
| `ui/workspace/module_ui_spec.py` | `ModuleUISpec`, `AreaSpec` (extended) |
| `ui/workspace/layout_builder.py` | `LayoutBuilder` |

### 10.2 Acceptance criteria

- [ ] `LayoutBuilder.build(spec, editor_registry)` returns a `LayoutTree`.
- [ ] Resolves `editor_id` values via `EditorRegistry`.
- [ ] Creates `Area` instances with `EditorHost` populated.
- [ ] Rejects specs without `CENTRAL`.

### 10.3 Tests

| Test | File | Type |
|---|---|---|
| `test_build_single_central` | `tests/integration/ui/test_layout_builder.py` | Integration |
| `test_build_left_central_right` | `tests/integration/ui/test_layout_builder.py` | Integration |
| `test_build_creates_areas_with_editors` | `tests/integration/ui/test_layout_builder.py` | Integration |

---

## 11. Phase 6 — Layout Renderer

**Goal:** `LayoutRenderer` renders a `LayoutTree` into nested
`QSplitter` widgets.

### 11.1 Deliverables

| File | Purpose |
|---|---|
| `ui/workspace/layout_renderer.py` | `LayoutRenderer` |

### 11.2 Acceptance criteria

- [ ] `Leaf` renders as the `Area` widget.
- [ ] `Split` renders as a `QSplitter` (H or V).
- [ ] Renderer keeps a cache of widgets (`split_widgets`, `area_widgets`).
- [ ] Cache is rebuildable from the tree.
- [ ] Renderer never invents structure.

### 11.3 Tests

| Test | File | Type |
|---|---|---|
| `test_render_single_area` | `tests/integration/ui/test_layout_renderer.py` | Integration |
| `test_render_split_horizontal` | `tests/integration/ui/test_layout_renderer.py` | Integration |
| `test_render_split_vertical` | `tests/integration/ui/test_layout_renderer.py` | Integration |
| `test_cache_rebuildable` | `tests/integration/ui/test_layout_renderer.py` | Integration |

---

## 12. Phase 7 — Regions and Overlays

**Goal:** `Region` derived from the tree; `Overlay` positions itself
over a Region.

### 12.1 Deliverables

| File | Purpose |
|---|---|
| `ui/workspace/region.py` | `Region` |
| `ui/workspace/overlay.py` | `Overlay` ABC |
| `ui/workspace/overlay_manager.py` | `OverlayManager` |
| `ui/workspace/top_overlay.py` | `TopOverlay` (Upper Panel) |

### 12.2 Acceptance criteria

- [ ] `LayoutTree.find_regions()` returns geometric regions.
- [ ] `Region.bounds` computed from rendered Areas.
- [ ] `OverlayManager.register` adds an Overlay.
- [ ] `TopOverlay` positions over `Region.CENTRAL`.
- [ ] Overlays reposition on layout change.

### 12.3 Tests

| Test | File | Type |
|---|---|---|
| `test_find_regions_single_central` | `tests/unit/ui/test_region.py` | Unit |
| `test_find_regions_left_central_right` | `tests/unit/ui/test_region.py` | Unit |
| `test_overlay_registers` | `tests/unit/ui/test_overlay.py` | Unit |
| `test_top_overlay_positions_over_central` | `tests/integration/ui/test_overlay.py` | Integration |
| `test_overlay_repositions_on_layout_change` | `tests/integration/ui/test_overlay.py` | Integration |

---

## 13. Phase 8 — Persistence

**Goal:** the `LayoutTree` serializes to JSON and deserializes back.

### 13.1 External dependency

- A minimal `Project` model (JSON file with metadata).
- A JSON schema versioning system.

### 13.2 Deliverables

| File | Purpose |
|---|---|
| `ui/workspace/layout_io.py` | Serialize / deserialize layout |
| `infrastructure/persistence/json/project_io.py` | Project file I/O |

### 13.3 Acceptance criteria

- [ ] Layout serializes to JSON.
- [ ] Layout deserializes from JSON.
- [ ] Round-trip preserves all Areas.
- [ ] Unknown Areas are ignored with a warning.
- [ ] Malformed JSON raises `ValueError` with clear message.

### 13.4 Tests

| Test | File | Type |
|---|---|---|
| `test_layout_serialization` | `tests/unit/ui/test_layout_io.py` | Unit |
| `test_layout_deserialization` | `tests/unit/ui/test_layout_io.py` | Unit |
| `test_layout_round_trip` | `tests/integration/ui/test_layout_io.py` | Integration |
| `test_layout_ignores_unknown_areas` | `tests/integration/ui/test_layout_io.py` | Integration |
| `test_layout_malformed_json_raises` | `tests/unit/ui/test_layout_io.py` | Unit |

### 13.5 Risks

**Medium.** Requires a Project subsystem that does not exist yet.

**Mitigation:** implement a minimal `Project` model. Full model later.

---

## 14. Phase 9 — Advanced Features

**Goal:** power-user layout features.

### 14.1 Deliverables

| Feature | Purpose |
|---|---|
| Drag-and-drop between Leaves | Move Areas interactively |
| Floating Areas | Detach Areas to separate windows |
| Multi-monitor support | Remember position per monitor |
| Custom trees | User-defined arrangements |
| Tree presets per Flow | Different trees per clinical flow |

### 14.2 Acceptance criteria

- [ ] User can drag an Area from one Leaf to another.
- [ ] User can detach an Area into a floating window.
- [ ] Floating window position is remembered per monitor.
- [ ] User can save the current tree as a preset.

---

## 15. Dependencies Between Phases

```text
Phase 1 (Base Model)
    |
    v
Phase 2 (Editor Host)
    |
    v
Phase 3 (Editor Registry)
    |
    v
Phase 4 (Layout Tree)
    |
    +----------------+----------------+
    |                                   |
    v                                   v
Phase 5 (Layout Builder)          Phase 6 (Layout Renderer)
    |                                   |
    +----------------+------------------+
                     |
                     v
              Phase 7 (Regions and Overlays)
                     |
                     v
              Phase 8 (Persistence)
                     |
                     v
              Phase 9 (Advanced Features)
```

Phases 5 and 6 can be developed in parallel if dependencies allow.

---

## 16. Testing Strategy Summary

| Level | Tool | Coverage |
|---|---|---|
| Unit | pytest | Models, layout logic, IO |
| Widget | pytest-qt | Areas, Workspace, Editors |
| Integration | pytest-qt | Registration, layout, persistence |
| Visual | (later) | Regression screenshots |

**Target coverage:** ≥ 80% for `ui/workspace/`.

See [workspace-testing.md](../workspace-testing.md) for details.

---

## 17. Definition of Done

A phase is considered **done** when:

- [ ] All deliverables are implemented.
- [ ] All acceptance criteria pass.
- [ ] All tests pass in CI.
- [ ] Code is reviewed.
- [ ] Documentation is updated.
- [ ] CHANGELOG has an entry.
- [ ] An ADR is written if the phase introduces an architectural
  decision.

---

## 18. Milestones

| Milestone | Phases | Notes |
|---|---|---|
| M1 — Base model runs | Phase 1 | Core types exist. |
| M2 — EditorHost works | Phases 2, 3 | Editors and registry. |
| M3 — Layout tree builds | Phase 4 | `LayoutTree.from_specs` works. |
| M4 — Module spec builds UI | Phase 5 | `LayoutBuilder` works. |
| M5 — Tree renders as Qt | Phase 6 | `LayoutRenderer` works. |
| M6 — Overlays position | Phase 7 | Regions and TopOverlay. |
| M7 — Layout persists | Phase 8 | JSON round-trip. |
| M8 — Power-user layout | Phase 9 | Drag-and-drop, floating, multi-monitor. |

Each milestone is a natural stopping point. The Workspace is usable at
every milestone from M1 onward.

---

## 19. Recommendations

Given the scope:

1. **Implement Phases 1–7 first.** They have no external dependencies
   (except Qt/PySide6) and give a fully functional Workspace.
2. **Stub Phase 8 if needed.** Implement a minimal `Project` model to
   allow persistence without the full Project subsystem.
3. **Defer Phase 9.** Advanced features (drag-and-drop, floating)
   require significant UX design and should be added after the core
   is stable.

---

## 20. Open Questions

### 20.1 Should the `LayoutRenderer` be stateless or stateful?

**Option A:** Stateless — pure function `tree → widget`.
**Option B:** Stateful — keeps a cache of widgets for re-use.

**Current lean:** Option B. Keeps a cache, but the cache is
rebuildable from the tree at any time.

### 20.2 How to test floating Areas in CI?

Headless CI environments do not have multiple monitors.

**Current lean:** mock the screen geometry, test window flags instead
of actual positions.

### 20.3 Should Editor swap animation be added?

**Option A:** Yes — fade or slide transition.
**Option B:** No — instant swap.

**Current lean:** Option B.

### 20.4 Should Phase 8 block the initial release?

**Option A:** Yes — persistence is required for a usable release.
**Option B:** No — the Workspace can ship without persistence;
persistence is added in a later phase.

**Current lean:** Option B.

### 20.5 Should `LayoutBuilder` and `LayoutRenderer` be merged?

**Option A:** Keep separate — build is a pure data operation; render
is a UI operation.
**Option B:** Merge into one class.

**Current lean:** Option A. Separate responsibilities.
