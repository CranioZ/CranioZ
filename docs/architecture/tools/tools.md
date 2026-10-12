# Tools
## 1. Overview
A Tool represents an action or interaction mode made available to the user by a CranioZ module. Tools are one of the main interfaces between the user and the application's executable functionality, and may be presented in toolbars, menus, panels, contextual menus, or Editors without their definition depending on a specific Workspace location.

A Tool does not represent the module itself and should not contain clinical, geometric, or infrastructure logic. Its responsibility is to define what it represents, how it is identified, in which contexts it is available, and how interaction is initiated. Execution is delegated to the application layer through Commands and Application Services.

    User → Tool → Command → Command Executor → Application Service → Domain
Not every Tool results directly in a single Command. Interactive Tools may produce a sequence of operations or generate a Command only when interaction completes.

## 2. Objectives
The Tool system should provide a uniform interface for actions and interaction modes, allow modules and plugins to expose functionality, separate interaction and presentation from application logic, support multiple presentation forms for the same Tool, facilitate discovery and registration, support contextual availability, provide metadata for UI construction, allow activation by humans or automation, keep Tools independent of Workspace location, allow reuse by menus, shortcuts, workflows, scripts, and MCP, and enable extensibility through plugins.

A Tool should be sufficiently declarative for the application to determine what it is, when it can be used, and how it should be presented, without its implementation needing to know Workspace-specific details.

## 3. Tool, Command, and Service
A Tool represents an action or interaction mode made available to the user. It answers: what does it represent, how is it identified, how does it appear, in which contexts is it available, how is interaction initiated, what type of interaction does it support.

A Command represents an operation executable by the application. It answers: what operation will be executed, what are its parameters, how can it be undone, how does it participate in history, what changes does it produce, what events are generated.

A Service implements application operations or rules that should not belong to the Tool. Algorithms and specific rules remain in their appropriate layers.

    Tool      → may create/execute → Command
    Command   → does not necessarily depend on a Tool
    Service   → coordinates application logic
A Command may be triggered by a Tool, shortcut, menu, macro, workflow, automation, MCP, script, or internal operation. A Tool may represent a complex interaction resulting in one or more Commands. The preferred flow is:


    Tool → Command → CommandExecutor → CommandStack → Application Service → Domain

The CommandExecutor handles execution, history, and Undo/Redo. The Tool should not implement these responsibilities. CommandStack remains independent of the Tool.

Example:

    Tool:                Create Le Fort I Osteotomy
    Command:             CreateOsteotomyCommand
    Application Service: OsteotomyService
    Domain:              Osteotomy, Bone, Geometry

## 4. Tool as a Contract
Tool should be treated as a contract. Using Protocol (structural typing) rather than ABC reduces coupling and allows plugins to implement Tools without inheriting from a framework base class.

The base contract should remain small and stable, describing identity, metadata, presentation, and contextual availability. Execution is not mandatory in the base contract, since different Tool modalities exist.

    python
    class Tool(Protocol):
        identifier: str
        label: str
        description: str
        icon: str | None
        category: str | None
    
        def is_available(self, context: ToolContext) -> bool:
            ...

is_enabled does not belong exclusively to subclasses. The UI needs to present Tools of different modalities and determine whether each can be triggered. If the operation depended on inspecting the concrete modality to discover is_enabled, complexity would shift into UI components. Instead, the framework should resolve availability and enablement through a dedicated component (e.g., ToolStateResolver), using declared requirements and context. The UI must not rely on improvised type checks.

### 4.1 Action Tool
An ActionTool represents a discrete action. It normally results in the execution of a Command or application operation.

    python
    class ActionTool(Tool, Protocol):
        def execute(self, context: ToolContext) -> ToolResult:
        ...
Examples: Save, Undo, Add Landmark, Create Plate, Calculate Cephalometry.

### 4.2 Interactive Tool
An InteractiveTool represents a continuous interaction mode. The definitive interface should remain small.

    python
    class InteractiveTool(Tool, Protocol):
        def activate(self, context: ToolContext) -> None:
            ...
    
        def deactivate(self, context: ToolContext) -> None:
            ...
    
        def handle_event(self, event: ToolEvent, context: ToolContext) -> None:
        ...
Examples: Select, Move, Rotate, Measure, Place Landmark, Define Osteotomy Plane, Paint Segmentation, Sculpt.

## 5. Identity
Each Tool must have a unique and stable identifier.


    orthognathic.cephalometry.add_landmark
    osteotomy.create_lefort_i
