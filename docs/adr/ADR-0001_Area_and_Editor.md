Status: Accepted
Date: 2026-10-12
Deciders: Architecture team
Related: overview.md, workspace_en.md, workspace_pt.md, editors.md, workspace-implementation.md

## 1. Context
The architecture documents disagree about the relationship between Area and Editor.

The overview.md §5.4 states:

    "In CranioZ, Area and Editor refer to the same concept: a unit of the UI that occupies a position in the Workspace Layout tree and provides a specific functional experience. There is no separate EditorHost or Editor abstraction. A Toolbar is internal to the Area; it is declared and materialized by the Area itself."

The workspace_en.md §2 states:

    "An Area is a container of Editors. It hosts one or more Editors, organized in its own internal Editor Layout Tree."

The workspace_pt.md §2.1 states:

    "Hospeda um EditorHost (que, por sua vez, hospeda um ou mais Editores)."

The editors.md §3 states:

    "Area and Editor are distinct concepts, but they share responsibilities through composition."

The workspace-implementation.md Phase 2 states:

    "EditorHost manages a list of Editors, with one active."

The prototype (Prototipagem_UI_06.pdf) shows:

* Areas labeled Area Left, Area Central, Area Right, Area Bottom.
* Each Area hosting one or more Editors (via tabs at the bottom of the Area).
* The Central Area can be split horizontally and vertically, hosting multiple Editors simultaneously (e.g., 2×2 grid of MPR viewers).

The contradiction: three incompatible readings exist:
* Area = Editor (single concept, no EditorHost).
* Area ⊃ EditorHost ⊃ Editor (Area is a structural container; EditorHost manages Editors).
* Area ⊃ Editor (Area directly hosts Editors, no EditorHost).

This ADR resolves the contradiction.

Decision:
* Area and Editor are distinct concepts.
* Area is a structural container provided by the Workspace. It occupies a position in the Area Layout Tree and hosts one or more Editors.
* Editor is a functional unit provided by the system, a Module, or a Plugin. It provides a specific interaction experience (Viewport3D, MPR Viewer, Console, Properties, etc.).
* An Area hosts Editors. The Central Area may be split horizontally and vertically, hosting multiple Editors simultaneously in an internal Editor Layout Tree.
* There is no EditorHost component.
* The EditorHost mentioned in earlier drafts (workspace_pt.md §2.1, workspace-implementation.md Phase 2) is removed. The Area itself manages its Editors directly.
* The overview.md §5.4 statement is corrected: Area and Editor are not the same concept. The correct statement is that they are complementary: Area provides where, Editor provides what.

## 3. Rationale
### 3.1 The prototype demands the distinction
The prototype shows:

Area Left, Area Central, Area Right, Area Bottom as structural regions.

The Central Area split into a 2×2 grid, hosting four different Editors (Axial MPR, Sagittal MPR, Coronal MPR, 3D Viewport).
Tabs at the bottom of each Area to switch between Editors.

If Area = Editor, then:
* The Central Area would have to be four different Areas (one per quadrant), losing the "Central" identity.
* The tabs at the bottom would have to belong to four different entities.
* The Region concept (a geometric grouping of Areas) would lose its meaning.
* The distinction is required by the design.

### 3.2 The Region concept requires Areas to be containers
The workspace_en.md §7.2 defines Region as "a geometric area derived from the Area Layout Tree that groups related Areas." If Area = Editor, then Regions group Editors, and the concept of "Central Region" becomes "group of Editors that happen to be in the center."

With the distinction, Regions group Areas, and an Area may host multiple Editors. The Central Region can contain one Area (Central) hosting a 2×2 grid of Editors. This matches the prototype.

### 3.3 The EditorLayoutSpec requires the distinction
The workspace_en.md §3.5 defines:

    python
    @dataclass(frozen=True)
    class EditorLayoutSpec:
        type: LayoutType                          # LEAF | SPLIT
        direction: SplitDirection | None = None   # HORIZONTAL | VERTICAL
        children: tuple["EditorLayoutSpec", ...] = ()
        editor_id: str | None = None              # when type == LEAF

This describes an internal tree of Editors inside an Area. If Area = Editor, this structure has no place to live. The distinction gives it a home.

### 3.4 The Editor lifecycle requires the distinction
editors.md §4 defines a lifecycle for Editors:


    instantiated → registered → inserted → activated ⇄ deactivated → removed → disposed
And a separate lifecycle for Areas (workspace_en.md §2.3):

    created → registered → placed → activated → deactivated → unregistered → destroyed

If Area = Editor, these two lifecycles must be merged. The merge would be awkward: an Editor is created by the EditorRegistry, inserted into an Area, activated, deactivated, removed, disposed — while the Area goes through its own lifecycle. Keeping them separate is cleaner.

### 3.5 Toolbars, Tools, and EditorContext belong to Editors
editors.md §10, §11, and §15 define:

* Toolbar is internal to an Editor.
* Tools are referenced by Toolbars.
* EditorContext is provided to an Editor.

If Area = Editor, then all of these become properties of Areas, which contradicts the Workspace's single rule (workspace_en.md §1.2):

"The Workspace manages Areas and Overlays... it does not own clinical state, Tools, Toolbars, or Module behavior."

The Workspace must not know about Toolbars or Tools. If Areas were Editors, and Editors have Toolbars, then the Workspace would indirectly own Toolbars. The distinction preserves the rule.

## 4. Consequences
## 4.1 Positive consequences
The prototype is consistent. Areas as containers, Editors as content, tabs at the bottom of each Area, 2×2 grid inside the Central Area.

Regions group Areas, not Editors. The Central Region can contain one Area (Central) with a complex internal Editor Layout Tree.

Two Editors of the same type may coexist. Within a single Area, each Editor must have a unique `editor_id`. A user who wants two Viewport3D
Editors in the same Area registers them under distinct editor_ids (e.g. `editor.viewport_3d.left` and `editor.viewport_3d.right`), both
pointing to the same Editor class in the EditorRegistry.

`Area.add_editor` rejects duplicate editor_ids with a clear `AreaError`. The LayoutBuilder propagates that error without swallowing it.

* The EditorLayoutSpec has a home — inside the Area.
* The Workspace remains ignorant of Toolbars, Tools, and Editor behavior.
* Modules declare Editor IDs, not Editor classes. The EditorRegistry resolves them.

### 4.2 Negative consequences
* The overview.md §5.4 must be corrected. The statement "Area and Editor are the same concept" is wrong.
* The EditorHost is removed. The workspace_pt.md §2.1, workspace-implementation.md Phase 2, and the folder structure must be updated.
* The Area must manage its Editors directly. The Area exposes methods to add, remove, and activate Editors, and to host the internal Editor Layout Tree.
* Two parallel lifecycles must be documented clearly. The Area lifecycle and the Editor lifecycle are related but distinct. The editors.md §4 and workspace_en.md §2.3 must be cross-referenced.