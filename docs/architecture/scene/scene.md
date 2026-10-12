# Scene

## 1. Overview

A **Scene** represents the spatial organization and state of domain
objects within a specific planning context in CranioZ.

The Scene is a **domain-level concept**, independent of UI, rendering
engine, viewport implementation, and visualization framework.

The Scene defines:

- object membership;
- spatial hierarchy;
- spatial relationships;
- object transforms;
- reference frames;
- the coordinate system.

The Scene does **not** own the lifecycle of domain objects.

> **The Scene does not own domain objects. It owns the spatial
> organization of objects within a specific planning context.**

A domain object represents **what** an object is.
A Scene represents **where** it exists and **how** it relates to other
objects.
A rendering representation represents **how** it is visualized.
Domain Object ≠ Scene ≠ Rendering Actor ≠ Viewport

text

---

## 2. Architectural Role

The Scene belongs to the Domain layer. 

    ┌──────────────────────────────────────────┐
    │ UI │
    │ Areas · Editors · Toolbars · Overlays │
    └──────────────────┬───────────────────────┘
    │
    ┌──────────────────▼───────────────────────┐
    │ Application │
    │ Tools · Commands · Services · Flows │
    │ Transactions · Event Coordination │
    └──────────────────┬───────────────────────┘
    │
    ┌──────────────────▼───────────────────────┐
    │ Domain │
    │ Project │
    │ ├── DomainObjectStore │
    │ └── Scenes │
    │ ├── Membership │
    │ ├── Hierarchy │
    │ ├── Transforms │
    │ └── Relationships │
    └──────────────────┬───────────────────────┘
    │
    ┌──────────────────▼───────────────────────┐
    │ Infrastructure │
    │ DICOM · VTK · ITK · OCCT · Storage │
    │ Rendering Adapters · Spatial Indexes │
    └──────────────────────────────────────────┘


The UI layer is composed of Areas (structural containers), Editors (functional units hosted in Areas), Toolbars (internal to Editors, see ADR-0002), and Overlays (floating layers managed by the Workspace).
See ADR-0001 for the relationship between Area and Editor.

A **View** is a visual representation of an aspect of the Scene. It is rendered by a **Viewport**, hosted by an **Editor**, hosted by an **Area**. The Scene does not know about Viewports or Views.

---

## 3. Project and Scene Context

A Scene always belongs to a **Project**, which provides the persistent
boundary.

    Project
    ├── DomainObjectStore
    └── Scenes
    ├── Scene A
    ├── Scene B
    └── ...

The Project is responsible for the complete persistent planning context.
The Scene is responsible only for its spatial context.


## 4. DomainObjectStore

The **DomainObjectStore** is the canonical registry and lifecycle
authority for domain objects belonging to a Project.

    Project
    └── DomainObjectStore
    ├── Maxilla
    ├── Mandible
    ├── Tooth 11
    ├── Tooth 21
    ├── CT Volume
    └── Surgical Splint


The DomainObjectStore is **Project-scoped**, not application-global.

This provides:

- isolation between Projects;
- deterministic object identity;
- explicit lifecycle boundaries;
- straightforward persistence;
- prevention of cross-Project references.

The detailed contract is defined separately.

---

## 5. Scene and DomainObjectStore

The Scene references objects belonging to the DomainObjectStore of the
same Project.

    Project
    ├── DomainObjectStore
    │ ├── Maxilla
    │ ├── Mandible
    │ └── Splint
    │
    └── Scene
    ├── object_id → Maxilla
    ├── object_id → Mandible
    └── object_id → Splint


The Scene does not create canonical copies.

> **While an object is a member of a Scene, its object ID must resolve
> to a valid domain object in the Project's DomainObjectStore.**

This invariant must hold throughout the lifetime of the Scene.

---

## 6. Ownership vs. Membership

**Ownership** and **membership** are distinct concepts.

**Object ownership.** The DomainObjectStore owns the canonical lifecycle.
Import CT → Create Volume Object → Register in DomainObjectStore → Add to Scene


**Scene membership.** A domain object participates in the spatial context
of a Scene. Membership does not transfer ownership.

    Scene
    ├── Maxilla
    ├── Mandible
    └── Splint

The Scene maintains references through stable identities.

---

## 7. Membership Integrity

Every membership reference must resolve to a valid object in the
DomainObjectStore.
Scene Membership → DomainObjectStore.get(object_id) → Valid Domain Object


