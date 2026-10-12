# Workspace
## 1. Concept
The Workspace is the runtime environment where clinical work happens. It is not a single widget nor a single class. It is a composition of Areas — containers that host Editors — and Overlays — floating layers over regions.

### 1.1 What the Workspace is
A container of Areas.

A layout coordinator that arranges Areas in a split tree.

A lifecycle manager for Areas and Editors.

An Overlay manager.

A configuration target whose layout is persisted per project and per Module.

A materializer of UI compositions declared by Modules.

### 1.2 The single rule
The Workspace manages Areas and Overlays and coordinates their layout and lifecycle. It may depend on the platform contracts required to materialize and manage them, but it does not own clinical state, Tools, Toolbars, or Module behavior.

If something is not an Area and not an Overlay, the Workspace does not interpret it. Toolbars, Tools and Modules are invisible to the Workspace, but the Workspace may use platform services (LayoutRenderer, EditorRegistry, OverlayManager) to materialize and manage its elements.

### 1.3 Module declares; Workspace materializes
The Module declares the UI composition. The Workspace materializes that declaration.

The Module does not own Areas or Editors. It describes what it wants through a ModuleUISpec.

The Workspace materializes it:

Resolves editor_id values in the EditorRegistry.

Creates Editor instances.

Creates Areas.

Builds the two layout trees (Area and Editor).

Renders into Qt widgets.

Positions Overlays.

The Workspace does not know the Module. It only receives the specification.

## 2. Core Concept: Area
An Area is the fundamental building block of the Workspace.

This is Principle #7 (Panels Are Areas): there are no SidePanel, BottomPanel, CentralArea or ToolbarArea classes. There is only Area.

### 2.1 What an Area is
An Area is a container of Editors. It:

Has a stable identifier within a layout context (e.g., area.left, area.central).

Has a title (user-facing, translatable via i18n).

Hosts one or more Editors, organized in its own internal Editor Layout Tree.

Has a visibility state (shown/hidden).

Is positioned by the Area Layout Tree, never by itself.

Every Area follows the same model. There is no special type of Area. Any Area (LEFT, CENTRAL, RIGHT, BOTTOM) may host one or multiple Editors.

### 2.2 What an Area is NOT
Not a Toolbar. A Toolbar is a widget inside an Editor.

Not a Module. A Module declares which Areas it wants the Workspace to materialize.

Not a state holder for clinical data. State lives in the Scene.

Not a manager of other Areas.

### 2.3 Area lifecycle
text
created → registered → placed → activated → deactivated → unregistered → destroyed
State	Meaning
created	Instance exists, not yet in the Workspace.
registered	Known to the AreaManager.
placed	Assigned to a position in the Area Layout Tree.
activated	Visible and receiving user input.
deactivated	Hidden but still registered.
unregistered	Removed from the AreaManager.
destroyed	Instance disposed.

## 3. Workspace Architecture
### 3.1 High-level composition
The Workspace is a split tree of Areas, not a fixed set of panels.

```
text
+-------------------------------------------------------+
|                     MainWindow                        |
+-------------------------------------------------------+
|  +----------+----------------------+----------+       |
|  | Area     | Area                 | Area     |       |
|  | left     | central              | right    |       |
|  +----------+----------------------+----------+       |
|                                                       |
|  +---------------------------------------------------+|
|  | Area — bottom                                     ||
|  +---------------------------------------------------+|
+-------------------------------------------------------+`
```

Every visible rectangle is an Area. Each Area hosts its own Editor Layout Tree, containing the Editors assigned to it.

The Workspace does not define a default layout. It is an empty skeleton until a Module declares the UI composition it wants.

Who decides how many and which Areas exist is the Module loaded by the Flow:

Module	UI composition
Patient	[central]
3D Mesh Editing	[left, central, right]
Tomography	[left, central, right, bottom]
The tree is the single source of truth for structure.

### 3.2 Relationship diagram

Key points:

The Workspace knows Area, AreaManager, LayoutTree, LayoutState, OverlayManager and EditorRegistry.

The Workspace has no reference to Scene, Editor, Toolbar or Module.

The Workspace materializes a ModuleUISpec, but does not know the Module.

AreaSpec references Editors via editor_id (string).

The EditorRegistry resolves editor_id to concrete classes.

The LayoutTree is an N-ary tree of Leaf and Split.

Each Area hosts an internal Editor Layout Tree (same model).

Structure lives in the trees; presentation state lives in LayoutState.

A Region is derived geometrically from the Area Layout Tree.

An Overlay covers a Region.

### 3.3 Application chrome
Some visual elements are not Areas nor Overlays:

The native OS menu bar (if any).

Native window controls (if not embedded in the Top Bar).

These belong to the MainWindow.

There is no status bar. The traditional status bar role is served by the Console Area (bottom), when the Module declares it.

For details on the Top Bar (Painel Superior) — a structural component of the Workspace, not an Overlay — and its 3 segments, see top-bar.md.

### 3.4 Data flow
The Workspace does not mutate clinical state. It only presents it.
```
text
User action → Editor → Command → CommandBus → Scene (mutation) → EventBus → Editors → redraw
```
Read/write separation:

Read: the Editor accesses the Scene via SceneProvider (read-only API).

Write: the Editor publishes Commands to the CommandBus. It never mutates the Scene directly.

This keeps the Scene as the single source of truth for clinical data.

Workspace actions (switching active Editor, changing visibility, resizing) are UI operations, not clinical Commands. They update LayoutState and are persisted with the project. They are not mixed with the clinical undo/redo history.

### 3.5 The Module declares the UI composition
The Workspace does not decide which Areas exist. Each Module declares its UI composition through a ModuleUISpec.
```
python
@dataclass(frozen=True)
class ModuleUISpec:
    areas: list[AreaSpec]
    overlays: list[OverlaySpec]

