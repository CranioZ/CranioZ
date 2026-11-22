# Editors

## 1. Overview

Editors are functional components of the CranioZ UI responsible for presenting and enabling interaction with a specific type of content or activity.

An Editor defines what the user is doing within an Area. It does not define where it is located.

The interface architecture follows this hierarchy:

```Workspace
├── Top Bar (structural)
├── Area Layout Tree
│   └── Area
│       └── Editor Layout Tree
│           └── Editor
│               ├── Toolbar
│               ├── Content
│               └── Overlays
└── Overlays (e.g., steps_panel)
```
This separation allows the same Editor to be used in different interface configurations without depending on a specific position.

The Area is provided by the Workspace; the Editor does not create or manage it.

## 2. Responsibilities
An Editor is responsible for:

* defining a functional editing or visualization experience;
* presenting a specific type of content;
* providing interaction specific to that content;
* declaring and materializing its own Toolbar and the Tools it references;
* translating user interactions into Commands;
* reacting to relevant changes in application state;
* maintaining presentation-specific state when necessary.

An Editor is not responsible for:

* determining its position in the interface;
* creating or managing Areas;
* defining the Workspace Layout;
* controlling docking or spatial division;
* managing other Editors;
* implementing clinical logic belonging to Modules;
* directly modifying the clinical state of the Scene.

The separation can be summarized as:

```
Area    → where (structural container of Editors)
Editor  → what (functional experience)
Tool    → user intention
Command → state change
Module  → clinical functionality
Scene   → clinical state
```

## 3. Editor versus Area
Area and Editor are distinct concepts, but they share responsibilities through composition.

Area
An Area is a structural container of Editors. It controls:

* position;
* size;
* visibility;
* spatial relationships with other Areas;
* the internal Editor Layout Tree it hosts.

An Area must not contain knowledge specific to surgery, imaging, cephalometry, or any other clinical functionality.

Editor
An Editor represents a functional experience. It controls:

* visualization;
* interaction;
* tools;
* selection;
* manipulation;
* navigation;
* information presentation.

An Editor must not assume that it is located in the center, on the side, or at the bottom of the window.
```
text
Area
└── Editor Layout Tree
    ├── Editor A
    ├── Editor B
    └── Editor C
```
An Area may host one or more Editors. The internal Editor Layout Tree organizes them (same N-ary model as the Area Layout Tree: Leaf and Split).

## 4. Base interface
All Editors derive from a common abstraction.

python
class Editor(ABC):
    editor_id: str
    title: str

    def initialize(self, context: "EditorContext") -> None: ...
    def activate(self) -> None: ...
    def deactivate(self) -> None: ...
    def dispose(self) -> None: ...

    # Content and internal chrome
    def content_widget(self) -> "QWidget": ...
    def toolbar_specs(self) -> list["ToolbarSpec"]: return []
    def overlays(self) -> list["Overlay"]: return []

    # Persistence contract (optional state)
    def persistent_state(self) -> dict: return {}
    def restore_state(self, state: dict) -> None: ...
Lifecycle
text
instantiated → registered → inserted → activated ⇄ deactivated → removed → disposed

    Stage	Meaning
    instantiated	The Editor instance is created.
    registered	The Editor type is registered in the EditorRegistry.
    inserted	The instance is added to an Area's Editor Layout Tree.
    activated	The instance is the active Editor within the Area.
    deactivated	No longer active, but still hosted.
    removed	The instance is removed from the composition.
    disposed	The instance is destroyed and its resources are released.
    Instance vs type: the EditorRegistry maintains types; the Workspace maintains instances.

Initialization with the Scene occurs at insertion (once). Later activations sync presentation, without re-initializing heavy resources.

## 5. EditorRegistry
The EditorRegistry resolves editor_id to concrete Editor types.
```
python
class EditorRegistry:
    def register(self, editor_id: str, editor_type: type[Editor]) -> None: ...
    def resolve(self, editor_id: str) -> type[Editor]: ...
    def create(self, editor_id: str) -> Editor: ...
```

The Registry registers types, not instances. It answers: "Which Editor types exist and how are they created?"

Availability is a separate concern handled by the EditorCatalog (see §6).

Registry population:

