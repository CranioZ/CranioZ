# Architecture Overview

## 1. Purpose

This document provides a high-level overview of the CranioZ system architecture.

It defines the principal architectural concepts, boundaries, responsibilities, and relationships between the major parts of the system.

The purpose of this document is to establish a common architectural vocabulary and provide a reference for the development of the core platform, user interface, clinical modules, plugins, and supporting infrastructure.

Detailed architectural decisions are documented separately as Architecture Decision Records (ADRs).

---

## 2. Architectural Goals

The CranioZ architecture is designed around the following goals:

* Provide a professional software platform for cranio-maxillofacial surgical planning.
* Separate clinical concepts from generic computational and graphical infrastructure.
* Allow the system to evolve through independent modules and plugins.
* Keep the core platform small, stable, and reusable.
* Favor Python as the primary implementation language.
* Reuse mature open-source libraries instead of reimplementing established functionality.
* Support multiple clinical workflows without coupling the core to a specific procedure.
* Allow modules to provide their own tools, services, data types, views, and workflows.
* Maintain explicit boundaries between domain logic, application orchestration, infrastructure, and presentation.
* Support deterministic operations, validation, undo/redo, and controlled state changes.
* Provide mechanisms for long-running operations without blocking the user interface.
* Provide a stable foundation for future automation and AI/MCP integration.
* Support reliable persistence, migration, and backward compatibility.
* Facilitate collaborative development and long-term maintenance.
* Provide architectural foundations for security, auditing, and applicable regulatory requirements.

---

## 3. Architectural Principles

### 3.1 Domain-first design

Clinical and scientific concepts should be represented explicitly in the domain model.

Examples include:

* Patient
* Project
* Scene
* Mesh
* Volume
* Landmark
* Bone
* Maxilla
* Mandible
* Tooth
* Osteotomy
* Surgical guide
* Plate
* Cephalometric landmark
* Registration
* Planning operation

Generic computational structures should not be forced to carry clinical semantics that do not belong to them.

---

### 3.2 Separation of responsibilities

The system is divided into architectural layers with explicit responsibilities.

The principal layers are:

1. **Domain**
2. **Application**
3. **Infrastructure**
4. **UI**

Modules and plugins extend these layers through defined contracts.

The layers are complementary rather than strictly hierarchical.

The Domain layer defines concepts and fundamental rules.

The Application layer coordinates operations, state changes, transactions, and workflows.

Infrastructure provides technical implementations and external integrations.

The UI presents application capabilities and system state to the user.

---

### 3.3 Composition over monolithic functionality

CranioZ should not be implemented as a single large application containing all clinical functionality.

The platform provides a stable core, while functionality is composed from modules and plugins.

For example, an orthognathic workflow may compose several modules:

```
Tomography
    ↓
Models
    ↓
Cephalometry
    ↓
Registration
    ↓
Osteotomy
    ↓
Splint
```

Another workflow may use:

```
Tomography
    ↓
Models
    ↓
Facial Analysis
    ↓
Implant Planning
    ↓
Surgical Guide
```

The same module may therefore participate in multiple workflows.

---

### 3.4 Clinical semantics over generic abstractions

Generic geometry, imaging, and data structures are necessary, but they should not replace clinical concepts.

For example:

```
Mesh
    ↓
Anatomical Structure
    ↓
Mandible
```

A `Mesh` represents geometric data.

A `Mandible` represents a clinical and anatomical concept that may reference or contain geometric representations.

This separation allows the same geometric infrastructure to support different clinical entities without making geometry itself responsible for clinical meaning.

---

### 3.5 Stable core, extensible edge

The core platform should remain intentionally small and stable.

New functionality should preferentially be implemented through:

* Modules
* Plugins
* Tools
* Services
* Data types
* Workflows
* UI components
* Public extension points

Core modifications should be reserved for capabilities that are genuinely fundamental to the platform.

---

### 3.6 Explicit operations

User-triggered operations should be represented explicitly rather than hidden inside UI callbacks.

A typical operation follows the conceptual path:

```
User
  ↓
Tool
  ↓
Command
  ↓
Application Service
  ↓
Domain
  ↓
State Change
  ↓
Event
  ↓
UI / Other Components
```

This architecture provides explicit boundaries for:

* Undo/redo
* Validation
* Transactions
* Logging
* Automation
* Workflow execution
* Testing
* Future AI integration

---

### 3.7 UI is not the domain

The user interface should not contain clinical rules or core computational logic.

UI components are responsible for:

* Presentation
* Interaction
* Input collection
* Visualization
* Tool activation
* State presentation

They should delegate actual operations to the Application and Domain layers.

---

### 3.8 Explicit architectural boundaries

Dependencies between architectural layers should be intentional and explicit.

Where a component requires an implementation supplied by another layer, the dependency should be represented through an appropriate contract or adapter rather than through direct coupling to an implementation.

CranioZ follows a **Ports and Adapters** approach where appropriate.

The Application layer may define ports for services such as:

* Persistence
* Project loading
* Project saving
* External computation
* Rendering integration
* Task execution
* Other replaceable infrastructure services

Infrastructure provides concrete adapters for those ports.

The Domain layer should remain independent of infrastructure implementations.

---

# 4. High-Level Architecture

The CranioZ architecture can be represented conceptually as follows:

```
┌───────────────────────────────────────────────────────────┐
│                         CranioZ                           │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐  │
│  │                       UI Layer                      │  │
│  │                                                     │  │
│  │  Areas · Views · Panels · Toolbars · Editors       │  │
│  └───────────────────────┬─────────────────────────────┘  │
│                          │                                │
│  ┌───────────────────────▼─────────────────────────────┐  │
│  │                  Application Layer                  │  │
│  │                                                     │  │
│  │ Commands · Services · Tasks · Flows · Events       │  │
│  │ State · Transactions · Application Ports            │  │
│  └───────────────────────┬─────────────────────────────┘  │
│                          │                                │
│  ┌───────────────────────▼─────────────────────────────┐  │
│  │                     Domain Layer                    │  │
│  │                                                     │  │
│  │ Objects · Anatomy · Geometry · Imaging · Planning  │  │
│  │ Scene · Project · Patient · Cephalometry · Units   │  │
│  └───────────────────────┬─────────────────────────────┘  │
│                          │                                │
│  ┌───────────────────────▼─────────────────────────────┐  │
│  │                 Infrastructure Layer                │  │
│  │                                                     │  │
│  │ VTK · ITK · DICOM · OCCT · CGAL · File I/O        │  │
│  │ Rendering · Persistence · External Services        │  │
│  │ Adapters · Platform Integration                    │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐  │
│  │                Modules / Plugins                    │  │
│  │                                                     │  │
│  │  Clinical capabilities and platform extensions      │  │
│  └─────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────┘
```

This diagram represents logical responsibilities rather than a strict runtime dependency graph.

Modules and plugins interact with the platform through defined contracts and extension points.

---

# 5. Core Architectural Layers

## 5.1 Domain

The `domain` layer contains the conceptual model of the CranioZ system.

It should be as independent as possible from:

* Qt
* VTK
* File formats
* Database implementations
* Operating-system APIs
* Rendering implementations
* External services

The domain may be divided into conceptual areas such as:

```
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
├── flow/
├── nodes/
├── units/
└── parametric_facial_model/
```

The Domain layer is responsible for representing meaningful system entities and their fundamental rules.

The Domain layer must not depend on UI, rendering, or infrastructure implementations.

---

## 5.2 Application

The `application` layer coordinates system operations and defines the execution boundaries of the application.

Typical responsibilities include:

* Commands
* Command execution
* Undo/redo
* Application services
* Tasks
* Event dispatch
* Workflow execution
* Application state
* Transaction boundaries
* Coordination between modules
* Validation orchestration
* Application ports

The Application layer should not become a second domain model.

Its primary responsibility is orchestration and coordination.

---

## 5.3 Infrastructure

The `infrastructure` layer contains technical implementations required by the system.

Examples include:

* DICOM access
* STL/OBJ import and export
* VTK integration
* ITK integration
* PyDicom
* NumPy integration
* Open CASCADE
* CGAL
* Rendering infrastructure
* Persistence
* Serialization
* Filesystem access
* External service integration
* Platform integration

