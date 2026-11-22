# Geometry Infrastructure

## 1. Purpose

The Geometry Infrastructure provides the canonical representation, validation, persistence, and processing foundations for geometric data in CranioZ.

Its primary responsibility is to manage geometry independently of rendering libraries, user interface components, and clinical workflows.

The initial implementation focuses on triangular meshes and establishes contracts that allow future geometric capabilities without introducing unnecessary abstractions.

### Design Principles

- Python-first implementation.
- Canonical geometry independent of external libraries.
- Immutable geometry revisions.
- Explicit coordinate systems and physical units.
- Structured validation and operation results.
- Deterministic persistence and asset ownership.
- CPU-first processing.
- Explicit memory ownership and lifecycle management.
- No direct mutation of Project or Scene state from workers.

---

## 2. Architectural Boundaries

Geometry Infrastructure is distributed across Domain, Application, and Infrastructure.

| Layer | Responsibilities |
|---|---|
| Domain | Geometry data contracts, attributes, revisions, coordinate conventions, and validation models. |
| Application | Geometry operations, commands, transactions, task coordination, and commit policies. |
| Infrastructure | File I/O, persistence, NumPy integration, VTK adapters, and processing implementations. |

### 2.1 Domain

The Domain defines geometry independently of VTK, Qt, file formats, and other infrastructure dependencies.

It owns:

- `Mesh`
- `MeshAttribute`
- `CoordinateFrame`
- `GeometryRevision`
- `ValidationIssue`
- `ValidationResult`
- Geometry-related invariants and identifiers.

### 2.2 Application

The Application coordinates operations and controls their effects on persistent application state.

It owns:

- Geometry commands.
- Geometry application services.
- Operation lifecycle.
- Cancellation and task coordination.
- Source revision checks.
- Transactional commits.
- Structured operation results.

### 2.3 Infrastructure

Infrastructure provides concrete implementations for:

- Geometry import and export.
- Array serialization.
- Persistent geometry assets.
- Structural validation implementations.
- VTK interoperability.
- Geometry processing algorithms.

Infrastructure adapters must not redefine Domain contracts.

---

## 3. Geometry Data Model

### 3.1 Mesh

`Mesh` is the canonical representation of a triangular surface mesh.

It consists of:

- Vertices.
- Triangle indices.
- Optional geometric attributes.
- An explicitly declared local coordinate frame.

The initial implementation supports triangular meshes only.

#### Canonical Representation

```python
@dataclass(frozen=True, slots=True)
class Mesh:
    vertices: NDArray[np.float32] | NDArray[np.float64]
    faces: NDArray[np.uint32] | NDArray[np.uint64]
    attributes: tuple["MeshAttribute", ...]
    coordinate_frame: "CoordinateFrame"
```

The declaration illustrates the public contract. Actual construction must enforce the invariants below.

#### Invariants

- `vertices` has shape `(N, 3)`.
- `faces` has shape `(M, 3)`.
- Vertex coordinates are finite.
- Face indices reference existing vertices.
- Vertex and face arrays use supported numeric dtypes.
- Arrays have compatible memory layout and ownership guarantees.
- The coordinate frame is explicitly defined.
- Attributes reference valid mesh elements and declare their association and data type.
- Canonical arrays cannot be modified through public interfaces.

Mesh construction must validate structural invariants before accepting data.

Array immutability must be enforced through controlled ownership and read-only access. A frozen dataclass alone does not guarantee NumPy buffer immutability.

### 3.2 Mesh Attributes

`MeshAttribute` stores additional data associated with a mesh.

Initial supported associations:

- `POINT`: one value per vertex.
- `CELL`: one value per triangle.
- `MESH`: one value per mesh.

Examples include:

- Normals.
- Colors.
- Confidence values.
- Anatomical classifications.
- Application-specific metadata.

Each attribute must declare:

- Identifier.
- Name.
- Association.
- Data type.
- Shape.
- Value storage.

Attributes must not introduce clinical semantics directly into the geometry representation. Anatomical meaning belongs to the Object System and its semantic components.

### 3.3 Geometry and Object Semantics

A `Mesh` represents geometric data, not an anatomical entity.

The distinction is:

```text
Object
 ├── Data: Mesh
 ├── Semantic: Anatomy.Bone.Mandible
 ├── Components
 └── Capabilities
```

Geometry does not determine whether an object is a mandible, maxilla, tooth, implant, or surgical guide.

Clinical meaning is defined by the Object System.