* System Editors register at boot.
* Modules register their Editors when loaded.
* Plugins register their Editors when activated.

## 6. EditorCatalog
The EditorCatalog answers: "Which registered Editors can be used in the current context?"

It considers:

* the active Scene and Project;
* required capabilities;
* required data (mesh, DICOM series, planning model);
* dependencies on other Modules.

Registry ≠ Catalog. The Registry provides types; the Catalog filters by context. The logic belongs to the Catalog, not to the Workspace.

7. Editor vs Module
A Module represents a CranioZ functionality. An Editor represents an interface experience used to work with that functionality.
```
text
Module
 ├── Commands
 ├── Tools
 ├── Services
 └── Editor specifications
```
A Module may declare that a feature uses a particular Editor, but it does not own or instantiate the Editor.

```
text
Orthognathic Module
    ├── declares: viewport_3d
    ├── declares: mpr_viewer
    └── declares: cephalometry
```
The Workspace and EditorRegistry create the actual instances. This allows different Modules to use the same Editor without duplicating its implementation.

## 8. Editor Layout Tree
An Area hosts an internal Editor Layout Tree, using the same N-ary split tree model as the Area Layout Tree.

A Leaf contains exactly one Editor (referenced by editor_id).

A Split contains two or more children and a direction (HORIZONTAL or VERTICAL).

```
text
Editor Layout Tree (area.central)
Split(HORIZONTAL)
├── Leaf(editor.viewport_3d)
└── Split(VERTICAL)
    ├── Leaf(editor.mpr_axial)
    └── Leaf(editor.mpr_sagittal)
```
Each Split is rendered as a QSplitter. Each Leaf is rendered as the Editor widget.

Structure vs state: the tree defines structure; proportions, visibility, and active Editor per Area are stored in LayoutState (not in the tree itself).

## 9. Layout materialization
The interface is created in distinct stages:
```
text
ModuleUISpec
    │
    ▼
LayoutBuilder  (validates and builds the trees)
    │
    ▼
AreaLayoutTree + EditorLayoutTrees
    │
    ▼
LayoutRenderer  (materializes as Qt widgets)
    │
    ▼
Qt Widgets
```
Separation of responsibilities:

    Component	Responsibility
    LayoutBuilder	Validates the spec and builds the trees
    LayoutRenderer	Materializes the trees as Qt widgets
    EditorRegistry	Resolves editor_id to concrete types
    EditorCatalog	Filters available Editors by context

The Editor's internal structure (Toolbar, Content, Overlays) is materialized by the Editor itself, not by the LayoutRenderer.

## 10. Toolbar
A Toolbar is an internal widget of an Editor, not an Area. Each Editor decides whether it wants its own Toolbar. The Workspace never hosts Toolbars.

```
text
Editor
├── Toolbar
│   └── Tools
├── Content
└── Overlays
```
The Toolbar is a declarative specification belonging to the Editor. Its materialization is the responsibility of the Editor itself, respecting the declared orientation (HORIZONTAL or VERTICAL).

Tools do not belong to a specific Toolbar. They belong to a shared catalog, the ToolRegistry, and may be referenced by Toolbars from different Editors.

Multiple Toolbars per Editor:
```
text
Editor
├── Toolbar Vertical:   Tool2, Tool4
├── Content
├── Overlays
└── Toolbar Horizontal: Tool1, Tool2, Tool4
```
A Toolbar must not be treated as a special ToolbarArea nor as a Layout responsibility.

## 11. Tools
Tools represent intentions or operations initiated by the user. A Tool is an independent functional unit. It does not belong to a specific Toolbar and may be referenced by multiple Toolbars.

Tools live in a shared subsystem (src/cranioz/tools/), outside ui/editors/. Each Editor references Tools by tool_id.

Resolution flow:
```
text
Toolbar (inside an Editor)
   │ resolves tool_id
   ▼
ToolRegistry
   │ returns factory/class
   ▼
Toolbar creates Tool
```
Behavior:
```
text
User → Tool → Command → CommandStack → Scene → EventBus → Editors
```
A Tool must not directly modify the clinical state. When activated, it receives a controlled ToolContext provided by the Editor through the Toolbar.

State isolation: because each Toolbar creates its own Tool instances, execution state is not shared between Toolbars. The same Tool referenced by two Toolbars produces two independent instances.