@dataclass(frozen=True)
class AreaSpec:
    area_id: str
    title: str
    placement: Placement
    editor_layout: EditorLayoutSpec

@dataclass(frozen=True)
class EditorLayoutSpec:
    type: LayoutType                          # LEAF | SPLIT
    direction: SplitDirection | None = None   # HORIZONTAL | VERTICAL
    children: tuple["EditorLayoutSpec", ...] = ()
    editor_id: str | None = None              # when type == LEAF
```
Important points:

Placement is semantic metadata. It is used to associate Areas with Regions and to build the initial tree.

It is preserved after construction, because Regions depend on it.

AreaSpec declares its Editors through an EditorLayoutSpec, not a flat list.

The Module does not import the Editor classes.

The EditorRegistry resolves the IDs to concrete classes.

Validation rules (enforced before materialization):

LEAF must have editor_id and must not have children.

SPLIT must have direction and at least two children, and must not have editor_id.

Every editor_id must resolve in the EditorRegistry.

Placement must be one of LEFT, CENTRAL, RIGHT, BOTTOM.

A ModuleUISpec must declare at least CENTRAL.

If any rule is violated, the Workspace rejects the load with a clear error. It does not fall back silently.

Example:
```
text
Orthognathic Module declares:

ModuleUISpec(
    areas=[
        AreaSpec("area.left", "Lists", Placement.LEFT,
            EditorLayoutSpec.leaf("editor.object_list")),

        AreaSpec("area.central", "Editing", Placement.CENTRAL,
            EditorLayoutSpec.split(HORIZONTAL, (
                EditorLayoutSpec.leaf("editor.viewport_3d"),
                EditorLayoutSpec.split(VERTICAL, (
                    EditorLayoutSpec.leaf("editor.mpr_axial"),
                    EditorLayoutSpec.leaf("editor.mpr_sagittal"),
                )),
            ))),

        AreaSpec("area.right", "Tools", Placement.RIGHT,
            EditorLayoutSpec.split(VERTICAL, (
                EditorLayoutSpec.leaf("editor.properties"),
                EditorLayoutSpec.leaf("editor.material"),
            ))),

        AreaSpec("area.bottom", "Consoles", Placement.BOTTOM,
            EditorLayoutSpec.split(HORIZONTAL, (
                EditorLayoutSpec.leaf("editor.console"),
                EditorLayoutSpec.leaf("editor.history"),
                EditorLayoutSpec.leaf("editor.ai_assistant"),
            ))),
    ],
)
```
Placement rules:

    CENTRAL — the center of the Area Layout Tree. There may be multiple Central Areas in a complex composition.
  
    LEFT — flanks the central region on the left.
  
    RIGHT — flanks the central region on the right.
  
    BOTTOM — sits below the horizontal row.

Switching Modules: the Workspace receives a new ModuleUISpec and reconciles its current layout against it (see §6.4).

### 3.6 EditorRegistry
The EditorRegistry resolves editor_id to concrete Editor implementations.

```
python
class EditorRegistry:
    def register(self, editor_id: str, editor_type: type[Editor]) -> None: ...
    def resolve(self, editor_id: str) -> type[Editor]: ...
    def create(self, editor_id: str) -> Editor: ...
