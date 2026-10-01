src/cranioz/ui/
│
├── __init__.py
├── py.typed
├── main_window.py                          # MainWindow (QMainWindow shell)
│
├── workspace/
│   ├── __init__.py
│   │
│   ├── workspace.py                        # Workspace
│   ├── area.py                             # Area
│   ├── area_manager.py                     # AreaManager
│   │
│   ├── placement.py                        # Placement (enum)
│   ├── area_spec.py                        # AreaSpec
│   ├── module_ui_spec.py                   # ModuleUISpec
│   │
│   ├── layout_tree.py                      # LayoutTree, Leaf, Split, SplitDirection
│   ├── layout_builder.py                   # LayoutBuilder
│   ├── layout_renderer.py                  # LayoutRenderer
│   ├── layout_io.py                        # LayoutIO
│   │
│   ├── region.py                           # Region
│   ├── overlay.py                          # Overlay (ABC)
│   ├── overlay_manager.py                  # OverlayManager
│   └── top_overlay.py                      # TopOverlay
│
└── editors/
    ├── __init__.py
    │
    ├── base_editor.py                      # Editor (ABC)
    ├── editor_host.py                      # EditorHost
    ├── editor_registry.py                  # EditorRegistry
    │
    ├── viewport_3d/                        # complex Editor → subpackage
    │   ├── __init__.py
    │   ├── editor.py                       # Viewport3DEditor
    │   ├── toolbar.py                      # own toolbar
    │   └── tools/
    │       ├── __init__.py
    │       ├── rotate_tool.py
    │       ├── pan_tool.py
    │       └── zoom_tool.py
    │
    └── mpr_viewer/                         # complex Editor → subpackage
        ├── __init__.py
        ├── editor.py                       # MPRViewerEditor
        ├── toolbar.py
        └── tools/
            ├── __init__.py
            ├── window_level_tool.py
            └── reslice_tool.py