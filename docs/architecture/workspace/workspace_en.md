Workspace
1. Concept
The Workspace is the runtime environment where clinical work happens. It is not a single widget nor a single class. It is a composition of Areas — containers that host Editors — and Overlays — floating layers over regions.

1.1 What the Workspace is
A container of Areas.

A layout coordinator that arranges Areas in a split tree.

A lifecycle manager for Areas.

An Overlay manager.

A configuration target whose layout can be persisted per project.

A materializer of UI compositions declared by Modules.

1.2 The single rule
The Workspace hosts Areas and Overlays. Nothing else.

If something is not an Area and not an Overlay, the Workspace does not know it exists. Toolbars, Tools and Modules are invisible to the Workspace.

1.3 Module declares; Workspace materializes
The Module declares the UI composition. The Workspace materializes it.

The Module does not own Areas or Editors. It describes what it wants through a ModuleUISpec.

The Workspace materializes it:

Resolves editor_id values in the EditorRegistry.

Creates Editor instances.

Creates Areas.

Builds the two layout trees (Area and Editor).

Renders into Qt widgets.

Positions Overlays.

The Workspace does not know the Module. It only receives the specification.

2. Core Concept: Area
An Area is the fundamental building block of the Workspace.

This is Principle #7 (Panels Are Areas): there are no SidePanel, BottomPanel, CentralArea or ToolbarArea classes. There is only Area.

2.1 What an Area is
An Area is a container of Editors. It:

Has a stable identifier (e.g., area.left, area.central).

Has a title (user-facing, translatable via i18n).

Hosts one or more Editors, organized in its own internal Editor Layout Tree.

Has a visibility state (shown/hidden).

Is positioned by the Area Layout Tree, never by itself.

Every Area follows the same model. There is no special type of Area. Any Area (LEFT, CENTRAL, RIGHT, BOTTOM) may host one or multiple Editors.

The Area does not store placement. The placement is construction metadata of the AreaSpec. Once the trees are built, it is no longer consulted.

2.2 What an Area is NOT
Not a Toolbar. A Toolbar is a widget inside an Editor.

Not a Module. A Module declares which Areas it wants the Workspace to materialize.

Not a state holder. State lives in the Scene.

Not a manager of other Areas.

2.3 Area lifecycle
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
3. Workspace Architecture
3.1 High-level composition
The Workspace is a split tree of Areas, not a fixed set of panels.

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
+-------------------------------------------------------+
Every visible rectangle is an Area. Each Area hosts its own Editor Layout Tree, containing the Editors assigned to it.

The Workspace does not define a default layout. It is an empty skeleton until a Module declares the UI composition it wants.

Who decides how many and which Areas exist is the Module loaded by the Flow:

Module	UI composition
Patient	[central]
3D Mesh Editing	[left, central, right]
Tomography	[left, central, right, bottom]
The tree is the single source of truth for the layout.

3.2 Relationship diagram






























































































Key points:

The Workspace knows Area, AreaManager, LayoutTree, OverlayManager and EditorRegistry.

The Workspace has no reference to Scene, Editor, Toolbar or Module.

The Workspace materializes a ModuleUISpec, but does not know the Module.

AreaSpec references Editors via editor_id (string).

The EditorRegistry resolves editor_id to concrete classes.

The LayoutTree is an N-ary tree of Leaf and Split.

Each Area hosts an internal Editor Layout Tree (same model).

A Region is derived geometrically from the LayoutTree.

An Overlay covers a Region.

3.3 Application chrome
Some visual elements are not Areas nor Overlays:

The native OS menu bar (if any).

Native window controls (if not embedded in the Top Bar).

These belong to the MainWindow.

There is no status bar. The traditional status bar role is served by the Console Area (bottom), when the Module declares it.

For details on the Top Bar (Painel Superior) and its 3 segments, see top-bar.md.

3.4 Data flow
The Workspace does not mutate clinical state. It only presents it.

text
User action → Editor → Command → CommandBus → Scene (mutation) → EventBus → Editors → redraw
Read/write separation:

Read: the Editor accesses the Scene via SceneProvider (read-only API).

Write: the Editor publishes Commands to the CommandBus. It never mutates the Scene directly.

This keeps the Scene as the single source of truth.

3.5 The Module declares the UI composition
The Workspace does not decide which Areas exist. Each Module declares its UI composition through a ModuleUISpec.

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
    children: list[EditorLayoutSpec] = []
    editor_id: str | None = None              # when type == LEAF
Important points:

Placement is construction metadata. Used by the LayoutBuilder to build the Area Layout Tree.

AreaSpec declares its Editors through an EditorLayoutSpec, not a flat list.

The Module does not import the Editor classes.

The EditorRegistry resolves the IDs to concrete classes.

Example:

text
Orthognathic Module declares:

ModuleUISpec(
    areas=[
        AreaSpec("area.left", "Lists", Placement.LEFT,
            EditorLayoutSpec.leaf("editor.object_list")),

        AreaSpec("area.central", "Editing", Placement.CENTRAL,
            EditorLayoutSpec.split(HORIZONTAL, [
                EditorLayoutSpec.leaf("editor.viewport_3d"),
                EditorLayoutSpec.split(VERTICAL, [
                    EditorLayoutSpec.leaf("editor.mpr_axial"),
                    EditorLayoutSpec.leaf("editor.mpr_sagittal"),
                ]),
            ])),

        AreaSpec("area.right", "Tools", Placement.RIGHT,
            EditorLayoutSpec.split(VERTICAL, [
                EditorLayoutSpec.leaf("editor.properties"),
                EditorLayoutSpec.leaf("editor.material"),
            ])),

        AreaSpec("area.bottom", "Consoles", Placement.BOTTOM,
            EditorLayoutSpec.split(HORIZONTAL, [
                EditorLayoutSpec.leaf("editor.console"),
                EditorLayoutSpec.leaf("editor.history"),
                EditorLayoutSpec.leaf("editor.ai_assistant"),
            ])),
    ],
)
Placement rules:

CENTRAL — always exists; it is the center of the Area Layout Tree.

LEFT — flanks the central on the left.

RIGHT — flanks the central on the right.

BOTTOM — sits below the horizontal row.

Constraint: a ModuleUISpec must declare at least CENTRAL. Otherwise, the Workspace rejects the load with a clear error.

Switching Modules: when another Module is selected, the Workspace receives a new ModuleUISpec and discards the current Area Layout Tree. Areas with the same area_id may be reused if their declared editor layouts are compatible.

3.6 EditorRegistry
The EditorRegistry resolves editor_id to concrete Editor implementations.

python
class EditorRegistry:
    def register(self, editor_id: str, editor_type: type[Editor]) -> None: ...
    def resolve(self, editor_id: str) -> type[Editor]: ...
    def create(self, editor_id: str) -> Editor: ...
Why it exists:

The Module does not need to import the concrete Editor classes.

Plugins can register new Editors without changing the Workspace code.

Registry population:

System Editors register at boot.

Modules register their Editors when loaded.

Plugins register their Editors when activated.

4. Editor
An Editor is the functional unit hosted by an Area. There is no distinction between "Viewport", "Panel" or "Editor". They are all Editors.

For full details on the Editor lifecycle and catalog, see editors.md.

4.1 What an Editor is
An Editor is a widget that:

Renders or edits a specific type of content.

Receives Scene events via SceneProvider (read).

Emits user intent via Command (write).

May have its own internal toolbar.

The Workspace does not know what an Editor does.

4.2 Editor catalog
The system keeps a global Editor catalog, organized by category:

Category	Editors
View	Viewport3DEditor, MPRViewerEditor
Mesh	MeshEditor, NodeEditor
Data	PropertiesEditor, SceneEditor, DocumentEditor
Console	ConsoleEditor
Aux	AIConsoleEditor, HistoryEditor, AnimationEditor
Populated by: System Editors, Editors registered by Modules, Editors registered by Plugins.

4.3 Where an Editor sits
The Editor does not decide where it sits. The Area hosts it. The Area's internal Editor Layout Tree determines the position.

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