```
The Registry registers types, not instances. It answers:

"Which Editor types exist and how are they created?"

Availability is a separate concern. Not every registered Editor is usable in every context. Availability depends on:

The active Scene.

The active project.

The current Area.

Required capabilities and data.

Registry population:

System Editors register at boot.

Modules register their Editors when loaded.

Plugins register their Editors when activated.

## 4. Editor
An Editor is the functional unit hosted by an Area. There is no distinction between "Viewport", "Panel" or "Editor". They are all Editors.

For full details on the Editor lifecycle and catalog, see editors.md.

### 4.1 What an Editor is
An Editor is a widget that:

Renders or edits a specific type of content.

Receives Scene events via SceneProvider (read).

Emits user intent via Command (write).

May have its own internal toolbar.

The Workspace does not know what an Editor does.

### 4.2 Editor lifecycle
The Editor lifecycle is distinct from the Area lifecycle:

Stage	Meaning
instantiated	The Editor instance is created.
registered	The Editor type is registered in the EditorRegistry.
inserted	The instance is added to an Area's Editor Layout Tree.
activated	The instance is the active Editor within the Area.
deactivated	The instance is no longer active but is still hosted.
removed	The instance is removed from the composition.
disposed	The instance is destroyed and its resources are released.
Instance vs type: the EditorRegistry maintains types; the Workspace maintains instances. They are different concepts and must not be confused.

Initialization with the Scene occurs at insertion (once). Later activations sync the presentation state, without re-initializing heavy resources.

### 4.3 Editor catalog
The system keeps a global Editor catalog, organized by category:

Category	Editors
View	Viewport3DEditor, MPRViewerEditor
Mesh	MeshEditor, NodeEditor
Data	PropertiesEditor, SceneEditor, DocumentEditor
Console	ConsoleEditor
Aux	AIConsoleEditor, HistoryEditor, AnimationEditor
Populated by: System Editors, Editors registered by Modules, Editors registered by Plugins.

### 4.4 Where an Editor sits
The Editor does not decide where it sits. The Area hosts it. The Area's internal Editor Layout Tree determines its position.

Who decides which Editor goes in which Area:

The Module, when declaring its AreaSpec.

The user, when adding an Editor to an existing Area.

Typical conventions (not rules):

Editor	Where it typically sits
PropertiesEditor	Right or Bottom
ConsoleEditor	Bottom
NodeEditor	Central
Viewport3DEditor	Central
MPRViewerEditor	Central
Instance policy: each Editor is a new instance. Two Viewport3DEditor are two independent instances.

### 4.5 Toolbars
A Toolbar is an internal widget of an Editor, not an Area. Each Editor decides whether it wants its own Toolbar. The Workspace never hosts Toolbars.
```
text
Editor
├── Toolbar
│   └── Tools
├── Content
└── Overlays
```
The Toolbar is a declarative specification of the Editor. It is materialized by the Editor itself, respecting the declared orientation (HORIZONTAL or VERTICAL).

Tools do not belong to a specific Toolbar. They belong to a shared catalog, the ToolRegistry, and may be referenced by Toolbars from different Editors.

An Editor may declare more than one Toolbar, with independent orientations:
```
text
Editor
├── Toolbar Vertical:   Tool2, Tool4
├── Content
├── Overlays
└── Toolbar Horizontal: Tool1, Tool2, Tool4
```

### 4.6 Adding and switching Editors
Adding an Editor (a UI operation):

The system opens the available Editor catalog for the current context.

The user chooses an Editor.

The system creates a new instance.

The Editor is added to the Area's internal Editor Layout Tree.

The new Editor becomes active.

Switching the active Editor (a UI operation):

The current Editor is deactivated (without destroying it).

The new Editor is activated.

The activation syncs with the current Scene state.

LayoutState.active_editor_per_area is updated.

These are UI operations, not clinical Commands. They are persisted with the layout, not with the clinical history.

Removing an Editor is different from switching. Removing is done via ❌ and triggers the removal lifecycle.

For details, see editors.md.

## 5. Layout Model — Dual N-ary Split Trees
### 5.1 The model
The Workspace has two kinds of layout trees, both following the same N-ary split tree model:

Area Layout Tree (external) — organizes the Areas of the Workspace.

Editor Layout Trees (internal) — each Area has its own, organizing the Editors hosted by that Area.

Node types (both trees):

A Leaf contains exactly one element (Area or Editor).

A Split contains two or more children and a direction (HORIZONTAL or VERTICAL).

```
text
Workspace
├── Area Layout Tree (external)
│   ├── Area LEFT      → Editor Layout Tree (internal)
│   ├── Area CENTRAL   → Editor Layout Tree (internal)
│   ├── Area RIGHT     → Editor Layout Tree (internal)
│   └── Area BOTTOM    → Editor Layout Tree (internal)
└── Overlays
```
This is the only layout mechanism. No slots, no predefined templates, no grid.

There is no special Area. LEFT, CENTRAL, RIGHT, and BOTTOM follow the same model.

### 5.2 Initial state
The Workspace starts empty. There is no pre-built tree.

Both trees are built when the first Module is loaded, from the ModuleUISpec.

Examples:

Patient Module ([central] with one Editor):
```
text
Area Layout Tree: Leaf(area.central)
Editor Layout Tree (area.central): Leaf(editor.patient)
```
Tomography Module (central with 2×2 Editors, right with 2 Editors, bottom with 3 Editors):
```
text
Area Layout Tree:
Split(VERTICAL)
├── Split(HORIZONTAL)
│   ├── Leaf(area.left)
│   ├── Leaf(area.central)
│   └── Leaf(area.right)
└── Leaf(area.bottom)
```

Editor Layout Tree (area.central):
```
Split(HORIZONTAL)
├── Leaf(editor.mpr_axial)
└── Split(VERTICAL)
    ├── Leaf(editor.mpr_sagittal)
    └── Leaf(editor.viewport_3d)
