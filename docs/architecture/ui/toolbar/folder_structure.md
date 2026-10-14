    src/cranioz/
    │
    ├── modules/
    │   ├── base/                       # Base implementations
    │   │   ├── __init__.py
    │   │   ├── base_tool.py
    │   │   ├── base_command.py
    │   │   └── base_service.py
    │   │
    │   ├── contracts/                  # Pure interfaces
    │   │   ├── __init__.py
    │   │   ├── tool.py                 # ABC Tool
    │   │   ├── command.py              # ABC Command
    │   │   ├── service.py              # ABC Service
    │   │   └── capability.py           # ABC Capability
    │   │
    │   └── ...                         # Módulos funcionais (osteotomy, mpr, ...)
    │
    ├── tools/
    │   ├── __init__.py
    │   ├── registry.py                 # ToolRegistry
    │   ├── specification.py            # ToolSpec, ToolbarSpec, GroupSpec
    │   │
    │   ├── selection/
    │   │   ├── __init__.py
    │   │   ├── select.py
    │   │   └── select_command.py       # Command alongside the Tool (optional)
    │   │
    │   ├── navigation/
    │   │   ├── __init__.py
    │   │   ├── pan.py
    │   │   ├── zoom.py
    │   │   └── rotate.py
    │   │
    │   ├── measurement/
    │   │   ├── __init__.py
    │   │   ├── distance.py
    │   │   ├── angle.py
    │   │   └── area.py
    │   │
    │   ├── imaging/
    │   │   ├── __init__.py
    │   │   ├── window_level.py
    │   │   ├── crosshair.py
    │   │   └── mpr.py
    │   │
    │   ├── modeling/
    │   │   ├── __init__.py
    │   │   ├── move.py
    │   │   ├── rotate.py
    │   │   └── scale.py
    │   │
    │   └── clinical/                   # or surgical/, planning/, ...
    │       ├── __init__.py
    │       ├── osteotomy.py
    │       ├── landmark.py
    │       └── ...
    │
    ├── ui/
    │   ├── toolbars/
    │   │   ├── __init__.py
    │   │   ├── base.py                 # Toolbar (widget)
    │   │   ├── item.py                 # ActionItem, ToggleItem, Separator, MenuItem
    │   │   ├── main_toolbar.py
    │   │   ├── editor_toolbar.py
    │   │   └── contextual_toolbar.py
    │   │
    │   └── menus/
    │       └── ...
    │
    └── app/
        ├── bootstrap.py                # Mounts the registry
        └── workspace.py