The Scene must never intentionally contain dangling references.

---

## 8. Object Removal vs. Membership Removal

**Remove membership.**
Scene.remove_object(object_id)



Removes spatial membership. The domain object remains in the
DomainObjectStore.

**Remove object from Project.**
DomainObjectStore.remove(object_id)


Removes the canonical domain object.

An object must not be removed from the DomainObjectStore while it is a
member of any Scene in the same Project.

    Remove Object from Project
    ↓
    Check Scene Memberships
    ↓
    ┌────┴────┐
    Exists None
    │ │
    ▼ ▼
    Reject Remove


The Application Core coordinates this operation.

---

## 9. Scene Core

The Scene Core contains the fundamental spatial state:

- Scene identity;
- metadata;
- object membership;
- coordinate-system definition;
- spatial hierarchy;
- transforms;
- spatial relationships;
- persistent reference-frame associations.

The Scene Core must remain deliberately small. It must not become a general-purpose container for Project state.

---

## 10. Spatial Hierarchy

Spatial hierarchy represents parent-child relationships that affect spatial interpretation.

    Mandible
    ├── Left Segment
    └── Right Segment
or:

    Patient Reference
    ├── Maxilla
    └── Mandible

Hierarchy is part of the Scene's spatial domain state.

---

## 11. Parent-Child Rules

An object may have **at most one parent within a given Scene**.

    Scene
    └── Mandible
    ├── Left Segment
    └── Right Segment


Conceptual operations:

    set_parent()
    get_parent()
    iter_children()


The hierarchy must not contain cycles.

The parent relationship belongs to the Scene, not to the domain object.
The same object may participate in different Scenes with different
parents.

    Scene A Scene B
    └── Mandible └── Osteotomy Reference
    └── Segment └── Segment

Only the spatial organization changes.

---

## 12. Transform Composition

    Parent-child hierarchy provides a basis for transform composition.
    Scene → Mandible → Left Segment

    T_scene_segment = T_scene_mandible · T_mandible_segment



For deeper hierarchies:

    T_scene_object = T_scene_parent · T_parent_child · T_child_object

The exact mathematical representation belongs to the geometry layer. Scene depends on domain-level transformation abstractions, not directly on NumPy, VTK, or OCCT.

---

## 13. Spatial Relationships

Not every relationship is parent-child hierarchy.

    SpatialRelationship
    ├── source
    ├── target
    ├── type
    ├── directed
    └── data


Examples:

    Registration(CT, IOS)
    AttachedTo(Plate, Mandible)
    DerivedFrom(OsteotomySegment, Mandible)


The Scene provides the spatial context. The algorithms that establish relationships belong to domain or application services.

---

## 14. Relationship Cardinality

A relationship type defines its own semantic constraints.

A relationship may be:

- directed or symmetric;
- unique or non-unique;
- one-to-one, one-to-many, many-to-many.

These properties must be defined by the relationship type.

Duplicate relationships should not be silently created.

---

## 15. Relationship Lifecycle

Relationships cannot reference objects that are not valid Scene members.

> **A Scene must not retain an active relationship whose required
> object references are no longer valid Scene members.**

Relationship cleanup is part of the Scene's structural integrity.

---

## 16. Coordinate System

Each Scene defines a global coordinate system.

- Units: **millimetres (mm)**.
- Handedness, axis orientation, and origin convention must be defined.

The exact anatomical convention is a project-wide geometry decision, defined separately in the geometry documentation and corresponding ADR.

---

## 17. Scene Origin and Reference Frames

The Scene origin represents the global technical reference frame.

It must not be confused with clinically meaningful anatomical reference
frames.

    Scene Coordinate System
    ├── Patient Reference Frame
    ├── Cranial Reference Frame
    ├── Maxillary Reference Frame
    └── Mandibular Reference Frame

A reference frame with persistent identity and clinical meaning may be a domain object. A transient mathematical frame may exist only as
temporary state.

---

## 18. Object Transforms

Objects may have local coordinate systems and transforms into Scene space.
Local Object Coordinates → Transform → Scene Coordinate System


The Scene maintains the resulting spatial state.

---

## 19. Rigid Transformations

Rigid transformations are first-class Scene operations.

Appropriate for:

- bone segments;
- dental models;
- implants;
- plates;
- splints;
- surgical guides;
- reference objects.

A rigid transform preserves distances, angles, and topology.

The Scene uses a validated domain-level rigid transformation type.

---

## 20. Deformable Transformations