---

## 4. Coordinate Systems and Units

### 4.1 Global Coordinate System

CranioZ uses RAS as its global coordinate convention.

| Axis | Direction |
|---|---|
| X | Right |
| Y | Anterior |
| Z | Superior |

All geometric coordinates are expressed in millimeters.

### 4.2 Local Coordinate Frames

Each Mesh declares a local coordinate frame.

A local frame may have its own origin and orientation. Its relationship to the global RAS frame must be explicit.

The transformation between local and global coordinates is managed by Scene.

Geometry operations must not assume that local coordinates are automatically global RAS coordinates.

### 4.3 Scene Transformations

Scene owns persistent rigid transformations and their composition.

Geometry operates on canonical local coordinates. When an operation requires transformed coordinates, it may use derived computational buffers.

These buffers must not silently replace canonical geometry.

Non-rigid transformations that modify geometric coordinates produce new geometry revisions.

### 4.4 Medical Imaging Interoperability

DICOM data commonly uses LPS coordinates.

The LPS-to-RAS conversion must occur at the Medical Imaging boundary.

Meshes extracted from medical image segmentations must preserve the physical RAS coordinates of the source volume.

For these meshes:

- No automatic recentering is performed.
- Physical coordinates are preserved.
- The initial Object transform is identity.
- Landmarks and measurements must remain spatially consistent with the source volume.

### 4.5 External Mesh Formats

External formats do not necessarily provide reliable coordinate or unit metadata.

STL import must require or resolve explicit unit and coordinate-frame information.

The importer must never silently assume that an external mesh uses millimeters or RAS.

---

## 5. Geometry Revisions

Geometry is immutable after creation.

Any operation that changes canonical geometric data produces a new revision.

### 5.1 Revision Identity

Three identifiers have distinct responsibilities:

| Identifier | Purpose |
|---|---|
| `Object ID` | Stable identity of the Domain Object. |
| `Geometry Revision ID` | Identity of a specific logical geometry revision. |
| `Array Asset ID` | Content-derived identity of a serialized array. |

Object IDs and Geometry Revision IDs use UUIDs.

Array Asset IDs use a cryptographic content hash, such as SHA-256.

A content hash identifies array content, not the logical revision itself.

### 5.2 Revision Model

A geometry revision records:

- Revision ID.
- Source Object ID.
- Parent revision references, when applicable.
- Geometry payload references.
- Operation provenance.
- Validation information.
- Creation metadata.

A revision must remain independently identifiable even when some of its underlying arrays are shared with another revision.

### 5.3 Provenance

Geometry-changing operations should record:

- Operation identifier.
- Input revision identifiers.
- Parameters.
- Algorithm or implementation version.
- Validation profile and version.
- Relevant timestamps.

Provenance must support reproducibility and traceability without unnecessarily duplicating large geometry payloads.

---

## 6. Persistence and Asset Management

### 6.1 Persistence Ownership

Project persistence is governed by `ADR-0009 — Project Persistence Format`.

Geometry Infrastructure defines the logical geometry payload and its serialization requirements. It does not independently establish a competing Project storage layout.

Geometry and medical imaging assets must follow the common Object Data persistence conventions.

A logical organization may follow:

```text
objects/
└── <object_id>/
    ├── object.json
    └── data/
        ├── geometry/
        │   └── revisions/
        └── imaging/
            └── volumes/
```

The authoritative physical layout is defined by ADR-0009.

### 6.2 Array Serialization

Canonical arrays are persisted independently of VTK internal representations.

Each stored array must have sufficient metadata to validate:

- Data type.
- Shape.
- Byte order.
- Content hash.
- Serialization format version.

NumPy loading must always use:

```python
np.load(path, allow_pickle=False)
```

Imported arrays must be treated as untrusted input.

Before use, validate:

- Checksum.
- Data type.
- Dimensions and shape.
- Array size limits.
- Finite coordinate values.
- Face index ranges.
- Expected payload structure.

### 6.3 Deduplication

Deduplication occurs at the array asset level.

Two revisions may reference the same vertex or face asset when its content is identical.

For example, a revision that modifies only vertices may reuse the previous face array.

Deduplication must not compromise revision identity or provenance.

### 6.4 Asset Lifecycle

Persistent assets may be removed only when no valid reference remains.

Garbage collection must account for:

- Project objects.
- Geometry revisions.
- Undo/redo history.
- Active operations.
- Other persistent references.

