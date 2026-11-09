# ...
_KNOWN_DEBT_FILES: frozenset[str] = frozenset(
    {
        "src/cranioz/ui/workspace/areas/area_widget.py",
        "src/cranioz/ui/workspace/workspace.py",
        "src/cranioz/ui/editors/viewport_3d/presets.py",
    }
)
_DEBT_MAX_LITERALS: dict[str, int] = {
    "src/cranioz/ui/workspace/areas/area_widget.py": 5,
    "src/cranioz/ui/workspace/workspace.py": 3,
    "src/cranioz/ui/editors/viewport_3d/presets.py": 3,
}
# ...