4.4 Toolbars
A Toolbar is an internal widget of an Editor, not an Area. Each Editor decides whether it wants its own Toolbar. The Workspace never hosts Toolbars.

text
Editor
├── Toolbar
│   └── Tools
├── Content
└── Overlays
The Toolbar is a declarative specification of the Editor. It is materialized by the Editor itself, respecting the declared orientation (HORIZONTAL or VERTICAL).

Tools do not belong to a specific Toolbar. They belong to a shared catalog, the ToolRegistry, and may be referenced by Toolbars from different Editors.

text
Viewport3DEditor
├── ViewportToolbar (VERTICAL)
│   ├── select_tool
│   ├── transform_tool
│   └── measure_tool
├── ViewportToolbar (HORIZONTAL)
│   ├── reset_view
│   └── fit_view
└── 3D View
Multiple Toolbars per Editor. An Editor may declare more than one Toolbar, with independent orientations:

text
Editor
├── Toolbar Vertical:   Tool2, Tool4
├── Content
├── Overlays
└── Toolbar Horizontal: Tool1, Tool2, Tool4
4.5 Adding an Editor
The user can add an Editor through:

+ button on the Area chrome.

Keyboard shortcut.

Context menu.

Flow:

The system opens the available Editor catalog.

The user chooses an Editor.

The system creates a new instance.

The Editor is added to the Area's internal Editor Layout Tree.

The new Editor becomes active.

Nothing is destroyed. The original Area keeps existing; the new Editor is additional.

4.6 Switching the active Editor
The user can switch between Editors within an Area:

The current Editor is detached (without destroying it).

The new Editor is attached.

The new Editor is initialized with the current Scene.

The change is recorded as a Command.

Note: switching the active Editor is different from removing an Editor. Removing is done via ❌.

For details, see editors.md.

5. Layout Model — Dual N-ary Split Trees
5.1 The model
The Workspace has two kinds of layout trees, both following the same N-ary split tree model:

Area Layout Tree (external) — organizes the Areas of the Workspace.

Editor Layout Trees (internal) — each Area has its own, organizing the Editors hosted by that Area.

Node types (both trees):

A Leaf contains exactly one element (Area or Editor).

A Split contains two or more children and a direction (HORIZONTAL or VERTICAL).

text
Workspace
├── Area Layout Tree (external)
│   ├── Area LEFT      → Editor Layout Tree (internal)
│   ├── Area CENTRAL   → Editor Layout Tree (internal)
│   ├── Area RIGHT     → Editor Layout Tree (internal)
│   └── Area BOTTOM    → Editor Layout Tree (internal)
└── Overlays
This is the only layout mechanism. No slots, no predefined templates, no grid.

There is no special Area. LEFT, CENTRAL, RIGHT, and BOTTOM follow the same model. Any Area may host one or multiple Editors.

5.2 Initial state
The Workspace starts empty. There is no pre-built tree.

Both trees are built when the first Module is loaded, from the ModuleUISpec.

Examples:

Patient Module ([central] with one Editor):

text
Area Layout Tree: Leaf(area.central)

Editor Layout Tree (area.central): Leaf(editor.patient)
3D Mesh Editing Module ([left, central, right] with one Editor each):

text
Area Layout Tree:
Split(HORIZONTAL)
├── Leaf(area.left)
├── Leaf(area.central)
└── Leaf(area.right)

Editor Layout Tree (area.left):    Leaf(editor.toolbox)
Editor Layout Tree (area.central): Leaf(editor.viewport_3d)
Editor Layout Tree (area.right):   Leaf(editor.properties)
Tomography Module (central with 2×2 Editors, right with 2 Editors, bottom with 3 Editors):

text
Area Layout Tree:
Split(VERTICAL)
├── Split(HORIZONTAL)
│   ├── Leaf(area.left)
│   ├── Leaf(area.central)
│   └── Leaf(area.right)
└── Leaf(area.bottom)