```

Editor Layout Tree (area.right):
```
Split(VERTICAL)
├── Leaf(editor.properties)
└── Leaf(editor.material)
```

Editor Layout Tree (area.bottom):
```
Split(HORIZONTAL)
├── Leaf(editor.console)
├── Leaf(editor.history)
└── Leaf(editor.ai_assistant)
```

### 5.3 Structure vs presentation state
The trees are the single source of truth for structure. They are not the single source of truth for all visual state.

The following are stored separately in LayoutState:

State	Purpose
Proportions	QSplitter sizes per node
Visibility	Which Areas are shown or hidden
Active Editor per Area	Which Editor receives input in each Area
The following are stored separately in OverlayState:

State	Purpose
Presence	Which Overlays exist
Configuration	Overlay-specific settings
Anchoring	Which Region each Overlay targets
These state models may be serialized together with the trees, but their responsibilities are distinct.

### 5.4 Resizing and reconciliation
Each Split (in either tree) is rendered as a QSplitter. The user can drag the dividers to resize adjacent elements.

Reconciliation rule:

The tree determines the structure.

LayoutState stores proportions and preferences.

The LayoutRenderer materializes both.

User interactions update the model that owns the value.

The renderer never silently alters structure to reflect a widget.

Without this rule, when a user drags a QSplitter divider, the new proportion would be lost on the next render.

### 5.5 Rendering
Rendering both trees into Qt widgets is the responsibility of the LayoutRenderer.

The layout trees are pure data models, with no Qt dependency. The LayoutRenderer is the Anti-Corruption Layer between the models and Qt.

The LayoutRenderer renders recursively:

An Area Layout Tree Split → QSplitter at the Workspace level.

An Area Layout Tree Leaf → the Area widget.

Inside each Area, its Editor Layout Tree Split → QSplitter.

Its Editor Layout Tree Leaf → the Editor widget.

### 5.6 Persistence
Layout persistence is keyed by context:
```

