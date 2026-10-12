# Architecture Overview

# 1. Purpose

This document provides a high-level overview of the CranioZ system architecture. It defines the principal architectural concepts, boundaries, responsibilities, and relationships between the major parts of the system.

The purpose is to establish a common architectural vocabulary and provide a reference for developing the core platform, UI, clinical modules, plugins, and infrastructure.

Detailed architectural decisions are documented separately as Architecture Decision Records (ADRs).

# 2. Architectural Goals

The CranioZ architecture is designed to:

- Provide a professional software platform for cranio-maxillofacial surgical planning.
- Separate clinical concepts from generic computational and graphical infrastructure.
- Evolve through independent modules and plugins.
- Keep the core platform small, stable, and reusable.
- Favor Python as the primary implementation language.
- Reuse mature open-source libraries rather than reimplementing established functionality.
- Support multiple clinical workflows without coupling the core to a specific procedure.
- Maintain explicit boundaries between domain logic, application orchestration, infrastructure, and presentation.
- Support deterministic operations, validation, undo/redo, and controlled state changes.
- Provide mechanisms for long-running operations without blocking the UI.
- Provide a stable foundation for automation and AI/MCP integration.
- Support reliable persistence, migration, and backward compatibility.
- Provide architectural foundations for security, auditing, and regulatory requirements.


# 3. Architectural Principles

### 3.1 Domain-first design

Clinical and scientific concepts are represented explicitly in the domain model: Patient, Project, Scene, Mesh, Volume, Landmark, Bone, Maxilla, Mandible, Tooth, Osteotomy, Surgical Guide, Plate, Cephalometric Landmark, Registration, Planning Operation.

Generic computational structures must not be forced to carry clinical semantics that do not belong to them.

### 3.2 Separation of responsibilities

The system is divided into four principal layers: Domain, Application, Infrastructure, and UI. Modules and plugins extend these layers through defined contracts.

The Domain defines concepts and fundamental rules. The Application coordinates operations, state changes, transactions, and workflows. Infrastructure provides technical implementations. The UI presents application capabilities to the user.

### 3.3 Composition over monolithic functionality

CranioZ is not a single large application. The platform provides a stable core; clinical functionality is composed from modules and plugins.

An orthognathic workflow may compose: Tomography → Models → Cephalometry → Registration → Osteotomy → Splint. Another workflow may use a different sequence. The same module may participate in multiple workflows.

### 3.4 Clinical semantics over generic abstractions

A Mesh represents geometric data. A Mandible represents a clinical concept that may reference or contain geometric representations. The same geometric infrastructure supports different clinical entities without making geometry responsible for clinical meaning.

### 3.5 Stable core, extensible edge

The core platform remains intentionally small and stable. New functionality is preferentially implemented through modules, plugins, tools, services, data types, workflows, UI components, and public extension points.

### 3.6 Explicit operations

User-triggered operations are represented explicitly rather than hidden inside UI callbacks:

```text
User → Tool → Command → Application Service → Domain → State Change → Event → UI
```

This provides explicit boundaries for undo/redo, validation, transactions, logging, automation, workflow execution, testing, and AI integration.

### 3.7 UI is not the domain
The UI must not contain clinical rules or core computational logic. UI components present state, collect input, and delegate operations to the Application and Domain layers.

### 3.8 Explicit architectural boundaries
CranioZ follows a Ports and Adapters approach. The Application layer defines ports for persistence, project loading and saving, external computation, rendering integration, and task execution. Infrastructure provides concrete adapters. The Domain remains independent of infrastructure implementations.

## 4. High-Level Architecture
The diagram below represents logical responsibilities, not a strict runtime dependency graph. The vertical arrangement does not represent dependency order.

