src/cranioz/modules/
│
├── __init__.py
│
├── base/
│   ├── __init__.py
│   ├── module.py
│   ├── module_context.py
│   ├── module_manifest.py
│   ├── module_state.py
│   └── lifecycle.py
│
├── contracts/
│   ├── __init__.py
│   ├── command_definition.py
│   ├── tool_definition.py
│   ├── service_definition.py
│   └── capability_definition.py
│
├── registry/
│   ├── __init__.py
│   ├── module_registry.py
│   ├── command_registry.py
│   ├── tool_registry.py
│   ├── service_registry.py
│   └── capability_registry.py
│
├── loader/
│   ├── __init__.py
│   ├── module_loader.py
│   ├── module_host.py
│   ├── module_graph.py
│   ├── dependency_resolver.py
│   ├── load_policy.py
│   └── load_state.py
│
└── builtin/
    │
    ├── patient/
    │   ├── __init__.py
    │   ├── module.py
    │   ├── manifest.py
    │   ├── domain/
    │   ├── commands/
    │   ├── tools/
    │   └── services/
    │
    ├── tomography/
    │   ├── __init__.py
    │   ├── module.py
    │   ├── manifest.py
    │   ├── domain/
    │   ├── commands/
    │   ├── tools/
    │   └── services/
    │
    ├── segmentation/
    │   ├── __init__.py
    │   ├── module.py
    │   ├── manifest.py
    │   ├── domain/
    │   ├── commands/
    │   ├── tools/
    │   └── services/
    │
    ├── alignment/
    │   ├── __init__.py
    │   ├── module.py
    │   ├── manifest.py
    │   ├── domain/
    │   ├── commands/
    │   ├── tools/
    │   └── services/
    │
    ├── osteotomies/
    │   ├── __init__.py
    │   ├── module.py
    │   ├── manifest.py
    │   ├── domain/
    │   ├── commands/
    │   ├── tools/
    │   └── services/
    │
    └── guide_builder/
        ├── __init__.py
        ├── module.py
        ├── manifest.py
        ├── domain/
        ├── commands/
        ├── tools/
        └── services/