Deformable transformations are separate from rigid Scene transforms.
    
    Base Geometry
    ├── Rigid Transform
    └── Deformation Field



A deformation field may be represented by displacement fields,
deformation fields, morph targets, facial rigs, or other domain-specific
models.

The deformation representation belongs to the domain object, not to the
Scene.

---

## 21. Registration

Registration establishes spatial correspondence between coordinate
systems.

    CT
    │ T_ct_to_scene
    ▼
    Scene
    ▲ T_ios_to_scene
    │
    IOS

Registration algorithms belong to domain services, application services, or infrastructure-backed algorithms.

The Scene stores the resulting transformation and/or spatial relationship.

---

## 22. Derived Objects

Some objects are derived from others.

    CT → Segmentation → Bone Mesh
    
    Mandible → Osteotomy → Osteotomy Segment
    
    CT + Facial Scan → Registration → Facial Model


Derived relationships support reproducibility, dependency tracking, invalidation, regeneration, and persistence.

The application/module layer performs the operation. The Scene maintains spatial organization and relevant relationships.

---

## 23. Measurements

Measurements are interpreted within the Scene coordinate system unless
associated with another reference frame.

    Distance(PointA, PointB) → mm


Measurement algorithms remain separate domain services.

---

## 24. Rendering Independence

The Scene is completely independent of the rendering engine.

It must not contain `vtkActor`, `vtkRenderer`, `vtkMapper`, cameras,
lights, OpenGL state, or viewport objects.

The **Editor** consumes Scene state via `SceneQuery` (read-only). The
**Rendering Adapter** creates visual representations (Views) inside
Viewports.

    Scene → Editor (SceneQuery) → Rendering Adapter → Viewport → View


The Scene does not know about Viewports, Views, or Editors.

---

## 25. Rendering Representation

A domain object and its visual representation are separate entities.

    Mandible (domain object)
    │
    ├── Viewport3DEditor
    │ └── Viewport → View: surface representation
    │
    ├── MPRViewerEditor
    │ └── Viewport → View: contour/intersection
    │
    └── PlanningEditor
    └── Viewport → View: translucent surface

The same domain object may have different Views in different Viewports,
hosted by different Editors.

---

## 26. Rendering Adapter

The Rendering Adapter bridges domain/application state and rendering
infrastructure. A VTK implementation may contain:

- `VTKActorFactory` — converts domain representations into VTK objects.
- `ActorRegistry` — maps object IDs to rendering actors.
- `VTKSceneRenderer` — manages the VTK rendering context.
- `SceneBridge` — synchronizes Scene events with rendering representations.

These components belong to Infrastructure/UI integration, not the Domain
layer. The Scene remains unaware of them.

---

## 27. Presentation State

Presentation concerns include color, opacity, visibility, selection,
representation mode, shading, and rendering style.

These are not Scene properties. The same Scene object may have different
presentation states in different Viewports.

---

## 28. Membership vs. Visibility
Scene membership ≠ Viewport visibility

text

An object can remain a Scene member while hidden in one or more
Viewports. This supports multiple Areas and Viewports without modifying
domain state.

---

## 29. Selection

Selection is an Application/UI concern. The Scene does not know which
object is currently selected. Selection state remains outside the Scene
Core.

---

## 30. Temporary and Preview Objects

Temporary objects include cutting planes, boolean operands, collision
proxies, registration markers, preview osteotomies, temporary splints,
simulation results, and construction geometry.

Temporary objects should not automatically become persistent Project
objects. Only objects intended to become part of the persistent domain
model are registered in the DomainObjectStore.

---

## 31. Scene API

Conceptual operations:

**Core:**

    add_object()
    remove_object()
    contains()
    get_object()
    iter_objects()
    get_transform()
    set_transform()


**Graph:**

    set_parent()
    get_parent()
    iter_children()
    iter_subtree()


**Relationship:**

    add_relationship()
    remove_relationship()
    get_relationships()
    iter_relationships()

The API must remain independent of rendering frameworks.

---

## 32. Scene Invariants

- **Unique identity** — object identity is unique within the Project's
  DomainObjectStore.
- **Valid membership** — every membership reference resolves to a valid
  object.
- **No dangling membership** — the Scene never retains membership for a
  removed object.
- **Valid hierarchy** — no cycles; at most one parent per object per Scene.
- **Valid relationships** — required endpoints resolve to valid objects.
- **Valid transforms** — mathematically valid and using the Scene's
  coordinate conventions.