```
text
┌───────────────────────────────────────────────────────────┐
│                         CranioZ                           │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐  │
│  │                       UI Layer                      │  │
│  │  Areas · Editors · Toolbars · Overlays              │  │
│  │  Depends on Application for operations              │  │
│  └───────────────────────┬─────────────────────────────┘  │
│                          │ depends on                     │
│  ┌───────────────────────▼─────────────────────────────┐  │
│  │                  Application Layer                  │  │
│  │ Commands · Services · Tasks · Flows · Events        │  │
│  │ State · Transactions · Application Ports            │  │
│  └───────────────────────┬─────────────────────────────┘  │
│                          │ coordinates                    │
│  ┌───────────────────────▼─────────────────────────────┐  │
│  │                     Domain Layer                    │  │
│  │ Objects · Anatomy · Geometry · Imaging · Planning   │  │
│  │ Scene · Project · Patient · Cephalometry · Units    │  │
│  │ Independent of all infrastructure                   │  │
│  └───────────────────────▲─────────────────────────────┘  │
│                          │ implements contracts           │
│  ┌───────────────────────┴─────────────────────────────┐  │
│  │                 Infrastructure Layer                │  │
│  │ VTK · ITK · DICOM · OCCT · CGAL · File I/O          │  │
│  │ Adapters for Application/Domain contracts           │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐  │
│  │              Modules / Plugins (transversal)        │  │
│  │  Clinical capabilities and platform extensions      │  │
│  └─────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────┘
```

Infrastructure is orthogonal, not inferior. Modules and Plugins are transversal extensions, not a fifth layer.

## 5. Core Architectural Layers
### 5.1 Domain
The domain layer contains the conceptual model. It must be independent of Qt, VTK, file formats, database implementations, OS APIs, rendering implementations, and external services.

```
text
domain/
├── objects/
├── anatomy/
├── geometry/
├── imaging/
├── scene/
├── project/
├── patient/
├── planning/
├── cephalometry/
├── flow/           # conceptual model of Flows (structure, steps, requirements)
├── nodes/
├── units/
└── parametric_facial_model/
```

domain/flow/ contains the conceptual model of Flows. The execution engine belongs to the Application layer. The definitions are stored in versioned JSON. The progress is persisted in project state.

### 5.2 Application
The application layer coordinates system operations: Commands, command execution, undo/redo, application services, tasks, event dispatch, workflow execution, workflow requirement evaluation and step transitions, application state, transaction boundaries, coordination between modules, validation orchestration, and application ports.

Its primary responsibility is orchestration, not a second domain model.

### 5.3 Infrastructure
The infrastructure layer contains technical implementations: DICOM access, STL/OBJ import and export, VTK/ITK integration, PyDicom, NumPy, Open CASCADE, CGAL, rendering, persistence, serialization, and platform integration.

Implementations must be replaceable when practical. The Domain must not know whether a mesh is internally represented using VTK, OpenMesh, or another library.

The UI layer contains the graphical interface. It presents application state and collects user interaction.

Conceptual UI elements include:

* Application Menu
* Home Page — project table with actions, filters, and application-level icons
* Splash Screen — CranioZ startup screen
* Configurações Iniciais — first-run wizard
* Workspace
* Top Bar — structural component of the Workspace (see §18)
* Areas — structural containers that host Editors
* Editors — functional units hosted inside Areas
* Toolbars — internal to each Editor, declared and materialized by the Editor itself
* Overlays — floating layers managed by the Workspace, including the shared steps_panel
* Dialog and modal windows
* Application settings screens

Area and Editor are distinct concepts
In CranioZ, Area and Editor are distinct but complementary concepts:

An Area is a structural container provided by the Workspace. It occupies a position in the Area Layout Tree and provides the space where Editors are hosted.

An Editor is a functional unit provided by the system, a Module, or a Plugin. It provides a specific interaction experience (Viewport3D, MPR Viewer, Console, Properties, etc.).

Terminology: Area emphasizes where (position, structure); Editor emphasizes what (function, experience).