## 12. Editor content
The content presented by an Editor varies according to its purpose.
```
text
Viewport3DEditor       MPRViewerEditor        PropertiesEditor
├── 3D viewport        ├── axial view         ├── object information
├── camera             ├── sagittal view      ├── transform
├── selection          ├── coronal view       ├── appearance
├── overlays           ├── crosshair          └── clinical properties
└── tools              ├── slice navigation
                       └── image tools
```
Specific content must not be confused with the Area that hosts it.

## 13. Planned Editors
The architecture does not require all Editors to exist from the beginning. Natural candidates for CranioZ:
    
    Category	Editors
    Visualization	Viewport3DEditor, MPRViewerEditor, ImageViewerEditor, SceneEditor
    Planning	CephalometryEditor, OsteotomyEditor, SplintEditor, ImplantEditor, SurgicalGuideEditor
    Modeling	MeshEditor, NodeEditor, SculptEditor
    Information	PropertiesEditor, OutlinerEditor, PatientEditor, DocumentEditor
    Animation	AnimationEditor

## 14. Shared Editors
Editors must be designed for reuse.

Viewport3DEditor may be used for:

* orthognathic planning;
* facial implants;
* osteosynthesis;
* mandibular reconstruction;
* rhinoplasty planning;
* surgical guide planning;
* model analysis.

The Editor provides the generic interaction experience. Application-specific logic is provided by Modules, Tools, Commands, Services, Scene, and the application context.

## 15. EditorContext

An Editor receives a small, interface-oriented execution context. It is
provided once at insertion and remains stable throughout the Editor's
lifetime.

```
    EditorContext
    ├── editor_id                → stable identifier within the Area
    ├── correlation_id           → identifies the current operation (ADR-0012)
    ├── SceneQuery               → read-only access to the Scene
    ├── SelectionService         → query and observe the current selection
    ├── CommandDispatcher        → dispatch Commands (write intention)
    ├── EventSubscription        → subscribe to application events (activation-scoped)
    ├── ViewStateStore           → per-Editor presentation state
    ├── TaskManager              → dispatch long-running work (ADR-0011)
    ├── TelemetrySink            → emit events and measurements (ADR-0012)
    └── EditorServices           → additional Editor-scoped services
```

Each component has a specific role:

- **`editor_id`** — the Editor's stable identifier within its Area.
  Same as `Editor.editor_id`; exposed on the context so that shared
  services (e.g., the `TaskManager` binding) can identify the owner of
  a task.
- **`correlation_id`** — identifies the operation currently in progress
  (activation, Command dispatch, deactivation). It is `None` when no
  operation is in progress. The Editor passes it to every
  `telemetry.record_event(...)` and `telemetry.record_measurement(...)`
  call it makes during the operation (ADR-0012 §2.3).
- **`SceneQuery`** — exposes a read-only view of the Scene. The Editor
  never receives a mutable reference.
- **`SelectionService`** — exposes the current selection and allows
  the Editor to observe selection changes.
- **`CommandDispatcher`** — accepts Commands from the Editor. The
  Editor never mutates the Scene directly and never talks to the
  `CommandBus` itself.
- **`EventSubscription`** — allows the Editor to subscribe to
  relevant application events. Subscriptions are scoped to the
  Editor's activation scope; they are disposed automatically when the
  Editor is deactivated or disposed (ADR-0002 §2.1). The `EventBus`
  itself is not exposed. The `EventSubscription` instance is
  **stable across activations**: the Application rebinds it to a
  fresh scope between `deactivate()` and the next `activate()`,
  rather than creating a new instance.
- **`ViewStateStore`** — stores per-Editor presentation state (zoom,
  camera, current slice, visual selection, presentation mode). It is
  **not** part of the clinical state and is **not** the same as the
  Workspace `LayoutState`.
- **`TaskManager`** — the only mechanism for off-thread work
  (ADR-0011). The Editor must not create `QThread`,
  `ThreadPoolExecutor`, `ProcessPoolExecutor`, `asyncio` loops, or raw
  threads. Long-running operations (DICOM import, segmentation,
  registration, mesh processing, AI inference) are dispatched through
  `context.task_manager.dispatch(...)`.
