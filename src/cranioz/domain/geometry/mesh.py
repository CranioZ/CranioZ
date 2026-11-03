"""Mesh — the canonical representation of a triangular surface mesh.

A ``Mesh`` is immutable. It carries:

- Vertex coordinates, shape ``(N, 3)``, dtype ``float32`` or
  ``float64``.
- Face indices, shape ``(M, 3)``, dtype ``uint32`` or ``uint64``.
- An explicit ``CoordinateFrame``.

The arrays are read-only after construction. The public interface
never exposes a writable buffer: array immutability is enforced by
``setflags(write=False)`` at construction.

Mesh does NOT carry identity (that belongs to the Object System),
revision history, persistence metadata, or attributes. Those are
introduced in later phases of the Geometry Infrastructure document.

See the ``Geometry Infrastructure`` architecture document, §3.1.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from cranioz.domain.geometry.coordinate_frame import CoordinateFrame

#: Supported vertex coordinate dtypes.
_VERTEX_DTYPES = (np.dtype(np.float32), np.dtype(np.float64))

#: Supported face index dtypes.
_FACE_DTYPES = (np.dtype(np.uint32), np.dtype(np.uint64))


class MeshError(ValueError):
    """Raised when a Mesh violates its structural invariants."""


@dataclass(frozen=True, slots=True)
class Mesh:
    """A canonical triangular surface mesh.

    Construction validates the structural invariants (shape, dtype,
    finite coordinates, valid face indices) and marks the arrays as
    read-only.

    Raises:
        MeshError: if any invariant is violated.
    """

    vertices: np.ndarray
    faces: np.ndarray
    coordinate_frame: CoordinateFrame

    def __post_init__(self) -> None:
        self._validate_vertices()
        self._validate_faces()
        self._freeze_arrays()

    # ----- Validation ------------------------------------------------

    def _validate_vertices(self) -> None:
        v = self.vertices
        if not isinstance(v, np.ndarray):
            raise MeshError(f"Mesh.vertices must be a numpy.ndarray, got {type(v).__name__}")
        if v.ndim != 2 or v.shape[1] != 3:
            raise MeshError(f"Mesh.vertices must have shape (N, 3), got {v.shape}")
        if v.dtype not in _VERTEX_DTYPES:
            raise MeshError(
                f"Mesh.vertices dtype must be one of "
                f"{[str(d) for d in _VERTEX_DTYPES]}, got {v.dtype}"
            )
        if v.shape[0] == 0:
            raise MeshError("Mesh.vertices must contain at least one vertex")
        if not np.all(np.isfinite(v)):
            raise MeshError("Mesh.vertices must be finite")

    def _validate_faces(self) -> None:
        f = self.faces
        if not isinstance(f, np.ndarray):
            raise MeshError(f"Mesh.faces must be a numpy.ndarray, got {type(f).__name__}")
        if f.ndim != 2 or f.shape[1] != 3:
            raise MeshError(f"Mesh.faces must have shape (M, 3), got {f.shape}")
        if f.dtype not in _FACE_DTYPES:
            raise MeshError(
                f"Mesh.faces dtype must be one of {[str(d) for d in _FACE_DTYPES]}, got {f.dtype}"
            )
        if f.shape[0] == 0:
            raise MeshError("Mesh.faces must contain at least one face")

        vertex_count = self.vertices.shape[0]
        if int(f.max()) >= vertex_count:
            raise MeshError(
                f"Mesh.faces reference vertex index {int(f.max())} but "
                f"only {vertex_count} vertices exist"
            )

    def _freeze_arrays(self) -> None:
        self.vertices.setflags(write=False)
        self.faces.setflags(write=False)

    # ----- Convenience ----------------------------------------------

    @property
    def vertex_count(self) -> int:
        return int(self.vertices.shape[0])

    @property
    def face_count(self) -> int:
        return int(self.faces.shape[0])

    def __repr__(self) -> str:
        return (
            f"Mesh(vertices={self.vertex_count}, "
            f"faces={self.face_count}, "
            f"vertex_dtype={self.vertices.dtype}, "
            f"face_dtype={self.faces.dtype}, "
            f"frame={self.coordinate_frame.name!r})"
        )
