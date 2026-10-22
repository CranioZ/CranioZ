# ADR-0010: Layout Persistence

**Status:** Accepted
**Date:** 2026-10-22
**Deciders:** Architecture team
**Related:** workspace.md §5.3, §5.6, §6.4, ADR-0009

---

## 1. Context

`workspace.md` §5.3 distinguishes structure (the Area Layout Tree
and the Editor Layout Trees) from presentation state (`LayoutState`:
proportions, visibility, active editor per Area; `OverlayState`:
overlay configuration). §5.6 describes the persistence key
(`project_id + module_id + layout_schema_version`) and sketches a
JSON shape.

But no decision records:

- **Where** the layout is stored (which file, whose ownership).
- **When** it is written (on change, on close, on a timer).
- **How** reconciliation works when the persisted layout is
  incompatible with the current `ModuleUISpec`.
- **What** happens when the user has never opened a module before.

This ADR fills those gaps. It is the prerequisite for
`layout_state.py`, `layout_io.py`, and `overlay_state.py`.

## 2. Decision

### 2.1 Storage location and ownership

Layout persistence is stored in `layout.json`, owned by the
Layout persistence layer (see ADR-0009 §2.1). It is part of the
project directory, not user settings. The rationale is in
`workspace.md` §5.6: a layout must be reproducible when the project
is opened on another machine.

User preferences (theme, language, editor defaults) remain in
`settings/`, not in `layout.json`.

### 2.2 Keying

Layout is keyed by `(project_id, module_id, layout_schema_version)`.
A single `layout.json` may hold multiple entries, one per module.
The file is a dictionary keyed by `module_id`:

```json
{
  "layout_schema_version": 1,
  "layouts": {
    "orthognathic": { "area_tree": {}, "editor_trees": {}, "layout_state": {}, "overlay_state": {} },
    "tomography":   { "area_tree": {}, "editor_trees": {}, "layout_state": {}, "overlay_state": {} }
  }
}
```

Rationale: a user may personalize the layout of several modules in
the same project. Keying by (project_id, module_id) is the
minimum granularity that preserves reproducibility without
forcing a layout per Area.

## 2.3 Write policy
On module switch: the current layout is serialized before the
new ModuleUISpec is materialized.

On explicit save: the user may invoke a save action. This is
optional for Phase 4.

On project close: the current layout is serialized before the
Workspace is destroyed.

Not on every resize: QSplitter drags and Area visibility
toggles update the in-memory LayoutState. Serializing on every
change would spam the filesystem and force LayoutRenderer to
fight the user.

The in-memory LayoutState is the source of truth during the
session. The file is the persistence of the last committed state.

## 2.4 Read policy
On module activation:

Read layout.json if it exists. If it does not, use the
ModuleUISpec default.

If the entry for module_id exists, validate it against the
current layout_schema_version. Mismatch → migrate or discard.

Reconcile the persisted layout against the current
ModuleUISpec:

Area present in both: reuse the container. Reconcile the
internal Editor Layout Tree.

Area present only in persisted: drop the Area from the
persisted layout (the module no longer declares it).

Area present only in spec: add the Area from the spec.

Editor present in both: reuse the instance if compatible.

Editor present only in persisted: drop it.

Editor present only in spec: instantiate it.

If reconciliation fails (e.g., the persisted layout references
unknown editor_ids), fall back to the ModuleUISpec default and
record a warning. Do not fail silently.

## 2.5 LayoutState shape

    {
      "proportions": {
        "area.central.root_split": [0.7, 0.3],
        "area.central.editor_split": [0.5, 0.5]
      },
      "visibility": {
        "area.left": true,
        "area.right": true,
        "area.bottom": true
      },
      "active_editor_per_area": {
        "area.central": "editor.viewport_3d",
        "area.right": "editor.properties"
      }
    }

Proportions are QSplitter sizes, normalized to [0.0, 1.0].
Visibility is per Area. Active editor is per Area; the string is an
editor_id from the current tree.

## 2.6 OverlayState shape

    {
      "overlays": {
        "overlay.top_bar": { "visible": true },
        "overlay.steps_panel": { "visible": true, "position": {"x": 10, "y": 10} }
      }
    }

Overlays declared by the ModuleUISpec are stored here. The Top
Bar is structural (ADR-0005): its visibility may be persisted, but
its presence is not. Flow-dependent overlays (e.g., steps_panel)
are stored here as well.

