```
src/cranioz/
├── ui/
│   ├── main_window.py
│   ├── workspace/
│   │   ├── workspace.py
│   │   ├── area.py
│   │   ├── area_manager.py
│   │   ├── placement.py
│   │   ├── area_spec.py
│   │   ├── editor_layout_spec.py
│   │   ├── module_ui_spec.py
│   │   ├── layout_tree.py
│   │   ├── layout_builder.py
│   │   ├── layout_renderer.py
│   │   ├── layout_state.py
│   │   ├── layout_io.py
│   │   ├── region.py
│   │   ├── overlay.py
│   │   ├── overlay_manager.py
│   │   ├── overlay_state.py
│   │   └── structure/
│   │       └── top_bar.py
│   └── editors/
│       ├── base_editor.py
│       ├── editor_registry.py
│       ├── editor_catalog.py
│       ├── viewport_3d/
│       │   ├── editor.py
│       │   └── toolbar.py
│       └── mpr_viewer/
│           ├── editor.py
│           └── toolbar.py
│
└── tools/
    ├── contracts/
    ├── registry.py
    ├── catalog.py
    └── builtin/
        ├── selection/
        ├── navigation/
        ├── measurement/
        └── ...
```