Area hosts Editors
An Area hosts one or more Editors. The Central Area may be split horizontally and vertically, hosting multiple Editors simultaneously in an internal Editor Layout Tree (the same N-ary split tree model used by the Area Layout Tree).
```
text
Area Central
└── Editor Layout Tree
    Split(HORIZONTAL)
    ├── Split(VERTICAL)
    │   ├── Leaf(editor.mpr_axial)
    │   └── Leaf(editor.mpr_sagittal)
    └── Split(VERTICAL)
        ├── Leaf(editor.mpr_coronal)
        └── Leaf(editor.viewport_3d)
```
The Area provides methods to add, remove, and activate Editors. The Area does not know what an Editor does.

Toolbar is internal to the Editor
A Toolbar is an internal widget of an Editor, not an Area. Each Editor declares and materializes its own Toolbar(s) inside its own content area. An Editor may declare more than one Toolbar, with independent orientations (HORIZONTAL or VERTICAL).

The Workspace never hosts Toolbars. An Area never owns a Toolbar. The Area hosts Editors; the Editors host their Toolbars. This preserves the Workspace's single rule (§1.2): if something is not an Area and not an Overlay, the Workspace does not interpret it.
```
text
Editor
├── Toolbar (Vertical)
│   └── Tools
├── Content
├── Overlays
└── Toolbar (Horizontal)
    └── Tools
```
There is no separate EditorHost
There is no EditorHost abstraction. An Area manages its Editors directly, using its internal Editor Layout Tree. The Area provides the operations needed to host, activate, and remove Editors; the EditorRegistry provides the operations needed to resolve editor_id to concrete Editor types and create instances.

Relationship summary

```text
Workspace
├── Top Bar (Painel Superior)   ← structural component
│   ├── Left segment   — Menu, Home link, toggle Left
│   ├── Center segment — module tabs, + button
│   └── Right segment  — Extras, toggle Right, window controls
│
├── Area Layout Tree
│   ├── Area LEFT      → Editor Layout Tree
│   ├── Area CENTRAL   → Editor Layout Tree (may be split H/V)
│   ├── Area RIGHT     → Editor Layout Tree
│   └── Area BOTTOM    → Editor Layout Tree
│
└── Overlays
    └── steps_panel
```
* The Workspace manages Areas and Overlays.
* An Area hosts Editors and organizes them in its internal Editor Layout Tree.
* An Editor provides a functional experience and materializes its own Toolbars.
* A Toolbar presents Tools inside an Editor.
* A Tool represents an action or interaction mode, defined independently in the ToolRegistry.

Compliance with the single rule
The Workspace manages Areas and Overlays. It does not own clinical state, Tools, Toolbars, or Module behavior. Toolbars, Tools, and Editors are invisible to the Workspace. The Workspace may use platform services (LayoutRenderer, EditorRegistry, OverlayManager) to materialize and manage its elements, but it does not interpret them.

## 6. Module Composition
A module represents a coherent functional capability. Modules do not own or implement the fundamental UI infrastructure. They compose their functionality using platform-provided primitives and extension points.

A module may compose: Tools, Commands, Services, Data Types, Editors, Toolbars, Flows, and Capabilities.

Declared vs materialized
The contract between module and platform is:

The module declares its desired composition in a ModuleUISpec.

The platform validates the declaration.

The Workspace creates or reuses Areas and resolves the declared Editors.

The Workspace applies the composition to the LayoutTree.

Layout state may be personalized by the user and persisted with the project.

The initial composition declared by the module is distinct from the active layout, which may have been personalized. Activation of a module must not overwrite a saved personalized layout.

Semantic regions
```
text
Orthognathic Module
      │
      ▼
ModuleUISpec (Workspace Composition)
      │
      ├── LEFT      → Lists
      │                (Object List, Cephalometric Points, Masks)
      ├── CENTRAL   → Editing Area
      │                (3D Viewport, MPR Viewer)
      ├── RIGHT     → Auxiliary Tools
      │                (Properties, Material, Osteotomy Patterns)
      └── BOTTOM    → Consoles and Extras
                       (Console, History, AI Assistant)
```