Regenerable caches are managed separately from persistent Project assets.

### 6.5 Schema Versioning and Migrations

Persisted geometry data must include a schema version.

Migrations must:

- Be explicit and versioned.
- Preserve revision identity where applicable.
- Preserve provenance and attributes.
- Validate migrated data.
- Avoid overwriting original data before successful conversion.
- Reject unsupported schema versions.

Migration procedures must be covered by automated tests.

---

## 7. Geometry Validation

Validation determines whether geometry satisfies the requirements of a specific operation.

A mesh suitable for visualization is not necessarily suitable for Boolean operations, manufacturing, or other topology-sensitive processing.

### 7.1 Validation Severity

```python
class ValidationSeverity(Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
```

| Severity | Meaning |
|---|---|
| ERROR | Invalid for the requested operation; blocks commit. |
| WARNING | Potential issue; acceptance depends on the operation's validation policy. |
| INFO | Informational finding; does not block commit. |

### 7.2 Validation Profiles

A `ValidationProfile` defines the rules and tolerances used for a specific operation.

Examples:

- General mesh validation.
- Surface visualization.
- Mesh Boolean operations.
- Manufacturing preparation.

Profiles must be versioned.

There is no universal geometric epsilon. Tolerances must be defined according to the operation and numerical requirements.

Examples include:

- Degenerate triangle area.
- Vertex welding distance.
- Coordinate comparison tolerance.
- Surface intersection tolerance.

### 7.3 Validation Contracts

```python
@dataclass(frozen=True, slots=True)
class ValidationIssue:
    code: str
    severity: ValidationSeverity
    message: str
    affected_elements: tuple[int, ...] = ()
    details: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ValidationResult:
    is_valid: bool
    issues: tuple[ValidationIssue, ...]
    metrics: Mapping[str, float]
    profile_id: str
    profile_version: str
    source_revision_id: UUID
```

The result must identify the source revision and validation profile used.

Metrics may include:

- Vertex count.
- Triangle count.
- Degenerate triangle count.
- Boundary edge count.
- Non-manifold edge count.
- Connected component count.
- Bounding box dimensions.

The presence of warnings does not automatically imply rejection. Application policies determine whether warnings are acceptable for a particular operation.

### 7.4 Validation and Commit

Application commands must verify validation results before committing geometry changes.

An operation cannot commit a result containing blocking errors.

Validation must be repeated when necessary if the result or its relevant assumptions have changed.

---

## 8. Memory Management and NumPy Interoperability

NumPy is the primary array representation for the initial geometry implementation.

### 8.1 Array Ownership

Canonical arrays must have controlled ownership and predictable lifetimes.

Public APIs must not expose writable access to canonical buffers.

Derived computational arrays may be allocated for temporary processing.

The implementation must distinguish:

- Canonical geometry memory.
- Temporary working memory.
- Undo/redo history.
- Persistent Project assets.
- Regenerable caches.

### 8.2 Dtype Policy

Initial supported coordinate dtypes:

- `float32`
- `float64`

Initial supported face index dtypes:

- `uint32`
- `uint64`

Index dtype must be selected explicitly during import or mesh creation according to vertex count and supported index limits.

Operations must not silently promote index types.

### 8.3 Memory Optimization

Memory optimization must preserve canonical data integrity.

Preferred techniques include:

- Avoiding unnecessary copies.
- Reusing immutable arrays.
- Array-level deduplication.
- Explicit memory ownership.
- Controlled temporary allocations.
- Lazy loading where appropriate.

Zero-copy behavior must never be assumed without verifying ownership and lifetime guarantees.

---

## 9. Geometry Processing

Geometry processing operates on immutable input revisions and produces new candidate revisions.

Processing implementations must not mutate canonical input arrays.

### 9.1 Operation Contract

Geometry operations should follow a structured contract:

```python
class GeometryOperation(Protocol):
    def execute(
        self,
        inputs: GeometrySnapshot,
        parameters: Mapping[str, object],
        cancel_token: CancelToken,
    ) -> GeometryOperationResult: ...
```

The exact operation interfaces may specialize this contract when required.

### 9.2 Initial Processing Scope

The initial Geometry Foundation includes:

- Mesh construction.
- Structural validation.
- Basic mesh statistics.
- STL import and export.
- Internal geometry persistence.
- VTK interoperability.
- Scene transform integration.

Advanced operations remain outside the initial implementation scope.

### 9.3 STL Import and Export

STL is the initial external mesh interchange format.