text
project_id + module_id + layout_schema_version
```
Reason: different Modules require different compositions. A tomography flow and an orthognathic planning flow need distinct layouts. The Workspace must remember the personalization for each Module independently.

Serialization format:
```
json
{
  "layout_schema_version": 1,
  "module_id": "orthognathic",
  "area_tree": {
    "type": "split",
    "direction": "vertical",
    "children": [
      {
        "type": "split",
        "direction": "horizontal",
        "children": [
          { "type": "leaf", "area_id": "area.left" },
          { "type": "leaf", "area_id": "area.central" },
          { "type": "leaf", "area_id": "area.right" }
        ]
      },
      { "type": "leaf", "area_id": "area.bottom" }
    ]
  },
  "editor_trees": {
    "area.left": { "type": "leaf", "editor_id": "editor.object_list" },
    "area.central": {
      "type": "split", "direction": "horizontal",
      "children": [
        { "type": "leaf", "editor_id": "editor.viewport_3d" },
        { "type": "split", "direction": "vertical",
          "children": [
            { "type": "leaf", "editor_id": "editor.mpr_axial" },
            { "type": "leaf", "editor_id": "editor.mpr_sagittal" }
          ]
        }
      ]
    }
  },
  "layout_state": {
    "proportions": { "central_split": [0.7, 0.3] },
    "visibility": { "area.left": true, "area.right": true },
    "active_editor_per_area": {
      "area.central": "editor.viewport_3d"
    }
  },
  "overlay_state": {
    "top_bar": { "visible": true }
  }
}
```
This JSON is stored inside the project file, not in user settings.

Precedence when opening a project:

Persisted layout for (project_id, module_id) if compatible with the current ModuleUISpec.

Default layout declared by the ModuleUISpec.

System fallback (single central Area with a single Editor).

If the persisted layout is incompatible with the current ModuleUISpec, the Workspace reconciles it (see §6.4). If reconciliation is not possible, it rebuilds from the ModuleUISpec and reports the change.

If the ModuleUISpec itself is invalid, the Workspace rejects the load with a clear error. The system fallback is reserved for controlled recovery, not for masking configuration errors.

5.7 Why an N-ary tree
Simple: two node types.

Recursive: each subtree is a complete layout.

Composable: any element can be split; any split can be closed.

Persistable: JSON maps directly to the tree.

Direct mapping to Qt: each Split is rendered as a QSplitter; each Leaf as a widget.

### 5.8 Evolution
The tree model is stable. Future operations:

split and close of nodes.

Drag-and-drop to reorder Leaves.

Floating Areas.

Multiple Workspaces.

None of these operations changes the tree model.

## 6. Workspace Lifecycle
### 6.1 Startup
```
text
QApplication starts
    ↓
MainWindow created
    ↓
Workspace created (empty — no trees)
    ↓
Modules loaded via ModuleRegistry
    ↓
Initial Flow is selected
    ↓
First Module is loaded
    ↓
Workspace reads the Module's ModuleUISpec and validates it
    ↓
LayoutBuilder builds the Area Layout Tree + Editor Layout Trees
    ↓
LayoutRenderer renders as nested QSplitters
    ↓
Workspace positions Overlays over Regions
    ↓
Workspace shown to the user
```

### 6.2 Opening a project
```
text
Project opened
    ↓
Scene loaded from JSON
    ↓
Project Flow is selected
    ↓
Flow Module is loaded
    ↓
Persisted layout for (project_id, module_id) is loaded (if it exists)
    ↓
If compatible with the ModuleUISpec:
    Workspace reconciles the current trees against it
Else:
    LayoutBuilder builds the trees from the ModuleUISpec
    ↓
LayoutRenderer renders the trees
    ↓
Workspace positions Overlays over Regions
    ↓
Editors redraw from Scene state
```

### 6.3 Shutdown
```
text
User closes the window
    ↓
Workspace serializes:
    - Area Layout Tree
    - Editor Layout Trees
    - LayoutState
    - OverlayState
    ↓
Scene saved (if dirty)
    ↓
QApplication exits
```

### 6.4 Module switch — layout resolution
Rule: the layout is remembered per Module, not globally.
```
text
User selects another Module
    ↓
Workspace loads the ModuleUISpec and validates it
    ↓
If a persisted layout exists for (project_id, module_id):
    If compatible with the ModuleUISpec:
        Reuse the persisted layout
    Else:
        Rebuild from the ModuleUISpec and record the reason
Else:
    Build from the ModuleUISpec
    ↓
Reconcile the new trees against the current instances
    ↓
LayoutBuilder builds the trees
    ↓
LayoutRenderer renders the trees
    ↓
