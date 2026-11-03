"""Geometry infrastructure — I/O, adapters, and processing implementations.

This package provides concrete implementations for the geometry
contracts defined in ``cranioz.domain.geometry``.

Public API:

- ``read_stl``, ``write_stl`` — STL import/export.
- ``mesh_to_polydata`` — ``Mesh`` → ``vtkPolyData`` conversion.

The initial implementation covers the STL subset of Phase 2 of the
``Geometry Infrastructure`` document. Persistence, revisions, and
validation profiles are deferred.

See the ``Geometry Infrastructure`` architecture document, §2.3.
"""

from cranioz.infrastructure.geometry.adapters.vtk.polydata import (
    mesh_to_polydata,
)
from cranioz.infrastructure.geometry.io.stl import read_stl, write_stl

__all__ = [
    "mesh_to_polydata",
    "read_stl",
    "write_stl",
]