The regions LEFT, CENTRAL, RIGHT, and BOTTOM are semantic conventions used by the module to declare its initial composition. They are not fixed positions imposed on the user.

The Workspace layout is an N-ary tree of splits. The semantic regions guide the LayoutBuilder in constructing the initial tree. Once built, the user may move, resize, hide, or add Areas.

Separation between platform and module
```
text
Platform
    ├── Areas (host Editors)
    ├── Editors
    ├── Toolbars (internal to Editors)
    ├── Tools
    ├── Commands
    ├── Overlays (including steps_panel)
    └── Layout mechanism (N-ary tree of splits)
```
The module declares which Areas exist and which Editors occupy them. It does not declare Toolbars directly; the Toolbars are declared by the Editors the module selects. The module does not declare Overlays, the layout mechanism, or other modules.

A module is a consumer and composer of platform capabilities, not an owner of the underlying UI infrastructure.

## 7. Module Contract
A module may expose or register:

```
text
Module
├── Module Specification
├── Lifecycle
├── State
├── Tools
├── Commands
├── Services
├── Data Types
└── Capabilities
```
The module contract defines identity, lifecycle, dependencies, registration, public capabilities, extension points, state ownership, resource management, and compatibility requirements. The detailed contract is defined in a dedicated document and ADR.

## 8. Flows
A Flow represents an ordered sequence of steps to accomplish a task. Each step is associated with one module by default. A flow may reuse the same module in multiple steps.
```
text
Orthognathic Planning
  Step 1: Tomography   → tomography_module
  Step 2: Models       → models_module
  Step 3: Cephalometry → cephalometry_module
  Step 4: Registration → registration_module
  Step 5: Osteotomy    → osteotomy_module
  Step 6: Splint       → splint_module
```
Flows orchestrate. They do not implement clinical logic. The Flow declares:

Ordered steps and associated modules

Requirements (referencing registered validators)

Actions (referencing registered handlers)

Completion criteria and dependencies

Contextual actions and workflow configuration

Versioned user-facing labels and resource references

Identifiers in the JSON refer to implementations registered by the application. Unknown identifiers are configuration errors, not silently ignored.

The Python workflow engine belongs to the Application layer. It loads and validates the JSON, evaluates requirements, calculates step state, and determines the next step. When a step is completed, it asks the application to activate the module for the next step.

The steps_panel is a shared Overlay hosted by the Workspace. It presents the unified step list across module changes, sends user actions to the workflow engine, and displays progress. It is not an Area.

Flow definitions and case progress are separate. JSON stores the versioned definition; the project stores the active step, completion status, choices, and references.

Failure handling:

If a requirement is unmet, the step remains in blocked state.

If a module is unavailable, the engine reports a configuration error.

If a Flow definition was updated since the project was saved, the engine resolves against the version stored with the project, not the latest version.

Flows can be created, edited, removed, exported, and imported through Gerir Fluxos.

## 9. Tools, Commands, Services, and Tasks
Tool. An operational capability exposed to the user. A Tool does not necessarily contain the implementation.

Command. An executable application operation. Every state-changing operation passes through the Command mechanism.

Each Command declares:

Whether it is reversible (undo/redo) or requires a compensating action

Its transaction requirements

Its authorization requirements

The events it publishes on success

The Command mechanism ensures that all state-changing operations follow a consistent path. It does not automatically guarantee reversibility, atomicity, or authorization — those are declared in each Command's contract.

Service. Reusable application or domain functionality not naturally belonging to a single entity. Services have explicit contracts.

Task. A potentially long-running operation managed by the Application layer. Provides execution, progress, cancellation, error propagation, result delivery, and state reporting.

## 10. Transactions and State Consistency
Multi-step operations must not leave the project in an invalid intermediate state.
```
text
Command → Transaction Boundary → Domain Changes → Commit → Events
```

Not all infrastructure operations are transactional by nature. Changes to memory, files, and other resources may require different commit and recovery strategies.