Workspace repositions Overlays
```

Precedence:

First activation of the Module in the project: materialize the layout declared in the ModuleUISpec.

Subsequent activations: restore the personalized layout for that Module, if it exists and is compatible.

Missing or incompatible layout: rebuild from the ModuleUISpec.

Invalid ModuleUISpec: report a clear error. Do not use the system fallback to hide configuration errors.

### 6.5 Area and Editor reconciliation
Area identity is stable within a layout context (project_id + module_id). It does not imply that area.central is the same instance across all Modules.

Reconciliation rules:

area_id identifies an Area within the current layout context.

If the area_id remains, the Workspace reuses the container and reconciles its internal Editor Layout Tree.

If the internal tree changes:

Editors already present and compatible are preserved.

Editors no longer needed are removed (not destroyed immediately) and follow the removal lifecycle.

New Editors are instantiated and inserted.

If an Area no longer exists in the new composition, it is removed from the layout and follows the disposal lifecycle.

Compatibility is defined per Editor type, not by tree shape. Two different trees may share the same Editor instances.

This avoids destroying an entire Area just because its internal composition changed.

## 7. Overlays
### 7.1 Concept
An Overlay is a floating layer that the Workspace positions over a Region of Areas.

The Overlay:

Does not interfere with the layout — it floats over the Areas.

Is not an Area. It is not hosted by any Area.

Is managed by the Workspace (via OverlayManager).

The Top Bar is not an Overlay. It is a structural component of the Workspace. Overlays are floating elements with their own positioning and hit-testing contracts. The distinction is architectural, not visual.

### 7.2 Regions
A Region is a geometric area derived from the Area Layout Tree that groups related Areas.

A Region is not identified by coordinates alone. Region discovery must consistently determine which Areas compose a region and which bounds delimit it.

Discovery rules:

Placement provides the initial association between Areas and Regions.

Placement is preserved as semantic metadata after construction.

If the user rearranges the tree, the association is revalidated against the current structure.

Placement.CENTRAL may apply to multiple Central Areas in a complex composition.
```
  python
  @dataclass
  class Region:
      id: str                # "central", "left", "right", "bottom"
      bounds: Rect           # rectangle that contains the Region
      areas: list[Area]      # Areas that belong to the Region
      semantic_role: Placement | None
```
Why geometric, with structural support:

Allows arbitrary splits.

Allows multiple Areas per region.

Allows future floating areas.

Avoids fragile inferences based on pixel coordinates.

### 7.3 Overlay geometry and interaction
Each Overlay defines:

Target Region — the Region it floats over.

Anchoring rules — how it aligns within the Region (top, bottom, left, right, margins).

Resize behavior — how it adapts when the Region changes.

Focus behavior — whether it can receive focus.

Hit testing — how to distinguish interaction with the Overlay from interaction with content underneath.

Positioning limits — minimum and maximum sizes, allowed regions.

These contracts are documented in a dedicated specification.

### 7.4 When the layout changes
Whenever the layout changes (new Module, split, window resize, visibility of lateral Areas), the Workspace:

Recomputes the bounds of each Region.

Repositions the Overlays.

The Overlay is reactive.

### 7.5 Other Overlays
The Top Bar is a structural component, not an Overlay.

Future Overlays may include:

Floating tool palettes.

Context menus anchored to selection.

Temporary informational panels.

### 7.6 Persistence
The presence and configuration of Overlays are persisted in OverlayState, alongside the layout trees, inside the project file.

## 8. Open Questions
### 8.1 Is the layout per-project or per-user?
Decision: Hybrid.

Composition and personalization of the current project are persisted in the project, keyed by (project_id, module_id).

General interface preferences (theme, fonts, default proportions) are persisted in user settings.

Project-level personalization takes precedence for the current clinical composition.

### 8.2 Does the global Editor catalog exist?
Decision: Yes, with contextual availability.

The EditorRegistry maintains all Editor types known to the system. A selection catalog may present Editors available in the current context, respecting:

Required data (mesh, DICOM series, planning model).

Required capabilities.

Dependencies on other Modules.

This avoids both an artificially restricted catalog and the ability to open an Editor that cannot function in the current project.

### 8.3 How to handle floating Areas on multi-monitor?
Decision: Out of initial scope, preserving future extension.

The initial model does not add the complexity of floating windows, per-monitor restoration, or separate 3D rendering contexts. However, the model does not assume that every Area will always have the main Workspace as its only visual parent.

### 8.4 Where does the "active Area" concept live?
Decision: The Workspace is the authority for the active Area.

Each Area may maintain its own local focus state. The Workspace tracks which Area has global focus, which is required to route keyboard shortcuts, contextual commands, and actions such as "add Editor" to the correct Area.

### 8.5 Who registers Editors?
Decision: Registration is separate from availability.

The EditorRegistry answers: "Which Editor types exist and how are they created?"

The contextual selection answers: "Which of these Editors can be added to this Area, with this Scene and in this project?"

This separation is important for Editors that require specific data or capabilities. It does not require a complex permission framework — it only requires that global registration not be interpreted as universal availability.