The identifier should be unique within the system, remain stable across versions whenever possible, not depend on user-facing text, not depend on interface position, and be usable by menus, plugins, workflows, and automations. The label is intended for presentation only.

    yaml
    identifier: orthognathic.cephalometry.add_landmark
    label: Add Landmark
Changing the user-facing text should not change the Tool's identity.

## 6. Presentation and Metadata
A Tool should not determine where it is displayed. Positioning belongs to the UI layer and to the Workspace/Layout system.

    Tool                        → defines the action or interaction
    Workspace / Layout / Editor → defines where the Tool is presented

The Tool declares identity metadata: identifier, name, description, icon, semantic category, context requirements, and interaction modality. The UI configuration determines toolbar, menu position, display order, visual grouping, keyboard shortcut, and region-specific visibility.

category is a semantic metadata of the Tool. group deserves caution: if it does not have a consistent meaning for discovery or semantic grouping, it risks becoming merely a UI hint disguised as metadata. It should be kept only when there is a clear discovery or grouping use case, and treated as presentation metadata otherwise.

## 7. Tool and Editor
An Editor provides a specialized interaction space. A Tool provides an action or interaction mode usable in that space.

    3D Editor
    ├── Select, Move, Rotate, Measure, Landmark
    
    Cephalometric Editor
    ├── Add Landmark, Move Landmark, Remove Landmark, Measure Angle, Measure Distance
8. 
The Editor should not reimplement the logic of each Tool, and a Tool should not assume exclusive use by a particular Editor unless its definition explicitly requires a specific context.


    Editor → hosts / uses → Tool
and not:

    Tool → structurally belongs to → Editor

## 8. Execution Context
Tools often depend on the current state of the system. An osteotomy Tool may be available only when a patient is loaded, a valid mandible or maxilla exists, the model is in a compatible state, the module is available, a valid selection exists, and the current Editor supports the interaction.

ToolContext should represent the execution context provided by the framework, while services and specific interfaces provide access to the necessary operations. It should not become an excessively broad global context; each new need should not encourage additional dependencies in a monolithic context. Contexts may be segregated so that a Tool accesses only what it needs.


    class ToolContext(Protocol):
        @property
        def scene(self) -> SceneContext: ...
        @property
        def selection(self) -> SelectionContext: ...
        @property
        def editor(self) -> EditorContext | None: ...
        @property
        def permissions(self) -> PermissionContext: ...

A measurement tool may need selection and the active Editor, but not necessarily the Patient object or administrative permissions. The context may inform permissions, but effective authorization must be verified by the layer responsible for executing the operation.

### 8.1 Availability and Enablement
Available: the Tool makes sense in the current context and may be presented. Enabled: the Tool is available and can be activated immediately.

    Create Le Fort I Osteotomy

    Available: yes
    Enabled:   no

The Tool may be available because the osteotomy module is active and a patient exists, but remain disabled because no valid maxilla has been selected. The UI uses is_available(context) to decide whether to present the Tool and is_enabled(context) to decide whether it can be activated. This distinction prevents contextual logic from being embedded in UI components.

9. Tool State
The existence, availability, and activation of a Tool are different states. They are related properties, not necessarily successive phases of a universal state machine.

Concept	                Meaning
Registered	            The Tool was registered in the system.
Available	            The Tool can be used in the current context and presented.
Enabled	                The Tool can be triggered at that moment.
Active              	The Tool is executing an interaction session, when applicable.
Completed	            The interaction ended.

An ActionTool does not normally need a persistent Active state. An InteractiveTool may remain active until the user completes, cancels, or interrupts the interaction. Contextual state should be determined by the framework and the current context, not maintained as arbitrary state inside UI components. Tool state and session state are distinct: a Tool may be Available and Enabled with no active session, and the session has its own cycle (Idle → Interacting → Completed).

## 10. Execution and Result
Tool execution should not concentrate clinical, geometric, or infrastructure logic. The Tool acts as an interaction layer.

### 10.1 ToolResult
ToolResult and the result of a Command are distinct concepts. ToolResult is the result of the interaction or triggering of the Tool; the operational result belongs to the Command or service called.

An interactive Tool may complete successfully even when the operation requested by the user is cancelled before producing a persistent change. Likewise, a Tool may start an asynchronous Command and end its interaction before processing finishes.

    class ToolResult:
        interaction_status: Literal["completed", "cancelled", "interrupted"]
        command_result: CommandResult | None
        message: str | None
Keeping the results separate prevents ToolResult from becoming a generic container for all data produced by the system.

