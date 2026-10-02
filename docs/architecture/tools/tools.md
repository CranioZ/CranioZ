# Tools

## 1. Overview

A **Tool** represents an action or interaction mode that can be made available to the user by a CranioZ module.

Tools are one of the main interfaces between the user and the application's executable functionality. They may be presented in different areas of the interface—for example, in a toolbar, menu, panel, contextual menu, or Editor—without their definition depending on a specific location in the Workspace.

A Tool does not represent the module itself and should not directly contain clinical, geometric, or infrastructure logic. Its responsibility is to define **what the tool represents, how it is identified, in which contexts it is available, and how interaction with it is initiated**.

The actual execution of an operation should be delegated to the appropriate application layer, usually through Commands and Application Services.

The conceptual relationship is:

```text
User
  │
  ▼
Tool
  │
  ▼
Command
  │
  ▼
Application Service
  │
  ▼
Domain
```

Not every Tool needs to result directly in a single Command. Interactive Tools may produce a sequence of operations or generate a Command only when the interaction is completed.

Separating interaction, execution, and domain logic allows the same operation to be triggered by different mechanisms without duplicating logic.

---

## 2. Objectives

The Tool system should:

* provide a uniform interface for actions and interaction modes;
* allow modules to expose functionality to the user;
* separate interaction and presentation from application logic;
* support different presentation forms for the same Tool;
* facilitate the discovery and registration of functionality;
* support contextual availability;
* provide sufficient metadata for UI construction;
* allow activation by human interaction or automated systems;
* keep Tools independent of a specific Workspace location;
* allow operations to be reused by menus, shortcuts, workflows, scripts, and MCP;
* enable extensibility through plugins.

A Tool should be sufficiently declarative for the application to determine **what it is, when it can be used, and how it should be presented**, without its implementation needing to know Workspace-specific details.

---

## 3. A Tool Is Not a Command

Tool and Command are related but different concepts.

### 3.1 Tool

A Tool represents an **action or interaction mode made available to the user**.

It primarily answers the following questions:

* What does this tool represent?
* How is it identified?
* How does it appear in the interface?
* In which contexts is it available?
* How is its interaction initiated?
* What type of interaction does it support?

### 3.2 Command

A Command represents an **operation executable by the application**.

It primarily answers the following questions:

* What operation will be executed?
* What are its parameters?
* How can the operation be undone?
* How does it participate in history?
* What changes does it produce?
* What events are generated?

Therefore:

```text
Tool
  └── may create/execute → Command
```

but:

```text
Command
  └── does not necessarily depend on a Tool
```

A Command may be triggered by:

* a Tool;
* a keyboard shortcut;
* a menu;
* a macro;
* a workflow;
* automation;
* MCP;
* a script;
* another internal operation.

Likewise, a Tool may represent a more complex interaction that results in the execution of one or more Commands.

---

## 4. Tool as a Contract

In the framework, `Tool` should initially be treated as a **contract**.

The base contract should remain small and stable. It primarily describes:

* identity;
* metadata;
* presentation;
* contextual availability.

Execution should not be mandatory in the base contract, since different Tool modalities exist.

Conceptually:

```python
class Tool(ABC):
    identifier: str
    label: str
    description: str
    icon: str | None
    category: str | None
    group: str | None

    def is_available(self, context: ToolContext) -> bool:
        ...

    def is_enabled(self, context: ToolContext) -> bool:
        ...
```

Specific execution or interaction behavior is defined by derived interfaces.

### 4.1 Action Tool

An `ActionTool` represents a discrete action.

```python
class ActionTool(Tool):
    def execute(self, context: ToolContext) -> ToolResult:
        ...
```

Examples:

```text
Save
Undo
Add Landmark
Create Plate
Calculate Cephalometry
```

An `ActionTool` normally results in the execution of a Command or an application operation.

### 4.2 Interactive Tool