Infrastructure implementations should be replaceable when practical.

For example, the Domain layer should not need to know whether a mesh is internally represented using VTK, OpenMesh, or another library.

Infrastructure adapters implement the contracts required by the Application layer and other appropriate architectural boundaries.

---

## 5.4 UI

The `ui` layer contains the graphical interface of CranioZ.

It is responsible for presenting application state and collecting user interaction.

The UI architecture is based on reusable interface regions rather than procedure-specific screens.

Conceptual UI elements include:

* Application Menu
* Home
* Modules
* Extras
* Areas
* Views
* Panels
* Toolbars
* Editors
* Scene tree
* Context panels
* Status and assistant areas

An `Area` is a structural region of the interface.

A bottom region, for example, is still an `Area`; its position does not define a separate architectural concept.

UI elements should consume application capabilities rather than directly implement domain operations.

---

# 6. Modules

A module represents a coherent functional capability of the CranioZ platform.

Modules are the principal unit for organizing clinical functionality.

Examples include:

* Patient
* Tomography
* Segmentation
* Registration
* Cephalometry
* Osteotomy
* Splint
* Airway
* Facial Analysis
* Implant Planning
* Osteosynthesis Design
* Surgical Guides
* Documents
* 2D Editor
* Animation
* Fibula Reconstruction

A module may provide:

* Tools
* Commands
* Services
* Data types
* Views
* Areas
* UI components
* Flows
* Capabilities

Modules should depend on stable platform contracts rather than on other modules' internal implementations.

The detailed Module Contract and Service Provider Interface (SPI) are defined separately.

---

# 7. Module Contract

Modules interact with the CranioZ platform through explicit contracts.

A module may expose or register:

```
Module
├── Module Specification
├── Lifecycle
├── State
├── Tools
├── Commands
├── Services
├── Data Types
├── Views
├── Flows
└── Capabilities
```

Not every module needs to provide every component.

The module contract should define:

* Module identity
* Lifecycle
* Dependencies
* Registration
* Public capabilities
* Extension points
* State ownership
* Resource management
* Compatibility requirements

The detailed contract is defined in a dedicated architectural document and ADR.

---

# 8. Flows

A `Flow` represents an ordered sequence of modules used to accomplish a particular task.

For example:

```
Orthognathic Planning
    ↓
Tomography
    ↓
Models
    ↓
Cephalometry
    ↓
Registration
    ↓
Osteotomy
    ↓
Splint
```

Flows provide orchestration rather than duplicating the functionality of modules.

A flow may define:

* Module order
* Required modules
* Optional modules
* Initial state
* Navigation
* Dependencies
* Workflow-specific configuration

The architecture should allow users or extensions to define custom flows.

---

# 9. Tools, Commands, Services, and Tasks

These concepts are deliberately separated.

## 9.1 Tool

A `Tool` is an operational capability exposed to the user.

It defines how an operation becomes available through the UI or another interaction mechanism.

Examples include:

* Import DICOM
* Create Landmark
* Register Models
* Perform Osteotomy
* Generate Splint
* Create Plate

A Tool does not necessarily contain the implementation of the operation itself.

---

## 9.2 Command

A `Command` represents an executable application operation.

Commands provide a suitable boundary for:

* Execution
* Undo
* Redo
* Validation
* Transaction participation
* Logging
* Automation

A Tool may invoke a Command.

The same Command may also be invoked by:

* Another module
* A workflow
* An automation system
* MCP
* Future AI agents

---

## 9.3 Service

A `Service` represents reusable application or domain functionality that does not naturally belong to a single entity.

Examples include:

* Registration service
* Segmentation service
* Mesh processing service
* Cephalometric calculation service
* Planning service

Services should have explicit contracts and avoid becoming unstructured collections of utility functions.

---

## 9.4 Task

A `Task` represents a potentially long-running operation managed by the Application layer.

Tasks provide a standard mechanism for operations that should not block the UI event loop.

A task may provide:

* Execution
* Progress reporting
* Cancellation
* Completion
* Error propagation
* Result delivery
* State reporting

The exact concurrency mechanism is an implementation detail and should not be imposed on individual modules.

---

# 10. Transactions and State Consistency

CranioZ performs operations that may modify multiple related domain objects.

For example:

```
Apply Osteotomy
    ├── Create osteotomy segments
    ├── Transform maxilla
    ├── Update relationships
    ├── Update planning state
    └── Generate or invalidate dependent objects
```

A failure during a multi-step operation must not leave the project in an invalid intermediate state.

The Application layer therefore defines transaction boundaries for state-changing operations.

A transaction represents a controlled unit of application state change.

Conceptually:

```
Command
  ↓
Transaction Boundary
  ↓
Domain Changes
  ↓
Infrastructure Operations
  ↓
Commit
  ↓
Events
```

If the operation cannot be completed successfully, the application should provide an appropriate rollback or recovery mechanism.

The exact implementation of transaction boundaries, Unit of Work, snapshots, and rollback is defined separately.

---

# 11. Concurrency and Long-Running Operations

CranioZ performs computationally intensive operations such as:

* Volumetric segmentation
* Surface registration
* Mesh processing
* Boolean operations
* Geometric reconstruction
* Image processing
* CAD operations
* Numerical calculations

Potentially long-running operations must not block the Qt/PySide6 UI event loop.

Python's Global Interpreter Lock (GIL) is not, by itself, the architectural reason for this requirement. Libraries such as VTK, ITK, and Open CASCADE execute substantial portions of their workloads in native code and may release the GIL during specific operations.

The architectural requirement is therefore:

> Potentially long-running operations must be executed outside the UI event loop.

The Application layer provides the standardized task execution mechanism.

A conceptual execution model is:

```
UI
 ↓
Tool
 ↓
Command
 ↓
Task
 ↓
Application Service
 ↓
Domain / Infrastructure
 ↓
Progress / Result / Error
 ↓
Event
 ↓
UI
```

The task system should support, where appropriate:

* Background execution
* Progress reporting
* Cancellation
* Error propagation
* Completion events
* Task state
* Result delivery
* Safe UI synchronization

Modules should not independently reinvent the concurrency model.

The detailed concurrency architecture is defined separately.

---

# 12. Scene and Rendering Architecture

CranioZ maintains a distinction between the domain-level scene model and its graphical representation.

The Domain `Scene` represents the semantic state of the project.

The visualization backend, such as VTK, represents that state graphically.

These representations must not become independent sources of truth.

The preferred relationship is:

```
Domain Scene
     │
     │ state changes
     ▼
Application Events
     │
     ▼
Visualization Adapter
     │
     ▼
VTK Scene / Render Window
```

The Domain model should not depend directly on VTK.

A visualization adapter or equivalent Infrastructure component translates domain state into renderer-specific representations.

For example:

```
AddObjectCommand
      ↓
Scene state changed
      ↓
ObjectAddedEvent
      ↓
Visualization Adapter
      ↓
VTK Actor created
      ↓
Render update
```

This architecture reduces coupling between the Domain and visualization infrastructure.

It also provides a clear mechanism for handling:

* Object creation and removal
* Visibility
* Selection
* Transformations
* Geometry updates
* Material and appearance changes

The VTK representation remains an implementation detail of the visualization infrastructure.

---

# 13. Event Architecture

CranioZ uses explicit commands and events to reduce coupling between components.

A simplified interaction is:

```
Tool
  ↓
Command
  ↓
Domain / Service
  ↓
State Change
  ↓
Event
  ↓
Subscribers
```

Commands express that something should happen.

Events communicate that something happened.

For example:

```
MoveMandibleCommand
```

requests an operation.

After successful execution:

```
MandibleMovedEvent
```

communicates that the operation occurred.

Events should not normally be used as hidden commands.

The Event Bus is an application communication mechanism and should not cause the Domain layer to become dependent on the UI or rendering system.

---

# 14. Data Architecture

CranioZ distinguishes between conceptual data models and technical data representations.

The system may work with:

* Volumes
* Meshes
* Images
* Landmarks
* Anatomical structures
* Teeth
* Surgical plans
* Osteotomies
* Plates
* Guides
* Patient information
* Project information

Technical representations may include:

* DICOM
* STL
* OBJ
* JSON
* Image arrays
* VTK data structures
* Open CASCADE structures

The Domain model represents the meaning of data independently from its persistence or visualization format whenever practical.

---

## 14.1 Objects and DataTypes

CranioZ distinguishes between general `Object` concepts and specific `DataType` definitions.

An `Object` provides common identity and metadata behavior.

A `DataType` defines a stable type recognized by the platform.

This mechanism supports:

* Type identification
* Serialization
* Registry-based discovery
* Module interoperability
* Plugin extensibility
* Persistence

The detailed data architecture is documented separately.

---

# 15. Persistence

CranioZ projects require a versioned semantic project representation.

The project representation should distinguish between:

* Semantic project metadata
* Object identity and relationships
* Configuration and state
* Large binary data
* Domain-specific data formats

JSON may be used for structured semantic project information, while specialized formats may be used for large or domain-specific data.

The persistence architecture must address:

* Schema versioning
* Migration between versions
* Stable object identifiers
* Backward compatibility
* Deterministic serialization
* Integrity of references
* Separation of metadata and large data
* Error recovery

The exact project storage format, directory structure, schema, and migration strategy are defined separately.

---

# 16. Dependency Architecture

CranioZ follows a Ports and Adapters approach where explicit boundaries are required.

The conceptual dependency direction is:

```
┌──────────────┐
│     UI       │
└──────┬───────┘
       ↓
┌──────────────┐
│ Application  │
│    Ports     │
└──────┬───────┘
       ↓
┌──────────────┐
│    Domain    │
└──────────────┘
```

Infrastructure provides concrete adapters for appropriate application or domain-facing contracts:

```
Application / Domain Contract
            ↑
            │
     Infrastructure
        Adapter
```

The exact ownership of a contract depends on its responsibility.

Domain abstractions should represent domain concepts.

Application ports should represent application-level dependencies.

Infrastructure should implement those contracts without exposing its implementation details to the Domain.

---

# 17. Plugin Architecture and API Stability

The plugin system provides controlled extensibility.

A plugin may provide one or more:

* Modules
* Tools
* Services
* Data types
* UI components
* Flows
* Capabilities
* Integrations

Plugins should communicate with the platform through public APIs and extension points.

Plugins should not depend on private implementation details of the core platform.

Public extension points should be explicitly identified and versioned.

These may include:

* Module contracts
* Tool contracts
* Command contracts
* Service interfaces
* DataType registration
* Flow definitions
* UI extension points
* Plugin manifests
* Event contracts
* Capability interfaces

The plugin system should distinguish between:

* **Public API** — supported for external use
* **Internal API** — private to the core implementation
* **Experimental API** — available for development but subject to change

Plugins should declare their compatibility requirements with the CranioZ API.

The detailed versioning strategy is defined separately.

---

# 18. Workspace and UI Composition

The workspace provides the environment in which modules and their UI components operate.

The UI is designed around interchangeable Areas and Views.

Conceptually:

```
Workspace
├── Header
├── Left Area
├── Central Area
├── Right Area
└── Bottom Area
```

Areas may host different views depending on the active module and context.

The bottom area is not a special architectural category. It is an `Area` positioned at the bottom of the workspace.

This allows the same architectural model to support different arrangements without introducing position-specific UI abstractions.

---

# 19. Clinical Semantics and Geometry

A fundamental architectural distinction is made between:

```
Geometry
```

and:

```
Clinical Meaning
```

For example:

```
Mesh
  ↓
Anatomical Structure
  ↓
Mandible
```

and:

```
Mesh
  ↓
Surgical Object
  ↓
Osteotomy Segment
```

The geometric representation may be shared, replaced, or transformed without changing the clinical concept.

This approach allows CranioZ to support multiple representations of the same clinical entity.

---

# 20. Observability and Auditability

CranioZ should provide structured mechanisms for diagnosing application behavior and recording relevant system activity.

Observability may include:

* Structured logging
* Error reporting
* Metrics
* Performance measurements
* Tracing where appropriate
* Diagnostic information

Observability should support:

* Development
* Debugging
* Performance analysis
* Reliability monitoring
* Support

Observability should be distinguished from clinical or security auditing.

Audit mechanisms may record relevant information such as:

* Actor
* Timestamp
* Action
* Affected object or project
* Operation result

Audit requirements depend on the deployment context and applicable regulatory requirements.

---

# 21. Security and Compliance

CranioZ may process patient-related information and must therefore provide architectural mechanisms for protecting sensitive data.

Security considerations include:

* Authentication
* Authorization
* Access control
* Data protection
* Encryption in transit
* Encryption at rest where appropriate
* Secure storage
* Secure data exchange
* Auditability
* Sensitive-data handling
* Dependency and supply-chain security

Regulatory requirements depend on the deployment context, jurisdiction, intended use, and regulatory classification of the software.

The architecture should therefore provide mechanisms that can support applicable requirements without assuming that a single regulatory framework applies to every deployment.

Relevant frameworks may include, depending on context:

* LGPD
* Applicable ANVISA requirements
* HIPAA
* MDR and other medical-device regulations

Security and regulatory requirements should be documented separately from the general architectural overview.

---

# 22. Automation and MCP

Automation is considered an extension of the existing application architecture rather than a separate execution model.

An external agent should interact with CranioZ through the same explicit capabilities available to the application.

Conceptually:

```
AI / MCP
    ↓
Tool / Command / Service
    ↓
Application
    ↓
Domain
    ↓
State
```

Operations exposed to automation should provide:

* Explicit contracts
* Input validation
* Deterministic behavior where possible
* Error reporting
* Permission boundaries
* Undo/rollback where appropriate

AI should not bypass the Application and Domain layers to directly manipulate internal objects.

---

# 23. Testing and Validation

Testing should follow architectural boundaries and account for the numerical and geometric nature of the system.

## 23.1 Domain Tests

Validate:

* Domain entities
* Domain rules
* Clinical semantics
* Mathematical calculations
* Invariants

---

## 23.2 Application Tests

Validate:

* Commands
* Services
* Tasks
* Flows
* Events
* State transitions
* Transaction boundaries

---

## 23.3 Infrastructure Tests

Validate:

* File I/O
* DICOM handling
* Serialization
* External library adapters
* Rendering integration
* Persistence

---

## 23.4 UI Tests

Validate:

* User interaction
* View behavior
* Tool presentation
* Workspace composition
* UI state synchronization

---

## 23.5 Geometric and Numerical Validation

Geometric and numerical operations require tests that validate properties of the resulting data rather than only execution success.

Examples include:

* Mesh validity
* Watertightness
* Manifoldness
* Surface area
* Volume
* Normal orientation
* Topological invariants
* Distance tolerances
* Transformation accuracy
* Landmark preservation
* Registration error
* Numerical stability

Where appropriate, the test suite should use:

* Property-based tests
* Geometric invariants
* Numerical tolerance checks
* Reference datasets
* Regression datasets
* Golden/reference results
* Visual regression testing

Tests should distinguish between exact equality and tolerance-based numerical equivalence.

---

# 24. Architectural Boundaries

The following boundaries should be preserved:

| Boundary               | Principle                                                         |
| ---------------------- | ----------------------------------------------------------------- |
| Domain ↔ UI            | Domain must not depend on UI                                      |
| Domain ↔ Qt            | Domain should not depend on Qt                                    |
| Domain ↔ VTK           | Domain should not depend directly on VTK                          |
| Application ↔ UI       | UI invokes application capabilities rather than implementing them |
| Module ↔ Core          | Modules use public platform contracts                             |
| Module ↔ Module        | Prefer explicit contracts over internal access                    |
| Plugin ↔ Core          | Plugins use public extension points                               |
| Persistence ↔ Domain   | Persistence is an implementation concern                          |
| Rendering ↔ Domain     | Rendering state is derived from semantic application state        |
| AI/MCP ↔ Core          | AI uses explicit application capabilities                         |
| Long-running Work ↔ UI | Computational tasks must not block the UI event loop              |