Import must:

- Validate file readability.
- Resolve units and coordinate frame.
- Validate numeric values.
- Validate triangle indices and degeneracies.
- Preserve source geometry where possible.
- Return structured import diagnostics.

Export must:

- Require explicit output units.
- Apply the requested coordinate transformation explicitly.
- Report conversion or precision limitations.
- Avoid silently changing canonical geometry.

### 9.4 Vertex Welding

Vertex welding is disabled by default.

Welding must be an explicit operation with a user- or operation-defined tolerance.

Its result must include a structured report containing:

- Welding tolerance.
- Original and resulting vertex counts.
- Number of merged vertices.
- Topological changes.
- Degenerate elements introduced or removed.
- Validation findings.

Import must not silently weld STL vertices.

### 9.5 Boolean Operations

Production mesh Boolean operations are outside the initial Geometry Foundation.

An early technical evaluation must compare:

1. Surface mesh Boolean algorithms.
2. Volumetric alternatives based on segmentation or labelmap editing followed by surface extraction.

The evaluation must consider:

- Geometric accuracy.
- Topological robustness.
- Runtime.
- Peak memory.
- Sensitivity to mesh defects.
- Resolution and anisotropy limitations of volumetric methods.

No production backend should be selected before this evaluation.

---

## 10. Backend Architecture

VTK is the initial geometry processing and visualization integration backend.

The canonical geometry model remains independent of VTK.

### 10.1 Initial Strategy

The first implementation uses direct infrastructure adapters.

A generic backend registry is not required while only one backend is implemented.

A registry may be introduced when a second concrete backend creates a demonstrated need for dynamic selection or capability discovery.

### 10.2 Backend Requirements

Backend adapters must:

- Accept canonical geometry or immutable derived inputs.
- Respect coordinate conventions.
- Document thread-safety constraints.
- Define memory ownership and buffer lifetime.
- Return structured results.
- Avoid modifying canonical input arrays.
- Report unsupported operations explicitly.

An operation must not silently switch backends when the selected implementation fails.

---

## 11. VTK Interoperability

VTK is used for geometry processing and integration with the Visualization Infrastructure.

VTK-specific objects must remain outside Domain contracts.

### 11.1 NumPy-to-VTK Conversion

Vertex arrays may use shared memory through `numpy_to_vtk(deep=False)` when dtype, contiguity, and lifetime requirements are satisfied.

The NumPy owner must remain alive for the entire lifetime of the VTK object referencing its memory.

Face arrays stored canonically as `(N, 3)` do not directly match the modern `vtkCellArray` connectivity representation.

Conversion to VTK offsets and connectivity arrays is expected.

For large meshes, this conversion may require substantial additional memory and must be benchmarked.

Canonical face arrays must never be stored in VTK-specific connectivity layout.

### 11.2 Conversion Policy

Adapters must:

- Validate input arrays before conversion.
- Preserve coordinate values and topology.
- Define ownership explicitly.
- Avoid unnecessary copies.
- Report unsupported dtypes or layouts.
- Release temporary buffers deterministically.

### 11.3 Visualization Boundary

Geometry Infrastructure does not own:

- `VTKActorFactory`.
- `ActorRegistry`.
- `VTKSceneRenderer`.
- `SceneBridge`.
- Viewport state.
- Picking interactions.

These responsibilities belong to the Visualization Infrastructure and Application layers.

Geometry may provide data required by visualization adapters but must not depend on rendering components.

---

## 12. Spatial Queries

Basic spatial operations may be implemented within Geometry Infrastructure when they are required by concrete workflows.

Potential operations include:

- Bounding box calculation.
- Surface area.
- Volume estimation where mathematically valid.
- Nearest-point queries.
- Point-to-surface distance.
- Triangle intersection queries.

Advanced spatial indexing and query systems are deferred until required by actual clinical workflows.

Spatial query results must use explicit coordinate conventions and units.

---

## 13. Asynchronous Execution and Consistency

Geometry processing may be computationally expensive and must support asynchronous execution through the Application TaskManager.

### 13.1 Execution Model

The execution flow is:

```text
Application Command
       |
       v
Create Immutable Snapshot
       |
       v
TaskManager
       |
       v
Geometry Operation
       |
       v
Candidate Result
       |
       v
Validation
       |
       v
Application Commit Check
       |
       v
Command Commit
```

### 13.2 Worker Isolation

Workers receive immutable computation snapshots.