For operations that cannot be reverted automatically, the Command contract specifies the compensation or recovery mechanism.

## 11. Concurrency and Long-Running Operations
Potentially long-running operations must be executed outside the UI event loop.

The GIL is not the architectural reason: VTK, ITK, and Open CASCADE release the GIL during native operations.

text
UI → Tool → Command → Task → Application Service → Domain / Infrastructure → Progress / Result / Error → Event → UI
Modules must not independently reinvent the concurrency model.

## 12. Scene and Rendering Architecture
The Domain Scene represents semantic state. The visualization backend (VTK) represents that state graphically. These representations must not become independent sources of truth.
```
text
Domain Scene → Application Events → Visualization Adapter → VTK Scene / Render Window
```

The Domain does not depend directly on VTK. A visualization adapter translates domain state into renderer-specific representations. The VTK representation remains an implementation detail.

## 13. Event Architecture
text
Tool → Command → Domain / Service → State Change → Event → Subscribers
Commands express that something should happen. Events communicate that something happened.

Events are published only after successful commit. A rolled-back transaction must not publish success events.

Events must not be used as hidden commands. The Event Bus must not cause the Domain to depend on the UI or rendering system.

## 14. Data Architecture
The system works with Volumes, Meshes, Images, Landmarks, Anatomical Structures, Teeth, Surgical Plans, Osteotomies, Plates, Guides, Patient Information, and Project Information. Technical representations may include DICOM, STL, OBJ, JSON, image arrays, VTK data structures, and Open CASCADE structures.

14.1 Objects and DataTypes
An Object provides common identity and metadata. A DataType defines a stable type recognized by the platform.

Complete contracts for Object identity, lifecycle, registration, and serialization are defined in dedicated documents.

## 15. Persistence
CranioZ projects require a versioned semantic project representation, distinguishing between: semantic project metadata, object identity and relationships, configuration and state, large binary data, and domain-specific formats.

The persistence architecture addresses schema versioning, migration, stable object identifiers, backward compatibility, deterministic serialization, integrity of references, separation of metadata and large data, and error recovery.

Persisted case or project state includes workflow progress needed to resume work: workflow definition version, active step, completion state, and stable references.

## 16. Dependency Architecture
CranioZ follows a Ports and Adapters approach.
```
text
UI → Application Ports → Domain
```
Contracts are owned by the layer that defines them:

Domain contracts represent domain concepts.

Application ports represent application-level dependencies, implemented by Infrastructure.

Infrastructure adapters implement Application ports.

The Domain must not depend on infrastructure implementations.

## 17. Plugin Architecture and API Stability
A plugin may provide: Modules, Tools, Services, Data Types, UI components, Flows, Capabilities, and Integrations.

Plugins communicate through public APIs and extension points, not private implementation details.

Public extension points are versioned: module contracts, tool contracts, command contracts, service interfaces, DataType registration, flow definitions, UI extension points, plugin manifests, event contracts, and capability interfaces.

The plugin system distinguishes Public API, Internal API, and Experimental API. Plugins declare their compatibility requirements.

## 18. Workspace and UI Composition
The Workspace provides the environment in which modules and their UI components operate.

Structure and Overlays
The Workspace has two distinct structural categories:
```
text
Workspace
├── Top Bar (Painel Superior)   ← structural component
│   ├── Left segment   — Menu, Home link, toggle Left
│   ├── Center segment — module tabs, + button
│   └── Right segment  — Extras, toggle Right, window controls
│
├── Area Layout Tree
│   ├── Area LEFT      → Editor Layout Tree
│   ├── Area CENTRAL   → Editor Layout Tree (may be split H/V)
│   ├── Area RIGHT     → Editor Layout Tree
│   └── Area BOTTOM    → Editor Layout Tree
│
└── Overlays
    └── steps_panel
```
Structural components are part of the Workspace itself. They have a fixed position and are not repositionable or closeable by the user.

