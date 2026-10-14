src/cranioz/
│
├── ui/
│   │
│   ├── workspace/
│   │   ├── __init__.py
│   │   ├── workspace.py
│   │   ├── area.py
│   │   ├── area_manager.py
│   │   ├── layout.py
│   │   ├── placement.py
│   │   ├── editor_host.py
│   │   ├── layout_tree.py
│   │   ├── layout_builder.py
│   │   └── layout_renderer.py
│   │
│   └── editors/
│       ├── __init__.py
│       ├── base_editor.py
│       ├── editor_registry.py
│       ├── editor_context.py
│       ├── editor_manifest.py
│       │
│       ├── central/
│       │   ├── __init__.py
│       │   ├── patient_editor/
│       │   ├── mpr_viewer_editor/
│       │   ├── cpr_viewer_editor/
│       │   ├── segmentation_editor/
│       │   ├── registration_editor/
│       │   ├── object_alignment_editor/
│       │   ├── osteotomy_editor/
│       │   └── guide_builder_editor/
│       │
│       ├── right/
│       │   ├── __init__.py
│       │   ├── segmentation_panel_editor/
│       │   ├── registration_panel_editor/
│       │   ├── object_alignment_panel_editor/
│       │   ├── object_properties_panel_editor/
│       │   ├── object_material_panel_editor/
│       │   ├── object_position_panel_editor/
│       │   ├── orthognathic_movement_panel_editor/
│       │   └── scene_info_panel_editor/
│       │
│       ├── left/
│       │   ├── __init__.py
│       │   ├── object_list_editor/
│       │   ├── mask_list_editor/
│       │   ├── landmark_list_editor/
│       │   └── preset_list_editor/
│       │
│       └── bottom/
│           ├── __init__.py
│           ├── console_editor/
│           ├── history_editor/
│           ├── ai_editor/
│           ├── animation_editor/
│           ├── node_editor/
│           └── task_monitor_editor/
│
└── modules/
    ├── orthognathic/
    ├── segmentation/
    ├── cephalometry/
    └── ...




### Internal structure of each editor
<editor_name>/
├── __init__.py
├── editor.py          → implementação
├── manifest.py        → declaração (id, title, capabilities, toolbar)
├── toolbar.py         → especificação da Toolbar (opcional)
├── content/           → conteúdo separável (opcional)
├── overlays/          → overlays (opcional)
└── tools/             → Tools específicas do Editor (opcional)