An `InteractiveTool` represents a continuous interaction mode.

```python
class InteractiveTool(Tool):
    def activate(self, context: ToolContext) -> None:
        ...

    def deactivate(self, context: ToolContext) -> None:
        ...

    def handle_event(
        self,
        event: ToolEvent,
        context: ToolContext,
    ) -> None:
        ...
```

Examples:

```text
Select
Move
Rotate
Measure
Place Landmark
Define Osteotomy Plane
Paint Segmentation
Sculpt
```

The definitive interface should remain small. Additional features should be added only when there is a real architectural need.

---

## 5. Identity

Each Tool must have a unique and stable identifier.

Examples:

```text
orthognathic.cephalometry.add_landmark
```

or:

```text
osteotomy.create_lefort_i
```

The identifier should:

* be unique within the system;
* remain stable across versions whenever possible;
* not depend on the text presented to the user;
* not depend on the Tool's position in the interface;
* be usable by menus, plugins, workflows, and automations.

The `label` is intended for presentation.

Example:

```yaml
identifier: orthognathic.cephalometry.add_landmark
label: Add Landmark
```

Changing the text presented to the user should not change the identity of the Tool.

---

## 6. Presentation

A Tool should not directly determine where it is displayed.

For example, a Tool may be presented:

* in a toolbar;
* in a menu;
* in a panel;
* in a contextual menu;
* in a Command Palette;
* in an Editor;
* in a module-specific interface.

The positioning decision belongs to the UI layer and to the Workspace/Layout system.

Therefore:

```text
Tool
  └── defines the action or interaction

Workspace / Layout / Editor
  └── defines where the Tool is presented
```

This is particularly important in CranioZ because the same set of Tools may be used in different layouts and contexts.

A Tool should not assume that it permanently belongs to a particular Area.

---

## 7. Tool and Editor

Editors and Tools have different responsibilities.

An **Editor** provides a specialized interaction space.

A **Tool** provides an action or interaction mode that can be used in that space.

For example:

```text
3D Editor
├── Select
├── Move
├── Rotate
├── Measure
└── Landmark
```

or:

```text
Cephalometric Editor
├── Add Landmark
├── Move Landmark
├── Remove Landmark
├── Measure Angle
└── Measure Distance
```

The Editor should not need to reimplement the logic of each Tool.

Likewise, a Tool should not assume that it will be used exclusively by a particular Editor, unless its definition explicitly requires a specific context.

The relationship is therefore:

```text
Editor
  └── hosts / uses → Tool
```

and not:

```text
Tool
  └── structurally belongs to → Editor
```

This distinction is important to allow the same Tool to be used by different Editors.

---

## 8. Execution Context

Tools often depend on the current state of the system.

For example, an osteotomy Tool may be available only when:

* a patient is loaded;
* a valid mandible or maxilla exists;
* the model is in a compatible state;
* the corresponding module is available;
* a valid selection exists;
* the current Editor supports the interaction.

The Tool should therefore consult an application context.

Conceptually:

```text
Tool
  │
  ├── Context
  │   ├── Project
  │   ├── Patient
  │   ├── Selection
  │   ├── Scene
  │   ├── Active Editor
  │   ├── Active Module
  │   └── Application State
  │
  └── Interaction / Execution
```

`ToolContext` should provide only the information necessary for the Tool to determine its availability and execute its interaction.

Example:

```python
def is_available(self, context: ToolContext) -> bool:
    return (
        context.scene.has_patient
        and context.selection.has_mandible
    )
```

### 8.1 Availability and Enablement

It is important to distinguish **availability** from **enablement**.

* **Available**: the Tool makes sense in the current context and may be presented.
* **Enabled**: the Tool is available and can be activated immediately.

Example:

```text
Create Le Fort I Osteotomy

Available: yes
Enabled: no
```

The Tool may be available because the osteotomy module is active and a patient exists, but remain disabled because no valid maxilla has been selected.