Overlays are floating layers managed by the Workspace. They can be moved, resized, and closed. The steps_panel is the primary example.

Top Bar ownership
The Top Bar is a structural component of the Workspace, not an Overlay and not a MainWindow component.

The MainWindow is only the operating system frame. The Home Page has its own structural header (the home top bar with community actions), separate from the Workspace Top Bar.

The distinction matters:

Aspect	Top Bar	steps_panel
Category	Structural	Overlay
Position	Fixed at top	Repositionable
Lifecycle	Workspace	Active Flow
Movable	No	Yes
Closeable	No	Yes
Resizable	No	Yes
The Home Page and the Workspace each have their own structural header and their own overlays. Neither belongs to the MainWindow.

The steps_panel presents the active Flow across module boundaries. A module may contribute Areas and Editors to the Workspace (via its ModuleUISpec), while the steps_panel remains visible. The Editors hosted in those Areas declare their own Toolbars and reference Tools from the ToolRegistry.

## 19. Clinical Semantics and Geometry
A fundamental distinction is made between Geometry and Clinical Meaning.

text
Mesh → Anatomical Structure → Mandible
Mesh → Surgical Object → Osteotomy Segment
The geometric representation may be shared, replaced, or transformed without changing the clinical concept.

## 20. Observability and Auditability
Observability includes structured logging, error reporting, metrics, performance measurements, tracing, and diagnostic information.

Observability is distinguished from clinical or security auditing.

Audit mechanisms record actor, timestamp, action, affected object or project, and operation result. Audit requirements depend on the deployment context and applicable regulatory requirements.

## 21. Security and Compliance
CranioZ may process patient-related information and must provide architectural mechanisms for protecting sensitive data.

Security considerations include authentication, authorization, access control, data protection, encryption in transit and at rest, secure storage and data exchange, auditability, sensitive-data handling, and dependency and supply-chain security.

CranioZ captures professional identity information (name, professional license, address) during first-run configuration. This information is used in generated reports and signed clinical documents.

Professional identification, authentication, authorization, and digital signature are separate concerns. A stored signature image is not equivalent to a cryptographic digital signature. Each of these concerns has its own requirements, documented separately according to deployment and regulatory context.

Regulatory requirements depend on the deployment context, jurisdiction, intended use, and regulatory classification. Relevant frameworks may include LGPD, applicable ANVISA requirements, HIPAA, and MDR.

## 22. Automation and MCP
Automation is an extension of the existing architecture, not a separate execution model.

CranioZ treats AI as a first-class citizen. The AIAssistantEditor is a regular Editor presented in the Bottom Area. AI executes commands through the same Command mechanism used by human-triggered Tools.
```
text
AI / MCP → Tool / Command / Service → Application → Domain → State
```
Every AI-executed command is auditable (via AuditLog) and visible in the History Editor. Reversibility depends on the specific Command contract. Commands declare whether they support undo/redo or require a compensating action.

AI does not bypass the Application and Domain layers, and is subject to the same validation, authorization, and audit rules as human-triggered commands.

## 23. Testing and Validation
Tests follow architectural boundaries and account for the numerical and geometric nature of the system.

Domain tests validate entities, rules, clinical semantics, mathematical calculations, and invariants.

Application tests validate commands, services, tasks, flows, events, state transitions, and transaction boundaries.

Infrastructure tests validate file I/O, DICOM handling, serialization, external library adapters, rendering integration, and persistence.

UI tests validate user interaction, view behavior, tool presentation, workspace composition, UI state synchronization, Steps Panel state, and workflow navigation across module changes.

Geometric and numerical validation requires tests that validate properties of the resulting data: mesh validity, watertightness, manifoldness, surface area, volume, normal orientation, topological invariants, distance tolerances, transformation accuracy, landmark preservation, registration error, and numerical stability.

Where appropriate, the test suite uses property-based tests, geometric invariants, numerical tolerance checks, reference datasets, regression datasets, golden results, and visual regression testing.

