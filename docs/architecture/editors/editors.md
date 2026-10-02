# Editors

## 1. Overview

Editors are functional components of the CranioZ user interface responsible for presenting and enabling interaction with a specific type of content or activity.

An Editor defines **what the user is doing** within an `Area`. It does not define **where it is located** in the interface.

The interface architecture follows this hierarchy:

```text
Workspace
└── Layout
    └── Area
        └── EditorHost
            └── Editor
                ├── Toolbar
                │   └── Tools
                ├── Content
                └── Overlays
```

This separation allows the same Editor to be used in different interface configurations without depending on a specific position.

For example, an `MPRViewerEditor` may occupy a central, side, or bottom Area depending on the Layout, without the Editor knowing or controlling that position.

The Area is provided by the Workspace; the Editor does not create or manage it.

---

## 2. Responsibilities

An Editor is responsible for:

- defining a functional editing or visualization experience;
- presenting a specific type of content;
- providing interaction specific to that content;
- declaring its Toolbar and the Tools it references;
- translating user interactions into Commands;
- reacting to relevant changes in application state;
- maintaining presentation-specific state when necessary.

An Editor is **not** responsible for:

- determining its position in the interface;
- creating or managing Areas;
- defining the Workspace Layout;
- controlling docking or spatial division;
- managing other Editors;
- implementing clinical logic belonging to Modules;
- directly modifying the clinical state of the Scene;
- directly materializing Qt widgets.

The separation can be summarized as:

```text
Area    → where
Editor  → what
Tool    → user intention
Command → state change
Module  → clinical functionality
Scene   → clinical state
```

---

## 3. Editor versus Area

`Area` and `Editor` have different responsibilities.

### Area

An `Area` is a structural unit of the interface.

It controls aspects such as:

- position;
- size;
- visibility;
- docking;
- division;
- presentation;
- spatial relationships with other Areas.

An Area must not contain knowledge specific to surgery, imaging, cephalometry, segmentation, or any other clinical functionality.

### Editor

An Editor represents an interface function.

It controls aspects such as:

- visualization;
- interaction;
- tools;
- selection;
- manipulation;
- navigation;
- information presentation.

An Editor must not assume that it is located in the center, on the side, or at the bottom of the window.

```text
Area
└── EditorHost
    └── Editor
```

The Area provides the presentation space; the Editor provides the functional experience.

---

## 4. EditorHost

Communication between an Area and an Editor takes place through an `EditorHost`.

```text
Area
└── EditorHost
    └── Editor
```

The `EditorHost` acts as a hosting and adaptation layer between the Workspace's spatial infrastructure and the Editor implementation.

Its responsibilities include:

- hosting the Editor instance;
- connecting the Editor to the Area;
- managing the visual lifecycle;
- providing the context required by the Editor;
- materializing the Toolbar declared by the Editor;
- connecting the Toolbar and Content;
- adapting the Editor implementation to the Layout system.

The EditorHost must not assume clinical responsibilities.

The Editor declares its Toolbar; the EditorHost materializes that Toolbar in the space provided by the Area, respecting the Layout.

---

## 5. Base interface

All Editors must derive from a common abstraction.

A conceptual implementation may be represented as:

```python
class Editor(ABC):
    editor_id: str
    title: str

    def initialize(self, context: "EditorContext") -> None:
        ...

    def activate(self) -> None:
        ...

    def deactivate(self) -> None:
        ...

    def dispose(self) -> None:
        ...
```

The concrete interface may evolve according to the needs of the system.

The purpose of the base class is not to impose a specific visual implementation, but to establish a common contract for registration, creation, and lifecycle management.

### Lifecycle

```text
initialize(context) → called once when the Editor is created
activate()          → Editor becomes active
deactivate()        → Editor becomes inactive
dispose()           → Editor is destroyed
```

An Editor may remain hosted while inactive. Transient visual state may or may not persist between `deactivate()` and `activate()`, depending on the nature of the Editor.

`deactivate()` does not imply `dispose()`.

---

## 6. EditorRegistry

