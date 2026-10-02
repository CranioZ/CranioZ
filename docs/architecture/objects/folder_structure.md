A arquitetura de Objects pode ser resumida como:

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

O princípio fundamental permanece:
