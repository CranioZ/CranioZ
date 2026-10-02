# Scene

## 1. Overview

A **Scene** represents the spatial organization and state of domain objects within a specific planning context in CranioZ.

The Scene is a **domain-level concept**. It is independent of the user interface, rendering engine, viewport implementation, and visualization framework.

The Scene defines:

* object membership;
* spatial hierarchy;
* spatial relationships;
* object transforms;
* reference frames associated with the spatial context;
* the coordinate system used to interpret spatial state.

The Scene does **not** own the lifecycle of domain objects.

The fundamental architectural principle is:

> **The Scene does not own domain objects. It owns the spatial organization of objects within a specific planning context.**

A domain object represents **what an object is**.

A Scene represents **where that object exists and how it is spatially related to other objects**.

A rendering representation represents **how that object is visualized**.

A viewport represents **how the user sees and interacts with that representation**.

Therefore:

```
Domain Object
    ≠
Scene
    ≠
Rendering Actor
    ≠
Viewport
```

---

# 2. Architectural Role

The Scene belongs to the Domain layer and participates in the following architecture:

```
┌────────────────────────────────────────────┐
│                     UI                     │
│ Areas · Viewports · Panels · Interaction  │
└──────────────────────┬─────────────────────┘
                       │
                       ▼
┌────────────────────────────────────────────┐
│                Application                 │
│ Tools · Commands · Services · Flows        │
│ Transactions · Event Coordination          │
└──────────────────────┬─────────────────────┘
                       │
                       ▼
┌────────────────────────────────────────────┐
│                   Domain                  │
│                                            │
│ Project                                    │
│ ├── DomainObjectStore                      │
│ └── Scenes                                 │
│      ├── Membership                        │
│      ├── Hierarchy                         │
│      ├── Transforms                        │
│      └── Relationships                     │
│                                            │
└──────────────────────┬─────────────────────┘
                       │
                       ▼
┌────────────────────────────────────────────┐
│              Infrastructure               │
│ DICOM · VTK · ITK · OCCT · Storage         │
│ Rendering Adapters · Spatial Indexes       │
└────────────────────────────────────────────┘
```

The Scene is therefore domain state that is manipulated through the Application layer and consumed by Infrastructure and UI components.

---

# 3. Project and Scene Context

A Scene always belongs to a **Project**.

The Project provides the persistent boundary within which domain objects and Scenes exist.

Conceptually:

```
Project
├── DomainObjectStore
└── Scenes
      ├── Scene A
      ├── Scene B
      └── ...
```

The Project is responsible for the complete persistent planning context.

The Scene is responsible only for its spatial context.

---

# 4. DomainObjectStore

The **DomainObjectStore** is the canonical registry and lifecycle authority for domain objects belonging to a Project.

Conceptually:

```
Project
│
└── DomainObjectStore
      ├── Maxilla
      ├── Mandible
      ├── Tooth 11
      ├── Tooth 21
      ├── CT Volume
      └── Surgical Splint
```

The DomainObjectStore is **Project-scoped**, not application-global.

This provides:

* isolation between Projects;
* deterministic object identity;
* explicit lifecycle boundaries;
* straightforward persistence;
* prevention of accidental cross-Project references.

The detailed contract of the DomainObjectStore is defined separately.

---

# 5. Scene and DomainObjectStore

The Scene references objects belonging to the DomainObjectStore associated with the same Project.

Conceptually:

```
Project
│
├── DomainObjectStore
│     ├── Maxilla
│     ├── Mandible
│     └── Splint
│
└── Scene
      ├── object_id → Maxilla
      ├── object_id → Mandible
      └── object_id → Splint
```

The Scene does not create independent canonical copies of these objects.

The Scene assumes the following contract:

> **While an object is a member of a Scene, its object ID must resolve to a valid domain object in the Project's DomainObjectStore.**

This invariant must hold throughout the lifetime of the Scene.

---

# 6. Object Ownership and Scene Membership

Ownership and membership are distinct concepts.

## 6.1 Object ownership

The DomainObjectStore owns the canonical lifecycle of Project domain objects.

An object becomes an official Project domain object when it is registered in the store.

For example:

```
Import CT
    ↓
Create Volume Object
    ↓
Register in DomainObjectStore
    ↓
Add Object to Scene
```

---

## 6.2 Scene membership

Scene membership means that a domain object participates in the spatial context of a Scene.

Membership does not transfer ownership to the Scene.

For example:

```
Scene
├── Maxilla
├── Mandible
└── Splint
```

The Scene maintains references to these objects through their stable identities.

---

# 7. Membership Integrity

Every Scene membership reference must resolve to a valid object in the Project's DomainObjectStore.

Invalid membership references are not permitted as a normal state.

Therefore:

```
Scene Membership
      │
      ▼
DomainObjectStore.get(object_id)
      │
      ▼
Valid Domain Object
```

The Scene must never intentionally contain dangling references.

---

# 8. Object Removal and Membership Removal

Removing an object from a Scene and removing an object from a Project are different operations.

### Remove membership

```
Scene.remove_object(object_id)
```

means:

> Remove the object's spatial membership from this Scene.

The domain object remains in the DomainObjectStore.

### Remove object from Project

```
DomainObjectStore.remove(object_id)
```

means:

> Remove the canonical domain object from the Project.

An object must not be removed from the DomainObjectStore while it is still a member of any Scene in the same Project.

Therefore, before object removal:

```
Remove Object from Project
        ↓
Check Scene Memberships
        ↓
   ┌────┴────┐
   │         │
Exists     None
   │         │
   ▼         ▼
Reject     Remove
```

The Application Core is responsible for coordinating this operation.

The DomainObjectStore should not need to directly own or scan all Scenes.

---

# 9. Scene Core

The Scene Core contains the fundamental spatial state of the Scene.

It includes:

* Scene identity;
* metadata;
* object membership;
* coordinate-system definition;
* spatial hierarchy;
* transforms;
* spatial relationships;
* persistent reference-frame associations.

The Scene Core should remain deliberately small.

It must not become a general-purpose container for Project state.

---

# 10. Spatial Hierarchy

Spatial hierarchy is an explicit Scene-level concept.

It represents parent-child relationships that affect spatial interpretation.

For example:

```
Mandible
├── Left Segment
└── Right Segment
```

or:

```
Patient Reference
├── Maxilla
└── Mandible
```

Hierarchy is not merely an internal optimization.

It is part of the Scene's spatial domain state.

---

# 11. Parent-Child Rules

An object may have **at most one parent within a given Scene**.

Conceptually:

```
Scene
└── Mandible
      ├── Left Segment
      └── Right Segment
```

The Scene should provide operations conceptually equivalent to:

```
set_parent()
get_parent()
iter_children()
```

The hierarchy must not contain cycles.

The parent relationship belongs to the Scene, not to the domain object itself.

Therefore, the same domain object may theoretically participate in different Scenes with different parents.

For example:

```
Scene A
└── Mandible
      └── Segment

Scene B
└── Osteotomy Reference
      └── Segment
```

The object's intrinsic identity does not change.

Only its spatial organization within the Scene changes.

---

# 12. Hierarchy and Transform Composition

Parent-child hierarchy provides a basis for transform composition.

For example:

```
Scene
  │
  └── Mandible
        │
        └── Left Segment
```

The resulting Scene-space transform may be expressed conceptually as:

```
T_scene_segment =
    T_scene_mandible
    · T_mandible_segment
```

For deeper hierarchies:

```
T_scene_object =
    T_scene_parent
    · T_parent_child
    · T_child_object
```

The exact mathematical representation belongs to the geometry layer.

Scene depends on domain-level transformation abstractions rather than directly on NumPy, VTK, OCCT, or another mathematical library.

---

# 13. Spatial Relationships

Not every relationship between objects should be represented as parent-child hierarchy.

A Scene may maintain explicit **SpatialRelationships**.

Examples include:

* registration;
* attachment;
* correspondence;
* derivation;
* alignment;
* reference relationships.

Conceptually:

```
SpatialRelationship
├── source
├── target
├── type
├── directed
└── data
```

For example:

```
Registration(CT, IOS)

AttachedTo(Plate, Mandible)

DerivedFrom(OsteotomySegment, Mandible)
```

