"""CoordinateFrame — the local coordinate frame a mesh declares.

CranioZ uses RAS as its global coordinate convention (Right,
Anterior, Superior; millimetres). A ``Mesh`` declares its own local
frame; the relationship between the local frame and the global RAS
frame must be explicit.

The frame is a value object. It carries:

- The name of the frame (a stable identifier, e.g. "RAS" or a
  user-defined label).
- The origin in millimetres.
- The three basis vectors, each expressed in the parent frame.

The initial implementation only needs the identity frame (origin at
0, basis aligned with RAS) for STL validation. Rotated or translated
frames will be introduced when the Object System and Scene
transformations are implemented.

See the ``Geometry Infrastructure`` architecture document, §4.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


class CoordinateFrameError(ValueError):
    """Raised when a CoordinateFrame violates its invariants."""


@dataclass(frozen=True, slots=True)
class CoordinateFrame:
    """A local coordinate frame declared by a mesh.

    All units are millimetres. The frame is defined by an origin and
    three basis vectors, each expressed in the parent frame (which is
    RAS by convention for the initial implementation).

    The basis vectors must form an orthonormal right-handed basis.
    """

    #: Stable identifier, e.g. "RAS" for the global frame or a
    #: user-defined label for a local frame.
    name: str

    #: Origin in the parent frame, in millimetres.
    origin: tuple[float, float, float] = (0.0, 0.0, 0.0)

    #: Basis vectors (x, y, z), each expressed in the parent frame.
    #: Defaults to the identity basis.
    x_axis: tuple[float, float, float] = (1.0, 0.0, 0.0)
    y_axis: tuple[float, float, float] = (0.0, 1.0, 0.0)
    z_axis: tuple[float, float, float] = (0.0, 0.0, 1.0)

    def __post_init__(self) -> None:
        if not self.name:
            raise CoordinateFrameError("CoordinateFrame.name must not be empty")
        if any(not _is_finite(v) for v in self.origin):
            raise CoordinateFrameError(f"CoordinateFrame.origin must be finite, got {self.origin}")

    @classmethod
    def identity(cls, name: str = "RAS") -> CoordinateFrame:
        """Return the identity frame (origin at 0, basis aligned)."""
        return cls(name=name)

    def __repr__(self) -> str:
        return f"CoordinateFrame(name={self.name!r}, origin={self.origin!r})"


def _is_finite(value: float) -> bool:
    return math.isfinite(value)