These boundaries are guidelines for maintaining architectural integrity and should not result in unnecessary abstraction.

---

# 25. Architectural Invariants

The following invariants should guide implementation:

1. The UI event loop must remain responsive.
2. Potentially long-running operations must use the Application task mechanism.
3. The Domain layer must not depend on Qt, VTK, or infrastructure implementations.
4. The Domain `Scene` is the semantic source of truth for scene state.
5. Renderer-specific state must be derived from or synchronized with application/domain state.
6. Multi-step state-changing operations must have explicit transaction boundaries.
7. Modules must use standardized application mechanisms for long-running operations.
8. Plugins must use public extension points rather than internal implementation details.
9. Public plugin APIs must be versioned and compatibility must be explicit.
10. Events communicate state changes and should not become hidden execution mechanisms.
11. Persistence must support schema evolution and migration.
12. Numerical and geometric operations must be validated using appropriate tolerances and invariants.
13. Security-sensitive operations must have explicit authorization boundaries.
14. Clinical or audit-relevant actions should be traceable where required by the deployment context.
15. Rendering infrastructure must remain replaceable without redefining the domain model.

---

# 26. Project Structure

The high-level repository structure is:

```
cranioz/
├── .github/
├── src/
│   └── cranioz/
│       ├── domain/
│       ├── application/
│       ├── infrastructure/
│       ├── ui/
│       ├── settings/
│       ├── assets/
│       └── modules/
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

This structure separates the platform source code from external plugins, tests, documentation, examples, and development utilities.

---

# 27. Architectural Evolution

The architecture is intentionally designed to evolve.

Early versions should prioritize:

1. Stable domain concepts
2. Core object and DataType infrastructure
3. Application command model
4. Module contracts
5. UI workspace infrastructure
6. Basic persistence
7. Task execution infrastructure
8. Essential clinical modules
9. Validation and testing infrastructure

More advanced capabilities can be introduced progressively:

* Custom workflow editors
* Advanced CAD operations
* Parametric facial models
* Finite element analysis
* AI-assisted segmentation
* AI-assisted planning
* MCP integration
* Advanced automation
* Third-party plugin ecosystems

Architectural evolution should favor incremental changes over large-scale rewrites.

Changes to public contracts should be explicitly documented and versioned.

---

# 28. Architecture Decision Records

Specific architectural decisions should be documented separately under:

```
docs/architecture/adr/
```

The architecture is expected to have ADRs addressing, among others:

* Programming language and runtime
* UI framework
* Dependency architecture and Ports & Adapters
* Application transaction boundaries
* Unit of Work and rollback strategy
* Concurrency and task execution
* Module Contract / SPI
* Plugin API and versioning
* DataType registry
* Command architecture
* Event system
* Scene and rendering synchronization
* Persistence format
* Project schema versioning and migration
* Dependency policy
* Rendering architecture
* Workflow architecture
* Observability
* Security and auditability
* Geometric and numerical validation
* MCP integration

The `overview.md` describes the architectural structure and principles.

The ADRs explain why specific architectural decisions were made.

---

# 29. Summary

CranioZ is structured as an extensible clinical software platform rather than as a monolithic surgical-planning application.

Its architecture separates:

```
Clinical Concepts
      ↓
Application Operations
      ↓
Technical Infrastructure
      ↓
User Interface
```

while allowing clinical functionality to be composed through:

```
Modules
    +
Tools
    +
Commands
    +
Services
    +
Tasks
    +
Flows
    +
Plugins
```

The architecture provides explicit mechanisms for:

* State management
* Transaction boundaries
* Long-running operations
* Scene/rendering synchronization
* Persistence and schema evolution
* Module and plugin extensibility
* Observability
* Security
* Geometric and numerical validation
* Automation

The central architectural objective is to provide a stable and reusable platform in which new cranio-maxillofacial capabilities can be developed independently without compromising the integrity of the core system.

The architecture therefore favors explicit contracts, clear responsibilities, modularity, extensibility, controlled state changes, numerical robustness, and reuse of mature computational libraries.