Editors are registered in the `EditorRegistry`.

The Registry is responsible for:

- registering available Editors;
- locating an Editor by `editor_id`;
- providing metadata;
- creating new instances;
- managing factories;
- validating Editors requested by Layouts.

Conceptual example:

```text
EditorRegistry
│
├── viewport_3d
├── mpr_viewer
├── properties
├── scene
├── node
├── animation
└── cephalometry
```

The Registry allows the system to work with stable identifiers instead of depending directly on concrete classes.

For example:

```python
editor_id = "viewport_3d"
```

instead of:

```python
Viewport3DEditor(...)
```

in the Layout definition.

The Registry provides definitions or factories. It does not maintain execution instances; instance creation is performed by the Workspace or the corresponding host.

---

## 7. Layout and Editors

The Layout defines which Editors appear and where they are hosted.

However, the Layout does not instantiate Editor classes directly.

The flow is:

```text
Layout
   │
   │ editor_id
   ▼
EditorRegistry
   │
   │ create()
   ▼
Editor instance
```

This keeps the Layout definition declarative.

Conceptual example:

```python
AreaSpec(
    area_id="main_view",
    editor_id="viewport_3d",
)
```

The Layout knows:

```text
"viewport_3d"
```

but does not need to know:

```text
Viewport3DEditor
```

That responsibility belongs to the `EditorRegistry`.

---

## 8. LayoutTree

The `LayoutTree` is the source of truth for the spatial composition of the interface.

It describes:

- Areas;
- relationships between Areas;
- spatial divisions;
- docking;
- visibility;
- Editors associated with Areas;
- overlays;
- Layout configuration.

Conceptually:

```text
LayoutTree
│
├── Area
│   └── Editor: MPRViewer
│
├── Area
│   └── Editor: Viewport3D
│
└── Area
    └── Editor: Properties
```

The LayoutTree does not contain concrete Qt widgets. It represents the logical structure of the interface.

---

## 9. Layout materialization

The interface is created in distinct stages:

```text
LayoutTree
    │
    ▼
LayoutBuilder
    │
    ▼
Areas / EditorHosts
    │
    ▼
LayoutRenderer
    │
    ▼
Qt Widgets
```

### LayoutTree

Declarative representation of the composition.

### LayoutBuilder

Interprets the LayoutTree and creates the required structure.

### LayoutRenderer

Projects that structure into the Qt interface.

This separation prevents the logical Workspace structure from becoming coupled to the specific Qt implementation.

---

## 10. Toolbar

The Toolbar belongs to the Editor. Each Editor defines its own Toolbar, composed of Tools that may be shared with other Editors.

```text
Editor
├── Toolbar
│   └── Tools
├── Content
└── Overlays
```

The Toolbar is a declarative specification belonging to the Editor. Its materialization is the responsibility of the EditorHost, which projects it into the space provided by the Area through the LayoutRenderer.

Tools do not belong to a specific Toolbar. They belong to a shared catalog, the `ToolRegistry`, and may be referenced by Toolbars from different Editors.

Example:

```text
Viewport3DEditor
├── ViewportToolbar
│   ├── select_tool
│   ├── transform_tool
│   └── measure_tool
└── 3D View

MPRViewerEditor
├── MPRToolbar
│   ├── select_tool
│   └── measure_tool
└── 2D Views
```

A Toolbar must not be treated as a special `ToolbarArea` or as a Layout responsibility. It is part of the Editor experience and may be presented according to the Layout and the current interface state, without the Editor knowing the details of that presentation.

### Multiple Toolbars per Editor

An Editor may declare more than one Toolbar:

```text
Editor
├── Toolbar1: Tool2, Tool4
├── Toolbar2: Tool1, Tool2, Tool4
└── Content
```

The composition of each Toolbar is independent, even when the same Tool definitions are referenced.

---

## 11. Tools

Tools represent intentions or operations initiated by the user.

A Tool is an independent functional unit. It does not belong to a specific Toolbar and may be referenced by multiple Toolbars.