## 2.7 Migration
Layout migrations are pure functions registered per
layout_schema_version. Unknown future versions are rejected;
older versions are migrated or discarded (with a warning).

## 2.8 Not part of the clinical undo/redo
Layout changes are not clinical Commands (workspace.md §3.4).
They update LayoutState and are persisted on the triggers in
§2.3. They are not part of the clinical undo/redo history.

# 3. Rationale
## 3.1 Reproducibility
workspace.md §5.6 is explicit: the layout is stored in the
project file, not in user settings. A project opened on a second
machine must render identically. This rules out per-user storage.

## 3.2 Multiple modules per project
A project may be worked on under several modules (orthognathic,
tomography, cephalometry). Each has its own layout. Storing all in
one file keyed by module_id avoids scattering layout files
across the project directory.

## 3.3 Reconciliation is mandatory
ModuleUISpec changes between versions. A persisted layout that
references an area_id or editor_id that no longer exists
cannot be applied verbatim. Reconciliation is the rule
(workspace.md §6.5), and this ADR makes it explicit for
persistence.

## 3.4 In-memory is the session source of truth
Writing on every resize is wrong: it spams the filesystem and
makes the renderer fight the user. The in-memory LayoutState
during the session is authoritative; the file is committed on
specific triggers.

# 4. Consequences
4.1 Positive
Layouts are reproducible across machines.

Multiple modules coexist in one file.

Reconciliation handles schema evolution.

Writes are bounded to specific triggers.

## 4.2 Negative
LayoutRenderer must be able to reconcile a persisted tree
against a ModuleUISpec. This is non-trivial and requires
careful testing.

In-memory changes are lost on crash between commit points. A
crash-recovery mechanism is out of scope for Phase 4.

## 4.3 Neutral
User preferences (theme, language) remain outside layout.json.

The Top Bar is structural; its presence is not in
OverlayState.

# 5. Rules applied by this ADR
Layout is stored in layout.json, owned by the Layout
persistence layer.

Layout is keyed by (project_id, module_id).

In-memory LayoutState is the session source of truth.

Writes happen on module switch, explicit save, and project
close.

Reads reconcile the persisted layout against the current
ModuleUISpec.

Unknown future versions are rejected; older versions migrate or
are discarded with a warning.

Layout changes are not clinical Commands.

The Top Bar's presence is not in OverlayState; its visibility
may be.

Flow-dependent overlays (e.g., steps_panel) are in
OverlayState.

A crash-recovery mechanism is out of scope for Phase 4.

# 6. Rejected alternatives
## 6.1 Layout in user settings
Rejected. Breaks reproducibility across machines. A layout tuned
on one workstation would not appear on another, contradicting
workspace.md §5.6.

## 6.2 One file per module
Rejected. Scatters layout across the project directory. One file
keyed by module_id is simpler and diffable.

## 6.3 Write on every change
Rejected. Spams the filesystem and makes the renderer fight the
user. Writes happen on commit triggers.

## 6.4 Discard persisted layout on any mismatch
Rejected. Loses personalization for recoverable mismatches.
Reconciliation should be the default; discard is the fallback.

# 7. Summary
Layout persistence lives in layout.json, keyed by
(project_id, module_id), written on specific triggers, read with
reconciliation against the current ModuleUISpec. It is the
prerequisite for layout_state.py, layout_io.py, and
overlay_state.py.



---

## Verificação de B

Os quatro ADRs são documentação pura. Nenhum teste quebra. Verifique:

    ```powershell
    .venv\Scripts\python.exe -m pytest tests/ -q
    # Esperado: 864 passed
    
    # Conferir os arquivos criados
    dir docs\adr\
    # Esperado: ADR-0001_Area_and_Editor.md, ADR-0002_EditorContext_and_Toolbar_Materialization.md,
    #           ADR-0003_UI_Widgets_and_Editor_Overlays.md, ADR-0004_Patient_Domain.md,
    #           ADR-0005_TopBar_Structural_and_Floating.md,
    #           ADR-0006_MainWindow_Navigation_and_Window-Lifecycl_Orchestrator.md,
    #           ADR-0007_Commands_and_Transactions.md,
    #           ADR-0008_Scene_and_DomainObjectStore.md,
    #           ADR-0009_Project_Persistence_Format.md,
    #           ADR-0010_Layout_Persistence.md