The UI may use:

```python
tool.is_available(context)
```

to determine whether the Tool should be presented.

And:

```python
tool.is_enabled(context)
```

to determine whether it can be activated.

This distinction prevents contextual logic from being embedded directly in UI components.

---

## 9. Tool State

The existence, availability, and activation of a Tool are different states.

A Tool may be in the following states:

```text
Registered
    ↓
Available
    ↓
Enabled
    ↓
Activated
    ↓
Completed
```

Not all Tools use all of these states.

For example, an `ActionTool` may follow:

```text
Registered
    ↓
Available
    ↓
Enabled
    ↓
Executed
```

while an `InteractiveTool` may follow:

```text
Registered
    ↓
Available
    ↓
Enabled
    ↓
Activated
    ↓
Interacting
    ↓
Completed
    ↓
Deactivated
```

Contextual state should be determined by the framework and the current context, rather than maintained as arbitrary state inside UI components.

---

## 10. Execution

Tool execution should not concentrate clinical, geometric, or infrastructure logic.

The preferred flow is:

```text
User
  │
  ▼
Tool
  │
  ▼
Command
  │
  ▼
Command Executor
  │
  ▼
Application Service
  │
  ▼
Domain
```

Example:

```text
Tool:
Create Le Fort I Osteotomy

Command:
CreateOsteotomyCommand

Application Service:
OsteotomyService

Domain:
Osteotomy
Bone
Geometry
```

The Tool acts as an interaction layer.

Application and domain logic remain outside the UI.

This prevents the UI from containing clinical rules or complex geometric operations.

### 10.1 Execution Result

When a Tool executes an action, it may need to provide an explicit result to the presentation layer.

Conceptually:

```python
class ToolResult:
    success: bool
    message: str | None
    data: Any | None
```

This result may provide:

* user feedback;
* information for the UI;
* data produced by the operation;
* information for automation;
* an indication of failure or success.

The `CommandExecutor` remains responsible for executing the Command, managing history, and handling Undo/Redo.

The Tool should not assume these responsibilities.

---

## 11. Interactive Tools

Not all Tools correspond to an instantaneous action.

Some represent continuous interaction with the user.

Examples:

* Select;
* Move;
* Rotate;
* Draw;
* Measure;
* Place Landmark;
* Define Osteotomy Plane;
* Paint Segmentation;
* Sculpt;
* Place Implant.

In these cases, the Tool has its own lifecycle.

Conceptually:

```text
Idle
  ↓
Activated
  ↓
Interacting
  ↓
Completed
  ↓
Deactivated
```

Example:

```text
Define Osteotomy Plane
        ↓
Tool activated
        ↓
User selects points
        ↓
Plane preview
        ↓
User confirms
        ↓
CreateOsteotomyCommand
        ↓
Command executed
        ↓
Tool deactivated
```

The Tool may function as an interaction state machine, while persistent changes to the model remain the responsibility of the application/domain layer.

### 11.1 Tool Session

For interactive Tools, it is useful to distinguish the Tool definition from a specific interaction session.

The architecture may use:

```text
Tool
  └── tool definition

ToolSession
  └── state of a specific interaction
```

Conceptually:

```python
class ToolSession:
    tool: Tool
    state: ToolState
    context: ToolContext
    started_at: datetime
    finished_at: datetime | None
```

This prevents the base Tool contract from being polluted with temporary interaction state.

A session may exist only while the Tool is active.

### 11.2 Activation and Deactivation

Activation of interactive Tools should be managed by a dedicated component, such as `ToolManager`.

Conceptually:

```python
class ToolManager:
    def activate(
        self,
        identifier: str,
        context: ToolContext,
    ) -> None:
        ...

    def deactivate(self) -> None:
        ...

    def active_tool(self) -> Tool | None:
        ...
```

`ToolManager` may ensure that:

* only one interactive Tool is active per Editor;
* the previous Tool is correctly deactivated;
* changing Editors ends the appropriate session;
* changing modules is handled correctly;
* activation and deactivation events are propagated.

This does not necessarily mean that only one Tool may be active throughout the application. Different Editors may have different active Tools, similarly to the editor model used by Blender.

---

## 12. Tool Modalities

Tools may be classified according to their behavior.

### 12.1 Action Tool

Executes a discrete action.

```text
Save
Undo
Add Landmark
Create Plate
Calculate Cephalometry
```

### 12.2 Interactive Tool

Remains active while the user interacts with the scene.

```text
Select
Move
Measure
Place Landmark
Draw Osteotomy
```

### 12.3 Toggle Tool

Switches between two states.

```text
Snap
Grid
Visibility
Orthographic / Perspective
```

### 12.4 Stateful Tool

Maintains a more complex interaction state.

```text
Segmentation Brush
Sculpt
Registration
Osteotomy Planning
```

This classification is primarily behavioral and should not create an excessively complex class hierarchy.

When two modalities can share the same contract, an additional abstraction should not be created solely for classification purposes.

---

## 13. Tool and Command History

When a Tool produces a persistent change to the project, that change should preferably occur through a Command.

Example:

```text
User clicks "Move Landmark"
        ↓
Move Landmark Tool
        ↓
MoveLandmarkCommand
        ↓
Command Executor
        ↓
Landmark moved
        ↓
Command Stack
```

This enables:

* Undo;
* Redo;
* history;
* macros;
* automation;
* operation auditing;
* future MCP integration.

The Tool should not implement the Undo/Redo mechanism directly.

The preferred path is:

```text
Tool
  ↓
Command
  ↓
CommandExecutor
  ↓
CommandStack
```

`CommandStack` should remain independent of the Tool.

---

## 14. Tool Groups

Tools may be grouped semantically for presentation and discovery purposes.

Example:

```text
Cephalometry
├── Add Landmark
├── Move Landmark
├── Delete Landmark
├── Measure Distance
└── Measure Angle
```

or:

```text
Osteotomy
├── Create Osteotomy
├── Edit Osteotomy
├── Move Segment
├── Rotate Segment
└── Confirm Osteotomy
```

Grouping does not change the identity of the Tool.

A Tool remains an independent unit that can be presented in different contexts.

### 14.1 Group versus Category

It is useful to distinguish:

* **Category**: a broader semantic classification.
* **Group**: a contextual grouping of Tools for presentation.

Example:

```text
Category:
Measurement

Group:
Cephalometry

Tool:
Measure Angle
```

Thus:

```text
Category → defines the type of Tool

Group → defines how it may be grouped in the UI
```

This prevents `category` from becoming a generic field responsible for different functions.

---

## 15. Tool Categories

A Tool may have a category to facilitate organization and discovery.

Initial categories may include:

* Selection;
* Navigation;
* Measurement;
* Annotation;
* Modeling;
* Planning;
* Segmentation;
* Analysis;
* Visualization;
* Documentation.

Categories should not be excessively rigid.

The framework may provide common categories, while modules and plugins may introduce specific categories when necessary.

---

## 16. Tool Parameters

Some Tools require parameters.

Example:

```text
Create Plate

thickness = 1.5 mm
hole_diameter = 2.0 mm
locking = true
```

The Tool should not necessarily store these values as permanent state.

When appropriate, it may request the parameters from the user and produce a parameterized Command.

Example:

```text
Create Plate Tool
        ↓
Plate Configuration
        ↓
CreatePlateCommand
        ↓
CommandExecutor
```

The Command receives the concrete values:

```python
CreatePlateCommand(
    thickness=1.5,
    hole_diameter=2.0,
    locking=True,
)
```

### 16.1 Parameters in the Tool versus Parameters in the Command

The recommended distinction is:

* The **Tool** defines or requests which parameters are required for the interaction.
* The **UI** collects the concrete values.
* The **Command** receives the concrete values required to execute the operation.
* The **Domain** validates the model-specific rules.

Conceptually:

```text
Tool
  ↓
Parameter Specification
  ↓
UI
  ↓
Concrete Parameters
  ↓
Command
  ↓
Domain
```

This keeps the definition of the operation separate from the presentation of its parameters.

---

## 17. Tool Registry

CranioZ should provide a Tool registration mechanism.

Conceptually:

```text
ToolRegistry
├── register(tool)
├── unregister(identifier)
├── get(identifier)
├── find(...)
└── list(...)
```

The Registry allows:

* modules to register their Tools;
* plugins to add Tools;
* the UI to discover available Tools;
* menus and toolbars to be built dynamically;
* automation systems to find Tools;
* Tools to be queried by identifier.

Example:

```text
Module
  ↓
register Tools
  ↓
ToolRegistry
  ↓
UI / Tool Manager / Automation
```

### 17.1 Identity Conflicts

The Registry must define clear rules for:

* `identifier` uniqueness;
* conflicts between modules;
* conflicts between plugins;
* priority;
* replacement;
* deactivation.

For example, if two plugins attempt to register:

```text
rhinoplasty.add_landmark
```

the Registry must have a deterministic policy for handling the conflict.

The preferred policy should be to **reject duplicate identifiers**, unless an explicit override mechanism has been defined.

---

## 18. Tools Provided by Modules

Each module may provide the Tools required to expose its functionality to the user.

Example:

```text
Cephalometry Module

Tools:
├── Add Landmark
├── Move Landmark
├── Delete Landmark
├── Measure Distance
└── Measure Angle
```

A module may contain:

```text
Module
├── Commands
├── Tools
├── Services
└── Capabilities
```

However, the module should not directly own the Workspace's `Areas` or `Editors`.

The relationship with the UI should occur through the appropriate UI, Layout, or Module Specification contracts.

This keeps the architecture modular and prevents coupling between a module's functional domain and the physical organization of the Workspace.

---

## 19. Tools Provided by Plugins

Plugins may register Tools in the same way as internal modules.

Example:

```text
Plugin
  ↓
ToolRegistry
  ↓
Custom Tool
```

This allows third parties to add functionality without modifying the CranioZ Core.

Hypothetical examples:

```text
AI Segmentation Plugin
└── Automatic Segmentation Tool
```

or:

```text
Rhinoplasty Plugin
├── Nasal Landmark Tool
├── Nasal Osteotomy Tool
└── Soft Tissue Simulation Tool
```

Plugin Tools should use the same contracts as native Tools whenever possible.

---

## 20. Tool Manifest

When a Tool belongs to a plugin, its metadata may be declared in the plugin manifest.

Conceptual example:

```yaml
tools:
  - id: rhinoplasty.add_landmark
    label: Add Landmark
    category: annotation
    group: landmarks

  - id: rhinoplasty.simulate
    label: Simulate
    category: analysis
    group: simulation
```

The manifest describes the Tool and its discovery metadata, but it does not replace its implementation.

Information that depends on code or context should not be unnecessarily duplicated in the manifest.

---

## 21. Tool and Capability

A **Capability** describes a capability offered by a module or component.

A **Tool** represents a way to use a capability through an action or interaction.

Example:

```text
Capability:
cephalometric_analysis

Tools:
├── Add Landmark
├── Measure Angle
└── Calculate Analysis
```

A Capability answers:

> "Does the system have this capability?"

A Tool answers:

> "What action or interaction can the user use to access it?"

This distinction will be especially important for:

* feature discovery;
* workflows;
* automation;
* plugins;
* MCP.

A Capability may exist without a corresponding Tool.

Likewise, a generic interaction Tool such as `Select` may not represent a specific clinical Capability.

---

## 22. Tool and Service