- **`TelemetrySink`** — emits events and measurements (ADR-0012). The
  Editor must pass `context.correlation_id` so that events from the
  same operation share one correlation id. The Editor includes
  `editor_id` as an attribute on the events it produces.
- **`EditorServices`** — additional services scoped to the Editor
  (e.g., Editor-specific caches, helpers). This is deliberately a
  narrow extension point, not a service locator.

The Editor must depend on abstractions and avoid direct dependencies on
concrete application components whenever possible.

A Tool receives an even narrower context:

```
    ToolContext
    ├── editor_id          → owning Editor
    ├── correlation_id     → same as the owning Editor's context
    ├── SceneQuery         → read-only access to the Scene
    ├── SelectionService   → query and observe the current selection
    ├── CommandDispatcher  → dispatch Commands
    ├── TelemetrySink      → emit events and measurements
    └── ToolServices       → additional Tool-scoped services
```

The `ToolContext` is a strict subset of the `EditorContext`. A Tool
never receives `EventSubscription`, `ViewStateStore`,
`TaskManager`, or `EditorServices`, because it does not own
presentation state, does not subscribe to events directly, and does
not spawn long-running work — it acts through the Editor, which owns
the `TaskManager` binding. A Tool that needs background work returns
a description of the work to the Editor (e.g., via a return value
or a Command), and the Editor dispatches it.

### 15.1 Task lifecycle on the Editor

The Editor owns the Tasks it dispatches through
`EditorContext.task_manager`. When the Editor is deactivated or
disposed, its Tasks are cancelled and awaited before the Editor's
lifecycle hooks return. A Task that outlives its Editor is a bug.

- **`initialize()`** — the Editor receives the `EditorContext` and
  may store a reference to it. The context is stable; the `TaskManager`
  is always available.
- **`activate()`** — the Editor may dispatch Tasks. The
  `TaskManager` binding is scoped to the activation; Tasks dispatched
  in this scope are cancelled when the scope closes.
- **`deactivate()`** — the Editor's activation scope closes. Pending
  Tasks are cancelled cooperatively (ADR-0011 §2.4). The
  `on_cancel` callbacks run on the GUI thread before `deactivate()`
  returns. The Editor must not rely on a Task completing after
  `deactivate()` returns.
- **`dispose()`** — the Editor is removed. Any Task still running is
  cancelled and awaited. `dispose()` is idempotent; a second call is
  a no-op.

The `EditorContext` is not recreated on `activate`/`deactivate`. The
`TaskManager` binding it exposes is rebound to a fresh activation
scope by the Application, mirroring the `EventSubscription` rebind
described in ADR-0002 §2.1.

### 15.2 Telemetry on the Editor

The Editor emits telemetry through `EditorContext.telemetry`. The
`correlation_id` from the context must be passed to every event and
measurement the Editor emits during an activation. The `editor_id`
should be included as an attribute on the events the Editor produces
(e.g., `tool.invoked`, `viewport.camera.changed`).

The Editor is responsible for not emitting patient-identifying
information as attributes (ADR-0012 §2.10). The `TelemetrySink`
contract is fire-and-forget; a sink that raises does not affect the
Editor's lifecycle.


## 16. Editor state
Clinical state must be separated from purely visual state.

Clinical state belongs to the application and the Scene: mandible position, osteotomy plane, implant position, landmarks, anatomical models, splints.

Visual state may belong to the Editor: zoom, camera, current slice, visual selection, presentation mode, viewport configuration, internal toolbar layout.

The Editor may declare which of its properties are persisted (persistent_state() / restore_state()) and which are derived from the Scene.

**Task state is not Editor state.** A Task is owned by the `TaskManager`; the Editor only holds a `TaskHandle`. When the Editor is
deactivated, the handle becomes invalid; the Editor must not call `wait()` on it after `deactivate()` returns. Task state is not
persisted in `persistent_state()` and is not restored in `restore_state()`.

## 17. Overlays
Overlays are temporary or floating elements presented over an Editor. They are internal to the Editor, not Workspace Overlays.

Examples: gizmos, crosshairs, measurements, markers, indicators, context menus, temporary information.
```
text
Editor
├── Toolbar
├── Content
└── Overlays (internal)
```
Guidelines:

* Overlays are managed by the Editor.
* Interactive Overlays (e.g., gizmos) may participate in hit testing.
* Overlays have a z-order defined by the Editor.
* Overlays must not directly change clinical state; interactive Overlays use Commands.

Note: Workspace Overlays (e.g., steps_panel) are a different concept and belong to the Workspace, not to Editors.

**Interactive overlays and Tasks.** An interactive overlay (e.g., a gizmo that triggers a re-computation) dispatches Tasks through the **Editor's** `EditorContext.task_manager`, not its own. The overlay does not receive a `TaskManager` directly; it uses the Editor's
context, which is bound to the Editor's activation scope. This keeps the Task lifecycle tied to the Editor, not to the overlay widget. An
overlay that attempts to create its own thread, `QThread`, or `asyncio` loop violates ADR-0011.

## 18. Spatial independence
One of the fundamental principles of Editors:

An Editor must not know where it is.

The same Editor may appear as:
```
text
┌─────────────────────────────┐
│        Viewport3DEditor     │
└─────────────────────────────┘

┌──────────────┬──────────────┐
│     MPR      │   Viewport   │
│              │      3D      │
└──────────────┴──────────────┘

┌─────────────────────────────┐
│         Viewport 3D         │
├─────────────────────────────┤
│          MPR Viewer         │
└─────────────────────────────┘
```
without modifying the Editor implementation. Composition belongs to the Workspace.

## 19. ToolRegistry
The ToolRegistry maintains the Tool definitions available in the system.
```
text
ToolRegistry
├── select_tool
├── transform_tool
├── measure_tool
├── landmark_tool
└── ...
```
The ToolRegistry does not maintain execution instances. It provides definitions or factories; the Toolbar creates and owns the instances it uses.

This separation enables:

* reuse of definitions between Toolbars;
* state isolation by instance;
* tests with mocked Tools;
* independent evolution of definitions and usage.

## 20. Validation
Validation of a ModuleUISpec is the responsibility of the **LayoutBuilder** before materialization. The rules are defined in **workspace.md** §3.5:

* LEAF must have editor_id and no children.
* SPLIT must have direction and at least two children, and no editor_id.
* Placement must be one of LEFT, CENTRAL, RIGHT, BOTTOM.
* A ModuleUISpec must declare at least CENTRAL.

Additionally, every editor_id must resolve in the EditorRegistry. This is verified by the EditorRegistry.resolve() call.
Any violation produces a clear error. The Workspace does not fall back silently.

## 21. Architectural principles
1. An Editor is functional, not spatial. Position belongs to the Area and the Layout.
2. An Editor does not instantiate other Editors. Composition of Areas belongs to the Workspace; composition of Editors within an Area belongs to the Area.
3. A Module does not own Editors. Modules declare interface needs; the EditorRegistry resolves and creates Editor instances; the Area hosts them.
4. Layout is declarative. Layouts use stable identifiers, not concrete classes.
5. The Registry registers types; the Catalog filters by context.
6. An Editor does not contain clinical logic. Clinical logic belongs to Modules, Services, Domain, and Application.
7. Persistent state changes use Commands. Editors never mutate the Scene directly.
8. Events notify changes. They do not replace Commands.
9. Visual and clinical state remain separate.
10. Editors must be reusable. An Editor type must be usable by multiple Modules and Layouts.
11. Context must be minimal. Dependencies are provided through specific interfaces.
12. Qt is a presentation detail. The logical Editor architecture remains independent from concrete Qt widgets.
13. The Editor declares and materializes its own Toolbar.
14. The ToolRegistry provides definitions; the Toolbar creates instances.
15. Editors must be testable without Qt. Qt-specific materialization must be isolated.
16. Tool switching is a UI operation, not a clinical Command. It is persisted in LayoutState, not in the clinical history.
17. Long-running work is dispatched through `EditorContext.task_manager`     (ADR-0011). The Editor does not create threads, event loops, or
    `processEvents()` calls.
18. Events and measurements are emitted through     `EditorContext.telemetry` with `EditorContext.correlation_id`
    (ADR-0012). The Editor includes `editor_id` as an attribute and does not emit patient-identifying information.