The Scene provides the spatial context for these relationships.

The algorithms that establish relationships belong to appropriate domain or application services.

---

# 14. Relationship Cardinality and Identity

A relationship type defines its own semantic constraints.

The Scene provides structural integrity but does not impose arbitrary cardinality rules on every relationship type.

For example:

```
Registration
    CT → IOS
```

may have different cardinality rules from:

```
DerivedFrom
    Segment → Mandible
```

or:

```
AttachedTo
    Plate → Mandible
```

A relationship may be:

* directed or symmetric;
* unique or non-unique;
* one-to-one;
* one-to-many;
* many-to-many.

These properties must be defined by the specific relationship type.

Unless explicitly defined otherwise, a relationship is identified by its complete semantic identity and duplicate relationships should not be silently created.

The detailed contract for relationship types should be documented separately.

---

# 15. Relationship Lifecycle

Relationships cannot reference objects that do not exist in the relevant Scene context.

When an object is removed from a Scene, relationships involving that membership must be handled according to the relationship contract.

The default rule is:

> **A Scene must not retain an active relationship whose required object references are no longer valid Scene members.**

Relationship cleanup is therefore part of the Scene's structural integrity.

The exact behavior for derived or persistent relationships may be defined by the relationship type.

---

# 16. Global Coordinate System

Each Scene defines a global coordinate system.

The coordinate system provides the reference frame for spatial interpretation.

The canonical spatial unit is:

```
millimetres (mm)
```

The coordinate system must define:

* units;
* handedness;
* axis orientation;
* origin convention.

The exact anatomical convention is a project-wide geometry decision and should be defined separately in the geometry documentation and corresponding ADR.

---

# 17. Scene Origin and Reference Frames

The Scene origin represents the global technical reference frame.

It must not be confused with clinically meaningful anatomical reference frames.

A Scene may contain or reference multiple reference frames:

```
Scene Coordinate System
│
├── Patient Reference Frame
├── Cranial Reference Frame
├── Maxillary Reference Frame
└── Mandibular Reference Frame
```

A reference frame with persistent identity and clinical meaning may be represented as a domain object and registered in the DomainObjectStore.

A transient mathematical reference frame may instead exist only as temporary domain/application state.

Reference frames may therefore have:

* identity;
* transform;
* parent reference frame;
* semantic type;
* persistence state.

The Scene defines how these frames participate in its spatial context.

---

# 18. Object Transforms

Objects may have local coordinate systems and transformations into Scene space.

Conceptually:

```
Local Object Coordinates
          │
          │ Transform
          ▼
Scene Coordinate System
```

This allows imported and generated objects to retain their local coordinate representation while being positioned within the Scene.

For example:

```
Dental Scan
    │
    ▼
Registration Transform
    │
    ▼
Scene Coordinates
```

The Scene maintains the resulting spatial state.

---

# 19. Rigid Transformations

Rigid transformations are first-class Scene operations.

They are appropriate for:

* bone segments;
* dental models;
* implants;
* plates;
* splints;
* surgical guides;
* reference objects.

A rigid transform preserves:

* distances;
* angles;
* topology.

The Scene should use a validated domain-level rigid transformation type.

---

# 20. Deformable Transformations

Deformable transformations are separate from rigid Scene transforms.

A deformable object may conceptually have:

```
Base Geometry
     │
     ├── Rigid Transform
     │
     └── Deformation Field
```

A deformation field may be represented by:

* displacement fields;
* deformation fields;
* morph targets;
* facial rigs;
* other domain-specific deformation models.

The deformation representation does not inherently belong to the Scene.

It belongs to the appropriate domain object, planning result, or simulation model.

The Scene provides the spatial context in which the resulting state is interpreted.

---

# 21. Registration

Registration establishes spatial correspondence between coordinate systems.

The Scene provides the common spatial context in which registered objects coexist.

For example:

```
CT
  │
  │ T_ct_to_scene
  ▼
Scene
  ▲
  │ T_ios_to_scene
  │
IOS
```

Registration algorithms are not implemented by the Scene.

They belong to domain services, application services, or infrastructure-backed algorithms.

The Scene stores the resulting transformation and/or spatial relationship.

---