- **Consistent units** — mm.

---

## 33. Commands and Scene Mutations

Scene mutations should occur through Application Commands.

Examples: `AddObject`, `RemoveObjectFromScene`, `RemoveObjectFromProject`,
`SetParent`, `TransformObject`, `AddRelationship`, `RemoveRelationship`,
`ApplyRigidMovement`.
Tool → Command → Application Service → DomainObjectStore / Scene → Events

text

This provides validation, transactions, undo/redo, event publication,
and auditability.

---

## 34. Transactions

Complex planning operations may modify multiple objects and Scene state.

    Apply Le Fort I Movement


may affect the maxillary segment, dental model, cephalometric landmarks,
and surgical splint.

Such operations are coordinated by the Application Core as a single logical transaction.

The Scene does not own transaction orchestration. It provides a state model that allows the Application Core to capture and restore the
relevant state.

---

## 35. Transaction and Computation Snapshots

**Transaction snapshot** — optimized for rollback. Contains only the state necessary to restore the affected logical Scene state: membership, hierarchy, transforms, relationships, relevant domain state.

Large geometry payloads should not be unnecessarily duplicated. If a transaction modifies object content (e.g., a recalculated mesh), the snapshot must include enough information to restore it. Immutable
payloads may be shared by reference.

**Computation snapshot** — provides stable input to asynchronous processing. Contains geometry, volume data, landmarks, transforms, and relevant metadata.

Requirements: stable read access, immutability, safe use by worker threads, efficient transfer or sharing.

The two snapshot mechanisms may share infrastructure but have different contracts.

---

## 36. Transaction Rollback Example

    Apply Le Fort I Movement
    ↓
    Transaction Started
    ↓
    Transform Maxillary Segment
    ↓
    Update dependent spatial state
    ↓
    Generate / Update Splint
    ↓
    Validate Splint
    ↓
    Validation Failed
    ↓
    Transaction Rolled Back
    ↓
    Restore Previous State


The rendering layer receives the resulting committed state.

---

## 37. Scene Events

Meaningful Scene state changes generate semantic events:

    ObjectAdded
    ObjectRemovedFromScene
    ObjectTransformed
    ParentChanged
    RelationshipAdded
    RelationshipRemoved


Events describe semantic state changes, not UI interactions. `ObjectTransformed` is a domain event. `MouseDragged` is not.

A generic `SceneChanged` event is intentionally avoided.

---

## 38. Event Semantics

**State information.** A state-change event provides sufficient
information for observers to determine what changed.

    ObjectTransformed
    ├── object_id
    ├── previous_transform
    └── new_transform


**Transaction boundaries.** Events generated during a transaction are
not interpreted as committed state until the transaction commits.

    TransactionStarted
    TransactionCommitted
    TransactionRolledBack

**Deterministic ordering.** Within a committed transaction, event
ordering is deterministic. Observers are independent. No observer may
depend on another observer having processed an event first.

If one operation genuinely depends on another, that dependency must be
expressed explicitly in the Application layer.

---

## 39. Spatial Indexing

The Scene does not directly manage spatial indexing or rendering performance. It supports external spatial services: spatial indexes, bounding-volume hierarchies, collision detection, nearest-neighbor
queries, proximity queries, intersection queries, region-of-interest queries.

    Scene
    ├── ObjectAdded
    ├── ObjectRemoved
    └── ObjectTransformed
    ↓
    SpatialIndexService
    ↓
    Spatial Index



The Scene remains independent of the concrete indexing implementation.

---

## 40. Spatial Observers

Infrastructure and Application services may observe Scene events:
`SpatialIndexService`, `RenderingAdapter`, `MeasurementCache`,
`CollisionService`, `DependencyTracker`.

Observers maintain derived state. They do not acquire ownership.

Authoritative state remains in `DomainObjectStore + Scene`.

---

## 41. Concurrency and Threading

The Scene is **application-thread confined by default**.

Domain mutations occur through the Application Core on the designated application thread. Worker threads must not mutate the live Scene.

Long-running operations (segmentation, registration, mesh processing, collision computation, deformation simulation) operate on stable computation snapshots.
    
    Application Thread → Scene → Computation Snapshot → Worker Thread
    ↓
    Processing
    ↓
    Result / Command
    ↓
    Application Thread ← Scene ←──── commit ──────────────────┘


When concurrent access is required, immutable snapshots or explicitly
defined read models should be used.

