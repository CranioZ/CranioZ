# Datatypes

## 1. Overview

A **Datatype** defines the fundamental structure of the data manipulated by CranioZ.

It answers the question:

> **How is this data represented?**

A Datatype does not, by itself, define the clinical meaning of the data.

For example, a triangular surface loaded from an STL file is a **Mesh**. It contains vertices, faces, normals, and other geometric information, but the `Mesh` Datatype does not know whether that surface represents a mandible, maxilla, tooth, osteosynthesis plate, or surgical guide.

This interpretation is assigned through a **Semantic Type**.

The architecture therefore separates:

```text
Object
├── Datatype
├── Semantic Type
├── Components
├── Capabilities
└── Relationships
```

Each concept has a specific responsibility:

```text
Datatype      → how the data is structured
Semantic      → what the data represents
Components    → what the object contains
Capabilities  → what the object can do
Relationships → how it relates to other objects
```

This separation allows Datatypes to remain generic and reusable, while clinical semantics determine how each Object is used by CranioZ.

---

# 2. Datatype × Semantic Type

A **Datatype** represents the structure of the data.

A **Semantic Type** represents the meaning assigned to that data.

For example:

```text
Mesh
└── Semantic Type: Anatomy.Bone.Mandible
```

or:

```text
Image2D
└── Semantic Type: Imaging.PanoramicRadiograph
```

or:

```text
Mesh
└── Semantic Type: Implant.OsteosynthesisPlate
```

Different Objects can therefore share the same Datatype:

```text
Mesh
├── Anatomy.Bone.Mandible
├── Anatomy.Bone.Maxilla
├── Anatomy.Tooth
├── Anatomy.Face
├── Implant.Dental
├── Implant.OsteosynthesisPlate
└── Surgical.SurgicalGuide
```

The Datatype remains `Mesh` in all of these cases.

What changes is the semantic classification assigned to the Object and, consequently, the Components and Capabilities that may be associated with or made available to it.

---

# 3. Objects and Datatypes

The Datatype is not the Object.

An Object is the entity manipulated by CranioZ and may use a Datatype as its underlying data representation.

Conceptually:

```text
Object
├── id
├── name
├── datatype
├── semantic_type
├── components
├── state
└── relationships
```

For example:

```text
Object
├── Datatype: Mesh
├── Semantic Type: Anatomy.Bone.Mandible
└── Components:
    └── Transform
```

In this case, `Mesh` defines the geometric structure, while `Mandible` defines the clinical meaning.

This distinction prevents the system from having to create specific classes for every possible combination.

Instead of:

```text
MandibleMesh
OrthognathicMandibleMesh
SegmentedMandibleMesh
MandibleWithLandmarks
MandibleWithImplantPlanning
```

the CranioZ architecture can represent these combinations through composition:

```text
Object
├── Datatype: Mesh
├── Semantic: Mandible
├── Components:
│   ├── Transform
│   └── Landmark
└── Capabilities:
    ├── Osteotomy
    ├── Landmark
    └── OrthognathicMovement
```

---

# 4. Fundamental Datatypes

The fundamental Datatypes represent generic data structures used throughout the system.

They should remain independent of clinical semantics whenever possible.

The main Datatypes currently planned are:

```text
Mesh
Volume
Image2D
Curve
Point
PointCloud
ROI
```

Additional Datatypes may be introduced as the system evolves.

---

# 5. Mesh

`Mesh` represents a three-dimensional polygonal geometry.

A Mesh may contain:

* vertices;
* edges;
* faces;
* normals;
* per-vertex attributes*