```text
Tools
├── Tool1
├── Tool2
├── Tool3
├── Tool4
└── Tool5

Toolbar1: Tool2, Tool4
Toolbar2: Tool1, Tool2, Tool4
```

Each Tool definition resides in the `ToolRegistry`. The Toolbar that uses it is responsible for creating the Tool instance.

Thus, `Tool2` in `Toolbar1` and `Tool2` in `Toolbar2` share the same definition but are independent instances:

```text
ToolRegistry
├── Tool1 (definition)
├── Tool2 (definition)
├── Tool3 (definition)
├── Tool4 (definition)
└── Tool5 (definition)

Toolbar1 creates Tool2 and Tool4
Toolbar2 creates Tool1, Tool2, and Tool4
```

### Resolution flow

```text
Toolbar
   │ resolves tool_id
   ▼
ToolRegistry
   │ returns factory/class
   ▼
Toolbar creates Tool
```

### Behavior

A Tool must not directly modify the clinical state. The preferred flow is:

```text
User
  ↓
Tool
  ↓
Command
  ↓
CommandStack
  ↓
Scene
  ↓
EventBus
  ↓
Editors
```

When activated, a Tool receives a controlled context provided by the Editor through the Toolbar. This context may contain references to Scene queries, Selection services, Command dispatching, Event subscriptions, and specialized services. A Tool must not assume knowledge of the Editor's position in the interface.

### Lifecycle

```text
Tool.__init__        → created by the Toolbar
Tool.activate(ctx)   → activated by the user
Tool.deactivate()    → deactivated
Tool.dispose()       → destroyed with the Toolbar
```

Transient Tool state may or may not persist between `deactivate()` and `activate()`, depending on the nature of the Tool. Measurement Tools generally reset; selection Tools generally preserve their state.

### State isolation

Because each Toolbar creates its own Tool instances, execution state is not accidentally shared between different Toolbars. This is especially important when the same Tool appears in different contexts, such as a `MeasureTool` in both a `Viewport3DEditor` and an `MPRViewerEditor`.

The architectural decision is therefore:

> The Toolbar creates its own Tool instances from definitions provided by the ToolRegistry. The same Tool may be referenced by different Toolbars, but each Toolbar maintains independent instances.

---

## 12. Editor content

The content presented by an Editor varies according to its purpose.

### 3D Viewport

```text
Viewport3DEditor
├── 3D viewport
├── camera
├── selection
├── overlays
└── tools
```

### MPR Viewer

```text
MPRViewerEditor
├── axial view
├── sagittal view
├── coronal view
├── crosshair
├── slice navigation
└── image tools
```

### Properties

```text
PropertiesEditor
├── object information
├── transform
├── appearance
└── clinical properties
```

### Node Editor

```text
NodeEditor
├── node canvas
├── nodes
├── links
├── node tools
└── graph navigation
```

Specific content must not be confused with the Area that hosts it.

---

## 13. Planned Editors

The architecture must not require all Editors to exist from the beginning. However, the following are natural candidates for CranioZ.

### Visualization

- `Viewport3DEditor`
- `MPRViewerEditor`
- `ImageViewerEditor`
- `SceneEditor`

### Planning

- `CephalometryEditor`
- `OsteotomyEditor`
- `SplintEditor`
- `ImplantEditor`
- `SurgicalGuideEditor`

### Modeling and geometry

- `MeshEditor`
- `NodeEditor`
- `SculptEditor`

### Information

- `PropertiesEditor`
- `OutlinerEditor`
- `PatientEditor`
- `DocumentEditor`

### Animation and simulation

- `AnimationEditor`

This list is extensible and is not intended to be exhaustive.

---

## 14. Editors and Modules

`Module` and `Editor` are not equivalent.

A **Module** represents a CranioZ functionality.

An **Editor** represents an interface experience used to work with that functionality.

Their relationship is:

```text
Module
 ├── Commands
 ├── Tools
 ├── Services
 └── Editor specifications
```

A Module may declare that a feature uses a particular Editor, but it does not own or instantiate the Editor.