---

## 42. Serialization

Scene state is serialized as part of the Project format.

Preserved:

- Scene identity;
- metadata;
- coordinate-system definition;
- object membership;
- hierarchy;
- transforms;
- spatial relationships;
- persistent reference-frame associations;
- persistent derived-object relationships.

Large binary assets are managed separately.

    Scene Data Assets
    ├── Object IDs      ├── DICOM
    ├── Hierarchy       ├── STL
    ├── Transforms      ├── OBJ
    ├── Relationships   └── other binary data
    └── Asset References

---

## 43. Serialization References

Scene deserialization resolves references between the Project's
DomainObjectStore and its Scenes.

The deserializer must reject or explicitly handle:

- missing object references;
- invalid hierarchy references;
- invalid relationship endpoints;
- unsupported schema versions;
- missing required assets.

For backward compatibility, the deserializer may apply schema migrations
before resolving references. Migration policies belong to the Project
serialization specification.

---

## 44. Multiple Scenes

A Project may contain multiple Scenes.

    Project
    ├── DomainObjectStore
    └── Scenes
    ├── Initial State
    ├── Surgical Plan
    ├── Simulation
    └── Comparison



Different Scenes may contain different memberships, hierarchies, transforms, and relationships while referencing the same objects.

For example, a Mandible may be a member of both an "Initial State" Scene and a "Surgical Plan" Scene, with different transforms in each. The DomainObjectStore owns the canonical Mandible; each Scene owns its own spatial organization of that Mandible.

The concept of an **active Scene** is application/UI state.

---

## 45. Scene and Flows

A Flow may operate on one or more Scenes.

    Orthognathic Flow
    ├── Tomography
    ├── Models
    ├── Cephalometry
    ├── Registration
    ├── Osteotomy
    └── Splint



The Flow orchestrates operations. The Scene provides the spatial state.
The Scene does not know which Flow is executing.

---

## 46. Scene and Modules

Modules create, modify, or consume Scene state through Application Commands and Services.

    Segmentation Module → Create Bone Object → DomainObjectStore → Add to Scene

    Osteotomy Module → Create Osteotomy Segment → DomainObjectStore → Add to Scene Hierarchy
    → Apply Transform


Modules must not bypass the Domain/Application boundaries by directly
manipulating rendering actors.

---

## 47. Example: Orthognathic Planning

    Scene (membership references to the DomainObjectStore)
    │
    ├── CT Volume
    ├── Maxilla
    ├── Mandible
    ├── Upper Dental Model
    ├── Lower Dental Model
    ├── Cephalometric Landmarks
    ├── Osteotomy Segments
    ├── Surgical Splint
    └── Reference Geometry


The Scene members are references to objects in the DomainObjectStore. The Scene does not duplicate them; it organizes them spatially.

    DomainObjectStore Scene
    ├── Mandible └── Mandible
    ├── Left Segment ├── Left Segment
    ├── Right Segment └── Right Segment
    └── Splint

---

## 48. Example: Composed Segment Movement
    
    Scene → Mandible
    ├── Left Segment
    └── Right Segment

    T_scene_left_segment = T_scene_mandible · T_mandible_left_segment


After surgical simulation:

    Left Segment → Transform = T_left
    Right Segment → Transform = T_right

The planning service calculates the transforms. The Scene maintains the resulting configuration. The rendering adapter observes the committed
state.

---

## 49. Example: Registration

    CT
    │ T_ct_to_scene
    ▼
    Scene
    ▲ T_ios_to_scene
    │
    IOS

The registration service calculates the transformation. The Scene stores the resulting spatial relationship. The rendering system displays both datasets in the same spatial context, without either domain object becoming dependent on VTK.

---

## 50. Example: Multiple Views

The same Scene may be consumed by multiple Editors, each hosting one or
more Viewports that render different Views of the Scene.

    Scene (spatial state)
    │
    ├── Viewport3DEditor
    │ └── Viewport → View: 3D representation
    │
    ├── MPRViewerEditor
    │ ├── Viewport → View: Axial slice
    │ ├── Viewport → View: Sagittal slice
    │ └── Viewport → View: Coronal slice
    │
    └── CurvedMPREditor
    └── Viewport → View: Panoramic reconstruction

Each Viewport may have its own camera, projection, orientation, visibility, representation mode, and selection.

These are not properties of the Scene Core.

All Viewports derive spatial information from the same Scene state. The Scene does not know which Viewports exist.