### 10.2 Threading and Asynchrony
Interactive Tools typically run on the UI thread, since they process input events and update previews. However, not every Command must be asynchronous. A simple command, such as changing a landmark property, may run synchronously. Segmentation, volume registration, complex geometric operations, and long calculations should be dispatched asynchronously when appropriate.

Recommended policy:

* Tool interaction: managed in the thread context required by the UI.
* Lightweight Commands: may run synchronously.
* Long operations: executed asynchronously by an appropriate mechanism.
* Shared state changes: coordinated by explicit concurrency and consistency rules.
* Preview and visual updates: synchronized with the UI thread.
* Cancellation: handled explicitly by the operation and the session lifecycle.

The Command — not the Tool — should declare its execution mode, so the CommandExecutor decides how to dispatch and the Tool remains unaware of threading.


    class Command(Protocol):
        execution_mode: Literal["sync", "async"] = "sync"

## 11. Interactive Tools
Some Tools represent continuous interaction with the user: Select, Move, Rotate, Draw, Measure, Place Landmark, Define Osteotomy Plane, Paint Segmentation, Sculpt, Place Implant. In these cases, the Tool has its own lifecycle.


    Idle → Activated → Interacting → Completed → Deactivated
Example:

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
The Tool may function as an interaction state machine, while persistent changes remain the responsibility of the application/domain layer.

### 11.1 Tool Session
It is useful to distinguish the Tool definition from a specific interaction session.


    Tool        → tool definition
    ToolSession → state of a specific interaction

    class ToolSession:
        tool: Tool
        state: ToolState
        context: ToolContext
        started_at: datetime
        finished_at: datetime | None
This prevents the base Tool contract from being polluted with temporary interaction state. A session may exist only while the Tool is active.

### 11.2 Activation and Deactivation
Activation of interactive Tools should be managed by a dedicated component, such as ToolManager.

    python
    class ToolManager:
        def activate(self, identifier: str, context: ToolContext) -> None: ...
        def deactivate(self) -> None: ...
        def active_tool(self) -> Tool | None: ...

ToolManager may ensure that only one interactive Tool is active per Editor, the previous Tool is correctly deactivated, changing Editors ends the appropriate session, changing modules is handled correctly, activation and deactivation events are propagated, an ActionTool may be executed even while an InteractiveTool is active in the same Editor (provided there is no conflict), and switching Editors with an active session suspends or terminates the session according to a defined policy. Different Editors may have different active Tools, similarly to the editor model used by Blender.

12. Tool Modalities
Tools may be classified according to behavior. This classification is primarily behavioral and should not create an excessively complex class hierarchy.

Modality                        Description          	                                    Contract
Action Tool	                    Executes a discrete action.	                                ActionTool
Interactive Tool	            Remains active while the user interacts with the scene.	    InteractiveTool
Toggle Tool	                    Switches between two states.	                            ActionTool (flips state)
Stateful Tool	                Maintains a more complex interaction state.	                InteractiveTool (with state)

Examples: Save, Undo, Add Landmark, Create Plate, Calculate Cephalometry (Action); Select, Move, Measure, Place Landmark, Draw Osteotomy (Interactive); Snap, Grid, Visibility, Orthographic/Perspective (Toggle); Segmentation Brush, Sculpt, Registration, Osteotomy Planning (Stateful).

A ToggleTool may be modeled as an ActionTool whose execution flips a state and returns the new state in ToolResult. A StatefulTool may be modeled as an InteractiveTool whose session carries additional state. A dedicated contract should only be introduced if the existing ones prove insufficient. ActionTool and InteractiveTool define interaction modalities; Toggle and Stateful describe behaviors or characteristics, not classes. Creating a class for each combination would increase complexity without improving the contract.

## 13. Tool Groups and Categories
Tools may be grouped semantically for presentation and discovery.


    Cephalometry
    ├── Add Landmark, Move Landmark, Delete Landmark, Measure Distance, Measure Angle
    
    Osteotomy
    ├── Create Osteotomy, Edit Osteotomy, Move Segment, Rotate Segment, Confirm Osteotomy
    Grouping does not change the identity of the Tool.

Category is a broader semantic classification. Group is a contextual grouping of Tools for presentation.

    Category: Measurement
    Group:    Cephalometry
    Tool:     Measure Angle
Category defines the type of Tool; Group defines how it may be grouped in the UI. This prevents category from becoming a generic field responsible for different functions.

Initial categories may include: Selection, Navigation, Measurement, Annotation, Modeling, Planning, Segmentation, Analysis, Visualization, Documentation. Categories should not be excessively rigid; the framework may provide common categories, while modules and plugins may introduce specific ones when necessary.