Editor Layout Tree (area.central):
Split(HORIZONTAL)
├── Leaf(editor.mpr_axial)
└── Split(VERTICAL)
    ├── Leaf(editor.mpr_sagittal)
    └── Leaf(editor.viewport_3d)

Editor Layout Tree (area.right):
Split(VERTICAL)
├── Leaf(editor.properties)
└── Leaf(editor.material)

Editor Layout Tree (area.bottom):
Split(HORIZONTAL)
├── Leaf(editor.console)
├── Leaf(editor.history)
└── Leaf(editor.ai_assistant)
The user can hide and re-show the Areas the Module declared.

The user can add new Editors to any Area's internal tree, and reorganize them.

5.3 Resizing
Each Split (in either tree) is rendered as a QSplitter. The user can drag the dividers to resize adjacent elements.

Sizes are relative.

Initial sizes are set once, when the tree is built.

Resizing does not change the tree structure — only the proportions.

5.4 Rendering
Rendering both trees into Qt widgets is the responsibility of the LayoutRenderer.

The layout trees are pure data models, with no Qt dependency. The LayoutRenderer is the Anti-Corruption Layer between the models and Qt.

The LayoutRenderer renders recursively:

An Area Layout Tree Split → QSplitter at the Workspace level.

An Area Layout Tree Leaf → the Area widget.

Inside each Area, its Editor Layout Tree Split → QSplitter.

Its Editor Layout Tree Leaf → the Editor widget.

Rules:

The layout trees are the single source of truth for structure.

The LayoutRenderer never invents structure.

If there is a divergence, the trees win.

5.5 Persistence
Both trees are serialized as nested JSON:

json
{
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
  "area_editor_trees": {
    "area.left": {
      "type": "leaf", "editor_id": "editor.toolbox"
    },
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
  }
}
This JSON is stored inside the project file, not in user settings.

Precedence when opening a project:

Persisted layout in the project (most specific).

Default layout declared by the Module.

System fallback (single central Area with a single Editor).

If the persisted layout is incompatible with the current Module, the Workspace discards it and rebuilds from the Module.

5.6 Why an N-ary tree
Simple: two node types.

Recursive: each subtree is a complete layout.

Composable: any element can be split; any split can be closed.

Persistable: JSON maps directly to the tree.

Direct mapping to Qt: each Split is rendered as a QSplitter; each Leaf as a widget.

5.7 Evolution
The tree model is stable. Future operations:

split and close of nodes.

Drag-and-drop to reorder Leaves.

Floating Areas.

Multiple Workspaces.

None of these operations changes the tree model.

6. Workspace Lifecycle
6.1 Startup
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
Workspace reads the Module's ModuleUISpec
    ↓
LayoutBuilder builds the Area Layout Tree + Editor Layout Trees
    ↓
LayoutRenderer renders as nested QSplitters
    ↓
Workspace positions Overlays over Regions
    ↓
Workspace shown to the user
6.2 Opening a project
text
Project opened
    ↓
Scene loaded from JSON
    ↓
Project Flow is selected
    ↓
Flow Module is loaded
    ↓
Persisted layout is loaded from the project (if it exists)
    ↓
If the persisted layout is compatible with the ModuleUISpec:
    Workspace uses the loaded layout
Else:
    LayoutBuilder builds the trees from the ModuleUISpec
    ↓
LayoutRenderer renders the trees
    ↓
Workspace positions Overlays over Regions
    ↓
Editors redraw from Scene state
6.3 Shutdown
text
User closes the window
    ↓
Workspace serializes the trees
    ↓
Scene saved (if dirty)
    ↓
QApplication exits
6.4 Module switch
text
User selects another Module
    ↓
Workspace discards the current trees
    ↓
For each AreaSpec of the new ModuleUISpec:
    If an Area is registered with the same area_id
    And the declared editor layouts are compatible:
        Reuse the instance
    Else:
        Create a new Area
    ↓
LayoutBuilder builds the new trees
    ↓
LayoutRenderer renders the new trees
    ↓
Workspace repositions Overlays
Explicit reuse rule:

An Area is reused only when the area_id is the same and the declared editor layouts are compatible.
Otherwise, the Area is reconfigured (Editors swapped) or replaced.

7. Overlays
7.1 Concept
An Overlay is a floating layer that the Workspace positions over a Region of Areas.

The Overlay:

Does not interfere with the layout — it floats over the Areas.

Is not an Area. It is not hosted by any Area.

Is managed by the Workspace (via OverlayManager).

7.2 Regions
A Region is a geometric area derived from the Area Layout Tree that groups related Areas.

The Region is computed from the rendered Areas (bounding boxes). The LayoutTree exposes find_regions().

The Region is NOT defined by Placement. Placement is only a semantic convention. The Region itself is geometric.

python
@dataclass
class Region:
    id: str                # "central", "left", "right", "bottom"
    bounds: Rect           # rectangle that contains the Region
    areas: list[Area]      # Areas that belong to the Region
    semantic_role: Placement | None
Why geometric and not semantic? Allows arbitrary splits, floating areas, multiple Workspaces, drag-and-drop, and lateral overlays.

7.3 The Top Bar
The Top Bar (Painel Superior) is an Overlay of the Central Region.

It:

Is anchored to the top of the Central Region.

Has the width of the Central Region (with fixed side margins).

Floats over the Central Areas.

Does not push content — it overlaps.

Is a single unit, independent of the number of Central Areas.

text
+-----------+-----------------------------------+----------+
|           |  ┌─────────────────────────────┐  |          |
| Area Left |  │        Top Bar              │  | Area Right|
|           |  └─────────────────────────────┘  |          |
|           |         Central Region            |          |
+-----------+-----------------------------------+----------+
|                    Bottom Area                           |
+----------------------------------------------------------+
7.4 Computing the bounds
python
x_min = right_edge_of(Region.LEFT)   or  0
x_max = left_edge_of(Region.RIGHT)   or  workspace_width
y_min = 0
y_max = top_edge_of(Region.BOTTOM)   or  workspace_height
The Top Bar is positioned at:

x = x_min + margin

y = y_min + margin_top

width = (x_max - x_min) - 2 * margin

height = fixed

7.5 Content: the three segments
The Top Bar is a single panel that behaves as three independent segments:

text
+---------------------------------------------------------------------------+
| [Left]                        [Center]                     [Right]        |
+---------------------------------------------------------------------------+
Segment	Alignment	Typical content
Left	Anchored left	Menu, Home, context title, Left toggle
Center	Centered	Module tabs loaded by the clinical workflow, +
Right	Anchored right	Extras, Right toggle, window controls
Each segment has its own width (based on content). The segments do not push each other — empty spaces fill the rest.

Each segment responds to width independently, collapsing as available space shrinks.

Visual effect: the Top Bar has frosted glass (blur + tint) in the background, capturing the Central Region content behind it.

For full details, see top-bar.md.

7.6 When the layout changes
Whenever the layout changes (new Module, split, window resize, visibility of lateral Areas), the Workspace:

Recomputes the bounds of each Region.

Repositions the Overlays.

The Overlay is reactive.

7.7 Other Overlays
In the future, other Overlays may be added:

Lower Panel (Central Region overlay, anchored to the bottom).

Lateral overlays (LEFT, RIGHT).

Floating overlays.

7.8 Persistence
The presence and configuration of Overlays are persisted with the layout trees, inside the project file.

8. Open Questions
8.1 Is the layout per-project or per-user?
Option A: Per-project.
Option B: Per-user.
Option C: Hybrid.

Current lean: Option C.

8.2 Does the global Editor catalog exist?
Option A: Yes — the user can open any system Editor.
Option B: No — only what the Module declared.

Current lean: Option A.

8.3 How to handle floating Areas on multi-monitor?
Requires extra handling (Qt handles most of it, but VTK viewports need care).

Current lean: define when multi-monitor support enters scope.

8.4 Where does the "active Area" concept live?
Option A: The Workspace tracks the active Area.
Option B: Each Area tracks its own focus.

Current lean: Option A, with per-Area focus as a secondary concept.