For example:

```text
Orthognathic Module
    │
    ├── declares: viewport_3d
    ├── declares: mpr_viewer
    └── declares: cephalometry
```

The Workspace and `EditorRegistry` are responsible for creating the actual instances.

This allows different Modules to use the same Editor without duplicating its implementation.

---

## 15. Shared Editors

Editors must be designed for reuse.

For example, `Viewport3DEditor` may be used for:

- orthognathic planning;
- facial implants;
- osteosynthesis;
- mandibular reconstruction;
- rhinoplasty planning;
- surgical guide planning;
- model analysis.

The Editor provides the generic interaction experience.

Application-specific logic is provided by:

- Modules;
- Tools;
- Commands;
- Services;
- Scene;
- application context.

---

## 16. EditorContext

An Editor may receive an execution context containing controlled references to the services it requires.

The context must be small and interface-oriented. It must not become a global communication bus or a God Object.

A conceptual context is:

```text
EditorContext
├── SceneQuery
├── SelectionService
├── CommandDispatcher
├── EventSubscription
├── ViewStateStore
└── EditorServices
```

The Editor must depend on abstractions and avoid direct dependencies on concrete application components whenever possible.

The Editor should not receive indiscriminate access to the entire Scene, all Services, the complete Workspace, concrete Qt details, or internal components of other Editors.

This separation facilitates:

- testing;
- reuse;
- plugins;
- maintenance;
- architectural evolution.

A conceptual example:

```python
class Viewport3DEditor(Editor):
    def initialize(self, context: EditorContext) -> None:
        self._scene_query = context.scene_query
        self._selection = context.selection_service
        self._commands = context.command_dispatcher
        self._events = context.event_subscription
```

The Editor receives only the context it needs.

A Tool should receive an even narrower `ToolContext` whenever possible:

```text
ToolContext
├── SceneQuery
├── SelectionService
├── CommandDispatcher
└── ToolServices
```

---

## 17. Editor state

Clinical state must be separated from purely visual state.

### Clinical state

Belongs to the application and the `Scene`.

Examples:

- the position of a mandible;
- an osteotomy plane;
- implant position;
- landmarks;
- anatomical models;
- splints.

### Visual state

May belong to the Editor.

Examples:

- zoom;
- camera;
- current slice;
- visual selection;
- presentation mode;
- temporary visibility;
- viewport configuration.

This separation prevents transient interface information from being confused with project clinical data.

---

## 18. Overlays

Overlays are temporary or floating elements presented over an Editor.

Examples include:

- gizmos;
- crosshairs;
- measurements;
- markers;
- indicators;
- context menus;
- temporary information.

Conceptually:

```text
Area
└── EditorHost
    └── Editor
        ├── Toolbar
        ├── Content
        └── Overlays
```

Overlays must not be turned into Editors merely because they occupy a visual region over the content.

### Guidelines

- Overlays are managed by the Editor or the EditorHost, depending on their nature.
- Interactive Overlays, such as gizmos, may participate in hit testing.
- Overlays have a rendering order, or z-order, defined by the Editor.
- Overlays must not directly change clinical state; interactive Overlays use Commands when a clinical change is required.

---

## 19. Spatial independence

One of the fundamental principles of Editors is:

> **An Editor must not know where it is.**

The same Editor may appear as:

```text
┌─────────────────────────────┐
│        Viewport3DEditor     │
│                             │
└─────────────────────────────┘
```

or:

```text
┌──────────────┬──────────────┐
│              │              │
│     MPR      │   Viewport   │
│              │      3D      │
│              │              │
└──────────────┴──────────────┘
```

or:

```text
┌─────────────────────────────┐
│         Viewport 3D         │
├─────────────────────────────┤
│          MPR Viewer         │
└─────────────────────────────┘
```

without modifying the Editor implementation.

Composition belongs to the Workspace.

---

## 20. ToolRegistry

The `ToolRegistry` maintains the Tool definitions available in the system.

It is responsible for:

- registering Tool definitions;
- locating a definition by `tool_id`;
- providing factories or classes;
- validating Tools referenced by Toolbars.

Conceptually:

```text
ToolRegistry
├── select_tool
├── transform_tool
├── measure_tool
├── landmark_tool
└── ...
```

The ToolRegistry does not maintain execution instances. It provides definitions or factories; the Toolbar creates and owns the instances it uses.

```text
Toolbar
   │ resolves tool_id
   ▼
ToolRegistry
   │ returns factory/class
   ▼
Toolbar creates Tool
```

This separation enables:

- reuse of definitions between Toolbars;
- state isolation by instance;
- tests with mocked Tools;
- independent evolution of definitions and usage.

---

## 21. Architectural principles

The following principles must guide implementation:

### 21.1 An Editor is functional, not spatial

Position belongs to the Area and the Layout.

### 21.2 An Editor does not instantiate other Editors

Composition is the responsibility of the Workspace and Layout.

### 21.3 A Module does not own Editors

Modules declare interface needs; the Workspace resolves and creates Editor instances.

### 21.4 Layout is declarative

Layouts use stable identifiers and specifications, avoiding direct references to concrete classes.

### 21.5 The Registry creates instances

Concrete classes do not appear in Layout definitions.

### 21.6 An Editor does not contain clinical logic

Clinical logic belongs to Modules, Services, Domain, and Application layers.

### 21.7 Persistent state changes use Commands

When an interaction changes persistent application state, the Editor must use Commands instead of directly modifying the clinical Scene.

### 21.8 Events notify changes

Events do not replace Commands and must not function as the primary write mechanism.

### 21.9 Visual and clinical state remain separate

The interface may maintain transient state without contaminating the clinical model.

### 21.10 Hosts control spatial presentation

Docking, floating, and multiple monitors must not contaminate the Editor implementation.

### 21.11 Editors must be reusable

An Editor type must be usable by multiple Modules and Layouts.

### 21.12 Context must be minimal

Dependencies are provided through specific interfaces.

### 21.13 Qt is a presentation detail

The logical Editor architecture must remain as independent as possible from concrete Qt widgets.

### 21.14 The Editor declares the Toolbar; the EditorHost materializes it

The Editor does not create Qt Toolbar widgets. It declares the composition; the EditorHost materializes its presentation.

### 21.15 The ToolRegistry provides definitions; the Toolbar creates instances

A Tool definition is registered once and may be reused. The execution instance belongs to the Toolbar that uses it.

### 21.16 Editors must be testable without Qt

The Editor contract must support unit testing without concrete widget dependencies.

---

## 22. Complete flow

The architecture can be summarized by the following flow:

```text
                    ┌───────────────┐
                    │     Module    │
                    └───────┬───────┘
                            │
                      declares Editor
                            │
                            ▼
                    ┌───────────────┐
                    │  LayoutTree   │
                    └───────┬───────┘
                            │
                         editor_id
                            ▼
                    ┌───────────────┐
                    │ EditorRegistry│
                    └───────┬───────┘
                            │
                          create
                            ▼
┌───────────┐       ┌───────────────┐
│   Area    │──────▶│  EditorHost   │
└───────────┘       └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │    Editor     │
                    └───────┬───────┘
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
          Toolbar        Content       Overlays
              │
              │ resolves tool_id
              ▼
        ┌───────────────┐
        │  ToolRegistry │
        └───────┬───────┘
                │ returns factory/class
                ▼
        Toolbar creates Tool(s)
                │
                │ activate(context)
                ▼
             Command
                │
                ▼
              Scene
                │
                ▼
             EventBus
                │
                ▼
             Editors
```

This architecture allows CranioZ to maintain a highly configurable interface without turning the Workspace into a collection of components specific to individual clinical Modules.

The central principle is:

```text
Workspace = composition
Layout    = organization
Area      = space
Editor    = functional experience
Toolbar   = Tool composition
Tool      = intention
Command   = change
Module    = functionality
Scene     = clinical state
```

This model should be considered the foundation for the evolution of the CranioZ Editor system.
