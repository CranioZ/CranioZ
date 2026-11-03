"""VTK adapters for canonical geometry.

These adapters translate between ``cranioz.domain.geometry`` and VTK
objects. They are the only place where geometry couples to VTK.
"""

from cranioz.infrastructure.geometry.adapters.vtk.polydata import (
    mesh_to_polydata,
)

__all__ = ["mesh_to_polydata"]
