# ADR-0008: Scene and DomainObjectStore

**Status:** Accepted
**Date:** 2026-10-22
**Deciders:** Architecture team
**Related:** scene.md, objects.md, project.md §17, ADR-0007

---

## 1. Context

CranioZ must organize clinical objects spatially without coupling
them to the rendering engine, the UI, or the persistence format. The
`scene.md` document specifies the contract. This ADR records the
decision to introduce the Scene and the DomainObjectStore as
separate, complementary concepts.

Two questions had to be answered before Phase 4 could begin:

1. **Where do domain objects live?** They must not be owned by the
   Scene, because the same object may participate in multiple Scenes
   with different spatial organizations.
2. **How is spatial state persisted?** It must be separable from the
   object payload (large geometry) and serializable per Scene.

## 2. Decision

### 2.1 Two concepts, two responsibilities

- **DomainObjectStore** is the canonical registry and lifecycle
  authority for domain objects belonging to a Project. It is
  Project-scoped, not application-global. It owns object identity and
  persistence.
- **Scene** is the spatial organization of objects within a specific
  planning context. It owns membership, hierarchy, transforms,
  relationships, and the coordinate system. It does not own object
  lifecycle.

### 2.2 Multiple Scenes per Project

A Project may contain multiple Scenes (Initial State, Surgical Plan,
Simulation, Comparison). Different Scenes may contain different
memberships, hierarchies, transforms, and relationships while
referencing the same objects. The DomainObjectStore owns the canonical
object; each Scene owns its own spatial organization.

### 2.3 Membership integrity

While an object is a member of a Scene, its `object_id` must resolve
to a valid object in the Project's DomainObjectStore. The Scene must
never intentionally contain dangling references. Removing an object
from the DomainObjectStore while it is a member of any Scene is
rejected by the Application layer.

### 2.4 Rendering independence

The Scene is completely independent of the rendering engine. It must
not contain `vtkActor`, `vtkRenderer`, `vtkMapper`, cameras, lights,
OpenGL state, or viewport objects. The Rendering Adapter is a
separate infrastructure component that bridges committed Scene state
to VTK.

### 2.5 Mutation through Commands

Scene mutations occur through Commands (ADR-0007). Editors access the
Scene through `SceneQuery` (read-only) and dispatch Commands through
`CommandDispatcher`. The Scene is never mutated directly by the UI.

### 2.6 Coordinate system

Each Scene defines a global coordinate system. Units are millimetres.
Handedness, axis orientation, and origin convention are fixed
project-wide and documented in the geometry specification. The exact
convention is a separate decision.

## 3. Rationale

### 3.1 Separation prevents the Scene from becoming a god object

`scene.md` §1 establishes that the Scene does not own domain objects.
Without the separation, the Scene would accumulate identity,
lifecycle, persistence, spatial organization, and rendering state —
exactly the god-object anti-pattern that ADR-0004 rejected for
Patient.

### 3.2 Multiple Scenes require a shared object registry

If each Scene owned its objects, the same Mandible would be duplicated
in every Scene. This breaks derived relationships, wastes memory
(large meshes are expensive), and makes cross-Scene consistency
impossible.

### 3.3 Rendering independence is an invariant

`overview.md` §25 (Architectural Invariants) requires that "the
Domain Scene is the semantic source of truth for scene state" and
"renderer-specific state must be derived from or synchronized with
application/domain state." Embedding VTK in the Scene would violate
both.

## 4. Consequences

### 4.1 Positive

- Multiple Scenes per Project with shared objects.
- Rendering remains replaceable (VTK, OCCT, future backends).
- Spatial state is separable from geometry for persistence.
- Commands provide the mutation path, enabling undo/redo.

### 4.2 Negative

- Two concepts (DomainObjectStore, Scene) must be coordinated by the
  Application layer. Removing an object requires checking membership
  in all Scenes.
- Serialization must preserve the association between objects and
  their Scene memberships.

### 4.3 Neutral

- The "active Scene" concept is Application/UI state, not a Scene
  property. Multiple Scenes may exist simultaneously.

## 5. Rules applied by this ADR

1. DomainObjectStore is Project-scoped.
2. Scene owns spatial state, not object lifecycle.
3. A Scene may reference objects from the same Project only.
4. Membership references must resolve to valid objects.
5. Removing an object while it is a member of any Scene is rejected.
6. The Scene is rendering-independent.
7. Scene mutations occur through Commands.
8. Units are millimetres.
9. Multiple Scenes per Project are allowed.
10. Spatial state is serialized separately from object payloads.

## 6. Rejected alternatives

### 6.1 Scene owns domain objects

Rejected. Breaks multiple Scenes, duplicates large geometry, and
creates the god-object anti-pattern.

### 6.2 A single global object registry

Rejected. Breaks isolation between Projects. Project-scoped
DomainObjectStore is the correct boundary.

### 6.3 VTK actors stored in the Scene

Rejected. Couples the domain to a specific rendering backend.

### 6.4 Direct Scene mutation by Editors

Rejected. Violates ADR-0007 and ADR-0002.

## 7. Summary

The Scene is the spatial context; the DomainObjectStore is the
canonical object registry. They are distinct, complementary, and
coordinated by the Application layer. Scene mutations go through
Commands. Rendering is a derived concern. This separation is the
prerequisite for Phase 4.