Workers must not:

- Modify Project state.
- Modify Scene state.
- Change Object lifecycle.
- Mutate canonical geometry.
- Access UI widgets.
- Commit application commands.

All persistent state changes occur through Application commands on the application thread, following `ADR-0011 — Threading and Task Execution`.

### 13.3 Cancellation

Long-running operations must support cooperative cancellation.

```python
class CancelToken(Protocol):
    @property
    def is_cancelled(self) -> bool: ...

    def raise_if_cancelled(self) -> None: ...
```

Operations must check cancellation at appropriate execution boundaries.

Cancellation must not leave partially committed geometry or inconsistent persistent state.

### 13.4 Structured Operation Results

```python
class GeometryOperationStatus(Enum):
    SUCCESS = "success"
    CANCELLED = "cancelled"
    FAILED = "failed"
    INVALID_RESULT = "invalid_result"
    CONFLICT = "conflict"


@dataclass(frozen=True, slots=True)
class GeometryOperationResult:
    status: GeometryOperationStatus
    revision: GeometryRevision | None
    validation: ValidationResult | None
    message: str | None = None
    diagnostics: Mapping[str, object] = field(default_factory=dict)
```

The result must distinguish successful execution from cancellation, processing failure, invalid output, and commit conflict.

### 13.5 Stale Result Policy

The default policy is **reject stale results**.

Before commit, Application must verify that all relevant source Object IDs and revision IDs still match the operation snapshot.

If any source revision has changed:

- The result is rejected.
- No persistent state is modified.
- The conflict is reported.
- A new operation must be initiated using current inputs.

Automatic reprocessing is not performed by Geometry Infrastructure.

### 13.6 Cleanup and Resource Lifecycle

Temporary resources must be released deterministically after:

- Success.
- Cancellation.
- Processing failure.
- Invalid output.
- Commit conflict.

TaskManager owns task lifecycle and cancellation coordination.

Application owns commit decisions and transaction consistency.

---

## 14. Performance and Benchmarking

Geometry performance must be evaluated using representative clinical datasets and documented hardware.

Initial benchmarks should include:

- 1 million triangles.
- 5 million triangles.

Measurements must include:

- Import and load time.
- Structural validation time.
- NumPy-to-VTK conversion time.
- Peak memory consumption.
- Processing overhead.
- Temporary allocation costs.

### 14.1 Provisional Engineering Targets

The following are initial engineering targets, not validated requirements or clinical guarantees.

| Operation | Provisional Target |
|---|---:|
| Load 1M triangles | < 3 s |
| Structural validation, 1M triangles | < 5 s |
| NumPy-to-VTK conversion, 1M triangles | < 3 s |
| Load 5M triangles | < 15 s |
| Peak memory during read/validation | < 2.5× canonical payload |

Targets must be evaluated on a defined reference machine.

Benchmark results must record hardware, software versions, dataset characteristics, and measurement methodology.

Targets may be revised based on actual measurements.

---

## 15. Security and Clinical Data Protection

Patient-derived geometry is potentially identifiable.

Facial surfaces reconstructed from CT, photogrammetry, or surface scans may retain identifiable characteristics even after metadata removal.

Geometry assets must receive the same protection as other clinical Project data.

Requirements include:

- Secure Project storage.
- Controlled access.
- Export-aware handling.
- Explicit de-identification procedures before sharing.
- Validation of imported files as untrusted input.
- Safe deserialization without executable object loading.

Metadata removal alone must not be treated as sufficient anonymization of facial geometry.

---

## 16. Dependencies and Licensing

Geometry dependencies must be reviewed before inclusion and distribution.

Potential dependencies include:

| Dependency | Primary Role | License Consideration |
|---|---|---|
| NumPy | Array representation | BSD-3-Clause |
| SciPy | Numerical algorithms | BSD-3-Clause |
| VTK | Geometry processing and visualization | BSD-3-Clause; review bundled components and dependencies |
| Trimesh | Mesh processing and file I/O | MIT |
| Open3D | Advanced geometry processing | MIT |
| CGAL | Computational geometry | GPL or commercial licensing, depending on edition and package |
| Open CASCADE | CAD and solid geometry | LGPL-2.1 with applicable exceptions and component-specific conditions |

CranioZ is distributed under **AGPL-3.0-or-later**.

Each dependency review must record:

- Package and version.
- License.
- Relevant components.
- Linking and distribution model.
- Applicable obligations.
- Compatibility assessment.

License compatibility must be reviewed for the exact package versions and distribution configuration. The table is an initial reference, not a legal determination.

Optional dependencies must only be introduced when justified by a concrete capability.

---

## 17. Initial Implementation Scope

### Phase 1 — Geometry Foundation

Implement:

- Canonical triangular Mesh model.
- Geometry coordinate-frame contract.
- Immutable geometry revisions.
- Structural validation.
- NumPy array ownership.
- Basic geometry statistics.

### Phase 2 — Persistence and Interoperability

Implement:

- Geometry asset serialization.
- Revision persistence.
- Content-based array deduplication.
- Schema versioning.
- STL import and export.
- VTK conversion adapters.

### Phase 3 — Application Integration

Implement:

- Geometry commands.
- Application services.
- TaskManager integration.
- Cancellation.
- Structured operation results.
- Validation and stale-result checks.
- Scene transform integration.

### Phase 4 — Evaluation and Optimization

Evaluate:

- Large-mesh performance.
- Peak memory.
- VTK conversion overhead.
- Advanced spatial queries.
- Mesh Boolean alternatives.
- Volumetric Boolean alternatives.

Production Boolean operations remain outside the initial implementation scope until the evaluation supports a concrete implementation decision.

---

## 18. Testing Strategy

Testing must cover data integrity, numerical behavior, persistence, interoperability, and execution consistency.

### 18.1 Geometry Fixtures

Maintain representative test meshes:

- Cube.
- Sphere.
- Torus.
- Open surface.
- Mesh with holes.
- Non-manifold mesh.
- Degenerate triangles.
- Disconnected components.

### 18.2 Domain Tests

Verify:

- Mesh invariants.
- Supported dtypes.
- Invalid index rejection.
- Finite coordinate enforcement.
- Attribute association and shape.
- Revision identity.
- Array immutability.
- Coordinate-frame behavior.

### 18.3 Persistence Tests

Verify:

- Serialization and loading.
- Checksum integrity.
- Array deduplication.
- Schema migration.
- Unsupported version rejection.
- Corrupt file handling.
- Invalid dtype and shape rejection.
- Safe loading with `allow_pickle=False`.

### 18.4 Interoperability Tests

Verify:

- NumPy-to-VTK conversion.
- Buffer ownership and lifetime.
- Face connectivity conversion.
- Coordinate preservation.
- Round-trip integrity.
- Explicit numerical tolerances.

Bitwise equality must not be required when a format or dtype conversion introduces legitimate numerical differences.

### 18.5 Application and Concurrency Tests

Verify:

- Cancellation.
- Failure cleanup.
- Invalid result rejection.
- Stale result rejection.
- No worker-side Project or Scene mutation.
- Transactional commit.
- Undo/redo behavior.
- Concurrent reads of immutable geometry.

### 18.6 Performance Tests

Benchmark 1M and 5M triangle meshes.

Record:

- Runtime.
- Peak memory.
- Conversion overhead.
- Validation costs.
- Persistent storage size.
- Temporary allocation behavior.

---

## 19. Package Structure

The initial package organization is:

```text
src/cranioz/
├── domain/
│   └── geometry/
│       ├── mesh.py
│       ├── attributes.py
│       ├── coordinate_frame.py
│       ├── revision.py
│       └── validation.py
│
├── application/
│   └── geometry/
│       ├── commands/
│       ├── services/
│       └── results.py
│
└── infrastructure/
    └── geometry/
        ├── io/
        │   └── stl.py
        ├── persistence/
        ├── validation/
        ├── adapters/
        │   └── vtk/
        └── processing/
```

This structure is an initial organizational contract. Additional modules should be introduced only when their responsibilities justify them.

---

## 20. Related Documentation

Geometry Infrastructure must remain consistent with:

- `objects.md` — Object identity, Data, Semantic, Components, and Capabilities.
- `scene.md` — Scene membership, hierarchy, coordinate systems, and transformations.
- `ADR-0009 — Project Persistence Format` — Project storage layout, serialization, and persistence lifecycle.
- `ADR-0011 — Threading and Task Execution` — Worker isolation, task lifecycle, and application-thread commits.
- Medical Imaging Infrastructure documentation — Image coordinate conventions, segmentation, and physical-space interoperability.
- Visualization Infrastructure documentation — Rendering adapters, VTK scene integration, and viewport responsibilities.

These documents define complementary responsibilities. Geometry Infrastructure must not duplicate or override their contracts.