# 22. Derived Objects

Some domain objects are derived from other objects.

Examples:

```
CT
  ↓
Segmentation
  ↓
Bone Mesh
```

or:

```
Mandible
  ↓
Osteotomy
  ↓
Osteotomy Segment
```

or:

```
CT + Facial Scan
  ↓
Registration
  ↓
Facial Model
```

Derived relationships may be important for:

* reproducibility;
* dependency tracking;
* invalidation;
* regeneration;
* persistence.

The application/module layer performs the operation that creates the derived object.

The Scene maintains its spatial organization and relevant relationships.

---

# 23. Measurements

Measurements are interpreted within the Scene coordinate system unless explicitly associated with another reference frame.

This provides consistent spatial interpretation for:

* distances;
* angles;
* bone thickness;
* segment displacement;
* overjet;
* overbite;
* implant dimensions;
* airway measurements;
* contact distances.

For example:

```
Distance(PointA, PointB) → mm
```

Measurement algorithms remain separate domain services.

---

# 24. Rendering Independence

The Scene is completely independent of the rendering engine.

It must not contain:

* `vtkActor`;
* `vtkRenderer`;
* `vtkMapper`;
* cameras;
* lights;
* OpenGL state;
* viewport objects.

The rendering system consumes Scene state and creates visual representations.

Conceptually:

```
Scene
  │
  ▼
Rendering Adapter
  │
  ├── Actor Factory
  ├── Actor Registry
  └── Renderer
  │
  ▼
Rendering Engine
```

---

# 25. Rendering Representation

A domain object and its visual representation are separate entities.

For example:

```
Domain Object
    Mandible
        │
        ▼
Rendering Adapter
        │
        ▼
    vtkActor
```

The same domain object may have different representations in different Areas or Viewports.

For example:

```
Mandible
├── 3D View
│     └── surface representation
│
├── MPR View
│     └── contour/intersection representation
│
└── Planning View
      └── translucent surface representation
```

---

# 26. Rendering Adapter

The Rendering Adapter bridges domain/application state and rendering infrastructure.

A VTK implementation may contain:

```
VTKActorFactory
ActorRegistry
VTKSceneRenderer
SceneBridge
```

These components belong to Infrastructure/UI integration, not the Domain layer.

---

## 26.1 VTKActorFactory

`VTKActorFactory` converts domain object representations into VTK rendering objects.

Conceptually:

```
Domain Object
      ↓
VTKActorFactory
      ↓
   vtkActor
```

The factory must not modify domain semantics.

---

## 26.2 ActorRegistry

`ActorRegistry` maintains the mapping between domain object IDs and rendering actors.

Conceptually:

```
Object ID → vtkActor
```

It is a rendering infrastructure component.

It is not the canonical storage location for domain objects.

---

## 26.3 VTKSceneRenderer

`VTKSceneRenderer` manages the VTK rendering context associated with a specific rendering surface.

It is responsible for:

* adding actors;
* removing actors;
* updating actors;
* managing renderer-specific state.

It does not own domain objects.

---

## 26.4 SceneBridge

`SceneBridge` coordinates synchronization between Scene/Application events and rendering representations.

For example:

```
ObjectAdded
    ↓
SceneBridge
    ↓
VTKActorFactory
    ↓
ActorRegistry
    ↓
VTKSceneRenderer
```

Or:

```
ObjectTransformed
    ↓
SceneBridge
    ↓
Update vtkActor transform
```

The SceneBridge must not become a general-purpose domain coordinator.

---

# 27. Presentation State

The following are generally presentation concerns:

* color;
* opacity;
* visibility;
* selection;
* representation mode;
* shading;
* rendering style.

These should not be placed indiscriminately in domain objects.

The same Scene object may therefore have different presentation states in different Viewports.

---

# 28. Scene Membership vs. Visibility

Scene membership is a domain concept.

Visibility is normally a presentation concept.

Therefore:

```
Scene membership
    ≠
Viewport visibility
```

An object can remain a Scene member while being hidden in one or more Viewports.

This distinction is required to support multiple Areas and Viewports without modifying domain state.

---

# 29. Selection

Selection is an Application/UI concern.

The Scene does not need to know which object is currently selected by the user.