## 14. Tool Parameters
Some Tools require parameters.


    Create Plate
    
    thickness     = 1.5 mm
    hole_diameter = 2.0 mm
    locking       = true
The Tool should not necessarily store these values as permanent state. When appropriate, it may request the parameters from the user and produce a parameterized Command.

    Create Plate Tool → Plate Configuration → CreatePlateCommand(thickness=1.5, hole_diameter=2.0, locking=True) → CommandExecutor
Recommended distinction:

The Tool defines or requests which parameters are required for the interaction.

The UI collects the concrete values.

The Command receives the concrete values required to execute the operation.

The Domain validates model-specific rules.

    Tool → Parameter Specification → UI → Concrete Parameters → Command → Domain
This keeps the definition of the operation separate from the presentation of its parameters.

15. Tool Registry and Discovery
CranioZ should provide a Tool registration mechanism.


    ToolRegistry
    ├── register(tool)
    ├── unregister(identifier)
    ├── get(identifier)
    ├── find(...)
    └── list(...)
The Registry allows modules to register Tools, plugins to add Tools, the UI to discover available Tools, menus and toolbars to be built dynamically, automation systems to find Tools, and Tools to be queried by identifier.


    Module → register Tools → ToolRegistry → UI / Tool Manager / Automation
A Registry is a component, not a contract. Contracts describe interfaces or expected behavior; a Registry maintains records, resolves identifiers, and applies uniqueness rules. It should live in the layer responsible for managing Tools (e.g., a Tools subsystem), not inside contracts/. The definitive location depends on who owns the lifecycle, discovery, and registration of Tools: the module framework or a specific application subsystem. That responsibility should be defined before fixing the file path.

### 15.1 Identity Conflicts
The Registry must define clear rules for identifier uniqueness, conflicts between modules and plugins, priority, replacement, and deactivation. If two plugins attempt to register rhinoplasty.add_landmark, the Registry must have a deterministic policy. The preferred policy is to reject duplicate identifiers, unless an explicit override mechanism has been defined.

### 15.2 Manifest and Implementation Resolution
When a Tool is declared in a plugin manifest, the framework must resolve the manifest entry to an implementation. An explicit entry point is recommended.

    yaml
    tools:
      - id: rhinoplasty.add_landmark
        label: Add Landmark
        category: annotation
        entry_point: rhinoplasty.tools.add_landmark:AddLandmarkTool

The Registry resolves entry_point via the plugin loader. Declarative metadata alone is not a complete Tool definition; the implementation is authoritative. Information that depends on code or context should not be duplicated in the manifest.

### 15.3 Tool Discovery
Declaring a Tool and deciding where it is presented are distinct responsibilities.


    Module              → declares functionalities and Tools
    Tool Registry/Manager → registers, discovers, resolves, manages Tools
    UI / Editor / Toolbar → chooses which Tools to present and where

A Tool may exist in the Registry without being currently visible. It may be used by a contextual menu, shortcut, workflow, or another interface without requiring its definition to change. The Editor declares which modalities/contexts it accepts, and the Registry filters compatible Tools. This is more flexible than having the Tool declare "I belong to Editor X".

## 16. Tools Provided by Modules and Plugins
Each module may provide the Tools required to expose its functionality.

    Cephalometry Module
    Tools: Add Landmark, Move Landmark, Delete Landmark, Measure Distance, Measure Angle

A module may contain:


    Module
    ├── Commands
    ├── Tools
    ├── Services
    └── Capabilities
However, the module should not directly own the Workspace's Areas or Editors. The relationship with the UI occurs through the appropriate UI, Layout, or Module Specification contracts.

Plugins may register Tools in the same way as internal modules.


    Plugin → ToolRegistry → Custom Tool

This allows third parties to add functionality without modifying the CranioZ Core. Examples:


    AI Segmentation Plugin
    └── Automatic Segmentation Tool
    
    Rhinoplasty Plugin
    ├── Nasal Landmark Tool
    ├── Nasal Osteotomy Tool
    └── Soft Tissue Simulation Tool
Plugin Tools should use the same contracts as native Tools whenever possible. A plugin manifest may declare metadata and entry points (see §15.2).

## 17. Tool and Capability
A Capability describes a capability offered by a module or component. A Tool represents a way to use a capability through an action or interaction.


    Capability: cephalometric_analysis
    
    Tools:
    ├── Add Landmark
    ├── Measure Angle
    └── Calculate Analysis
A Capability answers: "Does the system have this capability?" A Tool answers: "What action or interaction can the user use to access it?"

