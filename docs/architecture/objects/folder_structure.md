The architecture of Objects can be summarized as follows:

        domain/
        │
        ├── objects/
        │       Object
        │
        ├── datatypes/
        │       Mesh
        │       Volume
        │       Image2D
        │       Curve
        │       Point
        │       PointCloud
        │       ROI
        │
        ├── components/
        │       Transform
        │       Render
        │       Anatomical
        │       Landmark
        │       Image
        │       Volume
        │       Planning
        │
        ├── semantics/
        │       SemanticRegistry
        │       SemanticDefinition
        │
        ├── capabilities/
        │       CapabilityRegistry
        │       CapabilityResolver
        │       CapabilityDefinition
        │
        ├── relationships/
        │       RelationshipGraph
        │       Relationship
        │
        └── object_system/
                ObjectRegistry
                ObjectFactory
                ObjectRepository
                ObjectTypeRegistry


