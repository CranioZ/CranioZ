"""Workspace structure segments.

The Top Bar of the Workspace is composed of three segments, each a
plain presentation widget with no knowledge of Overlay, Region or
Placement. The TopOverlay holds them; the MainWindow wires them to
application handlers.

Public API:

- ``HomeSegment`` — ☰ / ⋮ / ⌂ buttons; the ⋮ opens a context menu
  with project actions.
- ``ModulesSegment`` — module buttons loaded from the active Flow
  (placeholder: "Tomografia" until Phase 5 delivers WorkflowEngine).
- ``ExtrasSegment`` — ⋮ (settings menu) and two panel toggles.
"""

from cranioz.ui.workspace.structure.extras_segment import ExtrasSegment
from cranioz.ui.workspace.structure.home_segment import HomeSegment
from cranioz.ui.workspace.structure.modules_segment import ModulesSegment

__all__ = [
    "ExtrasSegment",
    "HomeSegment",
    "ModulesSegment",
]