Services implement application operations or rules that should not belong to the Tool.

Example:

```text
Tool:
Register Models

Command:
RegisterModelsCommand

Service:
RegistrationService
```

The flow may be:

```text
Register Models Tool
        ↓
RegisterModelsCommand
        ↓
RegistrationService
        ↓
Registration Algorithm
```

The Tool initiates the interaction.

The Command represents the operation.

The Service coordinates the application logic.

Algorithms and specific rules remain in their appropriate layers.

---

## 23. Tool and MCP

The Tool system should be designed so that CranioZ operations can eventually be used by agents or external systems.

However, a **CranioZ Tool** and an **MCP Tool** should not necessarily be considered the same abstraction.

A CranioZ Tool represents an application action or interaction.

An MCP Tool represents an operation exposed to an external agent through the MCP protocol.

The architecture may allow both to use the same application layer:

```text
UI Tool
  │
  ▼
Command
  │
  ▼
Application Service
  │
  ▼
Domain
```

and:

```text
MCP Tool
  │
  ▼
Command
  │
  ▼
Application Service
  │
  ▼
Domain
```

Thus, MCP does not need to control the UI directly.

An agent could request:

```text
create_osteotomy(...)
```

and the application would execute the same fundamental operation used by the graphical interface, passing through the same validations.

### 23.1 MCP as an Adapter

An adapter-based architecture avoids duplication:

```text
┌───────────────┐
│   UI Tool     │
└───────┬───────┘
        │
        ▼
┌───────────────┐
│    Command    │
└───────┬───────┘
        │
        ▼
┌───────────────┐
│    Service    │
└───────┬───────┘
        │
        ▼
┌───────────────┐
│    Domain     │
└───────────────┘
```

and:

```text
┌───────────────┐
│   MCP Tool    │
└───────┬───────┘
        │
        ▼
┌───────────────┐
│    Command    │
└───────┬───────┘
        │
        ▼
┌───────────────┐
│    Service    │
└───────┬───────┘
        │
        ▼
┌───────────────┐
│    Domain     │
└───────────────┘
```

This allows the UI and automation to use the same application logic.

---

## 24. Security and Validation

Tools should not be considered a sufficient security or validation boundary.

An important operation should also be validated in the application and domain layers.

For example:

```text
UI Tool
  ↓
Command
  ↓
Application Validation
  ↓
Domain Validation
  ↓
Operation
```

This is necessary because Commands may be triggered by mechanisms other than the UI.

The system should consider, when applicable:

* input validation;
* permissions;
* authorization;
* auditing;
* operational limits;
* confirmation of destructive operations.

This becomes especially important when Commands may be triggered by automation, scripts, or MCP.

---

## 25. Example: Landmark Tool

A simple example:

```text
Tool:
Add Landmark

Context:
├── active patient
├── active 3D editor
└── valid anatomical model

Interaction:
└── user clicks on model

Result:
└── AddLandmarkCommand
```

Flow:

```text
Add Landmark Tool
        │
        │ user interaction
        ▼
Landmark Position
        │
        ▼
AddLandmarkCommand
        │
        ▼
Application Service
        │
        ▼
Cephalometric Landmark
        │
        ▼
Scene / Project
```

The Tool does not need to know the persistence details of the Landmark.

---

## 26. Example: Osteotomy Tool

An interactive osteotomy Tool may follow this flow:

```text
Define Osteotomy Tool
        │
        ▼
User selects anatomical region
        │
        ▼
Interactive preview
        │
        ▼
User confirms
        │
        ▼
CreateOsteotomyCommand
        │
        ▼
Application Service
        │
        ▼
Osteotomy Domain Object
        │
        ▼
Scene Update
```

The same operation may later be triggered by:

* a Toolbar;
* a Menu;
* a Shortcut;
* a Workflow;
* a Script;
* MCP.

The osteotomy logic does not need to be duplicated for each activation mechanism.