A Capability may exist without a corresponding Tool. A generic interaction Tool such as Select may not represent a specific clinical Capability.

## 18. Tool and MCP
A CranioZ Tool and an MCP Tool are not the same abstraction. A CranioZ Tool represents an application action or interaction; an MCP Tool represents an operation exposed to an external agent through the MCP protocol. Both may use the same application layer.

    UI Tool                         MCP Tool
      │                                │
      ▼                                ▼
    Command                         Command
      │                                │
      ▼                                ▼
    Application Service             Application Service
      │                                │
      ▼                                ▼
    Domain                          Domain

MCP does not need to control the UI directly. An agent could request create_osteotomy(...), and the application would execute the same fundamental operation used by the graphical interface, passing through the same validations. An adapter-based architecture avoids duplication and allows the UI and automation to share application logic.

## 19. Security and Validation
Tools should not be considered a sufficient security or validation boundary. Important operations should also be validated in the application and domain layers.

    UI Tool → Command → Application Validation → Domain Validation → Operation

This is necessary because Commands may be triggered by mechanisms other than the UI. The system should consider, when applicable: input validation, permissions, authorization, auditing, operational limits, and confirmation of destructive operations. ToolContext may inform permissions, but effective authorization remains in the application and domain layers. This becomes especially important when Commands may be triggered by automation, scripts, or MCP.

## 20. Examples
### 20.1 Landmark Tool

    Tool:      Add Landmark
    
    Context:
    ├── active patient
    ├── active 3D editor
    └── valid anatomical model
    
    Interaction:
    └── user clicks on model
    
    Result:
    └── AddLandmarkCommand

    Add Landmark Tool
            │ user interaction
            ▼
    Landmark Position
            ▼
    AddLandmarkCommand
            ▼
    Application Service
            ▼
    Cephalometric Landmark
            ▼
    Scene / Project
The Tool does not need to know the persistence details of the Landmark.

### 20.2 Osteotomy Tool

    Define Osteotomy Tool
            ▼
    User selects anatomical region
            ▼
    Interactive preview
            ▼
    User confirms
            ▼
    CreateOsteotomyCommand
            ▼
    Application Service
            ▼
    Osteotomy Domain Object
            ▼
    Scene Update
The same operation may later be triggered by a Toolbar, Menu, Shortcut, Workflow, Script, or MCP. The osteotomy logic does not need to be duplicated for each activation mechanism.

## 21. Code Organization
Contract definitions should remain in the framework's module infrastructure.


    src/cranioz/modules/
    ├── base/
    │   ├── module.py
    │   ├── module_state.py
    │   └── lifecycle.py
    │
    ├── contracts/
    │   ├── command.py
    │   ├── tool.py
    │   ├── tool_context.py
    │   ├── tool_result.py
    │   └── tool_session.py
    │
    └── specs/
        └── module_spec.py
The Tool contract should remain small and stable. Specific implementations should remain in the modules that use them.


    src/cranioz/modules/
    └── cephalometry/
        ├── tools/
        │   ├── add_landmark.py
        │   ├── move_landmark.py
        │   └── measure_angle.py
        ├── commands/
        └── services/
The Registry is not a contract and should live in the layer responsible for managing Tools, outside contracts/.

## 22. Architectural Principles
* A Tool is an interaction interface. It is not the domain and should not contain complex clinical or geometric logic.
* A Tool is not a Command. A Tool may create or execute a Command, but the Command remains independent of the UI.
* A Tool does not structurally belong to an Area. It may be presented in any compatible Area or Editor.
* A Tool should be contextual. Its availability may depend on the current project, selection, Editor, or module state.
* A Tool should have a stable identity. Its identifier is independent of its label and interface position.
* A Tool should be discoverable. Tools are registered and queried by the framework.
* A Tool should be reusable. The same operation is triggerable by different mechanisms.
* An interactive Tool should have its own lifecycle. Temporary interaction state is separated from the Tool's permanent definition.
* Validation should not depend on the UI. Important operations are validated in the application and domain layers.
* Plugins may provide Tools. The mechanism works for internal modules and external extensions.
* Tools should not know the Workspace organization. The Tool defines the interaction; the Workspace determines where it is presented.
* Commands should remain independent of Tools. The same operation is usable by the UI, workflows, scripts, and automation.
* Tools should be automation-compatible. The architecture allows the same operations to be used by workflows, scripts, and MCP.
* Threading must be explicit. Tool interaction runs on the UI thread; Commands declare their execution mode; the CommandExecutor decides how to dispatch.

The UI must not inspect concrete modalities. Availability and enablement are resolved by the framework.