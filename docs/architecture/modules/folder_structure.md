src/cranioz/modules/
│
├── __init__.py
│
├── base/
│   ├── __init__.py
│   ├── module.py              # Module Protocol + ModuleBase
│   ├── module_manifest.py     # ModuleManifest, ModuleDependency
│   ├── module_context.py      # ModuleContext (agregador de dependências)
│   └── module_state.py        # ModuleState (Enum)
│
├── registry/
│   ├── __init__.py
│   └── module_registry.py     # ModuleRegistry Protocol + InMemoryModuleRegistry
│
├── loader/
│   ├── __init__.py
│   ├── module_loader.py       # ModuleLoader Protocol + Impl
│   └── _internal/             # helpers privados do loader
│       ├── __init__.py
│       ├── dependency_graph.py    # grafo + topo sort + cycle detection
│       ├── load_state.py          # estado interno do loader
│       └── rollback.py            # rollback de load/unload
│
├── errors.py                  # ModuleError + subclasses
│
└── builtin/
    ├── __init__.py            # BUILTIN_MANIFESTS
    ├── patient/
    │   ├── __init__.py
    │   ├── module.py
    │   ├── manifest.py
    │   ├── commands/
    │   ├── tools/
    │   ├── services/
    │   └── ui_specs.py
    │
    ├── tomography/
    ├── segmentation/
    ├── alignment/
    ├── cephalometry/         
    ├── osteotomies/
    └── guide_builder/