For example:

```
Scene
├── Maxilla
├── Mandible
└── Tooth 11
```

A 3D Viewport may select the Mandible while another Area may select a landmark.

Selection state should therefore remain outside the Scene Core.

---

# 30. Temporary and Preview Objects

Planning workflows frequently generate temporary objects.

Examples include:

* cutting planes;
* boolean operands;
* collision proxies;
* registration markers;
* preview osteotomies;
* temporary splints;
* simulation results;
* construction geometry.

Temporary objects should not automatically become persistent Project objects.

The architecture distinguishes:

```
Persistent Domain Objects
```

from:

```
Temporary / Preview / Computational State
```

Only objects intended to become part of the persistent domain model should be registered in the DomainObjectStore.

---

# 31. Scene API

The Scene API should remain deliberately focused.

## 31.1 Scene Core API

Conceptually:

```
add_object()
remove_object()
contains()
get_object()
iter_objects()

get_transform()
set_transform()
```

---

## 31.2 Scene Graph API

Conceptually:

```
set_parent()
get_parent()
iter_children()

iter_subtree()
```

---

## 31.3 Relationship API

Conceptually:

```
add_relationship()
remove_relationship()
get_relationships()
iter_relationships()
```

The exact signatures and type contracts belong to the implementation specification.

The API must remain independent of rendering frameworks.

---

# 32. Scene Invariants

The Scene must maintain the following invariants.

## 32.1 Unique identity

Object identity is unique within the Project's DomainObjectStore.

## 32.2 Valid membership

Every Scene membership reference resolves to a valid object in the associated DomainObjectStore.

## 32.3 No dangling membership

A Scene must never intentionally retain membership for an object that has been removed from the Project.

## 32.4 Valid hierarchy

The hierarchy contains no cycles.

An object has at most one parent within a Scene.

## 32.5 Valid relationships

Required relationship endpoints must resolve to valid objects.

## 32.6 Valid transforms

Transforms must be mathematically valid and use the Scene's coordinate conventions.

## 32.7 Consistent units

Scene-space measurements use the canonical unit convention.

---

# 33. Commands and Scene Mutations

Scene mutations should preferably occur through Application Commands.

Examples include:

```
AddObject
RemoveObjectFromScene
RemoveObjectFromProject
SetParent
TransformObject
AddRelationship
RemoveRelationship
ApplyRigidMovement
```

Conceptually:

```
Tool
  ↓
Command
  ↓
Application Service
  ↓
DomainObjectStore / Scene
  ↓
Events
```

This provides a consistent mechanism for:

* validation;
* transactions;
* undo/redo;
* event publication;
* auditability.

---

# 34. Transactions

Complex planning operations may modify multiple domain objects and Scene state.

For example:

```
Apply Le Fort I Movement
```

may affect:

```
Maxillary Segment
Dental Model
Cephalometric Landmarks
Surgical Splint
```

Such operations are coordinated by the Application Core as a single logical transaction.

The Scene does not own transaction orchestration.

However, the Scene must provide a state model that allows the Application Core to capture and restore the relevant state.

---

# 35. Transaction State and Snapshots

Transaction snapshots and worker-computation snapshots are distinct concepts.

## 35.1 Transaction snapshot

A transaction snapshot is optimized for rollback.

It should contain only the state necessary to restore the affected logical Scene state, such as:

```
membership
hierarchy
transforms
relationships
relevant domain state
```

Large geometry payloads should not be unnecessarily duplicated.

---

## 35.2 Computation snapshot

A computation snapshot provides stable input to asynchronous processing.

It may contain:

```
geometry
volume data
landmarks
transforms
relevant metadata
```

Its primary requirements are:

* stable read access;
* immutability;
* safe use by worker threads;
* efficient transfer or sharing.

The two snapshot mechanisms may share implementation infrastructure, but they have different contracts and must not be treated as conceptually identical.

---

# 36. Transaction Rollback Example

Consider an orthognathic planning operation:

```
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
```

The rollback restores the relevant Scene and domain state to its state before the transaction.

The rendering layer receives the resulting committed state rather than being responsible for transaction management.

---

# 37. Scene Events