---

## 51. Example: Rendering Synchronization

**When an object is added:**

    AddObject
    ↓
    DomainObjectStore
    ↓
    Scene.add_object()
    ↓
    ObjectAdded
    ↓
    SceneBridge
    ↓
    VTKActorFactory → ActorRegistry → VTKSceneRenderer


**When an object is transformed:**

    TransformObject
    ↓
    Scene.set_transform()
    ↓
    ObjectTransformed
    ↓
    SceneBridge → Update vtkActor transform


The rendering system reacts to committed state.

---

## 52. Example: Spatial Index Synchronization

    ObjectAdded
    ↓ SpatialIndexService → Insert Object
    
    ObjectTransformed
    ↓ SpatialIndexService → Update Bounds
    
    ObjectRemovedFromScene
    ↓ SpatialIndexService → Remove Object


The Scene remains unaware of the concrete spatial-index implementation.

---

## 53. Reproducibility

The Scene should be deterministic enough to reconstruct the logical spatial planning state from serialized Project data.

Given `Project Data + Scene Data + Referenced Assets`, CranioZ should reconstruct the same logical spatial configuration.

This supports research reproducibility, planning review, collaboration, version control, automated testing, auditability, and Project migration.

---

## 54. What Scene Must Not Do

The Scene must not be responsible for:

- rendering;
- VTK actors, cameras, lights;
- layout (Area Layout Tree or Editor Layout Tree);
- UI selection;
- dock behavior;
- toolbar state (see ADR-0002);
- mouse interaction, keyboard shortcuts;
- DICOM or STL/OBJ loading;
- mesh processing algorithms;
- segmentation algorithms;
- registration algorithms;
- cephalometric calculations;
- surgical planning algorithms;
- persistence infrastructure;
- plugin discovery;
- module lifecycle management;
- rendering actor management;
- global Project object lifecycle.

These responsibilities belong to other architectural layers:

- **Editors** own their Toolbars and Toolbar state (ADR-0002).
- **Areas** own their Editors and their internal Editor Layout Tree
  (ADR-0001).
- **Workspace** owns the Area Layout Tree and Overlays.
- **Application Core** owns Commands, Transactions, and Services.
- **Infrastructure** owns Rendering Adapters, DICOM loading, and
  Spatial Indexes.

---

## 55. Architectural Summary

The Scene is the domain-level spatial context of CranioZ.
Spatial Membership + Spatial Hierarchy + Transforms

Spatial Relationships + Coordinate System + Reference Frames

Spatial State

text

The Project provides the persistent boundary.

The DomainObjectStore provides canonical object identity and lifecycle.

The Application layer provides Commands, Transactions, Services, Flows,
and Event Coordination.

Infrastructure implements Application ports (RenderingPort,
PersistencePort, ExternalComputationPort). The Scene does not depend on
Infrastructure implementations.
    
    ┌──────────────────────────────────────────┐
    │ Project                                  │
    │ ┌──────────────────┐ ┌─────────────────┐ │
    │ │ DomainObjectStore│ │ Scenes          │ │
    │ │ Canonical Objects│ │ Membership      │ │
    │ │ Identity         │ │ Hierarchy       │ │
    │ │ Lifecycle        │ │ Transforms      │ │
    │ │                    │ │ Relationships │ │
    │ └────────┬─────────┘ └────────┬────────┘ │
    └───────────┼─────────────────────┼────────┘
    │            │
    └──────────┬──────────┘
    │
    Commands / Events / Transactions
    │
    ▼
    ┌─────────────────────┐
    │ Application Core    │
    │ Commands            │
    │ Transactions        │
    │ Services            │
    │ Flows               │
    └──────────┬──────────┘
                │
                ▼
    ┌─────────────────────┐
    │ Infrastructure      │
    │ Rendering Adapter   │
    │ Spatial Index       │
    │ Persistence         │
    └─────────────────────┘

The fundamental separation:

    DomainObjectStore → owns canonical domain object lifecycle
    Scene → owns spatial organization within a planning context
    Application Core → owns orchestration, commands, and transactions
    Rendering Adapter → translates domain state into visual representations
    Viewport → presents a View of the Scene
    Editor → hosts Viewports and Toolbars
    Area → hosts Editors
    Workspace → hosts Areas and Overlays

This separation provides CranioZ with a modular, multi-Scene, rendering-independent spatial architecture suitable for clinical planning, simulation, visualization, and future extensions.