## 24. Architectural Boundaries
Boundary	Principle
Domain ↔ UI	Domain must not depend on UI
Domain ↔ Qt	Domain should not depend on Qt
Domain ↔ VTK	Domain should not depend directly on VTK
Application ↔ UI	UI invokes application capabilities rather than implementing them
Module ↔ Core	Modules use public platform contracts
Module ↔ Module	Prefer explicit contracts over internal access
Plugin ↔ Core	Plugins use public extension points
Persistence ↔ Domain	Persistence is an implementation concern
Rendering ↔ Domain	Rendering state is derived from semantic application state
AI/MCP ↔ Core	AI executes Commands through the same unified entry point as human tools
Long-running Work ↔ UI	Computational tasks must not block the UI event loop


## 25. Architectural Invariants
The UI event loop must remain responsive.

Potentially long-running operations must use the Application task mechanism.

The Domain layer must not depend on Qt, VTK, or infrastructure implementations.

The Domain Scene is the semantic source of truth for scene state.

Renderer-specific state must be derived from or synchronized with application/domain state.

Multi-step state-changing operations must have explicit transaction boundaries.

Modules must use standardized application mechanisms for long-running operations.

Plugins must use public extension points rather than internal implementation details.

Public plugin APIs must be versioned and compatibility must be explicit.

Events communicate state changes and are published only after successful commit.

Persistence must support schema evolution and migration.

Numerical and geometric operations must be validated using appropriate tolerances and invariants.

Security-sensitive operations must have explicit authorization boundaries.

Clinical or audit-relevant actions should be traceable where required.

Rendering infrastructure must remain replaceable without redefining the domain model.

26. Project Structure
```
text
cranioz/
├── .github/
├── src/
│   └── cranioz/
│       ├── domain/
│       ├── application/
│       ├── infrastructure/
│       ├── ui/
│       ├── modules/
│       ├── config/              # system configuration (defaults)
│       ├── settings/            # user preferences (logic)
│       └── assets/
├── plugins/
├── tests/
├── docs/
├── examples/
├── scripts/
├── pyproject.toml
├── README.md
├── LICENSE
├── CHANGELOG.md
├── CONTRIBUTING.md
└── CODE_OF_CONDUCT.md
```
Config vs Settings:

config/ — system configuration. Describes how the system works. Defined by developers/admins. Rarely changed. Versioned with the software.

settings/ — user preferences. Describes what the user chose. Defined by the user through the UI. Frequently changed. Persisted outside the package (e.g., ~/.cranioz/settings/).

The ConfigurationLoader merges defaults from config/ with user overrides from the OS-specific application data directory.

## 27. Architectural Evolution
Early versions prioritize stable domain concepts; core object and DataType infrastructure; application command model; module contracts; UI workspace infrastructure; basic persistence; task execution infrastructure; essential clinical modules; validation and testing infrastructure.

Advanced capabilities are planned for progressive introduction: advanced CAD operations; parametric facial models; finite element analysis; AI-assisted segmentation and planning; MCP integration; advanced automation; third-party plugin ecosystems.

Architectural evolution favors incremental changes over large-scale rewrites. Changes to public contracts are explicitly documented and versioned.

## 28. Architecture Decision Records
Specific architectural decisions are documented under docs/architecture/adr/.

The architecture is expected to have ADRs addressing: programming language and runtime; UI framework; dependency architecture and Ports & Adapters; application transaction boundaries; Unit of Work and rollback; concurrency and task execution; Module Contract / SPI; Plugin API and versioning; DataType registry; command architecture; event system; scene and rendering synchronization; persistence format; project schema versioning and migration; dependency policy; rendering architecture; workflow architecture; workflow definition schema and execution contract; Steps Panel and Workspace integration; Area = Editor; Top Bar ownership; Object Library; Custom Flows; AI command execution; observability; security and auditability; geometric and numerical validation; MCP integration.

The overview.md describes the structure and principles. The ADRs explain why specific decisions were made and the contracts developers will implement.