Meaningful Scene state changes may generate semantic events.

Examples include:

```
ObjectAdded
ObjectRemovedFromScene
ObjectTransformed
ParentChanged
RelationshipAdded
RelationshipRemoved
```

Events must describe semantic state changes rather than UI interactions.

For example:

```
ObjectTransformed
```

is a domain-level event.

The following is not:

```
MouseDragged
```

because it describes a UI interaction.

A generic `SceneChanged` event is intentionally avoided.

Specific state changes should use explicit event types so that consumers can understand exactly what changed.

---

# 38. Event Semantics

The detailed event infrastructure belongs to the Application layer, but Scene events follow these principles.

## 38.1 State information

A state-change event must provide sufficient information for observers to determine what changed.

For example:

```
ObjectTransformed
├── object_id
├── previous_transform
└── new_transform
```

An equivalent delta representation may be used.

---

## 38.2 Transaction boundaries

Events generated during a transaction must not be interpreted by external consumers as permanently committed state until the transaction commits.

Application-level transaction events may distinguish:

```
TransactionStarted
TransactionCommitted
TransactionRolledBack
```

The exact implementation belongs to the Application event system.

---

## 38.3 Deterministic ordering

Within a committed transaction, event ordering must be deterministic.

However, observers are independent consumers.

No observer may depend on another observer having processed an event first.

For example:

```
ObjectTransformed
        │
   ┌────┴────┐
   ▼         ▼
Renderer   Spatial Index
```

The Rendering Adapter and SpatialIndexService both consume the committed state independently.

If one operation genuinely depends on another, that dependency must be expressed explicitly in the Application layer rather than through implicit observer priority.

---

# 39. Spatial Indexing

The Scene does not directly manage spatial indexing or rendering performance.

However, it must support external spatial services.

Potential services include:

* spatial indexes;
* bounding-volume hierarchies;
* collision detection;
* nearest-neighbor queries;
* proximity queries;
* intersection queries;
* region-of-interest queries.

A spatial index may observe Scene changes through the event system.

Conceptually:

```
Scene
  │
  ├── ObjectAdded
  ├── ObjectRemoved
  └── ObjectTransformed
  │
  ▼
SpatialIndexService
  │
  ▼
Spatial Index
```

The Scene remains independent of the concrete indexing implementation.

---

# 40. Spatial Observers

Infrastructure and Application services may observe relevant Scene events.

Examples include:

```
SpatialIndexService
RenderingAdapter
MeasurementCache
CollisionService
DependencyTracker
```

Observers maintain derived state.

They do not acquire ownership of domain objects.

The authoritative state remains in:

```
DomainObjectStore
+
Scene
```

---

# 41. Concurrency and Threading

The Scene is **application-thread confined by default**.

Domain state mutations should occur through the Application Core on the designated application thread.

Worker threads must not freely mutate the live Scene.

Long-running operations such as:

* segmentation;
* registration;
* mesh processing;
* collision computation;
* deformation simulation;

should operate on stable computation snapshots.

Conceptually:

```
Application Thread
        │
        ▼
      Scene
        │
        ▼
  Computation Snapshot
        │
        ▼
    Worker Thread
        │
        ▼
     Processing
        │
        ▼
   Result / Command
        │
        ▼
Application Thread
        │
        ▼
      Scene
```

This prevents uncontrolled concurrent mutation and simplifies transaction, undo/redo, and event semantics.

Concurrent read-only access to live mutable Scene state is not assumed.

When concurrent access is required, immutable snapshots or explicitly defined read models should be used.

---

# 42. Serialization

Scene state is serialized as part of the Project format.

The Scene serialization must preserve, as applicable:

* Scene identity;
* metadata;
* coordinate-system definition;
* object membership;
* hierarchy;
* transforms;
* spatial relationships;
* persistent reference-frame associations;
* persistent derived-object relationships.

Large binary assets should not be embedded directly into the Scene structure unless explicitly required by the Project format.

For example:

```
Scene Data
├── Object IDs
├── Hierarchy
├── Transforms
├── Relationships
└── Asset References
```

while:

```
Assets
├── DICOM
├── STL
├── OBJ
└── other binary data
```

are managed separately.

---

