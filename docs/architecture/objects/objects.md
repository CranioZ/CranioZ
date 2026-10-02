## 1. The Conceptual Model
An Object can be understood through four complementary dimensions:


    Object
    │
    ├── Data
    │     └── What is the data?
    │
    ├── Semantic
    │     └── What does this data represent?
    │
    ├── Components
    │     └── What additional information/structures does it have?
    │
    └── Capabilities
          └── What can be done with this Object?
For example:


    Mandible
    │
    ├── Data
    │     └── Mesh
    │
    ├── Semantic
    │     └── Anatomy.Bone.Mandible
    │
    ├── Components
    │     ├── Transform
    │     ├── LandmarkSet
    │     └── AnatomicalProperties
    │
    └── Capabilities
          ├── Transform
          ├── Measure
          ├── Boolean
          ├── Cut
          ├── Osteotomy
          └── Landmark
This is much better than creating classes such as:


    MandibleMesh
    MandibleSurgicalMesh
    MandibleOrthognathicMesh
    MandibleSegmentedMesh
    MandibleOsteotomyMesh

## 2. Data: the physical representation
I would rename the previous term Data Type to simply Data or Data Representation.

The question is:

"What data does this Object contain or represent?"

Examples:


    Mesh
    Volume
    Image
    ImageSeries
    Point
    Curve
    Surface
    Region

This has no clinical semantics.

A Mesh can be:

    Mandible
    Maxilla
    Tooth
    Implant
    Plate
    Scan
    SurgicalGuide
Therefore:


    Mesh ≠ Mandible
and:

    Mandible ≠ Mesh

The mandible may have a Mesh as its geometric representation.

## 3. Semantic: the meaning of the Object
The second dimension is semantics.

The question is:

"What does this data represent?"

For example:

    Anatomy.Bone.Mandible
    Anatomy.Bone.Maxilla
    Anatomy.Tooth
    Anatomy.Zygoma
    
    Implant.Dental
    Implant.Facial
    
    Surgical.Osteotomy
    Surgical.Guide
    Surgical.Splint
    
    Imaging.CT
    Imaging.CBCT
    Imaging.Panoramic
This resolves an important issue:


    data:
        Mesh
    
    semantic:
        Anatomy.Bone.Mandible
The same Mesh could be:


    data:
        Mesh
    
    semantic:
        Scan.Intraoral
or:


    data:
        Mesh

    semantic:
        Implant.Facial
The geometry does not need to know these semantics.

## 4. Components
Here I would preserve an important part of the previous architecture, but make a distinction.

A Component represents additional information or structure associated with the Object.

Example:

    Mandible
    │
    ├── Mesh
    ├── Transform
    ├── LandmarkSet
    └── AnatomicalProperties
Or:

    PanoramicRadiograph
    │
    ├── Image
    ├── Transform2D
    └── ImageProperties
Or:


    Plate
    │
    ├── Mesh
    ├── Transform
    ├── PlateProperties
    └── MaterialProperties
This is different from Capability.

Component: "What does the Object have?"

Capability: "What can be done with the Object?"

This distinction is extremely useful.

## 5. Capabilities
Here is one of the most interesting ideas from the previous architecture, which I would keep.

A Capability represents an operational capability that can be applied to a given Object.

For example:


    Mandible
        capabilities:
            Transform
            Measure
            Boolean
            Cut
            Osteotomy
            Landmark
While:


    PanoramicRadiograph
        capabilities:
            Transform2D
            WindowLevel
            Crop
            Annotation
            Export
This avoids:

    if object.semantic_type == "Mandible":
        show_osteotomy_tool()

and enables something conceptually closer to:


    Object
        ↓
    CapabilityRegistry
        ↓
    Capabilities
        ↓
    Tools
The Toolbar, context, or module can then ask:

"Which Tools are compatible with the capabilities of this Object?"

## 6. But I would make an important change
I would not place capabilities as a static property simply stored on the Object.

That is, I would avoid thinking of:

python
object.capabilities = [
    "Transform",
    "Measure",
    "Osteotomy"
]
as being the definitive source of the architecture.

The Capability should be resolved by the system from the Object, its semantics, components, context, and, eventually, state.

For example:


    Mandible
        semantic:
            Anatomy.Bone.Mandible

components:

        Mesh
        Transform
        LandmarkSet

            ↓

    CapabilityResolver

            ↓

        Transform
        Measure
        Landmark
        Boolean
        Cut
        Osteotomy

This is more powerful because a Capability can depend on context.

For example:

    Mandible
may have:

    Osteotomy
but a particular osteotomy may require:

    Mesh
    + valid geometry
      + anatomical state

Therefore, a Capability is not just a "label". It can represent a verifiable capability of the system.

## 7. Capability is not Tool
This distinction is also important for the documentation we are writing now.

For example:

    Capability
        Osteotomy
means:

This Object can participate in osteotomy operations.