---

## 27. Code Organization

The contract definitions should remain in the framework's module infrastructure:

```text
src/cranioz/modules/

├── base/
│   ├── module.py
│   ├── module_state.py
│   └── lifecycle.py
│
├── contracts/
│   ├── command.py
│   ├── tool.py
│   ├── service.py
│   └── capability.py
│
└── specs/
    └── module_spec.py
```

The `Tool` contract should remain small and stable.

Specific implementations should remain in the modules that use them.

Example:

```text
src/cranioz/modules/
└── cephalometry/
    ├── tools/
    │   ├── add_landmark.py
    │   ├── move_landmark.py
    │   └── measure_angle.py
    │
    ├── commands/
    │   └── ...
    │
    └── services/
        └── ...
```

The exact directory organization may vary as the module matures, but the conceptual separation should be preserved.

---

## 28. Architectural Principles

The CranioZ Tool system should follow these principles:

1. **A Tool is an interaction interface**

   It is not the domain and should not contain complex clinical or geometric logic.

2. **A Tool is not a Command**

   A Tool may create or execute a Command, but the Command should remain independent of the UI.

3. **A Tool does not structurally belong to an Area**

   A Tool may be presented in any compatible Area or Editor.

4. **A Tool should be contextual**

   Its availability may depend on the current project, selection, Editor, or module state.

5. **A Tool should have a stable identity**

   Its identifier should be independent of its label and position in the interface.

6. **A Tool should be discoverable**

   Tools should be registered and queried by the framework.

7. **A Tool should be reusable**

   The same operation should be triggerable by different mechanisms.

8. **An interactive Tool should have its own lifecycle**

   Temporary interaction state should be separated from the Tool's permanent definition.

9. **Validation should not depend on the UI**

   Important operations should be validated in the application and domain layers.

10. **Plugins may provide Tools**

    The mechanism should work for both internal modules and external extensions.

11. **Tools should not know the Workspace organization**

    The Tool defines the interaction; the Workspace determines where it is presented.

12. **Commands should remain independent of Tools**

    The same operation should be usable by the UI, workflows, scripts, and automation.

13. **Tools should be automation-compatible**

    The architecture should allow the same operations to be used in the future by workflows, scripts, and MCP.

---

## 29. Conceptual Summary

The architecture can be summarized as follows:

```text
                         ┌───────────────┐
                         │     User      │
                         └───────┬───────┘
                                 │
                                 ▼
                         ┌───────────────┐
                         │     Tool      │
                         │               │
                         │ interaction   │
                         │ presentation  │
                         │ availability  │
                         └───────┬───────┘
                                 │
                                 ▼
                         ┌───────────────┐
                         │    Command    │
                         │               │
                         │ operation     │
                         │ undo/redo     │
                         └───────┬───────┘
                                 │
                                 ▼
                         ┌───────────────┐
                         │   Application │
                         │    Service    │
                         └───────┬───────┘
                                 │
                                 ▼
                         ┌───────────────┐
                         │    Domain     │
                         │               │
                         │ clinical      │
                         │ semantics     │
                         │ geometry      │
                         └───────────────┘
```

In parallel:

```text
Module
├── Tools
├── Commands
├── Services
└── Capabilities
```

In the interface:

```text
Workspace
│
├── Area
│   └── Editor
│       └── Tool
│
├── Area
│   └── Editor
│       └── Tool
│
└── Area
    └── Editor
        └── Tool
```

The central idea is that **Tool** is the framework's unit of action and interaction, while **Command** is the unit of operation and history, **Application Service** is the unit of application-logic coordination, **Domain** is the unit of clinical and computational meaning, and **Capability** describes what a module or component is able to provide.

This separation allows CranioZ to keep its interface decoupled from clinical logic, provide a modular and plugin-extensible architecture, and establish a consistent foundation for workflows, automation, scripts, and MCP.