# 43. Serialization References

Scene deserialization requires resolution of references between:

```
Project
  ├── DomainObjectStore
  └── Scenes
```

Objects must be resolved through the Project's DomainObjectStore.

The deserialization process must reject or explicitly handle:

* missing object references;
* invalid hierarchy references;
* invalid relationship endpoints;
* unsupported schema versions;
* missing required assets.

The detailed policies for:

* schema versioning;
* migrations;
* missing assets;
* backward compatibility;

belong to the Project serialization specification.

The Scene document defines only the architectural contract.

---

# 44. Project and Multiple Scenes

A Project may contain multiple Scenes.

For example:

```
Project
│
├── DomainObjectStore
│
└── Scenes
      ├── Initial State
      ├── Surgical Plan
      ├── Simulation
      └── Comparison
```

Different Scenes may contain different memberships, hierarchies, transforms, and relationships while referencing objects belonging to the same Project.

Whether a specific object may participate in multiple Scenes is a Project-level policy.

If an object participates in multiple Scenes, its spatial organization remains Scene-specific.

The concept of an **active Scene** is application/UI state and should not be treated as intrinsic Scene domain state.

---

# 45. Scene and Flows

A Flow represents an ordered clinical or planning workflow.

A Flow may operate on one or more Scenes.

For example:

```
Orthognathic Flow
    │
    ├── Tomography
    ├── Models
    ├── Cephalometry
    ├── Registration
    ├── Osteotomy
    └── Splint
```

The Flow orchestrates operations.

The Scene provides the spatial state on which those operations act.

The Scene does not know which Flow is currently executing.

---

# 46. Scene and Modules

Modules may create, modify, or consume Scene state through Application Commands and Services.

For example:

```
Segmentation Module
    ↓
Create Bone Object
    ↓
DomainObjectStore
    ↓
Add Object to Scene
```

or:

```
Osteotomy Module
    ↓
Create Osteotomy Segment
    ↓
DomainObjectStore
    ↓
Add to Scene Hierarchy
    ↓
Apply Transform
```

Modules must not bypass the Domain/Application boundaries by directly manipulating rendering actors.

---

# 47. Example: Orthognathic Planning

A simplified orthognathic Scene may contain:

```
Scene
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
```

The DomainObjectStore contains the canonical domain objects.

The Scene contains their spatial membership, hierarchy, transforms, and relationships.

For example:

```
DomainObjectStore
├── Mandible
├── Left Segment
├── Right Segment
└── Splint

Scene
└── Mandible
      ├── Left Segment
      └── Right Segment
```

---

# 48. Example: Composed Segment Movement

Consider a sagittal split osteotomy.

The hierarchy may be:

```
Scene
  │
  └── Mandible
        │
        ├── Left Segment
        └── Right Segment
```

The left segment transform may be composed as:

```
T_scene_left_segment =
    T_scene_mandible
    · T_mandible_left_segment
```

After surgical simulation:

```
Left Segment
    Transform = T_left

Right Segment
    Transform = T_right
```

The planning service calculates the appropriate transformations.

The Scene maintains the resulting spatial configuration.

The rendering adapter observes the resulting committed state and updates the visual representation.

---

# 49. Example: Registration

A CT volume and intraoral scan may originate from different coordinate systems.

Conceptually:

```
CT
  │
  │ T_ct_to_scene
  ▼
Scene
  ▲
  │ T_ios_to_scene
  │
IOS
```

The registration service calculates the transformation.

The Scene stores the resulting spatial relationship.

The rendering system can then display both datasets in the same spatial context without either domain object becoming dependent on VTK.

---

# 50. Example: Multiple Viewports

The same Scene may be consumed by multiple visualization contexts.

For example:

```
Scene
  │
  ├── 3D View
  ├── Axial MPR
  ├── Sagittal MPR
  ├── Coronal MPR
  └── Cephalometric View
```

Each Viewport may have its own:

* camera;
* projection;
* orientation;
* visibility;
* representation;
* overlays;
* selection.

These are not properties of the Scene Core.

All Views derive their spatial information from the same Scene state.

---

# 51. Example: Rendering Synchronization

When an object is added:

```
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
VTKActorFactory
    ↓
ActorRegistry
    ↓
VTKSceneRenderer
```

When an object is transformed:

```
TransformObject
    ↓
Scene.set_transform()
    ↓
ObjectTransformed
    ↓
SceneBridge
    ↓
Update vtkActor transform
```

The rendering system reacts to committed domain/application state rather than becoming the owner of that state.

---

# 52. Example: Spatial Index Synchronization

A spatial index may consume the same Scene events:

```
ObjectAdded
    ↓
SpatialIndexService
    ↓
Insert Object

ObjectTransformed
    ↓
SpatialIndexService
    ↓
Update Bounds

ObjectRemovedFromScene
    ↓
SpatialIndexService
    ↓
Remove Object
```

The Scene remains unaware of the concrete spatial-index implementation.

---

# 53. Reproducibility

The Scene should be deterministic enough to reconstruct the logical spatial planning state from serialized Project data.

Given:

```
Project Data
+
Scene Data
+
Referenced Assets
```

CranioZ should be able to reconstruct the same logical spatial configuration.

This supports:

* research reproducibility;
* planning review;
* collaboration;
* version control;
* automated testing;
* auditability;
* Project migration.

---

# 54. What Scene Must Not Do

The Scene must not become responsible for:

* rendering;
* VTK actors;
* cameras;
* lights;
* viewport layout;
* UI selection;
* dock panels;
* toolbar state;
* mouse interaction;
* keyboard shortcuts;
* DICOM loading;
* STL/OBJ loading;
* mesh processing algorithms;
* segmentation algorithms;
* registration algorithms;
* cephalometric calculations;
* surgical planning algorithms;
* persistence infrastructure;
* plugin discovery;
* module lifecycle management;
* rendering actor management;
* global Project object lifecycle.

These responsibilities belong to other architectural layers.

---

# 55. Architectural Summary

The Scene is the **domain-level spatial context of CranioZ**.

Its core responsibilities are:

```
Spatial Membership
      +
Spatial Hierarchy
      +
Transforms
      +
Spatial Relationships
      +
Coordinate System
      +
Reference Frames
      +
Spatial State
```

The Project provides the persistent boundary.

The DomainObjectStore provides canonical domain object identity and lifecycle.

The Application layer provides:

```
Commands
Transactions
Services
Flows
Event Coordination
```

Infrastructure provides:

```
DICOM
VTK
ITK
OCCT
CGAL
Storage
Rendering Adapters
Spatial Indexes
```

The resulting architecture is:

```
┌─────────────────────────────────────────────┐
│                    Project                  │
│                                             │
│  ┌──────────────────┐  ┌─────────────────┐ │
│  │ DomainObjectStore │  │     Scenes      │ │
│  │                  │  │                 │ │
│  │ Canonical Objects│  │ Membership      │ │
│  │ Identity         │  │ Hierarchy       │ │
│  │ Lifecycle        │  │ Transforms      │ │
│  │                  │  │ Relationships   │ │
│  └────────┬─────────┘  └────────┬────────┘ │
│           │                     │          │
└───────────┼─────────────────────┼──────────┘
            │                     │
            └──────────┬──────────┘
                       │
                    Commands
                    Events
                    Transactions
                       │
                       ▼
            ┌─────────────────────┐
            │ Application Core    │
            │                     │
            │ Commands            │
            │ Transactions        │
            │ Services            │
            │ Flows               │
            └──────────┬──────────┘
                       │
                       ▼
            ┌─────────────────────┐
            │ Infrastructure      │
            │                     │
            │ Rendering Adapter   │
            │ VTKActorFactory     │
            │ ActorRegistry       │
            │ VTKSceneRenderer    │
            │ Spatial Index       │
            └─────────────────────┘
```

The fundamental separation is:

```
DomainObjectStore
    → owns canonical domain object lifecycle

Scene
    → owns spatial organization within a planning context

Application Core
    → owns orchestration, commands, and transactions

Rendering Adapter
    → translates domain state into visual representations

Viewport
    → presents and interacts with those representations
```

This separation provides CranioZ with a modular, multi-Scene, rendering-independent spatial architecture suitable for clinical planning, simulation, visualization, and future extensions.