But the Tools may be:


    Create Osteotomy Plane
    Create BSSO
    Create Le Fort I
    Split Segment
    Move Segment
Therefore:


    Object
        ↓
    Capability
        ↓
    Tool
        ↓
    Command
        ↓
    Domain/Application Service
This chain becomes quite elegant for CranioZ.

## 8. The role of the ObjectRegistry
Here I would make a small correction relative to the previous architecture.

The ObjectRegistry should answer:

"Which Objects exist in this context?"

For example:

    ObjectRegistry
    │
    ├── Object #001
    │     semantic = Anatomy.Bone.Mandible
    │
    ├── Object #002
    │     semantic = Anatomy.Bone.Maxilla
    │
    ├── Object #003
    │     semantic = Anatomy.Tooth
    │
    └── Object #004
          semantic = Imaging.CBCT
It should not be responsible for determining the clinical meaning of the Object.

For that, there is the:

    SemanticRegistry
And to discover what can be done:


    CapabilityRegistry
Thus:


    ObjectRegistry
        "Which objects exist?"
    
    SemanticRegistry
        "What do these objects represent?"
    
    CapabilityRegistry
        "Which capabilities are available?"
    
    ObjectFactory
        "How are these objects created?"
This division remains very good.

## 9. ObjectTypeRegistry
I would also keep the ObjectTypeRegistry, but with a more precise definition.

It answers:

"Which types of Objects does the system know about?"

For example:

    ObjectTypeRegistry
    
        Mesh
        Volume
        Image
        ImageSeries
        Point
        Curve
        Landmark
        Measurement
        Transform
        CoordinateSystem
        Scan
        AnatomicalObject
        SurgicalGuide
        ...
This is different from the SemanticRegistry.

For example:

    Object Type:
        Mesh
    
    Semantic:
        Anatomy.Bone.Mandible

## 10. SceneGraph and RelationshipGraph
The previous architecture also had two structures worth preserving.

SceneGraph

It answers:

    "Where is this Object in the spatial/visual organization of the project?"

For example:

    Scene
    │
    ├── Patient
    │   ├── Maxilla
    │   ├── Mandible
    │   ├── Teeth
    │   └── FacialScan
    │
    └── Planning
        ├── Osteotomy
        ├── Segments
        └── SurgicalGuide
RelationshipGraph

It answers:

    "What is the semantic or dependency relationship between these Objects?"

For example:

    Measurement
        ├── references → Landmark A
        └── references → Landmark B
or:

    Segmentation
        └── derived-from → Volume
or:


    Mesh
        └── representation-of → Mandible
This separation is useful because visual hierarchy is not necessarily a domain relationship.

## 11. A more mature architecture
Combining the previous architecture with the current one, I would arrive at:


                              OBJECT
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                   │
            DATA              SEMANTIC           COMPONENTS
              │                  │                   │
          Mesh                 Mandible           Transform
          Volume               Maxilla            LandmarkSet
          Image                Tooth              Properties
          Point                Implant
          Curve                Scan
          Region               ...
              │                  │
              └──────────────────┼──────────────────┘
                                 │
                                 ↓
                         CAPABILITY RESOLUTION
                                 │
                ┌────────────────┼────────────────┐
                │                │                │
             Measure          Transform        Osteotomy
             Boolean          Landmark          Cut
             Register         Segment           ...
                │                │                │
                └────────────────┼────────────────┘
                                 ↓
                               TOOLS
                                 ↓
                              COMMANDS
                                 ↓
                         DOMAIN / APPLICATION
This preserves the original idea but prevents the Object from becoming a "god object".

## 12. Example: Mandible
I would document the example as follows:


    Object
    │
    ├── id
    │
    ├── data
    │   └── Mesh
    │
    ├── semantic
    │   └── Anatomy.Bone.Mandible
    │
    ├── components
    │   ├── Transform
    │   ├── LandmarkSet
    │   └── AnatomicalProperties
    │
    └── relationships
        ├── representation-of → Mandible
        └── references → ...
And its capabilities would be resolved:


    Mandible
        ↓
    CapabilityResolver
        ↓
    Transform
    Measure
    Boolean
    Cut
    Osteotomy
    Landmark
    Symmetry
We do not need to create:


    MandibleMesh
    MandibleSurgicalMesh
    MandibleOrthognathicMesh

## 13. Example: Panoramic Radiograph

    Object
    │
    ├── id
    │
    ├── data
    │   └── Image
    │
    ├── semantic
    │   └── Imaging.Radiography.Panoramic
    │
    ├── components
    │   ├── Transform2D
    │   └── ImageProperties
    │
    └── relationships
        └── ...
Capabilities:

    Transform2D
    WindowLevel
    Crop
    Annotation
    Measure2D
    Export
    ExternalEditor
    Note that the Object does not need to know that these capabilities correspond to buttons on a Toolbar.