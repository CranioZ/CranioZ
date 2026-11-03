"""Geometry domain — canonical representation of geometric data.

This package defines the geometry contracts independently of VTK, Qt,
file formats, and other infrastructure dependencies.

Public API:

- ``CoordinateFrame`` — the local coordinate frame a mesh declares.
- ``Mesh`` — the canonical triangular surface mesh.
- ``ValidationIssue``, ``ValidationResult``, ``ValidationSeverity``
  — structured validation findings.

See the ``Geometry Infrastructure`` architecture document, §3.
"""

from cranioz.domain.geometry.coordinate_frame import CoordinateFrame
from cranioz.domain.geometry.mesh import Mesh
from cranioz.domain.geometry.validation import (
    ValidationIssue,
    ValidationResult,
    ValidationSeverity,
)

__all__ = [
    "CoordinateFrame",
    "Mesh",
    "ValidationIssue",
    "ValidationResult",
    "ValidationSeverity",
]
